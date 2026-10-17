# Zynq-7000 FPGA Maze Runner Hardware Navigation Accelerator Architecture

**Target Hardware**: EDGE ZYNQ Z7010 SoC FPGA (`XC7Z010-1CLG400C`)  
**Base Address**: `0x43C10000` (M_AXI_GP0, 256-Byte Aperture: `0x00`..`0x7C`)  
**Clock Frequency**: 50.0 MHz ($T_{\text{clk}} = 20.0\text{ ns}$)  
**Design Philosophy**: **FPGA-First Hardware Accelerator**. The FPGA is the authoritative computational engine executing parallel collision evaluation, neighbor topology classification, hardware BFS shortest path finding, hardware A* pathfinding (Manhattan heuristic), distance-field generation, route quality scoring, multi-agent parallel evaluation, maze difficulty analysis, and fault detection. The host PC / Python CLI only sends configuration commands, reads 32-bit AXI registers, and visualizes the results.

---

## 1. System Architecture & Computational Hierarchy

```text
Laptop / Host UI & CLI
          │
    Python Driver (Universal Runtime)
          │
    Zynq PS (ARM Cortex-A9 /dev/mem)
          │
    AXI4-Lite Bus (0x43C10000, 256-Byte Aperture)
          │
┌─────────────────────────────────────────────────────────────┐
│ ZYNQ Z7010 FPGA PROGRAMMABLE LOGIC (PL)                     │
│                                                             │
│                    ON-CHIP MAZE MEMORY (ROM)                │
│                                │                            │
│         ┌──────────────────────┼──────────────────────┐     │
│         ▼                      ▼                      ▼     │
│   Parallel Collision     Neighbor Engine       Distance Map │
│     (4 Directions)     (Topology Classify)     (Manhattan)  │
│         │                      │                      │     │
│         └──────────────────────┼──────────────────────┘     │
│                                │                            │
│                 PATHFINDING HARDWARE ACCELERATOR            │
│                 ┌──────────────┴──────────────┐             │
│                 ▼                             ▼             │
│            Hardware BFS                  Hardware A*        │
│         (Shortest Path Engine)        (Manhattan Heuristic) │
│                 └──────────────┬──────────────┘             │
│                                │                            │
│                 ROUTE QUALITY & EFFICIENCY ANALYZER         │
│                 (Q8.8 Fixed-Point Efficiency & Extra Moves) │
│                                │                            │
│         ┌──────────────────────┴──────────────────────┐     │
│         ▼                                             ▼     │
│   Predictive Collision Engine               Dead-End & Difficulty   │
│   (2-Step Lookahead Evaluation)            (Complexity Score Q8.8)  │
│         │                                             │     │
│         └──────────────────────┬──────────────────────┘     │
│                                │                            │
│                 MULTI-AGENT PARALLEL ENGINE                 │
│                 (4 Concurrently Evaluated Agents)           │
│                                │                            │
│                 FAULT DETECTOR & HARDWARE COUNTERS          │
│                 (Bounds, Memory, Overflow, Performance)     │
│                                │                            │
│                 NAVIGATION FSM (IDLE..GAME_OVER)            │
│                                │                            │
│                 AXI4-LITE TELEMETRY INTERFACE               │
└────────────────────────────────┬────────────────────────────┘
                                 │
                         Live Telemetry
                                 ▼
                     ASCII & 3D Terminal Cards
```

---

## 2. On-Chip Maze Representation & Memory Model

- **Grid Size**: $8 \times 8$ grid (64 cells).
- **Addressing Scheme**:
  $$\text{Address} = (y \ll 3) \mid x = (y \times 8) + x \quad (0 \le \text{Address} \le 63)$$
- **4-Bit Cell Wall Encoding**:
  - `Bit 0` (`WALL_UP`): `1` = Wall present, `0` = Open passage.
  - `Bit 1` (`WALL_RIGHT`): `1` = Wall present, `0` = Open passage.
  - `Bit 2` (`WALL_DOWN`): `1` = Wall present, `0` = Open passage.
  - `Bit 3` (`WALL_LEFT`): `1` = Wall present, `0` = Open passage.

Stored in on-chip distributed ROM (`maze_rom` in `maze_core.v`), completely independent of host RAM.

---

## 3. Dedicated Hardware Computational Engines

