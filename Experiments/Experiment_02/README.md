# Experiment 02: Smart City Traffic Grid

**Difficulty Classification:** Beginner  
**Target Hardware:** AMD EDGE Zynq Z7010 SoC (`XC7Z010-1CLG400C`)  
**AXI4-Lite Base Address:** `0x43C10000` (or `0x43C40000` in Unified Multi-Scene Subsystem)  
**Primary Execution Clock:** 50.0 MHz (`s_axi_aclk`), Period = 20.0 ns  

---

## 1. Problem Statement

Modern municipal intersections encounter severe vehicular congestion, excessive idle emissions, and delayed emergency response vehicles when governed by conventional fixed-time or software-polled traffic signal controllers. Software-based optimization loops on central servers incur unacceptable network latencies and can fail catastrophically if operating system crashes cause conflicting green lights.

This experiment implements an authoritative **FPGA hardware accelerator in Programmable Logic (PL)** that executes 4-approach directional queue tracking, predictive queue estimation, demand-responsive dynamic green-split optimization, starvation prevention, emergency corridor preemption, and a **16-channel concurrent microscopic vehicle kinematics pipeline** with an enforced hard invariant: **ACTUAL VEHICLE COLLISION == 0**.

---

## 2. Objectives

1. Implement an AXI4-Lite memory-mapped peripheral with a 256-byte register aperture (`0x00`..`0x7C`).
2. Construct a 7-state hardware traffic signal FSM with gate-level mutual exclusion to mathematically prevent conflicting green signals.
3. Implement a 16-channel concurrent parallel vehicle datapath computing positions, velocities, and safe following distances simultaneously in a single clock cycle.
4. Calculate dynamic green splits ($G_{\text{NS}}, G_{\text{EW}}$) clamped between minimum ($G_{\min}$) and maximum ($G_{\max}$) limits.
5. Provide unserved wait-time tracking to detect and eliminate starvation.
6. Provide emergency vehicle preemption and multi-node corridor arterial wave coordination ($I_1 \to I_2 \to I_3 \to I_4$).

---

## 3. Technical Background & Mathematical Model

### 3.1 7-State Mutual-Exclusion FSM
```text
  ┌──────────┐  Timeout   ┌──────────┐  Timeout   ┌──────────┐
  │ NS_GREEN │ ─────────> │ NS_AMBER │ ─────────> │ ALL_RED  │
  └──────────┘            └──────────┘            └────┬─────┘
       ▲                                               │
       │                                               ▼
  ┌────┴─────┐  Timeout   ┌──────────┐  Timeout   ┌──────────┐
  │ ALL_RED  │ <───────── │ EW_AMBER │ <───────── │ EW_GREEN │
  └──────────┘            └──────────┘            └──────────┘
```
- Invariant 1: `ns_green` and `ew_green` can **never** be asserted simultaneously.
- Invariant 2: Transitions between conflicting phases **always** traverse an intermediate `ALL_RED` clearance buffer ($2\text{ s}$).

### 3.2 Dynamic Green Split & Starvation Optimizer
Green split allocation is dynamically proportional to directional queue pressure:
$$G_{\text{NS}} = \text{clamp}\left(G_{\min} + \frac{Q_{\text{NS}}}{Q_{\text{total}}} \cdot (G_{\max} - G_{\min}),\; G_{\min},\; G_{\max}\right)$$
$$G_{\text{EW}} = \text{clamp}\left(G_{\min} + \frac{Q_{\text{EW}}}{Q_{\text{total}}} \cdot (G_{\max} - G_{\min}),\; G_{\min},\; G_{\max}\right)$$
If unserved waiting time $W > T_{\text{starve}}$ ($45\text{ s}$), starvation flags trip, forcing immediate phase rotation regardless of current queue size.

### 3.3 16-Channel Parallel Vehicle Datapath
16 independent hardware registers track vehicle coordinates across North ($V_{0..3}$), South ($V_{4..7}$), East ($V_{8..11}$), and West ($V_{12..15}$):
$$x_i[n+1] = \begin{cases}
x_i[n] + v_i \cdot \Delta t & \text{if } d_{\text{lead}} \ge d_{\text{safe}} \text{ and } (x_i < x_{\text{stop}} \text{ or } \text{phase} = \text{GREEN}) \\
x_i[n] & \text{if brake required}
\end{cases}$$

---

## 4. Hardware & External Components

- **SoC Board:** AMD EDGE Zynq Z7010 (`XC7Z010-1CLG400C`).
- **Processing System:** Dual-core ARM Cortex-A9 @ 667 MHz running Petalinux / Embedded Linux.
- **Diagnostic Board Peripherals:**
  - `board_leds[3:0]` (M14, M15, K16, J16): Displays live 4-bit phase code.
  - `ns_green`, `ns_yellow`, `ns_red` (L14, L15, G14): Direct physical pins driving North-South traffic light head.
  - `ew_green`, `ew_yellow`, `ew_red` (J15, H15, V13): Direct physical pins driving East-West traffic light head.

---

## 5. RTL Architecture & Submodule Responsibilities

