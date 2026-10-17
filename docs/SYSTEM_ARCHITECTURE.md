# Universal Runtime Communication Architecture

## 1. Executive Summary

This architecture establishes a universal, common software communication framework for the **EDGE ZYNQ Z7010 SoC development board** running multi-scene FPGA simulations:
1. **Solar Gimbal** (Autonomous 3D sun-tracking and circular error correction)
2. **Maze Runner** (Autonomous 8x8 hardware maze navigation with collision evaluation)
3. **Mars Space Habitat** (Ballistic meteorite impact calculation and link isolation)
4. **Underwater Dynamic Probe** (Fluidic depth evolution, current drift, and obstacle recovery)
5. **Traffic Grid** (Autonomous signal phase arbitration and queue optimization)

---

## 2. Separation of Responsibilities

```text
                         USER
                          │
                          │ Human commands (e.g. "scene underwater", "set depth 40")
                          ▼
                  ┌─────────────────┐
                  │   PuTTY /       │
                  │   Serial CLI    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Python Runtime  │
                  │                 │
                  │ Command Parser  │
                  │ Scene Manager   │
                  │ Scene Driver    │
                  └────────┬────────┘
                           │
                           │ 32-bit register reads/writes
                           ▼
                  ┌─────────────────┐
                  │ AXI Interface   │
                  │ /dev/mem mmap   │
                  └────────┬────────┘
                           │
                           ▼
                 ┌──────────────────────┐
                 │     ZYNQ Z7010       │
                 │                      │
                 │ ARM Cortex-A9        │
                 │      │               │
                 │      │ AXI           │
                 │      ▼               │
                 │ AXI Interconnect     │
                 │      │               │
                 │      ▼               │
                 │ Scene AXI Peripheral │
                 │      │               │
                 │      ▼               │
                 │ Scene FPGA Core      │
                 └─────────┬────────────┘
                           │
                           │ Live 32-bit telemetry registers
                           ▼
                  ┌─────────────────┐
                  │ Python Decoder  │
                  │                 │
                  │ Telemetry Object│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ CLI Renderer    │
                  └────────┬────────┘
                           │
                           ▼
                         USER
```

### Strict Architectural Boundaries:
- **Vivado is NOT the runtime UI**: Vivado synthesizes RTL and programs the PL bitstream via JTAG. Once programmed, Vivado is closed or minimized.
- **Python is NOT the simulation engine**: Python never calculates wall collisions, fluid drift, impact damage, or sun tracking. Python translates human text to register writes and unpacks FPGA telemetry.
- **FPGA is Authoritative**: All state transitions, physics formulas, countdown timers, collision boundaries, and control logic execute purely in Verilog hardware logic.
- **PuTTY is the User Terminal**: PuTTY connects to Zynq Linux via serial/SSH, hosting the Python interactive CLI session.

---

## 3. Hardware / Software Partitioning Table

| Component | Responsibility | Technology |
|---|---|---|
| **User Interface** | Accepts text commands, renders ASCII status panels | PuTTY / Python CLI |
| **Command Translation** | Syntax validation, bounds checking, parameter scaling | `CommandParser` / `SceneManager` |
| **Hardware Driver** | Memory-mapped register packing, strobing, reading | `BaseFPGADriver` / `AXIInterface` |
| **Bus Bridge** | Memory-mapped physical address translation | Linux `/dev/mem` + `mmap` |
| **SoC Processor** | Executes Linux kernel and Python runtime | ARM Cortex-A9 PS |
| **Bus Interconnect** | High-performance memory-mapped AXI4-Lite switch | Xilinx `M_AXI_GP0` AXI Interconnect |
| **Peripheral Interface** | Address decoding, single-cycle strobes, register latching | Scene AXI Slave (`*_axi_slave.v`) |
| **Simulation Core** | Authoritative mathematics, FSM state updates, counters | Scene FPGA Core (`*_core.v`) |
