# Solar Gimbal Software Architecture & Mathematical Reference Layer

This directory contains the **MATLAB reference model, validation, and integration layer** for the dual-axis **Solar Gimbal** tracking system.

---

## 1. Overall System Architecture

```
CLI ──> Python ──> MATLAB ──> Python ──> Zynq FPGA ──> Python ──> CLI
```

The system is currently **software-first / value-driven** (no physical sensors or motors). The FPGA stage represents the eventual real-time hardware controller.

### Dual Execution Modes:

#### A. Pipeline Mode
```
CLI ──> Python ──> MATLAB Preprocessing ──> Python ──> FPGA Execution ──> Python ──> CLI Output
```
- Focuses on end-to-end data throughput and automated coordinate conditioning.

#### B. Comparison Mode
```
                 ┌─────────────────────────────────┐
                 │       CLI / User Input          │
                 │  set sun_azimuth 135 ... track  │
                 └────────────────┬────────────────┘
                                  │
                                  ▼
                     ┌───────────────────────────┐
                     │  Structured Input Object  │
                     └────────────┬──────────────┘
                                  │
            ┌─────────────────────┴─────────────────────┐
            ▼                                           ▼
┌──────────────────────────────┐            ┌───────────────────────────┐
│ MATLAB Reference Model       │            │ Zynq-7000 FPGA Hardware   │
│ (Double-Precision Float64)   │            │ (Fixed-Point Arithmetic)  │
│ - 360° modulo wrap-around    │            │ - Verilog state machine   │
│ - Elevation angle error      │            │ - AXI slave registers     │
│ - Direction determination    │            │ - Independent calculation │
└──────────────┬───────────────┘            └─────────────┬─────────────┘
               │                                          │
               │ MATLAB Result                            │ FPGA Result
               └────────────────────┬─────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │  Python Comparison Engine   │
                     │  (Tolerance: ±0.10°)        │
                     └──────────────┬──────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │ CLI Side-by-Side Comparison │
                     │ VERDICT: PASS / FAIL        │
                     └─────────────────────────────┘
```

---

## 2. Directory Structure

```
MATLAB/
├── solarGimbal/
│   ├── processSolarGimbal.m        # Primary dispatcher & entry point
│   ├── calculateAzimuthError.m     # Azimuth error with 360° wrap-around
│   ├── calculateElevationError.m   # Elevation error calculation
│   ├── calculateMovement.m         # Required movement and optional Kp control
│   ├── validateSolarGimbalInput.m  # Strict physical bounds validator
│   └── README.md                   # This specification file
│
├── integration/
│   └── prepareFPGAInput.m          # Packs result into deterministic FPGA packet
│
└── testing/
    └── testSolarGimbal.m           # 10 automated unit tests
```

---

## 3. Mathematical Model

### Azimuth Error with Angular Wrap-Around
Because azimuth is cyclic ($[0^\circ, 360^\circ)$), naive subtraction yields incorrect motion commands when crossing north ($0^\circ$).
For example:
$$\text{Sun} = 5^\circ, \quad \text{Panel} = 355^\circ \implies \text{Naive: } -350^\circ \quad (\text{WRONG!})$$
The correct shortest path is $+10^\circ$ clockwise.

#### Normalized Modulo Equation:
$$\text{azimuth\_error} = \text{mod}(\text{sun\_azimuth} - \text{panel\_azimuth} + 180^\circ, 360^\circ) - 180^\circ$$

- When $\text{error} > 0 \implies \text{"CLOCKWISE"}$ (turn right)
- When $\text{error} < 0 \implies \text{"COUNTER\_CLOCKWISE"}$ (turn left)
- When $\text{error} == 0 \implies \text{"HOLD"}$

### Elevation Error
$$\text{elevation\_error} = \text{sun\_elevation} - \text{panel\_elevation}$$

- When $\text{error} > 0 \implies \text{"UP"}$
- When $\text{error} < 0 \implies \text{"DOWN"}$
- When $\text{error} == 0 \implies \text{"HOLD"}$

### Movement Output
$$\text{required\_azimuth\_movement} = \text{azimuth\_error}$$
$$\text{required\_elevation\_movement} = \text{elevation\_error}$$

Optional proportional control:
$$u = K_p \times \text{error} \quad (\text{Default } K_p = 1.0)$$

---

## 4. Input & Output Contracts

