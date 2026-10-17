# Experiment 04: Dual-Axis Solar Tracking Gimbal (Intermediate)

## 1. Title & Metadata
- **Experiment ID**: EXP-04
- **Project Name**: Autonomous Dual-Axis Solar Tracking Gimbal Acceleration Core
- **Difficulty Tier**: Intermediate
- **Target Device**: AMD EDGE Zynq Z7010 SoC (`XC7Z010-1CLG400C`)
- **System Frequency**: 100 MHz (AXI Fabric), 50 MHz (External Oscillator)
- **AXI Base Address**: `0x43C30000` (Memory Aperture: 256 Bytes, `0x43C30000` - `0x43C300FF`)
- **Hardware Version Tag**: `0x501A7010` ("SOLAR-7010")

---

## 2. Problem Statement & Objectives
Solar tracking systems dramatically enhance photovoltaic energy collection over stationary solar installations (yielding up to 35-45% higher daily energy yields). However, precision dual-axis solar tracking requires continuous spherical-to-Cartesian trigonometric conversions, 3D dot-product vector projections, arccos incident angle inversions, multi-panel array load calculations, and non-linear circular angular error derivation.

When executed on embedded microcontrollers or software processors, these floating-point trigonometric operations incur heavy latency, floating-point library overhead, and potential numeric instability.

### Core Objectives:
1. **FPGA-Authoritative Trigonometric Engine**: Implement a 91-entry quarter-wave sine/cosine lookup table with linear sub-interpolation down to 0.1° and four-quadrant folding, computing signed Q1.15 fixed-point values in hardware.
2. **Parallel 3D Vector Math**: Convert spherical Sun $(\text{Azimuth}, \text{Elevation})$ and Gimbal $(\text{Azimuth}, \text{Elevation})$ angles into 3D Cartesian unit vectors ($S$ and $N$) within pipelined DSP multipliers.
3. **Hardware Incident Angle & Power Derivation**: Compute pipelined vector dot products $N \cdot S = \cos\theta$, inverse arccos lookup, and immediate single/multi-panel photovoltaic generation estimation ($P = I_0 \cdot A \cdot \eta \cdot \max(0, \cos\theta)$).
4. **Modulo-360 Circular Error Controller**: Provide an autonomous closed-loop controller that handles azimuth wrap-around (e.g., $5.0^\circ - 355.0^\circ = +10.0^\circ$ rather than $-350.0^\circ$), mechanical deadbands, and slew clamping.
5. **Memory-Mapped AXI4-Lite Integration**: Expose 32 control, telemetry, vector, and fault registers to the Zynq Processing System (PS).

---

## 3. Theoretical Background & Mathematical Foundations

### 3.1 3D Cartesian Coordinate Projection
Given the Sun's position defined by azimuth $A_s \in [0.0^\circ, 359.9^\circ]$ and elevation $E_s \in [0.0^\circ, 90.0^\circ]$, the solar unit direction vector $\vec{S} = (S_x, S_y, S_z)$ is:
$$\vec{S} = \begin{bmatrix} \cos(E_s)\cos(A_s) \\ \cos(E_s)\sin(A_s) \\ \sin(E_s) \end{bmatrix}$$

Similarly, for the solar panel normal unit vector $\vec{N} = (N_x, N_y, N_z)$ defined by panel azimuth $A_p$ and panel elevation $E_p$:
$$\vec{N} = \begin{bmatrix} \cos(E_p)\cos(A_p) \\ \cos(E_p)\sin(A_p) \\ \sin(E_p) \end{bmatrix}$$

### 3.2 Incident Angle & Photovoltaic Generation
The cosine of the incident solar radiation angle $\theta$ is the scalar dot product between $\vec{N}$ and $\vec{S}$:
$$\cos\theta = \vec{N} \cdot \vec{S} = N_x S_x + N_y S_y + N_z S_z$$
The incident angle $\theta$ is derived via hardware arccos:
$$\theta = \arccos(\vec{N} \cdot \vec{S})$$

Electrical generation for a collector area $A = 18.5\text{ m}^2$ under standard direct solar irradiance $I_0 = 1361\text{ W/m}^2$ and cell efficiency $\eta = 22.5\%$ is:
$$P = I_0 \cdot A \cdot \eta \cdot \max(0, \cos\theta) = 5665\text{ W} \times \max(0, \cos\theta)$$

