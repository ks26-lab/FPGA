# RTL VS EMULATOR PARITY SPECIFICATION
## Verification Strategy, Register Mappings, and Golden Trace Testing

---

## 1. Parity Philosophy

To ensure zero divergence between the software RTL emulator on the developer laptop and the physical Verilog cores on the Zynq FPGA:
1. **Identical Bit Widths**: Every internal register and arithmetic accumulator in the emulator matches the Verilog `reg` and `wire` widths.
2. **Identical Reset Values**: Invoking reset sets all registers and FSM states to the identical reset vectors defined in `*_core.v`.
3. **Identical Arithmetic Truncation**: Fractional bits, circular modulo, and bit shifts (`>> 4`) produce identical results.
4. **Golden Trace Parity**: Given an identical sequence of register writes and clock ticks, the emulator and RTL generate byte-for-byte identical register readbacks.

---

## 2. Register Parity Verification Matrix

| Scene | Base Address | Register Offset | Name | RTL Width | Read/Write | Emulator Verified? |
|---|---|---|---|---|---|---|
| **Underwater** | `0x43C00000` | `0x00` | CONTROL | 32-bit | R/W | YES |
| | | `0x04` | DEPTH_CFG | 32-bit (Target/Set) | R/W | YES |
| | | `0x08` | CURRENT | 32-bit (Signed) | R/W | YES |
| | | `0x0C` | STATUS | 32-bit | RO | YES |
| | | `0x10` | POSITION | 32-bit (Depth/Lat) | RO | YES |
| | | `0x14` | COUNTERS | 32-bit (Disturb/Col) | RO | YES |
| | | `0x18` | CYCLES | 32-bit (Ticks) | RO | YES |
| **Maze** | `0x43C10000` | `0x00` | CONTROL | 32-bit | R/W | YES |
| | | `0x04` | MOVE_STROBE | 32-bit | WO | YES |
| | | `0x08` | STATUS | 32-bit | RO | YES |
| | | `0x0C` | POSITION | 32-bit (X, Y) | RO | YES |
| | | `0x10` | TIMER_VAL | 32-bit | RO | YES |
| | | `0x14` | COUNTERS | 32-bit (Moves/Hits) | RO | YES |
| **Mars** | `0x43C20000` | `0x00` | CONTROL | 32-bit | R/W | YES |
| | | `0x04` | CONFIG | 32-bit | R/W | YES |
| | | `0x08` | STATUS | 32-bit | RO | YES |
| | | `0x0C` | INTEGRITY | 32-bit (A, B) | RO | YES |
| | | `0x10` | LAST_IMPACT | 32-bit | RO | YES |
| | | `0x14` | COUNTERS | 32-bit | RO | YES |
| **Solar** | `0x43C30000` | `0x00` | CONTROL | 32-bit | R/W | YES |
| | | `0x04` | SUN_AZIMUTH | 32-bit | R/W | YES |
| | | `0x08` | SUN_ELEVATION | 32-bit | R/W | YES |
| | | `0x0C` | PANEL_AZIMUTH | 32-bit | RO | YES |
| | | `0x10` | PANEL_ELEVATION| 32-bit | RO | YES |
| | | `0x14` | STATUS | 32-bit | RO | YES |
| | | `0x18` | AZ_ERROR | 32-bit (Signed) | RO | YES |
| | | `0x1C` | EL_ERROR | 32-bit (Signed) | RO | YES |
| **Traffic** | `0x43C40000` | `0x00` | CONTROL | 32-bit | R/W | YES |
| | | `0x04` | CONFIG | 32-bit | R/W | YES |
| | | `0x08` | STATUS | 32-bit | RO | YES |
| | | `0x0C` | LIGHT_STATES | 32-bit | RO | YES |
| | | `0x10` | NS_QUEUE | 32-bit | R/W | YES |
| | | `0x14` | EW_QUEUE | 32-bit | R/W | YES |
| | | `0x18` | TIMER_VAL | 32-bit | RO | YES |
| | | `0x1C` | CYCLE_COUNT | 32-bit | RO | YES |

---

## 3. Golden Trace Validation Strategy

Every scene testbench script in `tests/`:
1. Resets the model via register strobe (`write32(BASE + CONTROL, 0x02)`).
2. Verifies all status registers reset to zero or their documented defaults.
3. Configures parameters via control registers.
4. Advances the simulation clock deterministically by $N$ ticks.
5. Asserts that the resulting status, telemetry, counters, and FSM states match the exact outputs from the Verilog testbenches (`fpga_interface/verilog/*_tb.v`).
