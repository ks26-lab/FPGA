# Underwater Dynamic Probe Simulation — Zynq Z7010 FPGA Architecture

## 1. Full Communication Architecture

This system implements an authoritative FPGA hardware simulation of an underwater probe operating on the **EDGE ZYNQ Z7010 development board** (Xilinx XC7Z010-1CLG400C).

There is **NO MATLAB / Simulink runtime layer**.

```text
                    USER
                     │
                     ▼
             ┌──────────────┐
             │   CLI        │
             │ Python       │
             └──────┬───────┘
                    │ Human command (e.g. "set depth 50", "disturb whale")
                    ▼
             ┌──────────────┐
             │ Command      │
             │ Parser       │
             └──────┬───────┘
                    │ Structured Python Command Object
                    ▼
             ┌──────────────┐
             │ FPGA Driver  │
             │ Python       │
             └──────┬───────┘
                    │ AXI register read/write
                    ▼
        ┌────────────────────────┐
        │      ZYNQ Z7010        │
        │                        │
        │  Processing System     │
        │       ARM Cortex-A9    │
        │          │             │
        │         AXI            │
        │          │             │
        │          ▼             │
        │  AXI Slave Peripheral  │
        │  (underwater_probe_    │
        │   axi_slave.v)         │
        │          │             │
        │          ▼             │
        │ Underwater Probe Core  │
        │ (underwater_probe_     │
        │  core.v)               │
        │          │             │
        │          ▼             │
        │ Simulation Registers   │
        └───────────┬────────────┘
                    │
                AXI READ
                    │
                    ▼
             ┌──────────────┐
             │ FPGA Driver  │
             │ Python       │
             └──────┬───────┘
                    │ Decoded Telemetry object
                    ▼
             ┌──────────────┐
             │ CLI Renderer │
             └──────┬───────┘
                    │
                    ▼
                   USER
```

---

## 2. CLI → Python Flow

1. The user enters a human-readable command into the interactive prompt:
   - `set depth 50`
   - `target 80`
   - `current +20`
   - `disturb whale`
   - `start` / `stop` / `reset` / `status` / `poll`
2. `CommandParser.parse(raw_string)` validates the syntax and parameter bounds **before** touching the FPGA driver.
   - Example: `disturb elephant` is rejected immediately with `CommandParseError: Invalid disturbance type 'elephant'`.
   - Example: `current +500` is rejected with `CommandParseError: Current strength +500% out of range [-100, +100]%`.
3. If valid, the parser outputs a structured dictionary:
   ```python
   {"command": "SET_DEPTH", "value": 50.0}
   {"command": "DISTURB", "type": "WHALE"}
   ```

---

## 3. Python → AXI Flow

1. The `FPGADriver` receives the structured command and calls the corresponding typed method (e.g. `fpga.set_depth(50.0)` or `fpga.disturb("whale")`).
2. Numerical parameters are converted into FPGA fixed-point integer units:
   - Real-world depth $50.0\text{ m} \to 500\text{ units}$ ($1\text{ unit} = 0.1\text{ m}$).
   - Disturbance type `WHALE` $\to \text{code } 3$ (`2'b11`).
3. The driver constructs the 32-bit register words via `register_map.py` helpers:
   - `pack_depth_cfg(500, 800)` $\to$ `0x032001F4`
   - `pack_control(set_depth_we=True)` $\to$ `0x00000040` (Bit 6)
   - `pack_control(disturb_strobe=True, disturb_type=3)` $\to$ `0x00000038` (Bits [5:4]=3, Bit 3=1)
4. The driver calls `self.axi.write32(offset, value)` on the underlying `AXIInterface` (either `RealAXIInterface` via `/dev/mem` at `0x43C00000`, or `MockAXIInterface`).

---

## 4. AXI → Verilog Flow

