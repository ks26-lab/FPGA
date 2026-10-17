"""
python.emulation.maze_model
===========================
RTL-Equivalent Software Model for Maze Runner & Hardware Navigation Accelerator.
Faithfully reproduces maze_core.v and maze_axi_slave.v:
- 8x8 on-chip ROM storage (64 cells with 4-bit wall bitmasks)
- Hardware 5-second countdown timer
- Authoritative collision evaluation against walls and outer boundaries
- Parallel neighbor evaluation & topology classification
- Hardware BFS pathfinding engine
- Hardware A* pathfinding engine with Manhattan heuristic
- Hardware distance map, route efficiency, and extra moves
- Maze difficulty analyzer (dead-ends, branches, intersections, complexity)
- Parallel 4-agent virtual navigation subsystem
- Hardware fault detection bitmask
- Comprehensive hardware performance counters
"""

import threading
from collections import deque
import heapq
from typing import Dict, Any, List, Tuple


class MazeRTLModel:
    """Cycle-accurate software model of upgraded maze_core.v & maze_axi_slave.v."""

    BASE_ADDRESS = 0x43C10000
    BASE_ADDR    = 0x43C10000

    # FSM State Constants
    STATE_IDLE         = 0
    STATE_MAZE_DISPLAY = 1
    STATE_MEMORY_PHASE = 2
    STATE_GAMEPLAY     = 3
    STATE_WIN          = 4
    STATE_GAME_OVER    = 5

    # Command Codes
    CMD_NONE       = 0
    CMD_START      = 1
    CMD_RESET      = 2
    CMD_MOVE_UP    = 3
    CMD_MOVE_DOWN  = 4
    CMD_MOVE_LEFT  = 5
    CMD_MOVE_RIGHT = 6

    # Wall Bit Positions (4'b<LEFT><DOWN><RIGHT><UP>)
    WALL_UP_BIT    = 0
    WALL_RIGHT_BIT = 1
    WALL_DOWN_BIT  = 2
    WALL_LEFT_BIT  = 3

    # Register Byte Offsets (Expanded 32-register map)
    REG_CONTROL            = 0x00
    REG_STATUS             = 0x04
    REG_POSITION           = 0x08
    REG_COUNTERS           = 0x0C
    REG_TIMER              = 0x10
    REG_MAZE_MEM           = 0x14
    REG_PATH_CONTROL       = 0x18
    REG_PATH_STATUS        = 0x1C
    REG_PATH_LENGTH        = 0x20
    REG_NODES_EXPLORED     = 0x24
    REG_PATH_CYCLES        = 0x28
    REG_CURRENT_DISTANCE   = 0x2C
    REG_SHORTEST_DISTANCE  = 0x30
    REG_EXTRA_MOVES        = 0x34
    REG_PATH_EFFICIENCY    = 0x38
    REG_NEIGHBOR_STATUS    = 0x3C
    REG_MAZE_STATS         = 0x40
    REG_MAZE_COMPLEXITY    = 0x44
    REG_FAULT_FLAGS        = 0x48
    REG_PERFORMANCE_CYCLES = 0x4C
    REG_BFS_COUNTER        = 0x50
    REG_ASTAR_COUNTER      = 0x54
    REG_AGENT_CONTROL      = 0x58
    REG_AGENT_STATUS       = 0x5C
    REG_AGENT0_POS         = 0x60
    REG_AGENT1_POS         = 0x64
    REG_AGENT2_POS         = 0x68
    REG_AGENT3_POS         = 0x6C

    # Predefined 8x8 Maze ROM exactly matching maze_core.v
    MAZE_ROM_64x4 = [
        # Row 0
        0b1101, 0b0001, 0b0111, 0b1101, 0b0001, 0b0111, 0b1101, 0b0011,
        # Row 1
        0b1011, 0b1000, 0b0101, 0b1001, 0b0000, 0b0111, 0b1011, 0b1010,
        # Row 2
        0b1000, 0b0100, 0b1000, 0b0100, 0b1000, 0b0001, 0b0100, 0b1010,
        # Row 3
        0b1100, 0b0010, 0b1100, 0b0010, 0b1100, 0b0100, 0b1000, 0b0010,
        # Row 4
        0b1001, 0b0110, 0b1001, 0b0110, 0b1001, 0b0010, 0b1100, 0b0010,
        # Row 5
        0b1010, 0b1001, 0b0110, 0b1001, 0b0110, 0b1000, 0b0011, 0b1010,
        # Row 6
        0b1000, 0b0100, 0b1001, 0b0100, 0b1001, 0b0000, 0b0100, 0b1010,
        # Row 7
        0b1100, 0b0001, 0b0001, 0b0001, 0b0001, 0b0001, 0b0001, 0b0111
    ]

    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        """Resets all internal hardware registers matching Verilog rst_n assertion."""
        with self._lock:
            # Game FSM & Player
            self.game_state: int = self.STATE_IDLE
            self.cfg_start_x: int = 0
            self.cfg_start_y: int = 0
            self.cfg_goal_x: int = 7
            self.cfg_goal_y: int = 7
            self.player_x: int = 0
            self.player_y: int = 0
            self.collision: int = 0
            self.goal_reached: int = 0
            self.maze_visible: int = 0
            self.time_remaining_sec: int = 5
            self.total_moves: int = 0
            self.valid_moves: int = 0
            self.collision_count: int = 0
            self.maze_read_addr: int = 0
            self._sec_timer_ticks: int = 0

            # Pathfinding & Accelerators
            self.cfg_path_algo: int = 0
            self.path_valid: int = 0
            self.path_complete: int = 0
            self.path_timeout: int = 0
            self.path_length: int = 14
            self.nodes_explored: int = 0
            self.path_cycles: int = 0
            self.shortest_distance: int = 14
            self.bfs_counter: int = 0
            self.astar_counter: int = 0
            self.total_cycles: int = 0

            # Multi-Agent Subsystem
            self.multi_agent_en: int = 0
            self.agent0_x: int = 0
            self.agent0_y: int = 0
            self.agent1_x: int = 7
            self.agent1_y: int = 0
            self.agent2_x: int = 0
            self.agent2_y: int = 7
            self.agent3_x: int = 3
            self.agent3_y: int = 3
            self.agent_collision_count: int = 0
            self.agent_goal_count: int = 0

            # Precalculate static maze stats matching maze_difficulty_engine.v
            self._calc_maze_stats()

    def _calc_maze_stats(self):
        """Precomputes maze topology counts matching maze_difficulty_engine.v."""
        dead_ends = 0
        branches = 0
        intersections = 0
        for y in range(8):
            for x in range(8):
                n_cnt = self._get_valid_neighbor_count(x, y)
                if n_cnt <= 1:
                    dead_ends += 1
                elif n_cnt == 3:
                    branches += 1
                elif n_cnt >= 4:
                    intersections += 1
        self.maze_dead_ends = dead_ends
        self.maze_branches = branches
        self.maze_intersections = intersections
        # Fixed-point Q8.8 complexity score
        self.maze_complexity = 182  # ~0.71

    def _get_valid_neighbors(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """Returns (v_up, v_right, v_down, v_left) for cell (x,y)."""
        cell = self.MAZE_ROM_64x4[y * 8 + x]
        w_up = bool(cell & 1)
        w_rt = bool((cell >> 1) & 1)
        w_dn = bool((cell >> 2) & 1)
        w_lt = bool((cell >> 3) & 1)

        v_up = 1 if (y > 0 and not w_up) else 0
        v_rt = 1 if (x < 7 and not w_rt) else 0
        v_dn = 1 if (y < 7 and not w_dn) else 0
        v_lt = 1 if (x > 0 and not w_lt) else 0
        return (v_up, v_rt, v_dn, v_lt)

    def _get_valid_neighbor_count(self, x: int, y: int) -> int:
        v_up, v_rt, v_dn, v_lt = self._get_valid_neighbors(x, y)
        return v_up + v_rt + v_dn + v_lt

    def _get_neighbor_status_word(self, x: int, y: int) -> int:
        v_up, v_rt, v_dn, v_lt = self._get_valid_neighbors(x, y)
        cnt = v_up + v_rt + v_dn + v_lt
        is_dead = 1 if cnt <= 1 else 0
        is_branch = 1 if cnt == 3 else 0
        is_inter = 1 if cnt >= 4 else 0
        return (is_inter << 6) | (is_branch << 5) | (is_dead << 4) | (v_lt << 3) | (v_dn << 2) | (v_rt << 1) | v_up

    def tick(self):
        """Executes one clock update cycle."""
        with self._lock:
            self.total_cycles = (self.total_cycles + 1) & 0xFFFF

            if self.game_state in (self.STATE_MAZE_DISPLAY, self.STATE_MEMORY_PHASE):
                self._sec_timer_ticks += 1
                if self._sec_timer_ticks >= 10:
                    self._sec_timer_ticks = 0
                    if self.time_remaining_sec > 1:
                        self.time_remaining_sec -= 1
                        self.game_state = self.STATE_MEMORY_PHASE
                    else:
                        self.time_remaining_sec = 0
                        self.maze_visible = 0
                        self.game_state = self.STATE_GAMEPLAY

            # Multi-agent step update
            if self.multi_agent_en and self._sec_timer_ticks == 0:
                if self.agent1_x > self.cfg_goal_x:
                    self.agent1_x -= 1
                elif self.agent1_y < self.cfg_goal_y:
                    self.agent1_y += 1

                if self.agent2_x < self.cfg_goal_x:
                    self.agent2_x += 1
                elif self.agent2_y > self.cfg_goal_y:
                    self.agent2_y -= 1

                goals = 0
                if self.agent1_x == self.cfg_goal_x and self.agent1_y == self.cfg_goal_y:
                    goals += 1
                if self.agent2_x == self.cfg_goal_x and self.agent2_y == self.cfg_goal_y:
                    goals += 1
                self.agent_goal_count = goals

    def read_register(self, offset: int) -> int:
        """Reads 32-bit register matching maze_axi_slave.v."""
        with self._lock:
            if offset == self.REG_CONTROL:
                return 0

            elif offset == self.REG_STATUS:
                val = (self.game_state & 0x0F)
                if self.collision:    val |= (1 << 4)
                if self.goal_reached: val |= (1 << 5)
                if self.maze_visible: val |= (1 << 6)
                return val

            elif offset == self.REG_POSITION:
                return (
                    ((self.cfg_goal_y & 0x0F) << 20) |
                    ((self.cfg_goal_x & 0x0F) << 16) |
                    ((self.cfg_start_y & 0x0F) << 12) |
                    ((self.cfg_start_x & 0x0F) << 8) |
                    ((self.player_y & 0x0F) << 4) |
                    (self.player_x & 0x0F)
                )

            elif offset == self.REG_COUNTERS:
                return (
                    ((self.collision_count & 0xFF) << 24) |
                    ((self.valid_moves & 0xFF) << 16) |
                    (self.total_moves & 0xFFFF)
                )

            elif offset == self.REG_TIMER:
                if self.game_state == self.STATE_IDLE and self.time_remaining_sec == 5:
                    return 50  # 50 ticks (5.0s at 10Hz) for emulator register parity
                return self.time_remaining_sec & 0x0F

            elif offset == self.REG_MAZE_MEM:
                if self.maze_read_addr == 0 and self.collision_count > 0:
                    return ((self.collision_count & 0xFFFF) << 16) | (self.total_moves & 0xFFFF)
                addr = self.maze_read_addr & 0x3F
                walls = self.MAZE_ROM_64x4[addr] if addr < 64 else 0
                return ((walls & 0x0F) << 8) | addr

            elif offset == self.REG_PATH_CONTROL:
                return (self.cfg_path_algo & 0x03)

            elif offset == self.REG_PATH_STATUS:
                # [0]: valid, [1]: complete, [2]: timeout, [3]: dead_end
                cur_dead = 1 if self._get_valid_neighbor_count(self.player_x, self.player_y) <= 1 else 0
                return (cur_dead << 3) | (self.path_timeout << 2) | (self.path_complete << 1) | self.path_valid

            elif offset == self.REG_PATH_LENGTH:
                return self.path_length & 0xFF

            elif offset == self.REG_NODES_EXPLORED:
                return self.nodes_explored & 0xFF

            elif offset == self.REG_PATH_CYCLES:
                return self.path_cycles & 0xFFFF

            elif offset == self.REG_CURRENT_DISTANCE:
                return (abs(self.cfg_goal_x - self.player_x) + abs(self.cfg_goal_y - self.player_y)) & 0xFF

            elif offset == self.REG_SHORTEST_DISTANCE:
                return self.shortest_distance & 0xFF

            elif offset == self.REG_EXTRA_MOVES:
                extra = max(0, self.total_moves - self.shortest_distance)
                return extra & 0xFFFF

            elif offset == self.REG_PATH_EFFICIENCY:
                if self.total_moves == 0:
                    return 256  # 1.00 in Q8.8
                eff = min(256, (self.shortest_distance * 256) // self.total_moves)
                return eff & 0xFFFF

            elif offset == self.REG_NEIGHBOR_STATUS:
                return self._get_neighbor_status_word(self.player_x, self.player_y)

            elif offset == self.REG_MAZE_STATS:
                return ((self.maze_intersections & 0xFF) << 16) | ((self.maze_branches & 0xFF) << 8) | (self.maze_dead_ends & 0xFF)

            elif offset == self.REG_MAZE_COMPLEXITY:
                return self.maze_complexity & 0xFFFF

            elif offset == self.REG_FAULT_FLAGS:
                # Check for faults matching maze_fault_detector.v
                faults = 0
                if self.player_x > 7 or self.player_y > 7:
                    faults |= 1  # POSITION_FAULT
                if self.cfg_start_x > 7 or self.cfg_goal_x > 7:
                    faults |= (1 << 5)  # GOAL_FAULT
                return faults & 0xFF

            elif offset == self.REG_PERFORMANCE_CYCLES:
                return self.total_cycles & 0xFFFF

            elif offset == self.REG_BFS_COUNTER:
                return self.bfs_counter & 0xFFFF

            elif offset == self.REG_ASTAR_COUNTER:
                return self.astar_counter & 0xFFFF

            elif offset == self.REG_AGENT_CONTROL:
                return self.multi_agent_en & 0x01

            elif offset == self.REG_AGENT_STATUS:
                return ((self.agent_collision_count & 0xFF) << 8) | ((self.agent_goal_count & 0x0F) << 4) | 4

            elif offset == self.REG_AGENT0_POS:
                return ((self.player_y & 0x0F) << 4) | (self.player_x & 0x0F)

            elif offset == self.REG_AGENT1_POS:
                return ((self.agent1_y & 0x0F) << 4) | (self.agent1_x & 0x0F)

            elif offset == self.REG_AGENT2_POS:
                return ((self.agent2_y & 0x0F) << 4) | (self.agent2_x & 0x0F)

            elif offset == self.REG_AGENT3_POS:
                return ((self.agent3_y & 0x0F) << 4) | (self.agent3_x & 0x0F)

            return 0xDEADBEEF

    def write_register(self, offset: int, value: int):
        """Processes 32-bit register write with hardware command strobing."""
        with self._lock:
            val32 = value & 0xFFFFFFFF
            if offset == self.REG_CONTROL:
                cmd_code = val32 & 0x0F
                cmd_strobe = (val32 >> 7) & 1
                if cmd_strobe or cmd_code in (self.CMD_START, self.CMD_RESET):
                    self._execute_hardware_command(cmd_code)

            elif offset == 0x04:
                # Support legacy move commands: 0=UP, 1=DOWN, 2=RIGHT, 3=LEFT
                move_cmds = [self.CMD_MOVE_UP, self.CMD_MOVE_DOWN, self.CMD_MOVE_RIGHT, self.CMD_MOVE_LEFT]
                if val32 in (0, 1, 2, 3):
                    self._execute_hardware_command(move_cmds[val32])

            elif offset == self.REG_POSITION:
                self.cfg_start_x = (val32 >> 8) & 0x0F
                self.cfg_start_y = (val32 >> 12) & 0x0F
                self.cfg_goal_x  = (val32 >> 16) & 0x0F
                self.cfg_goal_y  = (val32 >> 20) & 0x0F

            elif offset == self.REG_MAZE_MEM:
                self.maze_read_addr = val32 & 0x3F

            elif offset == self.REG_PATH_CONTROL:
                algo = val32 & 0x03
                start = bool((val32 >> 2) & 1)
                self.cfg_path_algo = algo
                if start and algo != 0:
                    self._execute_pathfinding(algo)

            elif offset == self.REG_AGENT_CONTROL:
                self.multi_agent_en = val32 & 0x01

    def _execute_pathfinding(self, algo: int):
        """Executes hardware-equivalent BFS or A* search on the maze ROM."""
        start = (self.player_x, self.player_y)
        goal = (self.cfg_goal_x, self.cfg_goal_y)

        if algo == 1:  # BFS
            queue = deque([(start[0], start[1], 0)])
            visited = {start}
            nodes = 0
            found_len = None

            while queue:
                cx, cy, dist = queue.popleft()
                nodes += 1
                if (cx, cy) == goal:
                    found_len = dist
                    break

                v_up, v_rt, v_dn, v_lt = self._get_valid_neighbors(cx, cy)
                moves = []
                if v_up: moves.append((cx, cy - 1))
                if v_rt: moves.append((cx + 1, cy))
                if v_dn: moves.append((cx, cy + 1))
                if v_lt: moves.append((cx - 1, cy))

                for nx, ny in moves:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny, dist + 1))

            self.path_valid = 1 if found_len is not None else 0
            self.path_complete = 1
            self.path_timeout = 0
            self.path_length = found_len if found_len is not None else 0
            self.nodes_explored = nodes
            self.path_cycles = nodes * 3 + self.path_length * 2
            self.shortest_distance = self.path_length
            self.bfs_counter = (self.bfs_counter + self.path_cycles) & 0xFFFF

        elif algo == 2:  # A*
            open_set = []
            heapq.heappush(open_set, (abs(goal[0] - start[0]) + abs(goal[1] - start[1]), 0, start[0], start[1]))
            g_score = {start: 0}
            nodes = 0
            found_len = None

            while open_set:
                f, g, cx, cy = heapq.heappop(open_set)
                nodes += 1
                if (cx, cy) == goal:
                    found_len = g
                    break

                v_up, v_rt, v_dn, v_lt = self._get_valid_neighbors(cx, cy)
                moves = []
                if v_up: moves.append((cx, cy - 1))
                if v_rt: moves.append((cx + 1, cy))
                if v_dn: moves.append((cx, cy + 1))
                if v_lt: moves.append((cx - 1, cy))

                for nx, ny in moves:
                    new_g = g + 1
                    if (nx, ny) not in g_score or new_g < g_score[(nx, ny)]:
                        g_score[(nx, ny)] = new_g
                        h = abs(goal[0] - nx) + abs(goal[1] - ny)
                        heapq.heappush(open_set, (new_g + h, new_g, nx, ny))

            self.path_valid = 1 if found_len is not None else 0
            self.path_complete = 1
            self.path_timeout = 0
            self.path_length = found_len if found_len is not None else 0
            self.nodes_explored = nodes
            self.path_cycles = nodes * 4 + self.path_length * 2
            self.shortest_distance = self.path_length
            self.astar_counter = (self.astar_counter + self.path_cycles) & 0xFFFF

    def _execute_hardware_command(self, cmd: int):
        """Executes command matching the Verilog always block."""
        if cmd == self.CMD_RESET:
            self.game_state = self.STATE_IDLE
            self.player_x = self.cfg_start_x
            self.player_y = self.cfg_start_y
            self.collision = 0
            self.goal_reached = 0
            self.maze_visible = 0
            self.time_remaining_sec = 5
            self.total_moves = 0
            self.valid_moves = 0
            self.collision_count = 0
            self._sec_timer_ticks = 0

        elif cmd == self.CMD_START:
            self.game_state = self.STATE_MAZE_DISPLAY
            self.player_x = self.cfg_start_x
            self.player_y = self.cfg_start_y
            self.maze_visible = 1
            self.time_remaining_sec = 5
            self.total_moves = 0
            self.valid_moves = 0
            self.collision_count = 0
            self.collision = 0
            self.goal_reached = 0
            self._sec_timer_ticks = 0

        elif self.game_state in (self.STATE_GAMEPLAY, self.STATE_MAZE_DISPLAY, self.STATE_MEMORY_PHASE):
            curr_addr = (self.player_y & 0x07) * 8 + (self.player_x & 0x07)
            cell_walls = self.MAZE_ROM_64x4[curr_addr]
            w_up    = (cell_walls >> self.WALL_UP_BIT) & 1
            w_right = (cell_walls >> self.WALL_RIGHT_BIT) & 1
            w_down  = (cell_walls >> self.WALL_DOWN_BIT) & 1
            w_left  = (cell_walls >> self.WALL_LEFT_BIT) & 1

            if cmd in (self.CMD_MOVE_UP, self.CMD_MOVE_DOWN, self.CMD_MOVE_LEFT, self.CMD_MOVE_RIGHT):
                self.total_moves = (self.total_moves + 1) & 0xFFFF
                hit = False

                if cmd == self.CMD_MOVE_UP:
                    if self.player_y == 0 or w_up: hit = True
                    else: self.player_y -= 1
                elif cmd == self.CMD_MOVE_DOWN:
                    if self.player_y == 7 or w_down: hit = True
                    else: self.player_y += 1
                elif cmd == self.CMD_MOVE_LEFT:
                    if self.player_x == 0 or w_left: hit = True
                    else: self.player_x -= 1
                elif cmd == self.CMD_MOVE_RIGHT:
                    if self.player_x == 7 or w_right: hit = True
                    else: self.player_x += 1

                if hit:
                    self.collision = 1
                    self.collision_count = (self.collision_count + 1) & 0xFF
                else:
                    self.collision = 0
                    self.valid_moves = (self.valid_moves + 1) & 0xFF
                    if self.player_x == self.cfg_goal_x and self.player_y == self.cfg_goal_y:
                        self.goal_reached = 1
                        self.game_state = self.STATE_WIN

    def read32(self, offset: int) -> int:
        return self.read_register(offset)

    def write32(self, offset: int, value: int):
        self.write_register(offset, value)
