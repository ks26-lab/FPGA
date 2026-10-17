# Experiment 03: 3D Maze Runner & Hardware Pathfinding Accelerator

**Difficulty Classification:** Intermediate  
**Target Hardware:** AMD EDGE Zynq Z7010 SoC (`XC7Z010-1CLG400C`)  
**AXI4-Lite Base Address:** `0x43C20000` (or `0x43C10000` in Strategy B / `0x43C00000` in Strategy A)  
**Primary Execution Clock:** 50.0 MHz (`s_axi_aclk`), Period = 20.0 ns  

---

## 1. Problem Statement

Autonomous robotic navigation, graph search, and spatial pathfinding in bounded environments require significant CPU cycle budgets when executed as traditional recursive or pointer-heavy software routines. In memory-constrained embedded systems, maintaining dynamic queue structures and visited sets leads to cache thrashing and non-deterministic response times.

This experiment implements an authoritative **FPGA hardware navigation engine** on the Zynq-7000 PL that houses the entire $8 \times 8$ maze grid in dedicated on-chip distributed ROM, evaluates collision boundaries across all four cardinal directions in pure combinational logic, and hardware-accelerates both **Breadth-First Search (BFS)** and **A\* Heuristic Pathfinding** in fixed-cycle state machines.

---

## 2. Objectives

1. Implement an on-chip distributed ROM storing 64 maze cells with 4-bit wall bitmasks (`LEFT`, `DOWN`, `RIGHT`, `UP`).
2. Construct a 4-direction parallel collision engine evaluating boundary and wall constraints simultaneously in a single clock cycle.
3. Accelerate BFS shortest-path exploration directly in FPGA fabric, discovering optimal paths in exactly 120 clock cycles ($2.4\ \mu\text{s}$).
4. Accelerate A* heuristic search using Manhattan distance calculation ($h = |\Delta x| + |\Delta y|$), completing in 84 clock cycles ($1.68\ \mu\text{s}$).
5. Compute real-time distance fields, route extra moves, and Q8.8 fixed-point path efficiency ($256 = 1.00$).
6. Provide an interactive 6-state game FSM featuring a 5-second countdown memorization display.

---

## 3. Technical Background & Mathematical Model

### 3.1 On-Chip Grid & Wall Bitmask
The $8 \times 8$ maze consists of 64 cells addressed by:
$$\text{Address} = (y \ll 3) \mid x \quad (0 \le \text{Address} \le 63)$$
Each cell contains a 4-bit wall descriptor:
- `Bit 0` (`UP`): `1` = Wall, `0` = Open
- `Bit 1` (`RIGHT`): `1` = Wall, `0` = Open
- `Bit 2` (`DOWN`): `1` = Wall, `0` = Open
- `Bit 3` (`LEFT`): `1` = Wall, `0` = Open

### 3.2 4-Direction Parallel Collision Engine
In software, evaluating legal moves requires four conditional branches. In FPGA PL, four parallel comparators evaluate validity in a single gate delay:
$$\text{valid}_{\text{up}} = (y > 0) \land \neg \text{wall}[0]$$
$$\text{valid}_{\text{right}} = (x < 7) \land \neg \text{wall}[1]$$
$$\text{valid}_{\text{down}} = (y < 7) \land \neg \text{wall}[2]$$
$$\text{valid}_{\text{left}} = (x > 0) \land \neg \text{wall}[3]$$

### 3.3 Route Quality & Q8.8 Efficiency Metric
$$\text{efficiency} = \min\left(256,\; \frac{\text{shortest\_path\_length} \times 256}{\max(1,\; \text{total\_moves})}\right) \quad [\text{Q8.8 format}]$$
- Optimal path: $\text{efficiency} = 256$ ($1.00$).
- 2x extra moves: $\text{efficiency} = 128$ ($0.50$).

---

## 4. Hardware & External Components

- **SoC Board:** AMD EDGE Zynq Z7010 (`XC7Z010-1CLG400C`).
- **Processing System:** Dual-core ARM Cortex-A9 @ 667 MHz running Petalinux / Embedded Linux.
- **Diagnostic Board Peripherals:**
  - `board_leds[3:0]` (M14, M15, K16, J16): Displays live 4-bit game state.
  - `led_collision` (L14): Illuminates upon collision with a maze wall.
  - `led_goal_reached` (L15): Illuminates when $(x, y) == (goal\_x, goal\_y)$.
  - `led_maze_visible` (G14): Illuminates during the 5-second initial memorization window.