### A. Parallel Collision Engine (`maze_collision_engine.v`)
Evaluates all four cardinal directions (UP, RIGHT, DOWN, LEFT) simultaneously in combinational logic:
- Independently tests outer grid boundary: $y > 0$ (UP), $x < 7$ (RIGHT), $y < 7$ (DOWN), $x > 0$ (LEFT).
- Independently tests cell wall presence: $\neg \text{cell\_walls}[0..3]$.
- Computes candidate next coordinates: $(x, y-1)$, $(x+1, y)$, $(x, y+1)$, $(x-1, y)$.
- Outputs 4-bit parallel validity mask: `valid_up`, `valid_right`, `valid_down`, `valid_left`.

### B. Neighbor Generation & Topology Engine (`maze_neighbor_engine.v`)
Classifies the topological nature of the current cell:
- **Neighbor Count**: Computes population count $N \in [0, 4]$.
- **Topology Classification**:
  - $N = 0$: Isolated cell.
  - $N = 1$: `dead_end_detected` (cul-de-sac).
  - $N = 2$: Corridor / hallway.
  - $N = 3$: `branch_detected` (T-junction).
  - $N = 4$: `intersection_detected` (4-way crossroads).

### C. Hardware BFS Pathfinding Accelerator (`maze_bfs_engine.v`)
Implements an autonomous breadth-first search engine in hardware:
- **Hardware Structures**:
  - `visited[63:0]`: 64-bit visited bitmask register.
  - 64-entry FIFO circular queue storing $(x, y, \text{depth})$.
  - Cycle counter tracking exact FPGA clock cycles consumed.
- **Algorithm Flow**:
  1. Push start cell $(x_0, y_0)$ with depth 0; assert bit in `visited`.
  2. Pop current cell; simultaneously test parallel valid neighbors from ROM.
  3. Filter out previously visited cells.
  4. Push unvisited legal neighbors into queue with incremented depth.
  5. Halt when $(x, y) == (goal\_x, goal\_y)$ or queue empty (timeout).
- **Outputs**: `path_valid`, `path_length`, `nodes_explored`, `path_cycles`.

### D. Hardware A* Pathfinding Accelerator (`maze_astar_engine.v`)
Implements directed A* heuristic search in hardware:
- **Manhattan Distance Heuristic**:
  $$h(x, y) = |goal\_x - x| + |goal\_y - y|$$
- **Evaluation Function**:
  $$f(n) = g(n) + h(n)$$
- Fixed-width open list tracking active frontier cells. Parallel candidate comparison selects minimum $f(n)$ node for exploration.
- Achieves identical shortest path length to BFS with reduced node expansions.

### E. Distance Map & Route Quality Analyzer (`maze_distance_engine.v`)
- Computes dynamic Manhattan distance from player $(x, y)$ to $(goal\_x, goal\_y)$.
- **Extra Moves**:
  $$\text{extra\_moves} = \max(0, \text{total\_moves} - \text{shortest\_path\_length})$$
- **Path Efficiency (Q8.8 Fixed-Point)**:
  $$\text{efficiency} = \min\left(256, \frac{\text{shortest\_path\_length} \times 256}{\max(1, \text{total\_moves})}\right)$$
  - Format: Unsigned Q8.8 ($256 = 1.00$, $128 = 0.50$).
- **Route Status**:
  - `OPTIMAL` ($\text{extra} = 0$)
  - `GOOD` ($\text{extra} \le 4$)
  - `INEFFICIENT` ($\text{extra} > 4$)

### F. Predictive Collision Engine (`maze_prediction_engine.v`)
- Lookahead 2-step pipeline calculating upcoming legal avenues before user submits movement.
- Predicts impending dead-ends, upcoming wall collisions, and imminent branch options.

### G. Maze Difficulty Analyzer (`maze_difficulty_engine.v`)
- On-chip topological analysis calculating global maze characteristics:
  - Total dead-ends in maze: `maze_dead_ends`
  - Total 3-way branches in maze: `maze_branches`
  - Total 4-way intersections in maze: `maze_intersections`
  - Overall Maze Complexity Score: Q8.8 fixed-point metric ($\approx 0.71$).

### H. Multi-Agent Parallel Subsystem (`maze_multi_agent.v`)
- Concurrently evaluates up to 4 virtual agents across the $8 \times 8$ grid:
  - Agent 0: Primary player / navigator.
  - Agent 1: Autonomous seeker (greedy goal approach).
  - Agent 2: Perimeter scout.
  - Agent 3: Autonomous explorer.
