# V_SPACE Project Overview: Multi-Scene FPGA System

**Target Platform:** AMD EDGE ZYNQ Z7010 SoC Development Board (Xilinx XC7Z010-1CLG400C)  
**System Clock:** 50.000 MHz (AXI4-Lite, `FCLK_CLK0`)  
**Base Address Aperture:** `0x43C00000` – `0x43C4FFFF` (M_AXI_GP0, 64 KB per scene)  

---

## 1. Project Overview & Objectives

The **V_SPACE** project is an advanced, multi-domain cyber-physical FPGA system implementing five diverse real-time computation engines in Verilog RTL, coordinated by a dual-core ARM Cortex-A9 Processing System (PS) on the AMD EDGE Zynq Z7010 SoC.

### Core Objectives:
1. **Hardware-Authoritative Computation:** Execute all physical dynamics, FSM transitions, vector arithmetic, and safety pipelines strictly inside the FPGA Programmable Logic (PL).
2. **Deterministic Real-Time Performance:** Eliminate OS scheduling jitter by offloading control loops to dedicated hardware pipelines operating at 50 MHz.
3. **Structured Complexity Gradient:** Implement a strict hierarchy of five experiments (2 Beginner, 2 Intermediate, and 1 Advanced).
4. **Hardware/Software Parity:** Provide cycle-accurate, bit-accurate Python RTL emulation and MATLAB float64 reference models for automated verification without hardware in the loop.
5. **Universal PS-PL Communication:** A standard 32-bit memory-mapped AXI4-Lite register protocol bridging Linux software and hardware registers.

---

## 2. Hardware / Software Partitioning Architecture

```text
                          USER / OPERATOR
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
        PuTTY Serial Terminal        Web Control Panel
        (115200 baud, 8-N-1)         (HTML5 / CSS / JS)
                  │                           │
                  └─────────────┬─────────────┘
                                │
                                ▼
                       ZYNQ PROCESSING SYSTEM
                        (ARM Cortex-A9 Linux)
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
            CLI Dispatcher              Python Driver
           (Scene Manager)             (Command Parser)
                  │                           │
                  └─────────────┬─────────────┘
                                │
                                ▼
                       Linux /dev/mem Driver
                      (Physical mmap Aperture)
                                │
════════════════════════════════╪══════════════════════════════════════
                         M_AXI_GP0 BUS (50 MHz)
════════════════════════════════╪══════════════════════════════════════
                                │
                                ▼
                     ZYNQ PROGRAMMABLE LOGIC
                    (Xilinx XC7Z010-1CLG400C)
                                │
        ┌───────────────┬───────┴───────┬───────────────┐
        ▼               ▼               ▼               ▼
   EXP 01: UNDERSEA  EXP 02: TRAFFIC  EXP 03: MAZE   EXP 04: SOLAR
  (Depth PID, Drag) (Kinematics, FSM)(ROM, BFS, A*) (Vector Math, LUT)
        │               │               │               │
        └───────────────┼───────────────┼───────────────┘
                        ▼
                EXP 05: MARS HABITAT
            (Coupled Landing & Meteorites)
```

### Partitioning Rules:
- **Programmable Logic (PL):** Authoritative state machine transitions, discrete physics equations, 8-channel parallel spatial pipelines, collision evaluation, trigonometric vector math, timer countdowns.
- **Processing System (PS):** Command string parsing, user menu navigation, `/dev/mem` memory-mapped 32-bit register reads/writes, ASCII/telemetry formatting.

---

## 3. The Five FPGA Experiments

| Experiment | Title | Difficulty | Base Address | Primary Computation | Key RTL Modules |
|---|---|---|---|---|---|
| **01** | [Underwater Dynamic Probe](Experiments/Experiment_01/) | **Beginner** | `0x43C00000` | Closed-loop vertical depth seeking + hydrostatic drag + 7-state recovery FSM | `underwater_probe_core.v`, `underwater_physics_engine.v`, `underwater_pid_controller.v`, `underwater_drag_engine.v` |
| **02** | [Smart City Traffic Grid](Experiments/Experiment_02/) | **Beginner** | `0x43C40000` | Traffic signal arbitration + dynamic green split + 16-channel zero-collision safety pipeline | `traffic_core.v`, `traffic_parallel_vehicle_engine.v`, `traffic_green_split_optimizer.v`, `traffic_emergency_corridor.v` |
| **03** | [3D Maze Runner Game Engine](Experiments/Experiment_03/) | **Intermediate** | `0x43C10000` | Spatial reasoning + 8x8 ROM wall collision + BFS / A* hardware graph search accelerators | `maze_core.v`, `maze_bfs_engine.v`, `maze_astar_engine.v`, `maze_collision_engine.v` |
| **04** | [Dual-Axis Solar Tracking Gimbal](Experiments/Experiment_04/) | **Intermediate** | `0x43C30000` | 3D solar geometry vectors + trigonometric LUT + circular modulo error + 4-panel array estimation | `solar_gimbal_core.v`, `solar_vector_engine.v`, `solar_incident_angle_engine.v`, `solar_tracking_controller.v` |
| **05** | [Mars Space Habitat & Defense](Experiments/Experiment_05/) | **Advanced** | `0x43C20000` | Coupled descent dynamics + 8-channel parallel meteorite detection + kinetic energy + bulkhead isolation | `mars_habitat_core.v`, `mars_landing_physics.v`, `meteorite_parallel_engine.v`, `impact_calculator.v`, `habitat_damage_engine.v` |

---

## 4. Execution & Verification Frameworks

### 1. Physical Hardware Mode (`--hw`)
- Executed natively on the Zynq ARM Cortex-A9 processor.
- Maps physical address space `0x43C00000` via Linux `/dev/mem` using `mmap()`.
- Reads and writes genuine 32-bit registers in the FPGA fabric.
- Strict hardware fail-fast policy: haltes truthfully if `/dev/mem` is disconnected.

### 2. Software Emulator Mode (`--mock`)
- Executed on developer laptops or CI/CD pipelines without physical FPGA hardware.
- Bit-accurate Python emulation models in `python/emulation/` replicating registers, counters, FSM transitions, and arithmetic clamping.
- Validated via 25 automated unit test suites (`tests/`).

### 3. MATLAB Golden Reference Model
- Double-precision Float64 reference model in `MATLAB/` for mathematical verification.
- Compares MATLAB reference calculations against FPGA fixed-point output within strict tolerances (±0.10° on solar angles, ±0.1m on depth).