All Verilog source modules reside in the `RTL/` subdirectory:

| Module | File | Responsibility |
|---|---|---|
| **Top Wrapper** | `traffic_top.v` | Top-level integration module binding core, AXI slave, and physical LED/signal outputs. |
| **AXI Slave** | `traffic_axi_slave.v` | Memory-mapped AXI4-Lite slave decoding addresses `0x00`..`0x7C` (32 registers). |
| **Master Core** | `traffic_core.v` | 7-state deterministic FSM, gate-level mutual exclusion enforcement, performance counters. |
| **Queue Engine** | `traffic_queue_engine.v` | Directional approach tracking ($Q_N, Q_S, Q_E, Q_W$), departures, and 5-level congestion scoring. |
| **Prediction Engine** | `traffic_prediction_engine.v` | Computes queue velocity $\Delta Q$ and extrapolates arrival demand $Q_{\text{pred}}$. |
| **Split Optimizer** | `traffic_green_split_optimizer.v`| Dynamic green split calculation clamped between $G_{\min}$ and $G_{\max}$, starvation monitoring. |
| **Emergency Corridor**| `traffic_emergency_corridor.v`| Emergency vehicle preemption logic and 4-node arterial corridor synchronization ($I_1 \to I_2 \to I_3 \to I_4$). |
| **Vehicle Engine** | `traffic_parallel_vehicle_engine.v`| **16 concurrent hardware vehicle channels** simultaneously calculating positions and safe distances. |
| **Fault Detector** | `traffic_fault_detector.v` | Hardware safety supervisor detecting green conflicts, pedestrian clashes, and timer stalls. |

---

## 6. AXI4-Lite Register Map (`0x43C10000` / `0x43C40000`)

| Offset | Register Name | Access | Width | Description / Bitfields |
|:---:|:---:|:---:|:---:|:---|
| `0x00` | `REG_CONTROL` | W | 32 | `[0]` step, `[1]` reset, `[2]` override_en, `[3]` override_phase, `[4]` auto, `[5]` emg, `[7:6]` emg_dir, `[8]` ped |
| `0x04` | `REG_CONFIG` | R/W | 32 | `[7:0]` intersection_id, `[15:8]` queue_ns, `[23:16]` queue_ew |
| `0x08` | `REG_TIMING_CFG` | R/W | 32 | `[15:0]` min_green_s, `[31:16]` max_green_s |
| `0x0C` | `REG_STATUS` | R | 32 | `[3:0]` phase (0=NS_G..6=EMG), `[4]` alert, `[5]` override |
| `0x10` | `REG_TELEMETRY` | R | 32 | `[7:0]` green_rem_s, `[15:8]` congestion_score (0-100%), `[23:16]` clr_ns, `[31:24]` clr_ew |
| `0x14` | `REG_CYCLES` | R | 32 | Master simulation tick counter |
| `0x18` | `REG_APPROACH_QUEUES_NS` | R | 32 | `[7:0]` queue_north, `[23:16]` queue_south |
| `0x1C` | `REG_APPROACH_QUEUES_EW` | R | 32 | `[7:0]` queue_east, `[23:16]` queue_west |
| `0x20` | `REG_TOTAL_QUEUES` | R | 32 | `[9:0]` queue_total, `[23:16]` queue_ns_sum, `[31:24]` queue_ew_sum |
| `0x24` | `REG_DYNAMIC_SPLITS` | R | 32 | `[7:0]` calc_green_ns_s, `[23:16]` calc_green_ew_s |
| `0x28` | `REG_WAIT_TIMES` | R | 32 | `[15:0]` ns_wait_time_s, `[31:16]` ew_wait_time_s |
| `0x2C` | `REG_PREDICTED_QUEUES` | R | 32 | `[8:0]` pred_queue_ns, `[24:16]` pred_queue_ew |
| `0x30` | `REG_CONGESTION_LEVELS` | R | 32 | `[2:0]` global_level, `[15:8]` congestion_score |
| `0x34` | `REG_EMERGENCY_STATUS` | R | 32 | `[0]` emg_req, `[2:1]` emg_dir, `[4]` corridor_active, `[7:5]` curr_node, `[10:8]` next_node |
| `0x38` | `REG_PEDESTRIAN_STATUS`| R | 32 | `[0]` ped_walk_active, `[7:1]` ped_time_rem, `[15:8]` ped_serviced_count |
| `0x3C` | `REG_FAULT_FLAGS` | R | 32 | 16-bit safety supervisor fault flags bitmask |
| `0x40` | `REG_FAULT_COUNT` | R | 32 | `[15:0]` fault_count, `[31:16]` collision_events |
| `0x44` | `REG_VEHICLE_OCCUPANCY`| R | 32 | `[15:0]` vehicle_active_mask, `[31:16]` brake_required_mask |
| `0x48` | `REG_VEH_POS_NORTH` | R | 32 | `[7:0]=V0`, `[15:8]=V1`, `[23:16]=V2`, `[31:24]=V3` (meters) |
| `0x4C` | `REG_VEH_POS_SOUTH` | R | 32 | `[7:0]=V4`, `[15:8]=V5`, `[23:16]=V6`, `[31:24]=V7` (meters) |
| `0x50` | `REG_VEH_POS_EAST` | R | 32 | `[7:0]=V8`, `[15:8]=V9`, `[23:16]=V10`, `[31:24]=V11` (meters) |
| `0x54` | `REG_VEH_POS_WEST` | R | 32 | `[7:0]=V12`, `[15:8]=V13`, `[23:16]=V14`, `[31:24]=V15` (meters) |
| `0x58` | `REG_VEH_SPEEDS` | R | 32 | `[7:0]` avg_v_n, `[15:8]` avg_v_s, `[23:16]` avg_v_e, `[31:24]` avg_v_w |
| `0x5C` | `REG_STARVATION_FLAGS` | R/W | 32 | `[0]` ns_starving, `[1]` ew_starving, `[31:16]` starvation_limit_s |

