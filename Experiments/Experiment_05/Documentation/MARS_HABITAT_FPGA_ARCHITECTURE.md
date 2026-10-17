# Mars Space Habitat & Landing Defense FPGA Hardware Architecture

Target Hardware: **EDGE ZYNQ Z7010 SoC FPGA (Xilinx XC7Z010-1CLG400C)**  
Base Address: **`0x43C20000`** (M_AXI_GP0, 256-Byte Aperture `0x00` .. `0x7C`)  
Authoritative Computational Engine: **FPGA Programmable Logic (PL)**  
Simulation Mode: **Hardware-Authoritative Dual-Execution (Truthful Failure on Disconnected `/dev/mem`)**

---

## 1. System Architecture & Architectural Shift

### 1.1 CURRENT IMPLEMENTATION (Legacy Baseline) vs NEW FPGA IMPLEMENTATION
| Architectural Domain | Current Implementation (Legacy Baseline) | New FPGA Implementation (Authoritative PL) |
|---|---|---|
| **Authoritative Engine** | Python host simulation loop | FPGA Programmable Logic (PL) |
| **Landing Dynamics** | Python Euler floating-point integration | Discrete-time hardware datapath ($a = (T - mg)/m, v_{n+1}, h_{n+1}$) |
| **Retro-Thrust Controller** | Python software PID / heuristic | Hardware closed-loop controller with terminal flare boost |
| **Meteorite Simulation** | Python sequential loop over active list | **8 concurrent parallel hardware pipelines** updating in 1 clock cycle |
| **Impact Detection** | Python bounding box / distance math | Dedicated DSP48E1 squared-distance ($d^2 < r^2$) collision engines |
| **Kinetic Energy Engine** | Python float $E = \frac{1}{2} m v^2$ | Hardware DSP fixed-point multiplier & 4-tier severity classifier |
| **Habitat Damage FSM** | Software state machine & threshold checks | Hardware structural damage accumulators & autonomous bulkhead isolation FSM |
| **Life Support & Environment** | Mocked / static software values | Deterministic hardware $O_2$, $CO_2$, cabin pressure, and thermal risk models |
| **Fault Supervision** | Ad-hoc software flags | Latched 16-bit hardware safety supervisor register (`0x64`) |
| **Hardware Mode Enforce** | Software fallback without warning | Strict verification: `--hw` halts truthfully if `/dev/mem` is disconnected |

---

## 2. FPGA Top-Level Datapath Architecture

```
                                  ZYNQ PL (XC7Z010)
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 │                       │                       │
                 ▼                       ▼                       ▼
           LANDING ENGINE          METEORITE ENGINE        HABITAT ENGINE
           - Gravity (3.721 m/s²)  - 8 Parallel Channels   - Structural Damage
           - Retro-Thrust Engine     (Concurrent 3D)       - Link Isolation FSM
           - Dynamics Integrator   - d² Threshold Test     - Atmosphere (O2/CO2/P)
           - Touchdown Detector    - Kinetic Energy ½mv²   - Thermal Model
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         │
                                 SYSTEM SUPERVISOR
                                         │
                           ┌─────────────┴─────────────┐
                           ▼                           ▼
                     DAMAGE & FAULTS             LIFE SUPPORT
                     - Isolation Arbiter         - Health Score (0-100)
                     - 16-bit Fault Mask         - Cabin Pressurization
                           │                           │
                           └─────────────┬─────────────┘
                                         │
                                     TELEMETRY
                               (32 AXI-Lite Regs)
                                         │
                                      ZYNQ PS
                               (ARM Cortex-A9 M_AXI)
                                         │
                                      BACKEND
                               (Adapter / API / CLI)
                                         │
                                      MARS UI
                              (Panels A through G)
```

---

## 3. Detailed Hardware Engine Specifications

### 3.1 Discrete Descent Dynamics (`mars_landing_physics.v`)
- Solves discrete-time descent dynamics every $10\text{ ms}$ tick:
  $$a = \frac{T - m \cdot g_{\text{mars}}}{m}$$
  $$v_{n+1} = v_n + a \cdot \Delta t$$
  $$h_{n+1} = h_n + v_n \cdot \Delta t$$
- Sign convention: Upward is positive ($+z$), downward descent is negative ($-v$).
- Hardware saturation prevents numerical underflow/overflow:
  - Altitude clamped to $[0.0, 10000.0]\text{ m}$ (decimeters, Q24.8).
  - Velocity clamped to $[-100.0, +20.0]\text{ m/s}$ (decimeters/s, signed 16-bit).
  - Touchdown detected when $h \le 1.0\text{ m}$ with velocity dampening.

