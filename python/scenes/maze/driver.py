"""
python.scenes.maze.driver
=========================
Dedicated hardware driver for Maze Runner scene & graph navigation accelerator.
Base Address: 0x43C10000 (M_AXI_GP0)
Controls FPGA registers and decodes telemetry directly from PL hardware.
"""

from typing import Dict, Any, Optional

from python.core.fpga_driver import BaseFPGADriver
from python.core.axi_interface import AXIInterface, MockAXIInterface
from python.scenes.maze.register_map import (
    BASE_ADDRESS,
    REG_CONTROL,
    REG_STATUS,
    REG_POSITION,
    REG_COUNTERS,
    REG_TIMER,
    REG_MAZE_MEM,
    REG_PATH_CONTROL,
    REG_PATH_STATUS,
    REG_PATH_LENGTH,
    REG_NODES_EXPLORED,
    REG_PATH_CYCLES,
    REG_CURRENT_DISTANCE,
    REG_SHORTEST_DISTANCE,
    REG_EXTRA_MOVES,
    REG_PATH_EFFICIENCY,
    REG_NEIGHBOR_STATUS,
    REG_MAZE_STATS,
    REG_MAZE_COMPLEXITY,
    REG_FAULT_FLAGS,
    REG_PERFORMANCE_CYCLES,
    REG_BFS_COUNTER,
    REG_ASTAR_COUNTER,
    REG_AGENT_CONTROL,
    REG_AGENT_STATUS,
    REG_AGENT0_POS,
    REG_AGENT1_POS,
    REG_AGENT2_POS,
    REG_AGENT3_POS,
    CMD_START,
    CMD_RESET,
    CMD_UP,
    CMD_DOWN,
    CMD_LEFT,
    CMD_RIGHT,
    ALGO_NONE,
    ALGO_BFS,
    ALGO_ASTAR,
    NEIGHBOR_UP,
    NEIGHBOR_RIGHT,
    NEIGHBOR_DOWN,
    NEIGHBOR_LEFT,
    NEIGHBOR_DEAD_END,
    NEIGHBOR_BRANCH,
    NEIGHBOR_INTERSECT,
)
from python.scenes.maze.telemetry import decode_maze_telemetry

# 8x8 ROM bitmask layout matching maze_core.v
MAZE_LAYOUT_8X8 = [
    0b1101, 0b0001, 0b0111, 0b1101, 0b0001, 0b0111, 0b1101, 0b0011,
    0b1011, 0b1000, 0b0101, 0b1001, 0b0000, 0b0111, 0b1011, 0b1010,
    0b1000, 0b0100, 0b1000, 0b0100, 0b1000, 0b0001, 0b0100, 0b1010,
    0b1100, 0b0010, 0b1100, 0b0010, 0b1100, 0b0100, 0b1000, 0b0010,
    0b1001, 0b0110, 0b1001, 0b0110, 0b1001, 0b0010, 0b1100, 0b0010,
    0b1010, 0b1001, 0b0110, 0b1001, 0b0110, 0b1000, 0b0011, 0b1010,
    0b1000, 0b0100, 0b1001, 0b0100, 0b1001, 0b0000, 0b0100, 0b1010,
    0b1100, 0b0001, 0b0001, 0b0001, 0b0001, 0b0001, 0b0001, 0b0111
]


def compute_neighbor_status_word(x: int, y: int) -> int:
    """Helper computing neighbor status word matching maze_neighbor_engine.v."""
    cell = MAZE_LAYOUT_8X8[y * 8 + x]
    w_up = bool(cell & 1)
    w_rt = bool((cell >> 1) & 1)
    w_dn = bool((cell >> 2) & 1)
    w_lt = bool((cell >> 3) & 1)

    v_up = 1 if (y > 0 and not w_up) else 0
    v_rt = 1 if (x < 7 and not w_rt) else 0
    v_dn = 1 if (y < 7 and not w_dn) else 0
    v_lt = 1 if (x > 0 and not w_lt) else 0

    n_cnt = v_up + v_rt + v_dn + v_lt
    is_dead = 1 if n_cnt <= 1 else 0
    is_branch = 1 if n_cnt == 3 else 0
    is_inter = 1 if n_cnt >= 4 else 0

    return (is_inter << 6) | (is_branch << 5) | (is_dead << 4) | (v_lt << 3) | (v_dn << 2) | (v_rt << 1) | v_up


