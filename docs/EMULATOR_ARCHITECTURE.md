# EMULATOR ARCHITECTURE SPECIFICATION
## Software RTL Emulation Engine (`python/emulation/` & `python/backends/`)

---

## 1. High-Level Emulator Design

The `LaptopFPGAEmulator` provides an in-memory, bit-level software simulation of the FPGA execution layer. It sits underneath the `BaseExecutionBackend` interface:

```text
                  read32(address) / write32(address, value)
                                      │
                                      ▼
                        LaptopFPGAEmulator
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
[0x43C00000..0x43C0FFFF]    [0x43C10000..0x43C1FFFF]    [0x43C20000..0x43C2FFFF]
  UnderwaterRTLModel              MazeRTLModel             MarsHabitatRTLModel
          │                           │                           │
          └───────────────────────────┼───────────────────────────┘
                                      │
                           FPGASimulationClock
                           (tick() / run_ticks(N))
```

---

## 2. Emulation Clock Model (`FPGASimulationClock`)

In the physical FPGA, all five scene cores execute in parallel on the 50 MHz AXI clock (`FCLK0`).
To replicate synchronous execution on a laptop:

- **Master Clock**: `FPGASimulationClock` maintains an internal tick counter.
- **Autonomous Mode**: Runs a background daemon thread that invokes `.tick()` on all registered models at a calibrated frequency (e.g., 10.0 Hz).
- **Synchronous Mode**: For deterministic testing, the autonomous clock can be stopped and pulsed explicitly using `clock.tick()` or `clock.run_ticks(N)`.

```python
clock = FPGASimulationClock(tick_rate_hz=10.0)
clock.register_model(underwater_model)
clock.register_model(maze_model)
# Single synchronous tick across all cores
clock.tick()
```

---

## 3. Register-Level Parity Contract

The emulator reproduces:
1. **Write Side Effects**: Reset strobes (`bit 1`), start/stop strobes (`bit 0`), movement strobes.
2. **Read-Only Status Registers**: Real-time evaluation of FSM state, flags, counters, and telemetry without side effects.
3. **Bit-Field Isolation**: Masks and bit-shifting enforce 32-bit width limits (`& 0xFFFFFFFF`).
4. **Register Offset Decoding**: Translates physical 32-bit addresses into model offset indices.

---

## 4. Scene Emulation Implementation Details

### A. Underwater Model (`UnderwaterRTLModel`)
- Emulates 16-bit depth register: $0 \le D \le 10000$ (0.1m units).
- Emulates 16-bit signed velocity register: clamped to $[-15, 15]$.
- Emulates arithmetic shift for ocean current drift ($x \leftarrow x + (\text{current} \gg 4)$).
- Recovery ramp: When disturbance is cleared, transitions through `DISTURBANCE_RECOVERY` to `HOLD_DEPTH`.

### B. Maze Model (`MazeRTLModel`)
- 64-nibble ROM containing the identical maze layout as `maze_core.v`.
- Wall collision logic reproduces the 4-bit mask `[LEFT, DOWN, RIGHT, UP]`.
- Countdown timer decrements synchronously each tick.
- Goal detection at cell $(7, 7)$.

### C. Mars Habitat Model (`MarsHabitatRTLModel`)
- Implements exact Galois LFSR generator:
  ```python
  feedback = (lfsr & 1)
  lfsr = (lfsr >> 1) ^ (0x71 if feedback else 0)
  ```
- Replicates damage threshold checking ($E > 700 \implies A, E > 650 \implies B$).
- Emulates inter-segment isolation valve actuation when integrity falls below 40%.

### D. Solar Gimbal Model (`SolarGimbalRTLModel`)
- Replicates signed circular error modulo 3600.
- Implements proportional slew steps (Azimuth $\pm 10$, Elevation $\pm 5$).
- Replicates 3-tick lock confirmation before asserting `LOCKED` status bit.

### E. Traffic Grid Model (`TrafficGridRTLModel`)
- 5-phase deterministic countdown FSM (`NS_GREEN`, `NS_YELLOW`, `ALL_RED_1`, `EW_GREEN`, `EW_YELLOW`, `ALL_RED_2`).
- Adaptive timing extensions when vehicle queue exceeds 5.
- Queue dissipation logic (1 vehicle per 3 ticks of active green).
