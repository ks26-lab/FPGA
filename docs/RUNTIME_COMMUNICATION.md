# Runtime Communication Protocol & Data Flow

## 1. Command Flow Pipeline

Every human command follows a strict unidirectional dispatch pipeline:

```text
Human command string (e.g. "set depth 40")
      ↓
Interactive CLI (python/cli/cli.py)
      ↓
Universal Command Parser (python/cli/command_parser.py)
      ↓
Parameter Bounds & Syntax Validation
      ↓
Scene Manager (python/core/scene_manager.py)
      ↓
Scene Driver (e.g. UnderwaterDriver)
      ↓
Fixed-Point Register Encoding (40.0m → 400 units)
      ↓
AXI Interface write32(REG_DEPTH_CFG, value)
      ↓
Linux /dev/mem mmap write
      ↓
Zynq PS M_AXI_GP0 AXI4-Lite Transaction
      ↓
Scene AXI Peripheral (underwater_probe_axi_slave.v)
      ↓
FPGA Core Hardware Logic Execution (underwater_probe_core.v)
```

**Golden Rule:** The CLI never contains raw AXI register addresses. Hardware register offsets are strictly encapsulated in scene-specific driver and register map modules.

---

## 2. Telemetry Flow Pipeline

Telemetry flows in the exact reverse direction:

```text
FPGA Core Logic State Registers
      ↓
AXI Slave Peripheral Read Registers
      ↓
AXI Interface read32(REG_STATUS, REG_POSITION, ...)
      ↓
Scene Driver (get_telemetry())
      ↓
Scene Telemetry Decoder (telemetry.py)
      ↓
Standard Telemetry Envelope (Dict / JSON-serializable)
      ↓
CLI Renderer (python/cli/renderer.py)
      ↓
PuTTY Terminal Screen Display
```

---

## 3. Universal Telemetry Envelope Specification

Every scene produces a standard envelope ensuring uniform rendering and telemetry consumption:

```json
{
  "scene": "underwater",
  "timestamp": 1775466800.125,
  "hardware": true,
  "state": "MOVING_TO_TARGET",
  "data": {
    "depth": 40.0,
    "target_depth": 80.0,
    "velocity": 0.5,
    "displacement_x": 0,
    "current_strength": 20,
    "collision": false,
    "recovery": false,
    "target_reached": false,
    "active_object": "NONE",
    "collision_count": 0,
    "simulation_cycles": 142
  }
}
```

---

## 4. Hardware Diagnostics (`debug registers`)

The architecture provides a direct hardware diagnostic facility. Issuing `debug registers` bypasses telemetry abstractions and performs direct 32-bit hex dumps of the mapped AXI aperture:

```text
========================================================
HARDWARE DIAGNOSTICS: UNDERWATER
BASE ADDRESS: 0x43C00000
--------------------------------------------------------
  CONTROL          : 0x00000000
  DEPTH_CFG        : 0x03200190
  CURRENT          : 0x00000014
  STATUS           : 0x00000001
  POSITION         : 0x05000190
  COUNTERS         : 0x00000000
  CYCLES           : 0x0000008E
========================================================
```
