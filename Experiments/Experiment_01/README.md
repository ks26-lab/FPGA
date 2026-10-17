# Experiment 01: Underwater Dynamic Probe Simulation

**Difficulty Classification:** Beginner  
**Target Hardware:** AMD EDGE Zynq Z7010 SoC (`XC7Z010-1CLG400C`)  
**AXI4-Lite Base Address:** `0x43C00000` (Aperture: 64 KB / 256 B utilized)  
**Primary Execution Clock:** 50.0 MHz (`s_axi_aclk`), Period = 20.0 ns  

---

## 1. Problem Statement

Autonomous underwater vehicles (AUVs) and oceanographic probes require deterministic closed-loop depth stabilization under hydrodynamic drag, non-linear ocean current drift, and sudden kinetic impacts (marine debris, biological encounters). Software-only control loops executed on standard operating systems suffer from operating system scheduling jitter, unbounded interrupt latencies, and sequential execution overhead.

This experiment implements an authoritative **FPGA hardware accelerator in Programmable Logic (PL)** that executes continuous physics integration, PID depth regulation, quadratic drag computation, digital sensor filtering, collision severity classification, and asymptotic recovery in dedicated hardware datapaths with cycle-accurate determinism.

---

## 2. Objectives

1. Implement an AXI4-Lite memory-mapped peripheral on the Zynq-7000 PL interface (`M_AXI_GP0`).
2. Construct a 7-state deterministic finite state machine (FSM) governing probe trajectory and recovery.
3. Accelerate numerical depth integration ($10\text{ Hz}$ update tick derived from $50\text{ MHz}$ master clock) with signed fixed-point precision ($1\text{ unit} = 0.1\text{ m}$).
4. Implement a digital PID controller with anti-windup clamping to prevent integrator runaway.
5. Implement real-time hydrodynamic drag calculation ($F_{\text{drag}} = K_{\text{drag}} \cdot v_{\text{rel}} \cdot |v_{\text{rel}}|$) and discrete sensor filtering (4-tap MAF for depth, EMA for velocity).
6. Provide physical board diagnostics via LEDs and PWM ballast pump drive.

---

## 3. Technical Background & Mathematical Model

### 3.1 Arithmetic Representation
- **Depth & Position:** 16-bit signed integer in units of $0.1\text{ m}$ ($500 = 50.0\text{ m}$, range $0 \dots 1000.0\text{ m}$).
- **Velocity:** 8-bit signed integer in units of $0.1\text{ m/s}$ (clamped to $[-1.5, +1.5]\text{ m/s}$).
- **Thrust Force:** 16-bit signed integer in units of $0.1\text{ N}$ (nominal neutral buoyancy $= 50.0\text{ N} = 500\text{ units}$, max $= 140.0\text{ N} = 1400\text{ units}$).
- **Drag Force:** Fixed-point calculation with $K_{\text{drag}} = 0.25$:
  $$\Delta v_{\text{rel}} = v_{\text{probe}} - v_{\text{current}}$$
  $$F_{\text{drag}} = \frac{K_{\text{drag}} \cdot \Delta v_{\text{rel}} \cdot |\Delta v_{\text{rel}}|}{16}$$
- **Impact Energy:** Kinetic energy evaluated upon collision strobe:
  $$E_{\text{impact}} = \frac{m_{\text{object}} \cdot v_{\text{rel}}^2}{200}\quad [\text{Joules}]$$

### 3.2 7-State Master Trajectory FSM
```text
           [RESET]
              │
              ▼
         ┌─────────┐   cmd_start   ┌──────────────────────┐   |err| <= 0.5m   ┌──────────────────────┐
         │  IDLE   │ ────────────> │ MOVING_TO_TARGET (1) │ ────────────────> │ TARGET_REACHED (6)   │
         └─────────┘               └──────────┬───────────┘                   └──────────┬───────────┘
                                              │                                          │
                                              │ cmd_disturb_strobe                       │ |err| > 0.8m
                                              ▼                                          │
                                   ┌──────────────────────┐                              │
                                   │  COLLISION_DET (3)   │                              │
                                   └──────────┬───────────┘                              │
                                              │                                          │
                                              ▼                                          │
                                   ┌──────────────────────┐                              │
                                   │   DISPLACEMENT (4)   │                              │
                                   └──────────┬───────────┘                              │
                                              │                                          │
                                              ▼                                          │
                                   ┌──────────────────────┐                              │
                                   │     RECOVERY (5)     │ ─────────────────────────────┘
                                   └──────────────────────┘
```

