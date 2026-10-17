"""
python.scenes.maze.telemetry
============================
Telemetry decoding and data structures for Maze Runner FPGA core.
Strictly decodes FPGA hardware register values; does not perform pathfinding or physics in Python.
"""

import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

from python.scenes.maze.register_map import (
    STATE_NAMES,
    ALGO_NAMES,
    FAULT_DESCRIPTIONS,
    FAULT_POSITION,
    FAULT_MAZE_MEMORY,
    FAULT_QUEUE_OVERFLOW,
    FAULT_PATH_TIMEOUT,
    FAULT_INVALID_CMD,
    FAULT_GOAL_FAULT,
    FAULT_AGENT_COLLISION,
)


@dataclass
class MazeTelemetry:
    """Strongly-typed hardware telemetry model for Maze Runner FPGA navigation accelerator."""
    # FSM & Status
    state: str
    player_x: int
    player_y: int
    start_x: int
    start_y: int
    goal_x: int
    goal_y: int
    collision: bool
    goal_reached: bool
    maze_visible: bool
    time_remaining_s: int

    # Movement Counters
    total_moves: int
    valid_moves: int
    collision_count: int

    # Parallel Neighbor & Topology Engine
    valid_up: bool
    valid_right: bool
    valid_down: bool
    valid_left: bool
    neighbor_count: int
    dead_end: bool
    branch: bool
    intersection: bool

    # Hardware Pathfinding (BFS / A*)
    path_algorithm: str
    path_valid: bool
    path_complete: bool
    path_timeout: bool
    path_length: int
    nodes_explored: int
    path_cycles: int

    # Distance Map & Route Analysis
    current_distance: int
    shortest_distance: int
    extra_moves: int
    path_efficiency: float
    route_status: str

    # Maze Difficulty Engine
    maze_dead_ends: int
    maze_branches: int
    maze_intersections: int
    maze_complexity: float

    # Faults & Performance Counters
    fault_flags: int
    active_faults: List[str]
    total_cycles: int
    bfs_cycles: int
    astar_cycles: int

    # Multi-Agent Subsystem
    active_agents: int
    agent_collision_count: int
    agent_goal_count: int
    agent0_pos: tuple
    agent1_pos: tuple
    agent2_pos: tuple
    agent3_pos: tuple

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def q8_8_to_float(raw: int) -> float:
    """Decodes Q8.8 unsigned fixed-point value."""
    return round((raw & 0xFFFF) / 256.0, 3)