1. The ARM Cortex-A9 issues an AXI4-Lite write transfer on the `M_AXI_GP0` bus interface.
2. `underwater_probe_axi_slave.v` decodes address `s_axi_awaddr[5:2]`:
   - `4'h0` (`0x00`): Latches `cmd_start`, `cmd_stop`, `cmd_reset`, `cmd_disturb_strobe`, `cmd_disturb_type`, and `cfg_set_depth_we`. Single-cycle strobes auto-clear on the next clock edge.
   - `4'h1` (`0x04`): Latches `cfg_set_depth` [15:0] and `cfg_target_depth` [31:16].
   - `4'h2` (`0x08`): Latches `cfg_current_strength` [7:0].
3. `underwater_probe_core.v` reacts to strobes and register parameters:
   - If `cmd_reset`: Restores all registers to nominal baseline (depth: 50.0 m, target: 80.0 m, state: IDLE).
   - If `cfg_set_depth_we`: Overwrites `current_depth` with `cfg_set_depth`.
   - If `cmd_disturb_strobe`: Triggers collision FSM branch (`STATE_COLLISION_DETECTED`), injects lateral impulse $X$, depth displacement $\Delta D$, and increments `collision_counter`.
   - On each $10\text{ Hz}$ update tick (`update_tick`): Executes target-seeking proportional motion, water-current drift integration, and asymptotic recovery.

---

## 5. FPGA → Python Telemetry Flow

1. Python calls `fpga.get_telemetry()`.
2. The driver performs 32-bit reads across the memory-mapped registers:
   - `read32(0x0C)` $\to$ `REG_STATUS`
   - `read32(0x10)` $\to$ `REG_POSITION`
   - `read32(0x14)` $\to$ `REG_COUNTERS`
   - `read32(0x18)` $\to$ `REG_CYCLES`
   - `read32(0x04)` $\to$ `REG_DEPTH_CFG`
   - `read32(0x08)` $\to$ `REG_CURRENT`
3. `telemetry_decoder.decode_telemetry(...)` unpacks the bitfields:
   - Converts two's complement signed 16-bit depth $\to$ float meters ($/ 10.0$).
   - Converts two's complement signed 8-bit velocity $\to$ float m/s ($/ 10.0$).
   - Extracts state code, collision flag, recovery flag, and target reached flag.
4. Returns a strongly-typed `Telemetry` object to the CLI renderer.
5. The CLI prints the updated three-panel ASCII visualizer.

---

## 6. Register Map Specification

**Base Address:** `0x43C00000` (M_AXI_GP0, 64KB aperture)

| Offset | Name | Type | Reset Value | Bitfield Breakdown | Description |
|:---:|:---:|:---:|:---:|:---|:---|
| **`0x00`** | `CONTROL` | W | `0x00000000` | `[0]` start<br>`[1]` stop<br>`[2]` reset<br>`[3]` disturb_strobe<br>`[5:4]` disturb_type<br>`[6]` set_depth_we | Command strobes (auto-clearing single cycle pulses). |
| **`0x04`** | `DEPTH_CFG` | R/W | `0x032001F4` | `[15:0]` set_depth (x10)<br>`[31:16]` target_depth (x10) | Preset depth and target depth in 0.1m units (500=50m, 800=80m). |
| **`0x08`** | `CURRENT` | R/W | `0x00000014` | `[7:0]` current_strength | Signed 8-bit water current strength percentage (-100% to +100%). |
| **`0x0C`** | `STATUS` | R | `0x00000000` | `[3:0]` probe_state<br>`[4]` collision_detected<br>`[5]` recovery_active<br>`[6]` target_reached<br>`[8:7]` active_object_type | Live probe FSM state and boolean event indicators. |
| **`0x10`** | `POSITION` | R | `0x000001F4` | `[15:0]` current_depth (x10)<br>`[23:16]` displacement_x<br>`[31:24]` probe_velocity_z | Spatial coordinates and vertical velocity rate. |
| **`0x14`** | `COUNTERS` | R | `0x00000000` | `[15:0]` collision_counter | Total collision events since FPGA boot/reset. |
| **`0x18`** | `CYCLES` | R | `0x00000000` | `[31:0]` sim_cycle_counter | Hardware simulation tick counter (10 Hz hardware tick). |