---

## 4. Hardware & External Components

- **SoC Board:** AMD EDGE Zynq Z7010 (`XC7Z010-1CLG400C`).
- **Processing System:** Dual-core ARM Cortex-A9 @ 667 MHz running Petalinux / Embedded Ubuntu.
- **Interconnect:** Master AXI General Purpose port 0 (`M_AXI_GP0`), 32-bit data bus.
- **Diagnostic Board Peripherals:**
  - `board_leds[3:0]` (M14, M15, K16, J16): Displays live 4-bit state code.
  - `led_collision` (L14): Illuminates during kinetic collision strobe.
  - `led_recovery` (L15): Illuminates during active restorative centering.
  - `led_target_reached` (G14): Illuminates when depth error is within $\pm 0.5\text{ m}$.
  - `pump_pwm_out` (J15): 8-bit digital PWM output signal driving external ballast pump / MOSFET.

---

## 5. RTL Architecture & Submodule Responsibilities

All Verilog source modules reside in the `RTL/` subdirectory:

| Module | File | Responsibility |
|---|---|---|
| **Top Wrapper** | `underwater_probe_top.v` | Top-level module integrating AXI slave, core, physical LED assignments, and PWM generator. |
| **AXI Slave** | `underwater_probe_axi_slave.v` | Memory-mapped AXI4-Lite slave decoding addresses `0x00`..`0x7C` and synchronizing control strobes. |
| **Motion Core** | `underwater_probe_core.v` | Coordinates the 7-state trajectory FSM, $10\text{ Hz}$ update clock divider, and interconnect buses. |
| **Physics Engine** | `underwater_physics_engine.v` | Computes continuous depth error, acceleration, velocity clamping, and discrete depth updates. |
| **PID Controller** | `underwater_pid_controller.v` | Digital proportional-integral-derivative controller with anti-windup clamping and feed-forward drift cancellation. |
| **Drag Engine** | `underwater_drag_engine.v` | Three-stage pipelined quadratic hydrodynamic drag calculator. |
| **Collision Engine**| `underwater_collision_engine.v`| Evaluates kinetic impact energy and classifies severity (LOW, MEDIUM, HIGH, CRITICAL). |
| **Filter Engine** | `underwater_filter_engine.v` | 4-sample Moving Average Filter (depth) and Exponential Moving Average filter (velocity). |
| **Prediction Engine**| `underwater_prediction_engine.v`| Projects forward trajectory at $T+1$, $T+3$, and $T+5$ discrete future steps. |
| **Energy Optimizer**| `underwater_energy_optimizer.v`| Evaluates weighted control cost metric and suggests optimal thrust action. |
| **Fault Detector** | `underwater_fault_detector.v` | 8-channel safety supervisor detecting depth runaway, velocity surge, and sensor anomalies. |
| **Fixed-Point Pkg** | `underwater_fixed_point_pkg.vh`| Macros and arithmetic conversion constants. |

---

## 6. AXI4-Lite Register Map (`0x43C00000`)