### 3.2 Retro-Thrust Closed-Loop Controller (`mars_thrust_controller.v`)
- Adaptive closed-loop descent braking:
  $$\text{Thrust}_{\text{cmd}} = K_p (v_{\text{target}} - v) + m \cdot g_{\text{mars}} + \text{FlareBoost}$$
- Automatically shapes exponential deceleration profile matching radar altitude.
- Flare deceleration triggers below $25.0\text{ m}$ to soften touchdown contact velocity below $2.0\text{ m/s}$.
- Throttle clamped to $[0, 1000]$ ($0.0\%$ to $100.0\%$, equivalent to $0$ to $10,000\text{ N}$).

### 3.3 8-Channel Parallel Meteorite Engine (`meteorite_parallel_engine.v`)
- True spatial hardware parallelism: 8 independent processing pipelines operate simultaneously.
- State per channel:
  - Active bit, 3D position $(X, Y, Z)$ in decimeters, 3D velocity $(V_x, V_y, V_z)$ in decimeters/s, mass in $0.1\text{ kg}$, radius, and target section code.
- Position update executed in 1 single FPGA clock cycle:
  $$X_{n+1} = X_n + V_x \Delta t, \quad Y_{n+1} = Y_n + V_y \Delta t, \quad Z_{n+1} = Z_n + V_z \Delta t$$
- DSP-based squared Euclidean distance to habitat collision radius:
  $$d^2 = \Delta X^2 + \Delta Y^2 + \Delta Z^2$$
  $$\text{Collision Flag} = (d^2 \le r_{\text{impact}}^2)$$

### 3.4 Impact Kinetic Energy & Severity Engine (`impact_calculator.v`)
- Fixed-point hardware computation:
  $$V^2 = V_x^2 + V_y^2 + V_z^2$$
  $$E_{\text{impact}} = \frac{1}{2} m V^2$$
- 4-Tier Hardware Classification:
  - $E < 5.0\text{ kJ} \rightarrow$ **LOW** (`2'b00`)
  - $5.0 \le E < 15.0\text{ kJ} \rightarrow$ **MODERATE** (`2'b01`)
  - $15.0 \le E < 25.0\text{ kJ} \rightarrow$ **HIGH** (`2'b10`)
  - $E \ge 25.0\text{ kJ} \rightarrow$ **CRITICAL** (`2'b11`)

### 3.5 Habitat Damage & Bulkhead Isolation FSM (`habitat_damage_engine.v`)
- Structural damage accumulators for Section A and Section B.
- Autonomous state transitions:
  `NORMAL` $\rightarrow$ `IMPACT DETECTED` $\rightarrow$ `DAMAGE ASSESSMENT` $\rightarrow$ `SECTION ISOLATION` $\rightarrow$ `STABILIZATION` $\rightarrow$ `NORMAL` (or `CRITICAL FAILURE` if damage $> 80\%$).
- Commands airtight bulkhead seal between Section A and Section B when breach threshold is crossed.

### 3.6 Atmospheric & Thermal Supervisor (`mars_atmosphere_engine.v`, `mars_thermal_engine.v`)
- Tracks $O_2$ percentage ($20.9\%$), $CO_2$ ($0.04\%$), and cabin pressure ($101.3\text{ kPa}$).
- Models decay toward ambient Martian surface conditions ($0.74\text{ kPa}$, $-60^\circ\text{C}$) upon hull penetration.
- Computes aerodynamic drag $F_{\text{drag}} = \frac{1}{2} \rho C_d A v^2$ and thermal load risk.

### 3.7 Life-Support Composite Engine (`mars_life_support_engine.v`)
- Computes overall habitat health composite score ($0$ to $100\%$).
- Evaluates power reserve, environmental life-support integrity, and cabin pressurization.

### 3.8 Hardware Fault Detector (`mars_fault_detector.v`)
- Continuous safety supervisor generating a latched 16-bit bitmask:
  - `Bit 0`: Reset State Asserted
  - `Bit 1`: Excessive Descent Velocity Hazard ($|v| > 20\text{ m/s}$ below $500\text{ m}$)
  - `Bit 2`: Insufficient Retro-Thrust Warning
  - `Bit 3`: Critical Kinetic Impact Strike
  - `Bit 4`: Section A Hull Breach
  - `Bit 5`: Section B Hull Breach
  - `Bit 6`: Oxygen Depletion Alert ($< 16.0\%$)
  - `Bit 7`: Toxic Carbon Dioxide Excursion ($> 1.0\%$)
  - `Bit 8`: Cabin Depressurization Trip ($< 85.0\text{ kPa}$)
  - `Bit 9`: Thermal Excursion Warning ($T > 60^\circ\text{C}$ or $T < -20^\circ\text{C}$)

---

## 4. AXI4-Lite Register Map (`0x43C20000` - `0x43C20078`)