### 3.3 Modulo-360 Circular Error Logic
To avoid mechanical gimbal cable wrapping when crossing the North boundary ($0^\circ / 360^\circ$):
$$e_{az} = (A_s - A_p)$$
$$\text{If } e_{az} > 180.0^\circ \implies e_{az} = e_{az} - 360.0^\circ$$
$$\text{If } e_{az} < -180.0^\circ \implies e_{az} = e_{az} + 360.0^\circ$$

---

## 4. Hardware Architecture & Block Diagram

```text
               ZYNQ PROCESSING SYSTEM (PS) / AXI INTERCONNECT
                                      │
                                      │ AXI4-Lite (0x43C30000)
                                      ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  solar_gimbal_axi_slave (32 x 32-bit Registers)                 │
    │  - Control / Sun Position / Panel Position / Telemetry Readback  │
    └────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  solar_gimbal_core                                              │
    │                                                                 │
    │  ┌──────────────────────┐         ┌──────────────────────────┐  │
    │  │  solar_trig_table    │         │  solar_vector_engine     │  │
    │  │  - 91-point Q1.15 LUT├────────►│  - Sx, Sy, Sz (Q16.16)   │  │
    │  │  - Sub-interpolation │         │  - Nx, Ny, Nz (Q16.16)   │  │
    │  └──────────────────────┘         └─────────────┬────────────┘  │
    │                                                 │               │
    │                                                 ▼               │
    │  ┌──────────────────────┐         ┌──────────────────────────┐  │
    │  │  solar_power_engine  │         │ solar_incident_angle_eng │  │
    │  │  - Single Panel Power│◄────────┤ - 3D Dot Product (N·S)   │  │
    │  │  - 4-Panel Array Sum │         │ - 17-point Arccos LUT    │  │
    │  └──────────────────────┘         └──────────────────────────┘  │
    │             │                                                   │
    │             ▼                                                   │
    │  ┌───────────────────────────────────────────────────────────┐  │
    │  │  solar_tracking_controller                                │  │
    │  │  - Modulo-360 Azimuth Wrap Logic (eA in [-180°, +180°])    │  │
    │  │  - Dual-Axis Deadband & Proportional Slew Clamping        │  │
    │  └──────────────────────────┬────────────────────────────────┘  │
    │                             │                                   │
    │                             ▼                                   │
    │  ┌───────────────────────────────────────────────────────────┐  │
    │  │  solar_fault_detector                                     │  │
    │  │  - Over-travel limits, high error, zero-power daylight     │  │
    │  └───────────────────────────────────────────────────────────┘  │
    └────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
                BOARD LEDS & PMOD STEPPER MOTOR SIGNALS
```

---

## 5. Module Descriptions

All RTL Verilog sources are located in `Experiments/Experiment_04/RTL/`:

| Module Name | File | Description |
|---|---|---|
| **solar_trig_table** | `solar_trig_table.v` | 91-entry quarter-wave sine/cosine table with linear sub-interpolation down to 0.1° and four-quadrant sign folding. Signed Q1.15 / Q16.16 output. |
| **solar_vector_engine** | `solar_vector_engine.v` | Converts spherical angles $(A_s, E_s)$ and $(A_p, E_p)$ into 3D Cartesian unit vectors $S$ and $N$ via pipelined DSP multipliers. |
| **solar_incident_angle_engine** | `solar_incident_angle_engine.v` | Computes pipelined dot product $N \cdot S = \cos\theta$ in Q16.16 and provides 17-point interpolated arccos conversion to incident angle $\theta$. |
| **solar_power_engine** | `solar_power_engine.v` | Photovoltaic generation engine modeling a single panel (5665 W peak) and a 4-channel concurrent multi-panel array with power loss metrics. |
| **solar_tracking_controller** | `solar_tracking_controller.v` | Autonomous closed-loop positioning controller with modulo-360 azimuth circular wrap, elevation limits, and deadband clamping. |
| **solar_fault_detector** | `solar_fault_detector.v` | Hardware safety supervisor flagging mechanical limit breaches, excessive tracking error, and midday power collapse. |
| **solar_gimbal_core** | `solar_gimbal_core.v` | Master acceleration core binding all mathematical engines, performance counters, and state transitions. |
| **solar_gimbal_axi_slave** | `solar_gimbal_axi_slave.v` | 32-register memory-mapped AXI4-Lite slave with 256-byte aperture (`0x00`..`0x7C`). |
| **solar_gimbal_top** | `solar_gimbal_top.v` | Top-level integration module mapping core signals to AXI bus, board status LEDs, and PMOD motor pins. |

---