| Offset | Name | Type | Reset Value | Bitfield Description |
|:---:|:---:|:---:|:---:|:---|
| `0x00` | `CONTROL` | W | `0x00000000` | `[0]` start, `[1]` stop, `[2]` reset, `[3]` disturb_strobe, `[5:4]` disturb_type, `[6]` set_depth_we |
| `0x04` | `DEPTH_CFG` | R/W | `0x032001F4` | `[15:0]` set_depth (x10), `[31:16]` target_depth (x10) |
| `0x08` | `CURRENT` | R/W | `0x00000014` | `[7:0]` signed current strength % (-100 to +100) |
| `0x0C` | `STATUS` | R | `0x00000000` | `[3:0]` state, `[4]` collision, `[5]` recovery, `[6]` reached, `[8:7]` active_obj |
| `0x10` | `CURRENT_DEPTH` | R | `0x000001F4` | `[15:0]` depth x10 (default 50.0m = 500) |
| `0x14` | `TARGET_DEPTH` | R | `0x00000320` | `[15:0]` target depth x10 (default 80.0m = 800) |
| `0x18` | `VELOCITY` | R | `0x00000000` | `[7:0]` vertical velocity x10 (signed 0.1 m/s) |
| `0x1C` | `DEPTH_ERROR` | R | `0x0000012C` | `[15:0]` target - depth (signed 0.1m) |
| `0x20` | `FILTERED_DEPTH` | R | `0x000001F4` | `[15:0]` 4-tap smoothed depth |
| `0x24` | `FILTERED_VELOCITY`| R | `0x00000000` | `[7:0]` EMA smoothed velocity |
| `0x28` | `DRAG_FORCE` | R | `0x00000000` | `[15:0]` hydrodynamic drag (signed 0.1 N) |
| `0x2C` | `RELATIVE_VELOCITY`| R | `0x00000000` | `[15:0]` probe velocity minus water current |
| `0x30` | `P_TERM` | R | `0x00000000` | `[15:0]` PID proportional contribution |
| `0x34` | `I_TERM` | R | `0x00000000` | `[15:0]` PID integral contribution |
| `0x38` | `D_TERM` | R | `0x00000000` | `[15:0]` PID derivative contribution |
| `0x3C` | `CONTROL_OUTPUT`| R | `0x00000000` | `[15:0]` combined controller command |
| `0x40` | `THRUST_COMMAND`| R | `0x000001F4` | `[15:0]` bounded thrust (0.1 N units, neutral = 500) |
| `0x44` | `THRUST_DELTA` | R | `0x00000000` | `[15:0]` thrust slew rate per tick |
| `0x48` | `IMPACT_ENERGY` | R | `0x00000000` | `[15:0]` kinetic collision energy in Joules |
| `0x4C` | `IMPACT_SEVERITY`| R | `0x00000000` | `[2:0]` 0=NONE, 1=LOW, 2=MED, 3=HIGH, 4=CRIT |
| `0x50` | `RECOVERY_THRUST`| R | `0x000001F4` | `[15:0]` restorative vertical thrust |
| `0x58` | `PRED_DEPTH_1` | R | `0x000001F4` | `[15:0]` projected depth at T+1 tick |
| `0x5C` | `PRED_DEPTH_3` | R | `0x000001F4` | `[15:0]` projected depth at T+3 ticks |
| `0x60` | `PRED_DEPTH_5` | R | `0x000001F4` | `[15:0]` projected depth at T+5 ticks |
| `0x6C` | `FAULT_FLAGS` | R | `0x00000000` | `[7:0]` anomaly bitmask |
| `0x70` | `SIM_CYCLES` | R | `0x00000000` | `[31:0]` simulation cycle counter |

---

## 7. Clock, Reset, and Timing Requirements

- **Master Clock:** $50\text{ MHz}$ ($20.0\text{ ns}$ clock period), synchronous to `M_AXI_GP0_ACLK`.
- **Clock Constraint:** Defined in `Constraints/edge_zynq_z7010.xdc`:
  ```tcl
  create_clock -period 20.000 -name s_axi_aclk -waveform {0.000 10.000} [get_ports -quiet s_axi_aclk]
  ```
- **Reset:** Active-low synchronous reset (`s_axi_aresetn`), driven by PS reset block (`rst_ps7_50M`).
- **Timing Closure:** Target clock frequency is $50.0\text{ MHz}$. At $20.0\text{ ns}$, worst negative slack (WNS) exceeds $+12.4\text{ ns}$, ensuring robust timing closure across industrial operating temperatures.

---

## 8. Simulation & Verification