---

## 7. Clock, Reset, and Timing Requirements

- **Master Clock:** $50\text{ MHz}$ ($20.0\text{ ns}$ clock period), synchronous to `s_axi_aclk`.
- **Clock Constraint:** Defined in `Constraints/edge_zynq_z7010.xdc`:
  ```tcl
  create_clock -period 20.000 -name s_axi_aclk -waveform {0.000 10.000} [get_ports -quiet s_axi_aclk]
  ```
- **Reset:** Active-low synchronous reset (`s_axi_aresetn`).
- **Timing Closure:** Target clock frequency is $50.0\text{ MHz}$. At $20.0\text{ ns}$, worst negative slack (WNS) exceeds $+8.12\text{ ns}$.

---

## 8. Simulation & Verification

### 8.1 Verilog Testbench (`Testbench/traffic_tb.v`)
The testbench is self-checking and verifies:
1. Reset initialization to default phase `PHASE_NS_GREEN` ($20\text{ s}$).
2. The hard safety invariant: `actual_collision == 0` across continuous flow.
3. Dynamic green split calculation bounded within $[10, 45]\text{ s}$.
4. 16-channel concurrent microscopic vehicle position calculation.
5. Emergency vehicle corridor preemption and wave progression.
6. Safety supervisor mutual exclusion verification (zero conflicting green).

To simulate in Vivado XSim:
```tcl
xvlog -i ../RTL ../RTL/*.v ../Testbench/traffic_tb.v
xelab -debug typical traffic_tb -s traffic_sim
xsim traffic_sim -runall
```

### 8.2 Bit-Accurate Python RTL Simulation
To execute the comprehensive Python test suite:
```powershell
python Simulation/run_sim.py
```
Expected output:
```text
======================================================================
EXPERIMENT 02: SMART CITY TRAFFIC GRID — RTL SIMULATION TEST SUITE
Platform: AMD EDGE Zynq Z7010 SoC (XC7Z010-1CLG400C)
======================================================================
[TEST 1] Verifying Power-On Reset & Default Phase... -> PASS
[TEST 2] Verifying HARD INVARIANT: Zero actual collisions... -> PASS
[TEST 3] Verifying 16-Channel Concurrent Parallel Vehicle Datapath... -> PASS
[TEST 4] Verifying Dynamic Green-Split Calculation & Starvation Clamp... -> PASS
[TEST 5] Injecting Emergency Vehicle Preemption... -> PASS
[TEST 6] Checking Hardware Safety Supervisor... -> PASS
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
3. Adds RTL files from `Experiments/Experiment_02/RTL/`.
4. Adds constraints from `Experiments/Experiment_02/Constraints/edge_zynq_z7010.xdc`.
5. Synthesizes `synth_1` and implements `impl_1` through bitstream generation.
6. Bitstream output: `vivado_project/v_space_fpga.runs/impl_1/traffic_top.bit`.

---

## 10. Hardware Execution on Physical Board

1. Program bitstream via JTAG or copy to `/lib/firmware/`:
   ```bash
   echo traffic_top.bit > /sys/class/fpga_manager/fpga0/firmware
   ```
2. Run interactive CLI:
   ```bash
   python3 main.py
   scene traffic
   ```
3. Enter commands:
   - `step`: Advance simulation by 1 second.
   - `emg north`: Assert emergency preemption corridor.
   - `ped`: Request pedestrian walk phase.
   - `status`: Display ASCII traffic intersection with queue counters.

---

## 11. Known Limitations & Outstanding Tasks

1. **Fixed Road Geometry:** The 16-vehicle kinematics engine assumes a standardized 4-approach orthogonal intersection with approach lengths of $225\text{ m}$.
2. **Expansion Header IO:** External LED pins `L14..V13` require 3.3V LVCMOS signal conditioning if connected to high-current external indicator lamps.

---

## 12. References

- [TRAFFIC_GRID_FPGA_ARCHITECTURE.md](Documentation/TRAFFIC_GRID_FPGA_ARCHITECTURE.md)
- [Board Setup Guide](../../Documentation/Board_Setup.md)
- [AXI Register Map Specification](../../Documentation/AXI_Register_Map.md)
- [Resource Utilization Report](../../Documentation/Resource_Utilization.md)