---

## 7. Data Encoding & Numerical Formats

- **Depth Scaling:** $D_{\text{FPGA}} = \text{round}(D_{\text{meters}} \times 10.0)$.
  - Range: $0.0\text{ m} \dots 1000.0\text{ m} \iff 0 \dots 10000\text{ units}$.
- **Velocity Scaling:** $V_{\text{FPGA}} = \text{round}(V_{\text{m/s}} \times 10.0)$.
- **Displacement X:** Signed 8-bit integer $(-128 \dots +127)$, center line $= 0$.
- **Water Current:** Signed 8-bit two's complement integer $(-100 \dots +100)$.
- **Disturbance Encoding:**
  - `0` (`2'b00`): NONE
  - `1` (`2'b01`): FISH (Impulse: $\Delta X = +15, \Delta D = -0.8\text{ m}$)
  - `2` (`2'b10`): GARBAGE (Impulse: $\Delta X = -28, \Delta D = +1.4\text{ m}$)
  - `3` (`2'b11`): WHALE (Impulse: $\Delta X = +55, \Delta D = -3.2\text{ m}$)

---

## 8. Hardware Deployment Procedure (EDGE ZYNQ Z7010)

1. **Bitstream Synthesis & Implementation:**
   - In Vivado 2020.2+, instantiate `underwater_probe_axi_slave.v` connected to `M_AXI_GP0` of the Processing System block.
   - Address Editor: Assign base address `0x43C00000` with 64KB range.
   - Generate bitstream (`underwater_probe_top.bit`).
2. **Booting Zynq Linux:**
   - Program the Zynq PL bitstream via JTAG (`xsct`) or copy to SD card boot partition (`boot.bin`).
   - Boot embedded Linux (Petalinux / Ubuntu / PYNQ).
3. **Execution on Zynq PS:**
   ```bash
   cd /home/root/fpga_interface
   python3 underwater_probe_cli.py --hw
   ```
   The driver maps `/dev/mem` at physical address `0x43C00000` and directly reads/writes physical AXI registers.

---

## 9. Mock Mode Procedure (Developer Laptop / Windows)

When developing on a host computer without the physical board attached:
```powershell
python underwater_probe_cli.py --mock
```
The driver instantiates `MockAXIInterface`, running the bit-accurate RTL logic in Python with a 10 Hz background clock. All commands, register packs, telemetry decodes, and visual panels execute identically to hardware, clearly marked with:
`Status: [⚠ MOCK SIMULATION MODE (Windows/Dev)]`

---

## 10. Hardware Testing Procedure

### Acceptance Test Sequence
```text
$ python underwater_probe_cli.py

UNDERWATER PROBE FPGA SYSTEM

> reset
[CLI] Command accepted.
[FPGA] Reset successful.
[FPGA] Depth: 50.0 m | Target: 80.0 m | State: IDLE

> set depth 50
[CLI] Command accepted.
[FPGA] Depth = 50.0 m

> target 80
[CLI] Command accepted.
[FPGA] Target = 80.0 m

> current +20
[CLI] Command accepted.
[FPGA] Current = +20%

> start
[CLI] Command accepted.
[FPGA] Simulation started.

> status
[Renders live 3-panel screen showing probe moving from 50m toward 80m]

> disturb whale
[CLI] Command accepted.
[FPGA] Disturbance injected: WHALE. Collision strobe asserted.
[Probe is displaced to X = +55, depth bumped up by -3.2m, and enters RECOVERY state]
```

### Running Automated Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```
All unit tests verify parser validation, register encoding, telemetry decoding, and end-to-end integration.