### 8.1 Verilog Testbench (`Testbench/underwater_probe_tb.v`)
The testbench is self-checking and tests 10 operational aspects:
1. Reset initialization to default parameters ($50.0\text{ m}$, target $80.0\text{ m}$, state IDLE).
2. Start command and depth error calculation.
3. PID controller response and positive thrust generation.
4. Hydrodynamic drag calculation.
5. Moving Average and EMA filtering.
6. Look-ahead future depth prediction ($T+1, T+3, T+5$).
7. Energy optimizer cost metric.
8. Disturbance injection (`WHALE`) with kinetic impact energy calculation.
9. Asymptotic recovery FSM engagement.
10. Fault supervisor nominal state.

To simulate in Vivado XSim:
```tcl
xvlog -i ../RTL ../RTL/*.v ../Testbench/underwater_probe_tb.v
xelab -debug typical underwater_probe_tb -s probe_sim
xsim probe_sim -runall
```

### 8.2 Bit-Accurate Python RTL Simulation
To execute the comprehensive Python test suite without Vivado installed:
```powershell
python Simulation/run_sim.py
```
Expected output:
```text
======================================================================
EXPERIMENT 01: UNDERWATER DYNAMIC PROBE — RTL SIMULATION TEST SUITE
Platform: AMD EDGE Zynq Z7010 SoC (XC7Z010-1CLG400C)
======================================================================
[TEST 1] Verifying Power-On Reset & Default Register Values... -> PASS
[TEST 2] Verifying Target-Seeking PID Motion Loop...           -> PASS
[TEST 3] Injecting Kinetic Disturbance (WHALE)...              -> PASS
[TEST 4] Verifying 7-State Hardware Recovery Routine...       -> PASS
[TEST 5] Verifying Parallel Look-Ahead Depth Predictor...      -> PASS
[TEST 6] Verifying MAF/EMA Sensor Filtering...                -> PASS
[TEST 7] Checking Safety Supervisor Flags...                  -> PASS
======================================================================
SIMULATION COMPLETE: 7/7 TESTS PASSED (100% PASS RATE)
======================================================================
```

---

## 9. Vivado Synthesis & Implementation Workflow

1. Open Vivado in batch mode:
   ```bash
   vivado -mode batch -source ../../scripts/build_vivado_project.tcl
   ```
2. The script configures project `v_space_fpga` for part `xc7z010clg400-1`.
3. Adds RTL files from `Experiments/Experiment_01/RTL/`.
4. Adds constraints from `Experiments/Experiment_01/Constraints/edge_zynq_z7010.xdc`.
5. Synthesizes `synth_1` and implements `impl_1` through bitstream generation.
6. Bitstream output: `vivado_project/v_space_fpga.runs/impl_1/underwater_probe_top.bit`.

---

## 10. Hardware Execution on Physical Board

1. Copy bitstream to target Zynq Linux board via SCP:
   ```bash
   scp underwater_probe_top.bit root@192.168.1.10:/lib/firmware/
   ```
2. Program bitstream via FPGA Manager:
   ```bash
   echo underwater_probe_top.bit > /sys/class/fpga_manager/fpga0/firmware
   ```
3. Launch authoritative Python CLI on ARM Cortex-A9:
   ```bash
   python3 fpga_interface/python/underwater_probe_cli.py --hw
   ```
4. Enter commands:
   - `start`: Starts target tracking from $50.0\text{ m}$ toward $80.0\text{ m}$.
   - `disturb whale`: Injects kinetic impact; observe `led_collision` and `led_recovery`.
   - `status`: Displays live 3-panel terminal telemetry.

---

## 11. Known Limitations & Outstanding Tasks

1. **Board LED Pin Verification:** Pins `M14, M15, K16, J16` are mapped to standard Z7010 headers. Users must confirm against vendor board schematic if using a custom carrier board.
2. **Fixed-Point Granularity:** Depth scaling is fixed at $0.1\text{ m}$. Micro-depth excursions ($< 10\text{ cm}$) are quantized out.

---

## 12. References

- [UNDERWATER_PROBE_FPGA_ARCHITECTURE.md](Documentation/UNDERWATER_PROBE_FPGA_ARCHITECTURE.md)
- [Board Setup Guide](../../Documentation/Board_Setup.md)
- [AXI Register Map Specification](../../Documentation/AXI_Register_Map.md)
- [Resource Utilization Report](../../Documentation/Resource_Utilization.md)