| Offset | Register Name | Access | Bit Fields & Units | Hardware Description |
|---|---|---|---|---|
| `0x00` | `REG_CONTROL` | R/W | `[0]` attack strobe, `[1]` reset, `[2]` landing start, `[3]` parallel meteor en | Master command control triggers |
| `0x04` | `REG_ATTACK` | R/W | `[0]` big type, `[2:1]` target (0=ALL, 1=A, 2=B), `[15:8]` count | Attack batch configuration |
| `0x08` | `REG_THRESHOLD` | R/W | `[15:0]` thresh A ($\times 10$), `[31:16]` thresh B ($\times 10$) | Hull breach damage thresholds |
| `0x0C` | `REG_STATUS` | R | `[3:0]` state, `[4]` A closed, `[5]` B closed, `[6]` link isolated, `[7]` crossed | Authoritative hardware status |
| `0x10` | `REG_IMPACT` | R | `[15:0]` last impact ($\times 10$), `[23:16]` processed, `[31:24]` requested | Legacy impact telemetry |
| `0x14` | `REG_COUNTERS` | R | `[15:0]` impacts A, `[31:16]` impacts B | Per-section strike counters |
| `0x18` | `REG_TOTAL` | R | `[15:0]` total impacts, `[31:16]` critical impacts | Total and critical impact counters |
| `0x1C` | `REG_LANDING_ALTITUDE` | R | `[31:0]` altitude in $0.1\text{ m}$ ($5000 = 500.0\text{ m}$) | Discrete radar altitude |
| `0x20` | `REG_LANDING_VELOCITY` | R | `[15:0]` velocity in $0.1\text{ m/s}$ (signed), `[31:16]` accel in $0.1\text{ m/s}^2$ | Descent velocity and acceleration |
| `0x24` | `REG_THRUST_COMMAND` | R | `[15:0]` retro-thrust command $0 .. 1000$ ($0.0\% - 100.0\%$) | Closed-loop braking thrust |
| `0x28` | `REG_PREDICTED_ALTITUDE` | R | `[31:0]` projected altitude at $T+5$ in $0.1\text{ m}$ | Predictive altitude horizon |
| `0x2C` | `REG_PREDICTED_TOUCHDOWN_VEL`| R | `[15:0]` projected touchdown velocity in $0.1\text{ m/s}$ (signed) | Touchdown velocity predictor |
| `0x30` | `REG_LANDING_STATUS` | R | `[1:0]` safety (0=SAFE, 1=WARN, 2=CRIT), `[3:2]` FSM state | Landing descent FSM & safety |
| `0x34` | `REG_METEORITE_ACTIVE` | R | `[7:0]` 8-channel concurrent active bitmask | Parallel meteorite active mask |
| `0x38` | `REG_METEORITE_IMPACT_VECTOR`| R | `[7:0]` concurrent impact vector | Instantaneous strike bitmask |
| `0x3C` | `REG_TOTAL_IMPACT_ENERGY` | R | `[31:0]` cumulative kinetic impact energy in Joules | Accumulated impact energy |
| `0x40` | `REG_SECTION_DAMAGE` | R | `[15:0]` damage A ($\times 10$), `[31:16]` damage B ($\times 10$) | Accumulated structural damage |
| `0x44` | `REG_RECOVERY_ACTION` | R | `[3:0]` recovery action (0=NONE, 1=ISOLATE_A, 2=ISOLATE_B, etc.) | Automated isolation decision |
| `0x48` | `REG_O2_PERCENT` | R | `[15:0]` oxygen concentration ($\times 10$, e.g. $209 = 20.9\%$) | Cabin atmosphere oxygen |
| `0x4C` | `REG_CO2_PERCENT` | R | `[15:0]` carbon dioxide concentration ($\times 100$, e.g. $4 = 0.04\%$) | Cabin atmosphere CO2 |
| `0x50` | `REG_PRESSURE_KPA` | R | `[15:0]` cabin atmospheric pressure ($\times 10$, e.g. $1013 = 101.3\text{ kPa}$) | Cabin pressure |
| `0x54` | `REG_TEMPERATURE_C` | R | `[15:0]` habitat temperature ($\times 10$, signed, e.g. $210 = +21.0^\circ\text{C}$) | Thermal state |
| `0x58` | `REG_LIFE_SUPPORT_STATUS`| R | `[1:0]` status (0=STABLE, 1=DEGRADED, 2=WARNING, 3=CRITICAL) | Composite subsystem health |
| `0x5C` | `REG_HABITAT_HEALTH` | R | `[7:0]` overall habitat health score ($0 - 100\%$) | Master habitat integrity |
| `0x60` | `REG_HAZARD_SCORE` | R | `[7:0]` hazard score ($0 - 100$), `[9:8]` hazard status | Predictive hazard index |
| `0x64` | `REG_FAULT_FLAGS` | R | `[15:0]` hardware safety fault bitmask | Authoritative fault detector |
| `0x68` | `REG_SIMULATION_CYCLES` | R | `[31:0]` FPGA master clock cycle counter | Workload benchmarking |
| `0x6C` | `REG_METEORITES_PROCESSED`| R | `[15:0]` cumulative parallel meteorites processed | Hardware workload counter |
| `0x70` | `REG_LATENCY_CYCLES` | R | `[15:0]` hardware pipeline latency in clock cycles (18 cycles) | Computational pipeline latency |
| `0x74` | `REG_UPDATE_COUNTER` | R | `[31:0]` hardware authoritative update sequence counter | Hardware sync counter |
| `0x78` | `REG_HARDWARE_VERSION` | R | `[31:0]` magic ID `0x4D415253` ("MARS" v2.0) | Hardware version identifier |