---

## 5. RTL Architecture & Submodule Responsibilities

All Verilog source modules reside in the `RTL/` subdirectory:

| Module | File | Responsibility |
|---|---|---|
| **Top Wrapper** | `maze_top.v` | Top-level integration module binding core, AXI slave, and board LEDs. |
| **AXI Slave** | `maze_axi_slave.v` | Memory-mapped AXI4-Lite slave decoding addresses `0x00`..`0x7C`. |
| **Master Core** | `maze_core.v` | Coordinates 6-state FSM, 5-second countdown timer, and interconnects submodules. |
| **Maze ROM** | `maze_rom.v` | 64-word on-chip distributed ROM storing the 8x8 maze structure. |
| **Collision Engine**| `maze_collision_engine.v`| Combinational logic simultaneously testing all 4 cardinal directions and topological classification. |
| **Distance Engine** | `maze_distance_engine.v` | Calculates Manhattan distance, extra moves over optimal, and Q8.8 route efficiency. |
| **BFS Engine** | `maze_bfs_engine.v` | Hardware BFS and A* graph search engines evaluating shortest path. |

---

## 6. AXI4-Lite Register Map (`0x43C20000` / `0x43C10000`)

| Offset | Register Name | Access | Width | Description / Bitfields |
|:---:|:---:|:---:|:---:|:---|
| `0x00` | `CONTROL` | W | 32 | `[3:0]` cmd_code (1=START, 2=RESET, 3=UP, 4=DOWN, 5=LEFT, 6=RIGHT), `[7]` strobe |
| `0x04` | `STATUS` | R | 32 | `[3:0]` state (0=IDLE..5=GAMEOVER), `[4]` collision, `[5]` goal_reached, `[6]` maze_visible |
| `0x08` | `POSITION` | R/W | 32 | Read: `[3:0]` pl_x, `[7:4]` pl_y, `[11:8]` st_x, `[15:12]` st_y, `[19:16]` gl_x, `[23:20]` gl_y |
| `0x0C` | `COUNTERS` | R | 32 | `[15:0]` total_moves, `[23:16]` valid_moves, `[31:24]` collision_count |
| `0x10` | `TIMER` | R | 32 | `[3:0]` countdown_seconds_remaining (5 down to 0) |
| `0x14` | `MAZE_MEM` | R/W | 32 | Write: `[5:0]` addr (0..63) \| Read: `[11:8]` 4-bit wall data |
| `0x18` | `PATH_CONTROL` | R/W | 32 | `[1:0]` algo (1=BFS, 2=A*), `[2]` path_start strobe |
| `0x1C` | `PATH_STATUS` | R | 32 | `[0]` path_valid, `[1]` path_complete, `[3]` dead_end |
| `0x20` | `PATH_LENGTH` | R | 32 | `[7:0]` shortest path length (default = 14) |
| `0x24` | `NODES_EXPLORED`| R | 32 | `[7:0]` expanded graph nodes |
| `0x28` | `PATH_CYCLES` | R | 32 | `[15:0]` hardware search execution cycles |
| `0x2C` | `CURRENT_DISTANCE`| R | 32 | `[7:0]` Manhattan distance to goal |
| `0x34` | `EXTRA_MOVES` | R | 32 | `[15:0]` extra moves over shortest path |
| `0x38` | `PATH_EFFICIENCY`| R | 32 | `[15:0]` route efficiency in Q8.8 fixed-point ($256 = 1.00$) |
| `0x3C` | `NEIGHBOR_STATUS`| R | 32 | `[3:0]` valid dirs (UP, RT, DN, LT), `[4]` dead-end, `[5]` branch, `[6]` intersection |
| `0x48` | `FAULT_FLAGS` | R | 32 | `[7:0]` hardware safety detection bitmask |

---

## 7. Clock, Reset, and Timing Requirements

- **Master Clock:** $50\text{ MHz}$ ($20.0\text{ ns}$ clock period), synchronous to `s_axi_aclk`.
- **Clock Constraint:** Defined in `Constraints/edge_zynq_z7010.xdc`:
  ```tcl
  create_clock -period 20.000 -name s_axi_aclk -waveform {0.000 10.000} [get_ports -quiet s_axi_aclk]
  ```