def decode_maze_telemetry(
    status_reg: int,
    pos_reg: int,
    counters_reg: int,
    timer_reg: int,
    is_hardware: bool,
    path_ctrl_reg: int = 0,
    path_status_reg: int = 0,
    path_length_reg: int = 0,
    nodes_explored_reg: int = 0,
    path_cycles_reg: int = 0,
    current_dist_reg: int = 0,
    shortest_dist_reg: int = 0,
    extra_moves_reg: int = 0,
    path_efficiency_reg: int = 0,
    neighbor_status_reg: int = 0,
    maze_stats_reg: int = 0,
    maze_complexity_reg: int = 0,
    fault_flags_reg: int = 0,
    total_cycles_reg: int = 0,
    bfs_counter_reg: int = 0,
    astar_counter_reg: int = 0,
    agent_status_reg: int = 0,
    agent0_pos_reg: int = 0,
    agent1_pos_reg: int = 0,
    agent2_pos_reg: int = 0,
    agent3_pos_reg: int = 0,
) -> Dict[str, Any]:
    """
    Decodes raw 32-bit registers from maze_axi_slave into strongly-typed telemetry envelope.
    All data originates from hardware registers.
    """
    state_code = status_reg & 0x0F
    collision = bool((status_reg >> 4) & 1)
    goal_reached = bool((status_reg >> 5) & 1)
    maze_visible = bool((status_reg >> 6) & 1)

    player_x = pos_reg & 0x0F
    player_y = (pos_reg >> 4) & 0x0F
    start_x  = (pos_reg >> 8) & 0x0F
    start_y  = (pos_reg >> 12) & 0x0F
    goal_x   = (pos_reg >> 16) & 0x0F
    goal_y   = (pos_reg >> 20) & 0x0F

    total_moves = counters_reg & 0xFFFF
    valid_moves = (counters_reg >> 16) & 0xFF
    collision_count = (counters_reg >> 24) & 0xFF

    time_remaining_s = timer_reg & 0x0F
    state_str = STATE_NAMES.get(state_code, f"STATE_{state_code}")

    # Neighbor Engine
    valid_up = bool(neighbor_status_reg & 0x01)
    valid_rt = bool((neighbor_status_reg >> 1) & 0x01)
    valid_dn = bool((neighbor_status_reg >> 2) & 0x01)
    valid_lt = bool((neighbor_status_reg >> 3) & 0x01)
    dead_end_det = bool((neighbor_status_reg >> 4) & 0x01)
    branch_det = bool((neighbor_status_reg >> 5) & 0x01)
    inter_det = bool((neighbor_status_reg >> 6) & 0x01)
    n_count = (1 if valid_up else 0) + (1 if valid_rt else 0) + (1 if valid_dn else 0) + (1 if valid_lt else 0)

    # Pathfinding Telemetry
    algo_id = path_ctrl_reg & 0x03
    algo_str = ALGO_NAMES.get(algo_id, "NONE")
    path_valid = bool(path_status_reg & 0x01)
    path_complete = bool((path_status_reg >> 1) & 0x01)
    path_timeout = bool((path_status_reg >> 2) & 0x01)
    path_len = path_length_reg & 0xFF
    nodes_exp = nodes_explored_reg & 0xFF
    path_cyc = path_cycles_reg & 0xFFFF

    # Distance & Route Analyzer
    curr_dist = current_dist_reg & 0xFF
    short_dist = shortest_dist_reg & 0xFF
    x_moves = extra_moves_reg & 0xFFFF
    path_eff = q8_8_to_float(path_efficiency_reg)
    if x_moves == 0:
        route_str = "OPTIMAL"
    elif x_moves <= 4:
        route_str = "GOOD"
    else:
        route_str = "INEFFICIENT"

    # Maze Stats & Complexity
    dead_ends = maze_stats_reg & 0xFF
    branches = (maze_stats_reg >> 8) & 0xFF
    intersections = (maze_stats_reg >> 16) & 0xFF
    complexity = q8_8_to_float(maze_complexity_reg)

    # Faults
    fflags = fault_flags_reg & 0xFF
    active_faults = []
    for mask, desc in FAULT_DESCRIPTIONS.items():
        if fflags & mask:
            active_faults.append(desc)

    # Performance
    tot_cyc = total_cycles_reg & 0xFFFF
    bfs_cyc = bfs_counter_reg & 0xFFFF
    astar_cyc = astar_counter_reg & 0xFFFF

    # Multi-Agent Subsystem
    act_agents = agent_status_reg & 0x0F
    ag_goals = (agent_status_reg >> 4) & 0x0F
    ag_cols = (agent_status_reg >> 8) & 0xFF

    def parse_pos(reg_val: int):
        return (reg_val & 0x0F, (reg_val >> 4) & 0x0F)

    ag0 = parse_pos(agent0_pos_reg)
    ag1 = parse_pos(agent1_pos_reg)
    ag2 = parse_pos(agent2_pos_reg)
    ag3 = parse_pos(agent3_pos_reg)

    typed_telem = MazeTelemetry(
        state=state_str,
        player_x=player_x,
        player_y=player_y,
        start_x=start_x,
        start_y=start_y,
        goal_x=goal_x,
        goal_y=goal_y,
        collision=collision,
        goal_reached=goal_reached,
        maze_visible=maze_visible,
        time_remaining_s=time_remaining_s,
        total_moves=total_moves,
        valid_moves=valid_moves,
        collision_count=collision_count,
        valid_up=valid_up,
        valid_right=valid_rt,
        valid_down=valid_dn,
        valid_left=valid_lt,
        neighbor_count=n_count,
        dead_end=dead_end_det,
        branch=branch_det,
        intersection=inter_det,
        path_algorithm=algo_str,
        path_valid=path_valid,
        path_complete=path_complete,
        path_timeout=path_timeout,
        path_length=path_len,
        nodes_explored=nodes_exp,
        path_cycles=path_cyc,
        current_distance=curr_dist,
        shortest_distance=short_dist,
        extra_moves=x_moves,
        path_efficiency=path_eff,
        route_status=route_str,
        maze_dead_ends=dead_ends,
        maze_branches=branches,
        maze_intersections=intersections,
        maze_complexity=complexity,
        fault_flags=fflags,
        active_faults=active_faults,
        total_cycles=tot_cyc,
        bfs_cycles=bfs_cyc,
        astar_cycles=astar_cyc,
        active_agents=act_agents,
        agent_collision_count=ag_cols,
        agent_goal_count=ag_goals,
        agent0_pos=ag0,
        agent1_pos=ag1,
        agent2_pos=ag2,
        agent3_pos=ag3,
    )

    data_payload = typed_telem.to_dict()
    data_payload["player_pos"] = (player_x, player_y)

    return {
        "scene": "maze",
        "timestamp": time.time(),
        "hardware": is_hardware,
        "state": state_str,
        "player_pos": (player_x, player_y),
        "data": data_payload
    }