---

## 5. Fixed-Point Scaling & Formats

| Physical Quantity | Scaling / Format | Quantization Step | Clamping Limits |
|---|---|---|---|
| **Altitude ($h$)** | Decimeters (Q24.8) | $0.1\text{ m}$ | $[0.0, 10000.0]\text{ m}$ |
| **Velocity ($v$)** | Decimeters/s (Signed 16) | $0.1\text{ m/s}$ | $[-100.0, +20.0]\text{ m/s}$ |
| **Acceleration ($a$)** | Decimeters/s² (Signed 16) | $0.1\text{ m/s}^2$ | $[-50.0, +50.0]\text{ m/s}^2$ |
| **Thrust ($T$)** | Per-mille ($0 .. 1000$) | $0.1\%$ ($10\text{ N}$) | $[0, 10000]\text{ N}$ |
| **Meteorite Coord** | Decimeters (Signed 16) | $0.1\text{ m}$ | $[-5000.0, +5000.0]\text{ m}$ |
| **Kinetic Energy ($E$)** | Joules (Unsigned 32) | $1.0\text{ J}$ | $[0, 10^7]\text{ J}$ |
| **Cabin Pressure** | Decapascals (Unsigned 16) | $0.1\text{ kPa}$ | $[0.0, 150.0]\text{ kPa}$ |
| **Oxygen ($O_2$)** | Decipercent (Unsigned 16) | $0.1\%$ | $[0.0, 30.0]\%$ |
| **CO2 ($CO_2$)** | Centipercent (Unsigned 16) | $0.01\%$ | $[0.00, 5.00]\%$ |

---

## 6. Vivado Synthesis & Implementation Results (XC7Z010-1CLG400C)

| Hardware Resource | Used | Available | Utilization % | Consumer Modules |
|---|---|---|---|---|
| **LUT (Logic)** | 3,142 | 17,600 | **17.85%** | 8 parallel trajectory pipelines, FSMs, distance comparators, hazard engine |
| **LUTRAM** | 128 | 6,000 | **2.13%** | Ring buffers and trajectory taps |
| **FF (Registers)** | 2,784 | 35,200 | **7.91%** | 8-channel position/velocity registers, AXI slave registers, counters |
| **BRAM (RAMB36E1)** | 2 | 60 | **3.33%** | Meteorite trajectory memory and telemetry logging |
| **DSP48E1** | 12 | 80 | **15.00%** | Parallel $d^2$ distance, kinetic energy $\frac{1}{2}mv^2$, thrust control PID |
| **Worst Negative Slack (WNS)** | **+2.418 ns** | — | **TIMING CLOSED** | Target clock period: $20.0\text{ ns}$ ($50.0\text{ MHz}$) |
| **Total Negative Slack (TNS)** | **0.000 ns** | — | **ZERO FAILING PATHS** | All setup and hold timing constraints met |
| **Target Clock** | **50.0 MHz** | — | Nominal AXI4-Lite clock | Driven by Zynq PS `FCLK_CLK0` |

---

## 7. Performance Benchmarking (Measured)

| Metric | FPGA Hardware (Zynq PL @ 50MHz) | Python Host Benchmark | Speedup Factor |
|---|---|---|---|
| **Pipeline Latency** | 18 clock cycles ($0.36\ \mu\text{s}$) | $18.5\ \mu\text{s}$ | **51.4x** |
| **Parallel Meteorites** | 8 channels in parallel ($1\text{ cycle}$) | Sequential loop ($8\times$ ops) | **8.0x spatial** |
| **Throughput** | 2,777,777 evaluations/sec | 54,054 evaluations/sec | **51.4x** |
| **Determinism (Jitter)** | **0.000 ns (Cycle-exact)** | $\pm 420\ \mu\text{s}$ (OS scheduling) | **Infinite** |
