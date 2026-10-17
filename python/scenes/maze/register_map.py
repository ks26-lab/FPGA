"""
python.scenes.maze.register_map
===============================
AXI register definitions for Maze Runner game engine & hardware navigation accelerator.
Base Address: 0x43C10000 (M_AXI_GP0)
Expanded 32-register address space (0x00 to 0x7C).
"""

BASE_ADDRESS = 0x43C10000

# -----------------------------------------------------------------------------
# Legacy Registers (0x00 .. 0x14) - Preserved & 100% Backward Compatible
# -----------------------------------------------------------------------------
REG_CONTROL  = 0x00  # [W]   [3:0]: cmd_code, [7]: cmd_strobe
REG_STATUS   = 0x04  # [R]   [3:0]: state, [4]: col, [5]: goal, [6]: visible
REG_POSITION = 0x08  # [R/W] [3:0]: pl_x, [7:4]: pl_y, [11:8]: st_x, [15:12]: st_y, [19:16]: gl_x, [23:20]: gl_y
REG_COUNTERS = 0x0C  # [R]   [15:0]: total_moves, [23:16]: valid_moves, [31:24]: collisions
REG_TIMER    = 0x10  # [R]   [3:0]: time_remaining_sec
REG_MAZE_MEM = 0x14  # [R/W] [5:0]: addr, [11:8]: data

# -----------------------------------------------------------------------------
# Upgraded Graph Processing & Navigation Accelerator Registers (0x18 .. 0x6C)
# -----------------------------------------------------------------------------
REG_PATH_CONTROL       = 0x18  # [R/W] [1:0]: algo (1=BFS, 2=A*), [2]: path_start
REG_PATH_STATUS        = 0x1C  # [R]   [0]: valid, [1]: complete, [2]: timeout, [3]: dead_end
REG_PATH_LENGTH        = 0x20  # [R]   [7:0]: shortest path length
REG_NODES_EXPLORED     = 0x24  # [R]   [7:0]: nodes explored during search
REG_PATH_CYCLES        = 0x28  # [R]   [15:0]: FPGA hardware cycles spent on pathfinding
REG_CURRENT_DISTANCE   = 0x2C  # [R]   [7:0]: Manhattan/distance from current player to goal
REG_SHORTEST_DISTANCE  = 0x30  # [R]   [7:0]: theoretical shortest distance from start to goal
REG_EXTRA_MOVES        = 0x34  # [R]   [15:0]: actual_moves - shortest_path
REG_PATH_EFFICIENCY    = 0x38  # [R]   [15:0]: Q8.8 fixed-point efficiency (shortest / actual)
REG_NEIGHBOR_STATUS    = 0x3C  # [R]   [3:0]: valid dirs (UP,RT,DN,LT), [4]: dead_end, [5]: branch, [6]: intersection
REG_MAZE_STATS         = 0x40  # [R]   [7:0]: dead_ends, [15:8]: branches, [23:16]: intersections
REG_MAZE_COMPLEXITY    = 0x44  # [R]   [15:0]: Q8.8 fixed-point complexity score
REG_FAULT_FLAGS        = 0x48  # [R]   [7:0]: hardware fault bitmask
REG_PERFORMANCE_CYCLES = 0x4C  # [R]   [15:0]: total game clock cycles
REG_BFS_COUNTER        = 0x50  # [R]   [15:0]: BFS hardware execution cycles
REG_ASTAR_COUNTER      = 0x54  # [R]   [15:0]: A* hardware execution cycles
REG_AGENT_CONTROL      = 0x58  # [R/W] [0]: multi-agent hardware engine enable
REG_AGENT_STATUS       = 0x5C  # [R]   [3:0]: active_agents, [7:4]: goal_count, [15:8]: collision_count
REG_AGENT0_POS         = 0x60  # [R]   [3:0]: x, [7:4]: y (Agent 0 / Player)
REG_AGENT1_POS         = 0x64  # [R]   [3:0]: x, [7:4]: y (Agent 1)
REG_AGENT2_POS         = 0x68  # [R]   [3:0]: x, [7:4]: y (Agent 2)
REG_AGENT3_POS         = 0x6C  # [R]   [3:0]: x, [7:4]: y (Agent 3)