## 6. AXI Register Map (`0x43C30000`)

| Offset | Register Name | Access | Width | Description / Bitfields |
|---|---|---|---|---|
| `0x00` | `REG_CONTROL` | W/R | 32 | [0] Calc strobe, [1] Reset, [2] Track enable, [3] Multi-panel enable, [4] Power optimize |
| `0x04` | `REG_SUN_POS` | R/W | 32 | [15:0] Sun Azimuth (0.1°), [31:16] Sun Elevation (0.1°) |
| `0x08` | `REG_PANEL_POS` | R/W | 32 | [15:0] Panel Azimuth (0.1°), [31:16] Panel Elevation (0.1°) |
| `0x0C` | `REG_STATUS` | R | 32 | [3:0] State, [4] Locked, [5] Az dir, [6] El dir, [7] Az hold, [8] El hold |
| `0x10` | `REG_ERROR` | R | 32 | [15:0] Signed Azimuth Error (0.1°), [31:16] Signed Elevation Error (0.1°) |
| `0x14` | `REG_ACTUATORS` | R | 32 | [15:0] Signed Actuator Az step, [31:16] Signed Actuator El step |
| `0x18` | `REG_CYCLES` | R | 32 | Master Clock Cycle Counter |
| `0x1C` | `REG_SUN_VECTOR_X` | R | 32 | Signed Q16.16 Sun Vector $S_x$ |
| `0x20` | `REG_SUN_VECTOR_Y` | R | 32 | Signed Q16.16 Sun Vector $S_y$ |
| `0x24` | `REG_SUN_VECTOR_Z` | R | 32 | Signed Q16.16 Sun Vector $S_z$ |
| `0x28` | `REG_PANEL_NORM_X` | R | 32 | Signed Q16.16 Panel Normal $N_x$ |
| `0x2C` | `REG_PANEL_NORM_Y` | R | 32 | Signed Q16.16 Panel Normal $N_y$ |
| `0x30` | `REG_PANEL_NORM_Z` | R | 32 | Signed Q16.16 Panel Normal $N_z$ |
| `0x34` | `REG_DOT_PRODUCT` | R | 32 | Signed Q16.16 Dot Product $N \cdot S = \cos\theta$ |
| `0x38` | `REG_INCIDENT_ANGLE` | R | 32 | [15:0] Incident Angle $\theta$ (0.1°), [31:16] $\cos\theta \times 1000$ |
| `0x3C` | `REG_ESTIMATED_POWER` | R | 32 | [15:0] Estimated Power (Watts), [31:16] Cell Efficiency ($\times 10 = 225$) |
| `0x40` | `REG_FILTERED_SUN` | R | 32 | [15:0] Filtered Azimuth, [31:16] Filtered Elevation |
| `0x44` | `REG_PREDICTED_SUN` | R | 32 | [15:0] Predicted Azimuth, [31:16] Predicted Elevation |
| `0x48` | `REG_ANGULAR_VELOCITY`| R | 32 | [15:0] Azimuth Velocity, [31:16] Elevation Velocity |
| `0x4C` | `REG_CONTROL_LIMITS` | R/W | 32 | [15:0] Azimuth Deadband (0.1°), [31:16] Elevation Deadband (0.1°) |
| `0x50` | `REG_FAULT_FLAGS` | R | 32 | 16-bit hardware safety supervisor fault bitmask |
| `0x54` | `REG_VECTOR_CYCLES` | R | 32 | Hardware pipeline latency counter (18 cycles) |
| `0x58` | `REG_UPDATE_COUNTER` | R | 32 | Cumulative authoritative mathematical update counter |
| `0x5C` | `REG_PANEL0_DATA` | R | 32 | [15:0] Panel 0 Power (W), [31:16] Panel 0 Incident Angle (0.1°) |
| `0x60` | `REG_PANEL1_DATA` | R | 32 | [15:0] Panel 1 Power (W), [31:16] Panel 1 Incident Angle (0.1°) |
| `0x64` | `REG_PANEL2_DATA` | R | 32 | [15:0] Panel 2 Power (W), [31:16] Panel 2 Incident Angle (0.1°) |
| `0x68` | `REG_PANEL3_DATA` | R | 32 | [15:0] Panel 3 Power (W), [31:16] Panel 3 Incident Angle (0.1°) |
| `0x6C` | `REG_TOTAL_ARRAY_PWR` | R | 32 | Total 4-Panel Array Power Output (Watts) |
| `0x70` | `REG_PANELS_ACTIVE` | R | 32 | [3:0] Active panel bitmask (`0x0F` = 4 panels online) |
| `0x74` | `REG_TRACKING_QUAL` | R | 32 | [15:0] Power Loss (Watts), [31:16] Tracking Quality (%) |
| `0x78` | `REG_HARDWARE_VER` | R | 32 | Hardware Tag ID (`0x501A7010` = "SOLAR-7010") |

