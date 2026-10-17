# DUAL-EXECUTION ARCHITECTURE SPECIFICATION
## Universal Multi-Scene FPGA System for EDGE ZYNQ Z7010 SoC

---

## 1. Executive Overview & Purpose

The `V_SPACE` project is engineered for the **EDGE ZYNQ Z7010 SoC FPGA development board**.
To allow complete development, software driver testing, integration verification, and interactive demonstrations prior to receiving physical hardware, the project features a **Dual-Execution Architecture**:

```text
                         USER / CLI
                             │
                             ▼
                    Command Parser & CLI
                             │
                             ▼
                       Scene Manager
                             │
                             ▼
                   Scene Hardware Drivers
                     (Register Level)
                             │
                             ▼
               ┌───────────────────────────┐
               │   BaseExecutionBackend    │
               └─────────────┬─────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
   ┌────────────────────┐        ┌────────────────────┐
   │ FPGAHardwareBackend│        │ LaptopFPGAEmulator │
   │                    │        │                    │
   │  Linux /dev/mem    │        │  Software RTL      │
   │  AXI4-Lite MMAP    │        │  Equivalent Model  │
   └──────────┬─────────┘        └──────────┬─────────┘
              │                             │
              ▼                             ▼
       Physical PL RTL            Deterministic Emulation
       (Verilog Cores)            (Bit-Accurate Contract)
              │                             │
              └──────────────┬──────────────┘
                             ▼
                   Shared Register Map
                   Shared Telemetry Decoders
```

### Key Principles
1. **The Laptop Is Not Replacing the FPGA**: It temporarily emulates the FPGA execution layer.
2. **Strict FPGA Limitations**: The laptop emulator strictly implements the computational model intended for RTL execution on the Z7010 (fixed-point arithmetic, circular wrap-arounds, LFSR, FSMs, bounded arrays, deterministic clock ticks). High-level libraries (SciPy, float simulators, dynamic physics engines) are strictly disallowed in the emulator.
3. **Register-Level Transparence**: The scene drivers interact only via 32-bit register reads and writes (`read32` and `write32`). Scene drivers never know whether hardware is present or emulated.
4. **Transparent Identity**: The CLI explicitly identifies `[LAPTOP FPGA EMULATION]` when hardware is absent and `[ZYNQ FPGA HARDWARE]` when physically running on board. It never silently fakes hardware.

---

## 2. Execution Modes

The system supports 3 execution modes via `--mode <auto|fpga|emulator>`:

| Mode | Flag | Hardware Check | Fallback Behavior | Primary Use Case |
|---|---|---|---|---|
| **AUTO** | `--mode auto` (default) | Tests `/dev/mem` access | Falls back to `LaptopFPGAEmulator` | Development laptops and seamless deployment |
| **FPGA** | `--mode fpga` or `--hw` | Enforces `/dev/mem` mmap | Raises `HardwareUnavailableError` if absent | Production validation on physical Zynq ARM Linux |
| **EMULATOR** | `--mode emulator` or `--mock` | Bypasses hardware | Runs `LaptopFPGAEmulator` | Offline algorithmic debugging, CI/CD, golden trace testing |

---

## 3. Peripheral Address Mapping

Every scene peripheral is allocated a 64KB aperture in the Zynq-7000 PL memory space:

| Scene | Peripheral Base Address | Size | Primary Function |
|---|---|---|---|
| **Underwater Probe** | `0x43C00000` | 64 KB | Hydrodynamic fixed-point depth, current drift, recovery |
| **Maze Runner** | `0x43C10000` | 64 KB | 8x8 BRAM maze memory, collision FSM, countdown timer |
| **Mars Space Habitat** | `0x43C20000` | 64 KB | LFSR pseudo-random meteorite generator, impact damage |
| **Solar Gimbal** | `0x43C30000` | 64 KB | 360° circular modulo error, dual-axis tracking FSM |
| **Smart City Traffic** | `0x43C40000` | 64 KB | 5-phase signal FSM, adaptive queue arbitration |

---

## 4. Software RTL Emulation Engine

Located in `python/emulation/`, each model corresponds 1-to-1 with its Verilog core counterpart in `fpga_interface/verilog/`:

- `FPGASimulationClock`: Synchronous master clock supporting discrete `tick()`, batch `run_ticks(n)`, and autonomous thread execution.
- `UnderwaterRTLModel`: Replicates `underwater_probe_core.v`. 16-bit depth (0.1m units), velocity clamping $\pm 5$, arithmetic right shift `>> 4` for current drift, recovery ramp.
- `MazeRTLModel`: Replicates `maze_core.v`. 64x4-bit wall ROM, 5.0s countdown timer, coordinate saturation `[0..7]`, collision detection.
- `MarsHabitatRTLModel`: Replicates `mars_habitat_core.v` and `impact_calculator.v`. 8-bit Galois LFSR ($x^8 + x^6 + x^5 + x^4 + 1$), integer threshold comparisons, link isolation.
- `SolarGimbalRTLModel`: Replicates `solar_gimbal_core.v`. Signed circular azimuth error `(sun - panel + 1800) % 3600 - 1800`, elevation tracking, locked counter threshold.
- `TrafficGridRTLModel`: Replicates `traffic_core.v`. 5-phase traffic signal FSM, green time extension for heavy queues, saturating vehicle counters.