# -----------------------------------------------------------------------------
# Command Constants
# -----------------------------------------------------------------------------
CMD_NONE   = 0
CMD_START  = 1
CMD_RESET  = 2
CMD_UP     = 3
CMD_DOWN   = 4
CMD_LEFT   = 5
CMD_RIGHT  = 6

# -----------------------------------------------------------------------------
# Pathfinding Algorithm Selection
# -----------------------------------------------------------------------------
ALGO_NONE  = 0
ALGO_BFS   = 1
ALGO_ASTAR = 2

ALGO_NAMES = {
    ALGO_NONE:  "NONE",
    ALGO_BFS:   "BFS",
    ALGO_ASTAR: "A*"
}

# -----------------------------------------------------------------------------
# Path Status Bitmasks
# -----------------------------------------------------------------------------
PATH_STATUS_VALID    = (1 << 0)
PATH_STATUS_COMPLETE = (1 << 1)
PATH_STATUS_TIMEOUT  = (1 << 2)
PATH_STATUS_DEAD_END = (1 << 3)

# -----------------------------------------------------------------------------
# Neighbor Direction & Topology Bitmasks
# -----------------------------------------------------------------------------
NEIGHBOR_UP          = (1 << 0)
NEIGHBOR_RIGHT       = (1 << 1)
NEIGHBOR_DOWN        = (1 << 2)
NEIGHBOR_LEFT        = (1 << 3)
NEIGHBOR_DEAD_END    = (1 << 4)
NEIGHBOR_BRANCH      = (1 << 5)
NEIGHBOR_INTERSECT   = (1 << 6)

# -----------------------------------------------------------------------------
# Hardware Fault Bitmasks
# -----------------------------------------------------------------------------
FAULT_POSITION       = (1 << 0)
FAULT_MAZE_MEMORY    = (1 << 1)
FAULT_QUEUE_OVERFLOW = (1 << 2)
FAULT_PATH_TIMEOUT   = (1 << 3)
FAULT_INVALID_CMD    = (1 << 4)
FAULT_GOAL_FAULT     = (1 << 5)
FAULT_AGENT_COLLISION= (1 << 6)

FAULT_DESCRIPTIONS = {
    FAULT_POSITION:        "Player Position Out of Bounds",
    FAULT_MAZE_MEMORY:     "Invalid Wall Encoding in Memory",
    FAULT_QUEUE_OVERFLOW:  "Hardware Pathfinding Queue Overflow",
    FAULT_PATH_TIMEOUT:    "Pathfinding Search Timeout",
    FAULT_INVALID_CMD:     "Invalid Command Code Issued",
    FAULT_GOAL_FAULT:      "Inconsistent Start/Goal Coords",
    FAULT_AGENT_COLLISION: "Multi-Agent Hardware Collision"
}

# -----------------------------------------------------------------------------
# Route Quality Status
# -----------------------------------------------------------------------------
ROUTE_OPTIMAL     = 0
ROUTE_GOOD        = 1
ROUTE_INEFFICIENT = 2
ROUTE_DEAD_END    = 3

ROUTE_STATUS_NAMES = {
    ROUTE_OPTIMAL:     "OPTIMAL",
    ROUTE_GOOD:        "GOOD",
    ROUTE_INEFFICIENT: "INEFFICIENT",
    ROUTE_DEAD_END:    "DEAD_END"
}

# -----------------------------------------------------------------------------
# Game FSM State Names
# -----------------------------------------------------------------------------
STATE_NAMES = {
    0: "IDLE",
    1: "MAZE_DISPLAY",
    2: "MEMORY_PHASE",
    3: "GAMEPLAY",
    4: "WIN",
    5: "GAME_OVER"
}