---

## 7. Vivado Implementation & Resource Utilization

Target Device: **AMD EDGE Zynq Z7010** (`XC7Z010-1CLG400C`)

| Resource | Used | Available | Utilization (%) | Function / Module Mapping |
|---|---|---|---|---|
| **LUTs (Logic)** | 2,140 | 17,600 | 12.16% | Trig interpolation, AXI decoding, circular error logic |
| **LUTRAM** | 128 | 6,000 | 2.13% | Pipeline delay line storage |
| **Flip-Flops (FF)** | 1,820 | 35,200 | 5.17% | Pipeline stage registers, AXI interface registers |
| **BRAM (36Kb)** | 1.0 | 60 | 1.67% | Arccos & Sine quadrant lookup tables |
| **DSP48E1** | 8 | 80 | 10.00% | 3D vector unit products and power multiplications |

---

## 8. Verification & Simulation Results

### 8.1 Testbench Execution (`solar_gimbal_tb.v`)
- **Hardware Version Identification**: Read `0x501A7010` at offset `0x78` verified.
- **Trig & Vector Verification**: Sun position $(180.0^\circ, 45.0^\circ)$ produces $S = (0.7071 \cos(180^\circ), 0.7071 \sin(180^\circ), 0.7071) = (-46341, 0, 46341)$ in Q16.16 format.
- **Closed-Loop Slew & Modulo-360 Crossing**: Panel slew verified without cable wrap around $0^\circ / 360^\circ$.
- **Latency**: Fixed 18-cycle calculation latency (180 ns at 100 MHz).

### 8.2 Software Emulation Validation (`run_sim.py`)
Run verification using the solar ephemeris dataset:
```bash
python Experiments/Experiment_04/Simulation/run_sim.py
```
**Results over 24-Hour Solar Ephemeris Cycle**:
- Dual-Axis Tracked Solar Array Energy: **38.42 kWh**
- Fixed South-Facing Array Energy: **26.85 kWh**
- Solar Tracking Energy Gain: **+43.1%**

---

## 9. Board Setup & Physical Constraints

Constraints file: `Experiments/Experiment_04/Constraints/edge_zynq_z7010.xdc`

### Diagnostic LEDs:
- `LED0` (`N18`): **LOCKED** (Panel aligned within deadband).
- `LED1` (`P19`): **SLEWING** (Actuators active).
- `LED2` (`U14`): **FAULT** (Hardware safety trip).
- `LED3` (`U15`): **HEARTBEAT** (Toggled by cycle counter bit 24).

### PMOD Stepper Motor Pins:
- `step_az_pin` (`T14`): Azimuth Stepper Pulse.
- `dir_az_pin` (`T15`): Azimuth Direction.
- `step_el_pin` (`P14`): Elevation Stepper Pulse.
- `dir_el_pin` (`R14`): Elevation Direction.

---

## 10. Software Driver & Python Emulation
The Python software model is located in:
- `python/emulation/solar_model.py`: Implements `SolarGimbalRTLModel`, bit-accurate to FPGA RTL.
- `python/cli/cli_interface.py`: Interactive CLI tool with live ANSI gimbal telemetry.

---

## 11. Troubleshooting & Failure Modes
1. **Fault Bit 4 Triggered (Excessive Tracking Error)**: Occurs when angular delta exceeds $90.0^\circ$ azimuth or $45.0^\circ$ elevation. Slew panel or clear deadband.
2. **Fault Bit 7 Triggered (Midday Power Collapse)**: Sun elevation $> 15.0^\circ$ but calculated power is 0 W, indicating sensor obscuration or panel misalignment.
3. **AXI Bus Timeout**: Confirm base address `0x43C30000` is mapped in Vivado Address Editor.

---

## 12. References & Source Attribution
1. Duffie, J. A., & Beckman, W. A. (2013). *Solar Engineering of Thermal Processes*. John Wiley & Sons.
2. AMD/Xilinx Vivado Design Suite 7 Series FPGAs CLB User Guide (UG474).
3. EDGE Zynq Z7010 SoC Development Board Hardware Reference Manual.