### Input Object (Python $\rightarrow$ MATLAB)
```json
{
    "scene": "solar_gimbal",
    "sun_azimuth": 135.0,
    "sun_elevation": 42.0,
    "panel_azimuth": 90.0,
    "panel_elevation": 30.0,
    "time_step": 1.0
}
```

### MATLAB Result Structure (`processSolarGimbal`)
```matlab
result = struct( ...
    'scene', "solar_gimbal", ...
    'status', "OK", ...
    'sunAzimuth', 135.0, ...
    'sunElevation', 42.0, ...
    'panelAzimuth', 90.0, ...
    'panelElevation', 30.0, ...
    'azimuthError', 45.0, ...
    'elevationError', 12.0, ...
    'azimuthDirection', "CLOCKWISE", ...
    'elevationDirection', "UP", ...
    'requiredAzimuthMovement', 45.0, ...
    'requiredElevationMovement', 12.0, ...
    'timeStep', 1.0);
```

### Deterministic FPGA Input Packet (`prepareFPGAInput`)
```matlab
fpgaPacket = struct( ...
    'scene_id', uint8(2), ...
    'sun_azimuth', single(135.0), ...
    'sun_elevation', single(42.0), ...
    'panel_azimuth', single(90.0), ...
    'panel_elevation', single(30.0), ...
    'azimuth_error', single(45.0), ...
    'elevation_error', single(12.0), ...
    'status_byte', uint8(7), ...
    'checksum', uint16(43921));
```

---

## 5. CLI Control Panel Usage

Launch the retro interactive CLI:
```bash
python solar_gimbal_cli.py
```

### Example Session:
```text
SOLAR-GIMBAL> set sun_azimuth 135
[OK] sun_azimuth = 135.00°
SOLAR-GIMBAL> set sun_elevation 42
[OK] sun_elevation = 42.00°
SOLAR-GIMBAL> set panel_azimuth 90
[OK] panel_azimuth = 90.00°
SOLAR-GIMBAL> set panel_elevation 30
[OK] panel_elevation = 30.00°
SOLAR-GIMBAL> track

╔══════════════════════════════════════════╗
║          SOLAR GIMBAL OUTPUT             ║
╠══════════════════════════════════════════╣
║ SUN POSITION                             ║
║ Azimuth       : 135.00°                  ║
║ Elevation     : 42.00°                   ║
║                                          ║
║ PANEL POSITION                           ║
║ Azimuth       : 90.00°                   ║
║ Elevation     : 30.00°                   ║
║                                          ║
║ REQUIRED MOVEMENT                        ║
║ Azimuth       : +45.00°                  ║
║ Elevation     : +12.00°                  ║
║                                          ║
║ DIRECTION                                ║
║ Azimuth       : CLOCKWISE                ║
║ Elevation     : UP                       ║
║                                          ║
║ STATUS        : TRACKING                 ║
╚══════════════════════════════════════════╝
```

### Switching to Comparison Mode:
```text
SOLAR-GIMBAL> set mode comparison
[OK] Mode set to COMPARISON
SOLAR-GIMBAL> track

╔══════════════════════════════════════════╗
║       MATLAB vs FPGA COMPARISON          ║
╠══════════════════════════════════════════╣
║ Parameter             MATLAB    FPGA     ║
║ Azimuth Error          45.00°   45.00°   ║
║ Elevation Error        12.00°   12.01°   ║
║ Azimuth Movement       45.00°   45.00°   ║
║ Elevation Movement     12.00°   12.00°   ║
╠══════════════════════════════════════════╣
║ Maximum Error : 0.01°                    ║
║ Tolerance     : ±0.10°                   ║
║ VERDICT       : PASS                     ║
╚══════════════════════════════════════════╝
```

---

## 6. Running Automated Tests

In MATLAB:
```matlab
cd('C:/Users/karti/Desktop/HACK/V_SPACE/MATLAB/testing');
results = testSolarGimbal();
```

Tests include:
1. Normal tracking calculation ($135^\circ / 42^\circ$ vs $90^\circ / 30^\circ$)
2. Azimuth wrap-around ($5^\circ$ vs $355^\circ \implies +10^\circ$)
3. Negative wrap-around ($355^\circ$ vs $5^\circ \implies -10^\circ$)
4. Zero-error / hold condition
5. Downward elevation motion
6. Physical elevation boundaries ($-90^\circ, +90^\circ$)
7. Out-of-range azimuth rejection
8. Out-of-range elevation and negative time step rejection
9. Proportional controller scaling
10. Deterministic FPGA packet formatting