class MazeDriver(BaseFPGADriver):
    """Driver for Maze Runner & Navigation Accelerator on AXI peripheral 0x43C10000."""

    def __init__(self, axi: AXIInterface, base_address: int = BASE_ADDRESS):
        super().__init__(axi, scene_name="maze", base_address=base_address)
        if isinstance(self.axi, MockAXIInterface):
            self._setup_mock_hooks()

    def _setup_mock_hooks(self):
        """Mock behavior replicating upgraded maze_core.v logic."""
        mock = self.axi

        # Initialize Legacy Registers
        mock.registers[REG_CONTROL] = 0
        mock.registers[REG_STATUS] = 0  # IDLE
        mock.registers[REG_POSITION] = (7 << 20) | (7 << 16) | (0 << 12) | (0 << 8) | (0 << 4) | 0
        mock.registers[REG_COUNTERS] = 0
        mock.registers[REG_TIMER] = 5
        mock.registers[REG_MAZE_MEM] = 0

        # Initialize Upgraded Accelerator Registers
        mock.registers[REG_PATH_CONTROL] = 0
        mock.registers[REG_PATH_STATUS] = 0
        mock.registers[REG_PATH_LENGTH] = 14
        mock.registers[REG_NODES_EXPLORED] = 0
        mock.registers[REG_PATH_CYCLES] = 0
        mock.registers[REG_CURRENT_DISTANCE] = 14
        mock.registers[REG_SHORTEST_DISTANCE] = 14
        mock.registers[REG_EXTRA_MOVES] = 0
        mock.registers[REG_PATH_EFFICIENCY] = 256  # 1.00 in Q8.8
        mock.registers[REG_NEIGHBOR_STATUS] = compute_neighbor_status_word(0, 0)
        mock.registers[REG_MAZE_STATS] = (3 << 16) | (8 << 8) | 7  # 7 dead-ends, 8 branches, 3 intersections
        mock.registers[REG_MAZE_COMPLEXITY] = 182  # 0.71 in Q8.8
        mock.registers[REG_FAULT_FLAGS] = 0
        mock.registers[REG_PERFORMANCE_CYCLES] = 100
        mock.registers[REG_BFS_COUNTER] = 0
        mock.registers[REG_ASTAR_COUNTER] = 0
        mock.registers[REG_AGENT_CONTROL] = 0
        mock.registers[REG_AGENT_STATUS] = 4  # 4 active agents
        mock.registers[REG_AGENT0_POS] = (0 << 4) | 0
        mock.registers[REG_AGENT1_POS] = (0 << 4) | 7
        mock.registers[REG_AGENT2_POS] = (7 << 4) | 0
        mock.registers[REG_AGENT3_POS] = (3 << 4) | 3

        def on_control_write(val: int):
            cmd_code = val & 0x0F
            cmd_strobe = (val >> 7) & 1
            if not cmd_strobe and cmd_code == 0:
                return

            cur_pos = mock.registers.get(REG_POSITION, 0)
            cur_counters = mock.registers.get(REG_COUNTERS, 0)
            pl_x = cur_pos & 0x0F
            pl_y = (cur_pos >> 4) & 0x0F
            st_x = (cur_pos >> 8) & 0x0F
            st_y = (cur_pos >> 12) & 0x0F
            gl_x = (cur_pos >> 16) & 0x0F
            gl_y = (cur_pos >> 20) & 0x0F

            tot_m = cur_counters & 0xFFFF
            val_m = (cur_counters >> 16) & 0xFF
            col_m = (cur_counters >> 24) & 0xFF

            if cmd_code == CMD_RESET:
                mock.registers[REG_STATUS] = 0  # IDLE
                mock.registers[REG_POSITION] = (gl_y << 20) | (gl_x << 16) | (st_y << 12) | (st_x << 8) | (st_y << 4) | st_x
                mock.registers[REG_COUNTERS] = 0
                mock.registers[REG_TIMER] = 5
                mock.registers[REG_NEIGHBOR_STATUS] = compute_neighbor_status_word(st_x, st_y)
                mock.registers[REG_CURRENT_DISTANCE] = abs(gl_x - st_x) + abs(gl_y - st_y)
                mock.registers[REG_EXTRA_MOVES] = 0
                mock.registers[REG_PATH_EFFICIENCY] = 256
                mock.registers[REG_AGENT0_POS] = (st_y << 4) | st_x

            elif cmd_code == CMD_START:
                mock.registers[REG_STATUS] = 3 | (1 << 6)  # GAMEPLAY with visible initially
                mock.registers[REG_POSITION] = (gl_y << 20) | (gl_x << 16) | (st_y << 12) | (st_x << 8) | (st_y << 4) | st_x
                mock.registers[REG_COUNTERS] = 0
                mock.registers[REG_TIMER] = 0
                mock.registers[REG_NEIGHBOR_STATUS] = compute_neighbor_status_word(st_x, st_y)
                mock.registers[REG_CURRENT_DISTANCE] = abs(gl_x - st_x) + abs(gl_y - st_y)
                mock.registers[REG_EXTRA_MOVES] = 0
                mock.registers[REG_PATH_EFFICIENCY] = 256
                mock.registers[REG_AGENT0_POS] = (st_y << 4) | st_x

            elif cmd_code in (CMD_UP, CMD_DOWN, CMD_LEFT, CMD_RIGHT):
                curr_cell = MAZE_LAYOUT_8X8[pl_y * 8 + pl_x]
                w_up = curr_cell & 1
                w_rt = (curr_cell >> 1) & 1
                w_dn = (curr_cell >> 2) & 1
                w_lt = (curr_cell >> 3) & 1

                collision = False
                new_x, new_y = pl_x, pl_y

                if cmd_code == CMD_UP:
                    if pl_y == 0 or w_up: collision = True
                    else: new_y -= 1
                elif cmd_code == CMD_DOWN:
                    if pl_y == 7 or w_dn: collision = True
                    else: new_y += 1
                elif cmd_code == CMD_LEFT:
                    if pl_x == 0 or w_lt: collision = True
                    else: new_x -= 1
                elif cmd_code == CMD_RIGHT:
                    if pl_x == 7 or w_rt: collision = True
                    else: new_x += 1

                tot_m += 1
                if collision:
                    col_m += 1
                    status_col = (1 << 4)
                else:
                    val_m += 1
                    pl_x, pl_y = new_x, new_y
                    status_col = 0

                goal_reached = (pl_x == gl_x and pl_y == gl_y)
                st_code = 4 if goal_reached else 3  # WIN or GAMEPLAY
                status_goal = (1 << 5) if goal_reached else 0

                mock.registers[REG_STATUS] = st_code | status_col | status_goal
                mock.registers[REG_POSITION] = (gl_y << 20) | (gl_x << 16) | (st_y << 12) | (st_x << 8) | (pl_y << 4) | pl_x
                mock.registers[REG_COUNTERS] = ((col_m & 0xFF) << 24) | ((val_m & 0xFF) << 16) | (tot_m & 0xFFFF)
                mock.registers[REG_NEIGHBOR_STATUS] = compute_neighbor_status_word(pl_x, pl_y)
                mock.registers[REG_CURRENT_DISTANCE] = abs(gl_x - pl_x) + abs(gl_y - pl_y)
                short_len = mock.registers.get(REG_PATH_LENGTH, 14)
                x_moves = max(0, tot_m - short_len)
                mock.registers[REG_EXTRA_MOVES] = x_moves
                eff = min(256, (short_len * 256) // max(1, tot_m)) if tot_m > 0 else 256
                mock.registers[REG_PATH_EFFICIENCY] = eff
                mock.registers[REG_AGENT0_POS] = (pl_y << 4) | pl_x

        mock.write_hooks[REG_CONTROL] = on_control_write

        def on_mem_write(val: int):
            addr = val & 0x3F
            data = MAZE_LAYOUT_8X8[addr] if addr < 64 else 0
            mock.registers[REG_MAZE_MEM] = ((data & 0x0F) << 8) | addr

        mock.write_hooks[REG_MAZE_MEM] = on_mem_write

        def on_path_control_write(val: int):
            algo = val & 0x03
            start = bool((val >> 2) & 1)
            mock.registers[REG_PATH_CONTROL] = val & 0x07
            if start and algo != ALGO_NONE:
                # Emulate hardware BFS / A* search completion
                if algo == ALGO_BFS:
                    mock.registers[REG_PATH_STATUS] = 0x03  # valid (bit 0) and complete (bit 1)
                    mock.registers[REG_PATH_LENGTH] = 14
                    mock.registers[REG_NODES_EXPLORED] = 38
                    mock.registers[REG_PATH_CYCLES] = 120
                    mock.registers[REG_BFS_COUNTER] = mock.registers.get(REG_BFS_COUNTER, 0) + 120
                elif algo == ALGO_ASTAR:
                    mock.registers[REG_PATH_STATUS] = 0x03  # valid (bit 0) and complete (bit 1)
                    mock.registers[REG_PATH_LENGTH] = 14
                    mock.registers[REG_NODES_EXPLORED] = 26
                    mock.registers[REG_PATH_CYCLES] = 84
                    mock.registers[REG_ASTAR_COUNTER] = mock.registers.get(REG_ASTAR_COUNTER, 0) + 84

        mock.write_hooks[REG_PATH_CONTROL] = on_path_control_write

        def on_agent_control_write(val: int):
            en = val & 0x01
            mock.registers[REG_AGENT_CONTROL] = en
            if en:
                mock.registers[REG_AGENT_STATUS] = (1 << 8) | (0 << 4) | 4  # 4 active agents

        mock.write_hooks[REG_AGENT_CONTROL] = on_agent_control_write

    def send_cmd(self, cmd_code: int) -> None:
        """Sends command with bit 7 strobe asserted."""
        word = ((1 << 7) | (cmd_code & 0x0F)) & 0xFFFFFFFF
        self.write32(REG_CONTROL, word)

    def start(self) -> None:
        self.send_cmd(CMD_START)

    def start_game(self) -> None:
        self.start()

    def reset(self) -> None:
        self.send_cmd(CMD_RESET)

    def move_up(self) -> None:
        self.send_cmd(CMD_UP)

    def move_down(self) -> None:
        self.send_cmd(CMD_DOWN)

    def move_left(self) -> None:
        self.send_cmd(CMD_LEFT)

    def move_right(self) -> None:
        self.send_cmd(CMD_RIGHT)

    def move(self, direction: str) -> None:
        d = direction.lower()
        if d in ("up", "w"):
            self.move_up()
        elif d in ("down", "s"):
            self.move_down()
        elif d in ("left", "a"):
            self.move_left()
        elif d in ("right", "d"):
            self.move_right()

    def configure_endpoints(self, start_x: int, start_y: int, goal_x: int, goal_y: int) -> None:
        """Configures start and goal coordinates in REG_POSITION (0x08)."""
        val = ((goal_y & 0x0F) << 20) | ((goal_x & 0x0F) << 16) | ((start_y & 0x0F) << 12) | ((start_x & 0x0F) << 8)
        self.write32(REG_POSITION, val)

    def run_bfs(self) -> None:
        """Triggers hardware BFS pathfinding engine (Algorithm 1, start strobe)."""
        val = (1 << 2) | ALGO_BFS
        self.write32(REG_PATH_CONTROL, val)

    def run_astar(self) -> None:
        """Triggers hardware A* pathfinding engine (Algorithm 2, start strobe)."""
        val = (1 << 2) | ALGO_ASTAR
        self.write32(REG_PATH_CONTROL, val)

    def set_multi_agent(self, enabled: bool) -> None:
        """Enables or disables parallel 4-agent hardware engine."""
        val = 1 if enabled else 0
        self.write32(REG_AGENT_CONTROL, val)

    def read_maze_cell(self, addr: int) -> int:
        """Writes address to REG_MAZE_MEM and reads back 4-bit wall data."""
        self.write32(REG_MAZE_MEM, addr & 0x3F)
        val = self.read32(REG_MAZE_MEM)
        return (val >> 8) & 0x0F

    def get_telemetry(self) -> Dict[str, Any]:
        """Reads all 32 hardware registers and returns decoded telemetry."""
        status_reg       = self.read32(REG_STATUS)
        pos_reg          = self.read32(REG_POSITION)
        counters_reg     = self.read32(REG_COUNTERS)
        timer_reg        = self.read32(REG_TIMER)

        path_ctrl_reg    = self.read32(REG_PATH_CONTROL)
        path_status_reg  = self.read32(REG_PATH_STATUS)
        path_len_reg     = self.read32(REG_PATH_LENGTH)
        nodes_exp_reg    = self.read32(REG_NODES_EXPLORED)
        path_cycles_reg  = self.read32(REG_PATH_CYCLES)
        cur_dist_reg     = self.read32(REG_CURRENT_DISTANCE)
        short_dist_reg   = self.read32(REG_SHORTEST_DISTANCE)
        extra_moves_reg  = self.read32(REG_EXTRA_MOVES)
        path_eff_reg     = self.read32(REG_PATH_EFFICIENCY)
        neighbor_reg     = self.read32(REG_NEIGHBOR_STATUS)
        maze_stats_reg   = self.read32(REG_MAZE_STATS)
        complexity_reg   = self.read32(REG_MAZE_COMPLEXITY)
        fault_flags_reg  = self.read32(REG_FAULT_FLAGS)
        perf_cycles_reg  = self.read32(REG_PERFORMANCE_CYCLES)
        bfs_counter_reg  = self.read32(REG_BFS_COUNTER)
        astar_counter_reg= self.read32(REG_ASTAR_COUNTER)
        agent_status_reg = self.read32(REG_AGENT_STATUS)
        ag0_reg          = self.read32(REG_AGENT0_POS)
        ag1_reg          = self.read32(REG_AGENT1_POS)
        ag2_reg          = self.read32(REG_AGENT2_POS)
        ag3_reg          = self.read32(REG_AGENT3_POS)

        return decode_maze_telemetry(
            status_reg=status_reg,
            pos_reg=pos_reg,
            counters_reg=counters_reg,
            timer_reg=timer_reg,
            is_hardware=self.is_hardware,
            path_ctrl_reg=path_ctrl_reg,
            path_status_reg=path_status_reg,
            path_length_reg=path_len_reg,
            nodes_explored_reg=nodes_exp_reg,
            path_cycles_reg=path_cycles_reg,
            current_dist_reg=cur_dist_reg,
            shortest_dist_reg=short_dist_reg,
            extra_moves_reg=extra_moves_reg,
            path_efficiency_reg=path_eff_reg,
            neighbor_status_reg=neighbor_reg,
            maze_stats_reg=maze_stats_reg,
            maze_complexity_reg=complexity_reg,
            fault_flags_reg=fault_flags_reg,
            total_cycles_reg=perf_cycles_reg,
            bfs_counter_reg=bfs_counter_reg,
            astar_counter_reg=astar_counter_reg,
            agent_status_reg=agent_status_reg,
            agent0_pos_reg=ag0_reg,
            agent1_pos_reg=ag1_reg,
            agent2_pos_reg=ag2_reg,
            agent3_pos_reg=ag3_reg
        )

    def get_debug_registers(self) -> Dict[str, Any]:
        """Dumps all 32 hardware registers in hex for diagnostics."""
        return {
            "scene": "maze",
            "base_address": f"0x{self.base_address:08X}",
            "CONTROL": f"0x{self.read32(REG_CONTROL):08X}",
            "STATUS": f"0x{self.read32(REG_STATUS):08X}",
            "POSITION": f"0x{self.read32(REG_POSITION):08X}",
            "COUNTERS": f"0x{self.read32(REG_COUNTERS):08X}",
            "TIMER": f"0x{self.read32(REG_TIMER):08X}",
            "MAZE_MEM": f"0x{self.read32(REG_MAZE_MEM):08X}",
            "PATH_CONTROL": f"0x{self.read32(REG_PATH_CONTROL):08X}",
            "PATH_STATUS": f"0x{self.read32(REG_PATH_STATUS):08X}",
            "PATH_LENGTH": f"0x{self.read32(REG_PATH_LENGTH):08X}",
            "NODES_EXPLORED": f"0x{self.read32(REG_NODES_EXPLORED):08X}",
            "PATH_CYCLES": f"0x{self.read32(REG_PATH_CYCLES):08X}",
            "CURRENT_DISTANCE": f"0x{self.read32(REG_CURRENT_DISTANCE):08X}",
            "SHORTEST_DISTANCE": f"0x{self.read32(REG_SHORTEST_DISTANCE):08X}",
            "EXTRA_MOVES": f"0x{self.read32(REG_EXTRA_MOVES):08X}",
            "PATH_EFFICIENCY": f"0x{self.read32(REG_PATH_EFFICIENCY):08X}",
            "NEIGHBOR_STATUS": f"0x{self.read32(REG_NEIGHBOR_STATUS):08X}",
            "MAZE_STATS": f"0x{self.read32(REG_MAZE_STATS):08X}",
            "MAZE_COMPLEXITY": f"0x{self.read32(REG_MAZE_COMPLEXITY):08X}",
            "FAULT_FLAGS": f"0x{self.read32(REG_FAULT_FLAGS):08X}",
            "PERFORMANCE_CYCLES": f"0x{self.read32(REG_PERFORMANCE_CYCLES):08X}",
            "BFS_COUNTER": f"0x{self.read32(REG_BFS_COUNTER):08X}",
            "ASTAR_COUNTER": f"0x{self.read32(REG_ASTAR_COUNTER):08X}",
            "AGENT_CONTROL": f"0x{self.read32(REG_AGENT_CONTROL):08X}",
            "AGENT_STATUS": f"0x{self.read32(REG_AGENT_STATUS):08X}",
            "AGENT0_POS": f"0x{self.read32(REG_AGENT0_POS):08X}",
            "AGENT1_POS": f"0x{self.read32(REG_AGENT1_POS):08X}",
            "AGENT2_POS": f"0x{self.read32(REG_AGENT2_POS):08X}",
            "AGENT3_POS": f"0x{self.read32(REG_AGENT3_POS):08X}",
        }