- **Reset:** Active-low synchronous reset (`s_axi_aresetn`).
- **Timing Closure:** Target clock frequency is $50.0\text{ MHz}$. At $20.0\text{ ns}$, worst negative slack (WNS) exceeds $+13.42\text{ ns}$, allowing operation up to $151.9\text{ MHz}$.

---

## 8. Simulation & Verification

### 8.1 Verilog Testbench (`Testbench/maze_core_tb.v`)
The testbench is self-checking and verifies:
1. Reset initialization to default coordinates $(0,0)$ and IDLE state.
2. START command, 5-second countdown timer, and transition to GAMEPLAY.
3. Wall collision detection preventing illegal movement.
4. Valid directional movements updating $(x, y)$.
5. Parallel neighbor direction mask generation.
6. Hardware BFS shortest-path exploration (Length=14 steps, 120 cycles).
7. Hardware A* heuristic exploration (Length=14 steps, 84 cycles).
8. Distance field and Q8.8 route efficiency calculation.
9. Fault detection supervisor nominal state.

To simulate in Vivado XSim:
```tcl
xvlog -i ../RTL ../RTL/*.v ../Testbench/maze_core_tb.v
xelab -debug typical maze_core_tb -s maze_sim
xsim maze_sim -runall
```

### 8.2 Bit-Accurate Python RTL Simulation
To execute the comprehensive Python test suite:
```powershell
python Simulation/run_sim.py
```
Expected output:
```text
======================================================================
EXPERIMENT 03: 3D MAZE RUNNER — RTL SIMULATION TEST SUITE
Platform: AMD EDGE Zynq Z7010 SoC (XC7Z010-1CLG400C)
======================================================================
[TEST 1] Verifying Power-On Reset & Default Coordinates... -> PASS
[TEST 2] Testing Start Command & Countdown Timer...        -> PASS
[TEST 3] Testing Boundary & Wall Collision Checks...       -> PASS
[TEST 4] Triggering Hardware BFS Pathfinding Accelerator... -> PASS
[TEST 5] Triggering Hardware A* Pathfinding Accelerator...  -> PASS
[TEST 6] Evaluating Distance Map & Route Efficiency...      -> PASS
======================================================================
SIMULATION COMPLETE: 6/6 TESTS PASSED (100% PASS RATE)
======================================================================
```

---

## 9. Vivado Synthesis & Implementation Workflow

1. Open Vivado in batch mode:
   ```bash
   vivado -mode batch -source ../../scripts/build_vivado_project.tcl
   ```
2. The script targets part `xc7z010clg400-1`.
3. Adds RTL files from `Experiments/Experiment_03/RTL/`.
4. Adds constraints from `Experiments/Experiment_03/Constraints/edge_zynq_z7010.xdc`.
5. Synthesizes `synth_1` and implements `impl_1` through bitstream generation.
6. Bitstream output: `vivado_project/v_space_fpga.runs/impl_1/maze_top.bit`.

---

## 10. Hardware Execution on Physical Board

1. Program bitstream via FPGA Manager:
   ```bash
   echo maze_top.bit > /sys/class/fpga_manager/fpga0/firmware
   ```
2. Launch authoritative Python CLI on ARM Cortex-A9:
   ```bash
   python3 maze_runner_cli.py --hw
   ```
3. Enter commands:
   - `start`: Initiates 5-second memorization display.
   - `up`, `down`, `left`, `right`: Navigate through the maze.
   - `bfs`: Trigger on-chip BFS shortest path search.
   - `astar`: Trigger on-chip A* heuristic path search.

---

## 11. Known Limitations & Outstanding Tasks

1. **Static Maze Layout:** Default 8x8 maze is stored in distributed ROM. Dynamic reconfigurable maze layouts require writing to block RAM via `REG_MAZE_MEM` in runtime.
2. **Maximum Graph Size:** BFS circular FIFO is optimized for 64 cells. Larger grids ($16 \times 16$ or $32 \times 32$) require scaling BRAM depth.

---

## 12. References

- [MAZE_RUNNER_FPGA_ARCHITECTURE.md](Documentation/MAZE_RUNNER_FPGA_ARCHITECTURE.md)
- [Board Setup Guide](../../Documentation/Board_Setup.md)
- [AXI Register Map Specification](../../Documentation/AXI_Register_Map.md)
- [Resource Utilization Report](../../Documentation/Resource_Utilization.md)
