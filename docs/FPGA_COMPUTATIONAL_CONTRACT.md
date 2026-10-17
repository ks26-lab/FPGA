# FPGA COMPUTATIONAL CONTRACT
## Formal Arithmetic, Precision, Timing, and FSM Rules for EDGE ZYNQ Z7010

---

## 1. Universal Rules

1. **Integer & Fixed-Point Only**: All computations are performed using integer bit vectors. Floating-point operations (`float`, `double`) are strictly prohibited in the computational cores.
2. **Deterministic Clocks**: State advances only upon explicit clock ticks.
3. **Register Strobe Semantics**:
   - Bit 1 of Control Register (`0x00`) is a reset strobe: Writing `1` synchronously resets the core.
   - Read-only status registers update every clock tick based on datapath values.
4. **Saturation & Clamping**: Bit widths are fixed. Arithmetic operations saturate or wrap exactly as defined in Verilog RTL.

---

## 2. Scene Computational Contracts

### Scene 1: Underwater Dynamic Probe (`0x43C00000`)
- **Inputs**: Set Depth (16-bit uint), Target Depth (16-bit uint), Current Drift (8-bit signed int, -100 to +100).
- **Fixed-Point Scaling**: 1 unit = 0.1 meters. (e.g. 40.0 m = 400 units).
- **RTL Arithmetic**:
  - Velocity step: $\Delta v = \text{sign}(\text{target} - \text{depth}) \times 5$ (clamped to $[-15, 15]$ units/tick).
  - Current drift: Lateral displacement increment $x_{drift} = \text{current} \gg 4$.
  - Depth update: $D_{new} = \text{clamp}(D + v, 0, 10000)$ (0.0 m to 1000.0 m).
- **FSM States**:
  - `0`: IDLE
  - `1`: DIVING
  - `2`: LEVEL_FLIGHT
  - `3`: ASCENDING
  - `4`: HOLD_DEPTH
  - `5`: DISTURBANCE_RECOVERY
  - `6`: EMERGENCY_SURFACE

---

### Scene 2: Maze Runner (`0x43C10000`)
- **Memory**: $8 \times 8$ grid stored in 64-nibble ROM/BRAM.
- **Wall Encoding**: 4-bit bitmask per cell `[LEFT, DOWN, RIGHT, UP]`.
- **Inputs**: Strobe movement direction (UP: 0, RIGHT: 1, DOWN: 2, LEFT: 3).
- **Collision Arithmetic**:
  - Check bit `cell_walls[move_dir]`.
  - If `1`, increment collision counter and remain in current cell.
  - If `0`, update coordinates `(x, y)` clamped to $[0..7]$.
- **Timer**: 16-bit countdown register (starts at 50 ticks = 5.0s). When timer hits 0, game transitions to FAIL.
- **FSM States**:
  - `0`: IDLE / INIT
  - `1`: ACTIVE_GAMEPLAY
  - `2`: COLLISION_COOLDOWN
  - `3`: GOAL_REACHED (WIN)
  - `4`: TIMEOUT_FAIL (LOSE)

---

### Scene 3: Mars Space Habitat Defense (`0x43C20000`)
- **PRNG**: 8-bit Galois Linear Feedback Shift Register (LFSR) with characteristic polynomial $P(x) = x^8 + x^6 + x^5 + x^4 + 1$ (mask `0x71`). Seed: `0xA5`.
- **Impact Calculation**:
  - Sequence 0: Big meteorite impact energy = 874.
  - Sequences 1-3: Normal impact energy = $280 + (\text{LFSR}[5:0] \times 2)$.
- **Integrity Damage**:
  - Segment A Threshold: 700. If energy > 700, Segment A damaged (health -15%).
  - Segment B Threshold: 650. If energy > 650, Segment B damaged (health -10%).
  - Link Isolation: If either segment health < 40%, inter-segment atmospheric link isolates (`status[4] = 1`).
- **FSM States**:
  - `0`: MONITORING
  - `1`: WARNING_DETECTED
  - `2`: IMPACT_CALCULATION
  - `3`: DEFENSE_RESPONSE
  - `4`: INTEGRITY_ASSESSMENT

---

### Scene 4: Solar Tracking Gimbal (`0x43C30000`)
- **Angles**: 0.1° resolution. Azimuth: 0 to 3599 ($0.0^\circ - 359.9^\circ$). Elevation: 0 to 900 ($0.0^\circ - 90.0^\circ$).
- **Circular Modulo Error**:
  $$\text{diff} = \text{sun\_az} - \text{panel\_az}$$
  $$\text{if } \text{diff} > 1800 \implies \text{diff} = \text{diff} - 3600$$
  $$\text{if } \text{diff} < -1800 \implies \text{diff} = \text{diff} + 3600$$
- **Control Law**: Proportional step clamp. Azimuth max $\pm 10$ ($1.0^\circ$/tick), Elevation max $\pm 5$ ($0.5^\circ$/tick).
- **Lock Condition**: $|\text{err}_{az}| \le 5$ and $|\text{err}_{el}| \le 5$ sustained for 3 consecutive ticks.
- **FSM States**:
  - `0`: IDLE
  - `1`: ACQUIRE
  - `2`: TRACKING
  - `3`: LOCKED
  - `4`: SLEW_HOLD
  - `5`: EMERGENCY_STOW

---

### Scene 5: Smart City Traffic Grid (`0x43C40000`)
- **Phase Timing**:
  - Base Green: 30 ticks
  - Extended Green (Adaptive): 45 ticks (triggered if queue > 5 vehicles)
  - Yellow: 5 ticks
  - All Red: 2 ticks
- **Queue Saturation**: 8-bit vehicle counters ($0 - 255$). Dissipation rate: 1 vehicle per 3 green ticks.
- **FSM States**:
  - `0`: NS_GREEN
  - `1`: NS_YELLOW
  - `2`: ALL_RED_1
  - `3`: EW_GREEN
  - `4`: EW_YELLOW
  - `5`: ALL_RED_2
