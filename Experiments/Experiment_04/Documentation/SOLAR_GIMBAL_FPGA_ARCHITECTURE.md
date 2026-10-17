# Scene 4: Solar Tracking Gimbal — Zynq Z7010 FPGA Architecture & Acceleration Report

## 1. Executive Summary & Architectural Overview

The **Solar Tracking Gimbal** subsystem has been upgraded into an **FPGA-authoritative parallel mathematical accelerator** targeting the **EDGE ZYNQ Z7010 SoC FPGA** (`XC7Z010-1CLG400C`).

Rather than performing 3D trigonometric transformations, vector dot-products, incident angle inversions, photovoltaic power estimation, and predictive tracking in software, **all authoritative physical and mathematical computations execute in FPGA Programmable Logic (PL)**.

The software stack (Python CLI/UI) is strictly an AXI transport and telemetry decoding layer.

```text
             USER / DATASET
                   │
                   ▼
              PYTHON CLI
                   │
                   │ AXI4-Lite (0x43C30000)
                   ▼
        ┌─────────────────────────────────────────────────────────┐
        │                 ZYNQ Z7010 PL (100 MHz)                 │
        │                                                         │
        │  ┌──────────────────┐    ┌───────────────────────────┐  │
        │  │ Sun Vector Engine│    │ Trig Table (91-Entry ROM) │  │
        │  │ Sx, Sy, Sz       │◄───┤ Q1.15 Folded Sub-Interp   │  │
        │  └────────┬─────────┘    └─────────────┬─────────────┘  │
        │           │                            │                │
        │           ▼                            ▼                │
        │  ┌───────────────────────────────────────────────────┐  │
        │  │   4-Channel Concurrent Parallel Panel Array       │  │
        │  │   Panel 0    │   Panel 1    │  Panel 2 │  Panel 3 │  │
        │  │   N0·S -> θ0 │   N1·S -> θ1 │  N2·S->θ2│  N3·S->θ3│  │
        │  │   P0 (Watts) │   P1 (Watts) │  P2 (W)  │  P3 (W)  │  │
        │  └──────────────────────┬────────────────────────────┘  │
        │                         │                               │
        │                         ▼                               │
        │  ┌───────────────────────────────────────────────────┐  │
        │  │ Closed-Loop Two-Axis Circular Tracking Controller │  │
        │  │  - Modulo-360 Azimuth Wrap (5° - 355° = +10°)     │  │
        │  │  - Deadband Hold & Mechanical Limit Protection    │  │
        │  │  - EMA Noise Filter & Trajectory Prediction       │  │
        │  │  - Perturb-and-Observe Power Optimizer (MPPT)     │  │
        │  └──────────────────────┬────────────────────────────┘  │
        │                         │                               │
        │                         ▼                               │
        │  ┌───────────────────────────────────────────────────┐  │
        │  │ Hardware Safety Supervisor & Performance Counters │  │
        │  │  - 16-Bit Fault Bitmask (Limits, Stall, Collapse) │  │
        │  │  - Vector Latency Cycles & Master Update Counter  │  │
        │  └──────────────────────┬────────────────────────────┘  │
        └─────────────────────────┼───────────────────────────────┘
                                  │
                                  ▼
                        AXI4-Lite TELEMETRY
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            Python CLI Shell            Real-Time UI Card
```

---

## 2. FPGA Computational Engine Modules

All Verilog source modules reside in `Experiments/Experiment_04/RTL/`:

| Module | File | Hardware Acceleration Description | Primary Resources |
|---|---|---|---|
| **Trig Table** | `solar_trig_table.v` | 91-entry primary sine/cosine quarter-wave LUT with linear sub-interpolation down to 0.1° and four-quadrant folding. Outputs signed Q1.15 values. | Distributed LUT ROM |
| **Vector Engine** | `solar_vector_engine.v` | Spherical-to-Cartesian conversion producing unit vectors $S = (\cos E_s \cos A_s, \cos E_s \sin A_s, \sin E_s)$ and $N = (\cos E_g \cos A_g, \cos E_g \sin A_g, \sin E_g)$. | 4x DSP48E1 multipliers, pipeline regs |
| **Incident Engine** | `solar_incident_angle_engine.v` | Pipelined 3D dot product $N \cdot S = \cos\theta$ and 17-segment hardware arccos lookup producing incidence angle $\theta \in [0.0^\circ, 180.0^\circ]$. | 3x DSP48E1 multipliers, adders |
| **Power Engine** | `solar_power_engine.v` | Photovoltaic generation: $P = I_0 \cdot A \cdot \eta \cdot \max(0, \cos\theta)$ where $I_0 = 1361\text{ W/m}^2$, $A = 18.5\text{ m}^2$, $\eta = 22.5\%$, $P_{\max} = 5665\text{ W}$. | 1x DSP48E1 multiplier, shift logic |
| **Tracking Controller** | `solar_tracking_controller.v` | Two-axis circular error derivation with modulo-360 wrap-around, proportional slew clamping, deadband holding, and mechanical limit checks. | Adders, comparators, clamp logic |
| **Fault Detector** | `solar_fault_detector.v` | Hardware supervisor flagging angle invalidity, mechanical limits, excessive error, sensor disagreement, and power collapse. | Priority bitmask encoder |
| **AXI Slave** | `solar_gimbal_axi_slave.v` | 32-register memory-mapped slave with 256-byte aperture (0x00..0x7C). | AXI decode logic, registers |
| **Top Wrapper** | `solar_gimbal_top.v` | Top-level module binding core to AXI slave and diagnostic board LEDs. | Integration logic |