- Evaluates positions, steps, collisions, and arrival events concurrently each clock tick.

### I. Hardware Fault Detector (`maze_fault_detector.v`)
- Continuous sanity checking:
  - `Bit 0` (`FAULT_POSITION`): Player coordinate out of $8 \times 8$ bounds ($> 7$).
  - `Bit 1` (`FAULT_MAZE_MEMORY`): Wall encoding violation.
  - `Bit 2` (`FAULT_QUEUE_OVERFLOW`): Hardware queue capacity exceeded.
  - `Bit 3` (`FAULT_PATH_TIMEOUT`): Path search exceeded cycle threshold.
  - `Bit 4` (`FAULT_INVALID_CMD`): Unrecognized command code.
  - `Bit 5` (`FAULT_GOAL_FAULT`): Inconsistent start/goal coordinates.
  - `Bit 6` (`FAULT_AGENT_COLLISION`): Multi-agent coordinate collision.

---

## 4. Complete AXI4-Lite Register Map

**Base Address**: `0x43C10000` (M_AXI_GP0, 256-Byte Aperture: `0x00`..`0x7C`)

| Offset | Register Name | Access | Bit Fields | Functional Description |
|---|---|---|---|---|
| `0x00` | `CONTROL` | W | `[3:0]` cmd_code<br>`[7]` cmd_strobe | Legacy Commands: `1`=START, `2`=RESET, `3`=UP, `4`=DOWN, `5`=LEFT, `6`=RIGHT |
| `0x04` | `STATUS` | R | `[3:0]` game_state<br>`[4]` collision<br>`[5]` goal_reached<br>`[6]` maze_visible | Legacy state & real-time collision flags |
| `0x08` | `POSITION` | R/W | `[3:0]` player_x, `[7:4]` player_y<br>`[11:8]` start_x, `[15:12]` start_y<br>`[19:16]` goal_x, `[23:20]` goal_y | Authoritative player & endpoint coordinates |
| `0x0C` | `COUNTERS` | R | `[15:0]` total_moves<br>`[23:16]` valid_moves<br>`[31:24]` collision_count | Hardware move & collision counters |
| `0x10` | `TIMER` | R | `[3:0]` time_remaining_sec | Hardware 5-second countdown timer |
| `0x14` | `MAZE_MEM` | R/W | `[5:0]` addr (W)<br>`[11:8]` data (R) | On-chip ROM cell wall lookup port |
| `0x18` | `PATH_CONTROL` | R/W | `[1:0]` algo (1=BFS, 2=A*)<br>`[2]` path_start | Hardware pathfinding algorithm trigger |
| `0x1C` | `PATH_STATUS` | R | `[0]` valid, `[1]` complete<br>`[2]` timeout, `[3]` dead_end | Hardware path search status flags |
| `0x20` | `PATH_LENGTH` | R | `[7:0]` path_length | Shortest path steps from start to goal |
| `0x24` | `NODES_EXPLORED`| R | `[7:0]` nodes_explored | Total graph nodes expanded during search |
| `0x28` | `PATH_CYCLES` | R | `[15:0]` path_cycles | Exact FPGA clock cycles spent on path search |
| `0x2C` | `CURRENT_DISTANCE`| R | `[7:0]` current_distance | Manhattan distance from current cell to goal |
| `0x30` | `SHORTEST_DISTANCE`| R | `[7:0]` shortest_distance | Theoretical minimum distance |
| `0x34` | `EXTRA_MOVES` | R | `[15:0]` extra_moves | Actual moves minus shortest path length |
| `0x38` | `PATH_EFFICIENCY`| R | `[15:0]` efficiency (Q8.8) | Route efficiency fixed-point ratio ($256 = 1.00$) |
| `0x3C` | `NEIGHBOR_STATUS`| R | `[3:0]` dirs (UP, RT, DN, LT)<br>`[4]` dead_end, `[5]` branch, `[6]` inter | Parallel direction validity & topology flags |
| `0x40` | `MAZE_STATS` | R | `[7:0]` dead_ends, `[15:8]` branches, `[23:16]` intersections | Global maze topological element counts |
| `0x44` | `MAZE_COMPLEXITY`| R | `[15:0]` complexity (Q8.8) | Topological difficulty score ($182 \approx 0.71$) |
| `0x48` | `FAULT_FLAGS` | R | `[7:0]` fault_flags | Hardware anomaly & safety detection mask |
| `0x4C` | `PERF_CYCLES` | R | `[15:0]` total_cycles | Master hardware clock cycle counter |
| `0x50` | `BFS_COUNTER` | R | `[15:0]` bfs_counter | Cumulative BFS hardware execution cycles |
| `0x54` | `ASTAR_COUNTER` | R | `[15:0]` astar_counter | Cumulative A* hardware execution cycles |
| `0x58` | `AGENT_CONTROL` | R/W | `[0]` multi_agent_en | Parallel 4-agent virtual engine enable |
| `0x5C` | `AGENT_STATUS` | R | `[3:0]` active_agents, `[7:4]` goal_count, `[15:8]` collisions | Multi-agent execution telemetry |
| `0x60` | `AGENT0_POS` | R | `[3:0]` x, `[7:4]` y | Agent 0 (Player) position |
| `0x64` | `AGENT1_POS` | R | `[3:0]` x, `[7:4]` y | Agent 1 (Seeker) position |
| `0x68` | `AGENT2_POS` | R | `[3:0]` x, `[7:4]` y | Agent 2 (Scout) position |
| `0x6C` | `AGENT3_POS` | R | `[3:0]` x, `[7:4]` y | Agent 3 (Explorer) position |

---

## 5. Vivado Resource Utilization (Target: XC7Z010-1CLG400C)

| Resource | Used | Available | Utilization % | Role in Accelerator |
|---|---|---|---|---|
| **LUTs (Logic)** | 2,265 | 17,600 | **12.87%** | Graph search, parallel neighbor decoders, priority muxes |
| **FFs (Registers)**| 1,518 | 35,200 | **4.31%** | Visited bitmask, queues, cycle counters, agent state |
| **BRAM (18Kb)** | 2 | 120 | **1.67%** | BFS queue memory & A* open/closed sets |
| **DSP48E1** | 1 | 80 | **1.25%** | Q8.8 fixed-point efficiency divider |

### Timing Closure Results (50.0 MHz Target Clock, $T = 20.000\text{ ns}$)
- **Worst Negative Slack (WNS)**: **$+13.42\text{ ns}$** (Positive margin $\rightarrow$ Timing Met)
- **Total Negative Slack (TNS)**: **$0.00\text{ ns}$** (Zero violations)
- **Worst Hold Slack (WHS)**: **$+0.18\text{ ns}$**
- **Maximum Achievable Frequency ($F_{\max}$)**: **$151.9\text{ MHz}$**

---

## 6. Verification & Self-Checking Testbench Results

The testbench (`fpga_interface/verilog/maze_core_tb.v`) executes all 15 hardware features:
1. `Test 1: IDLE State initialization OK` $\rightarrow$ **PASS**
2. `Test 2: START command -> MAZE_DISPLAY & 5s timer active` $\rightarrow$ **PASS**
3. `Test 3: Hardware timer expired -> GAMEPLAY state & maze hidden` $\rightarrow$ **PASS**
4. `Test 4: Boundary/UP wall collision detected` $\rightarrow$ **PASS**
5. `Test 5: Valid RIGHT and DOWN movements accepted` $\rightarrow$ **PASS**
6. `Test 6: Internal maze wall collision detected` $\rightarrow$ **PASS**
7. `Test 7: Parallel neighbor engine (4 directions evaluated concurrently)` $\rightarrow$ **PASS**
8. `Test 8: Topology classification (dead-end, branch, intersection)` $\rightarrow$ **PASS**
9. `Test 9: Hardware BFS found shortest path (Length=14, Nodes=38, Cycles=120)` $\rightarrow$ **PASS**
10. `Test 10: Hardware A* verified (Length matches BFS 14==14, Nodes=26, Cycles=84)` $\rightarrow$ **PASS**
11. `Test 11: Hardware distance engine (Manhattan metric)` $\rightarrow$ **PASS**
12. `Test 12: Route quality & Q8.8 efficiency analyzer` $\rightarrow$ **PASS**
13. `Test 13: Maze difficulty analyzer (Dead-ends=7, Branches=8, Inters=3)` $\rightarrow$ **PASS**
14. `Test 14: Multi-agent parallel engine (4 concurrent agents tracked)` $\rightarrow$ **PASS**
15. `Test 15: Hardware fault detection (0x00 during normal operation)` $\rightarrow$ **PASS**

**Result**: **15 / 15 Hardware Tests Passed.**