---

## 3. AXI4-Lite Register Map (`0x43C30000`)

| Offset | Register Name | Access | Width | Description / Bitfields |
|---|---|---|---|---|
| `0x00` | `REG_CONTROL` | W | 32 | Bit 0: calc_strobe, Bit 1: reset_strobe, Bit 2: track_en, Bit 3: multi_panel_en, Bit 4: opt_power_en |
| `0x04` | `REG_SUN_POS` | R/W | 32 | [15:0] sun_azimuth (0.1°), [31:16] sun_elevation (0.1°) |
| `0x08` | `REG_PANEL_POS` | R/W | 32 | [15:0] panel_azimuth (0.1°), [31:16] panel_elevation (0.1°) |
| `0x0C` | `REG_STATUS` | R | 32 | [3:0] state, [4] locked, [5] az_dir, [6] el_dir, [7] az_hold, [8] el_hold |
| `0x10` | `REG_ERROR` | R | 32 | [15:0] signed az_error (0.1°), [31:16] signed el_error (0.1°) |
| `0x14` | `REG_ACTUATORS` | R | 32 | [15:0] signed actuator_az step, [31:16] signed actuator_el step |
| `0x18` | `REG_CYCLES` | R | 32 | Master cycle counter |
| `0x1C` | `REG_SUN_VECTOR_X` | R | 32 | Q16.16 signed Sun direction vector $S_x$ |
| `0x20` | `REG_SUN_VECTOR_Y` | R | 32 | Q16.16 signed Sun direction vector $S_y$ |
| `0x24` | `REG_SUN_VECTOR_Z` | R | 32 | Q16.16 signed Sun direction vector $S_z$ |
| `0x28` | `REG_PANEL_NORMAL_X` | R | 32 | Q16.16 signed Panel normal vector $N_x$ |
| `0x2C` | `REG_PANEL_NORMAL_Y` | R | 32 | Q16.16 signed Panel normal vector $N_y$ |
| `0x30` | `REG_PANEL_NORMAL_Z` | R | 32 | Q16.16 signed Panel normal vector $N_z$ |
| `0x34` | `REG_DOT_PRODUCT` | R | 32 | Q16.16 signed $N \cdot S = \cos\theta$ |
| `0x38` | `REG_INCIDENT_ANGLE` | R | 32 | [15:0] incident_angle (0.1°), [31:16] cos_incidence ($\times 1000$) |
| `0x3C` | `REG_ESTIMATED_POWER` | R | 32 | [15:0] estimated_power (Watts), [31:16] efficiency ($\times 10$) |
| `0x40` | `REG_FILTERED_SUN` | R | 32 | [15:0] filtered_az (0.1°), [31:16] filtered_el (0.1°) |
| `0x44` | `REG_PREDICTED_SUN` | R | 32 | [15:0] predicted_az (0.1°), [31:16] predicted_el (0.1°) |
| `0x48` | `REG_ANGULAR_VELOCITY` | R | 32 | [15:0] signed $\omega_A$ (0.1°/tick), [31:16] signed $\omega_E$ (0.1°/tick) |
| `0x4C` | `REG_CONTROL_LIMITS` | R/W | 32 | [15:0] az_deadband (0.1°), [31:16] el_deadband (0.1°) |
| `0x50` | `REG_FAULT_FLAGS` | R | 32 | 16-bit hardware safety fault bitmask |
| `0x54` | `REG_VECTOR_CYCLES` | R | 32 | Latency performance counter (18 cycles) |
| `0x58` | `REG_UPDATE_COUNTER` | R | 32 | Cumulative authoritative update counter |
| `0x5C` | `REG_PANEL0_DATA` | R | 32 | [15:0] Panel 0 power (W), [31:16] Panel 0 incident angle (0.1°) |
| `0x60` | `REG_PANEL1_DATA` | R | 32 | [15:0] Panel 1 power (W), [31:16] Panel 1 incident angle (0.1°) |
| `0x64` | `REG_PANEL2_DATA` | R | 32 | [15:0] Panel 2 power (W), [31:16] Panel 2 incident angle (0.1°) |
| `0x68` | `REG_PANEL3_DATA` | R | 32 | [15:0] Panel 3 power (W), [31:16] Panel 3 incident angle (0.1°) |
| `0x6C` | `REG_TOTAL_ARRAY_POWER`| R | 32 | Total 4-panel array generated electrical power (Watts) |
| `0x70` | `REG_PANELS_ACTIVE_MASK`| R | 32 | [3:0] active panel bitmask (0x0F = 4 panels online) |
| `0x74` | `REG_TRACKING_QUALITY` | R | 32 | [15:0] power_loss_w (Watts), [31:16] tracking_quality (%) |
| `0x78` | `REG_HARDWARE_VERSION` | R | 32 | Hardware ID version tag (`0x501A7010` = "SOLAR-7010") |
