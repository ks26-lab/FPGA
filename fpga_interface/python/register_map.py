"""
fpga_interface.python.register_map
==================================
Authoritative memory-mapped AXI4-Lite register definitions for the
Zynq Z7010 Underwater Probe Simulation peripheral.

Matches the hardware RTL in underwater_probe_axi_slave.v:
Base Address: 0x43C00000

Register Map:
  Offset | Name      | Access | Description
  -------+-----------+--------+-----------------------------------------------
  0x00   | CONTROL   | W      | Command strobes, disturbance type, write-enables
  0x04   | DEPTH_CFG | R/W    | [15:0] set_depth (x10), [31:16] target_depth (x10)
  0x08   | CURRENT   | R/W    | [7:0] water current strength (signed -100..+100)
  0x0C   | STATUS    | R      | State, collision, recovery, target_reached, obj
  0x10   | POSITION  | R      | [15:0] depth, [23:16] disp_x, [31:24] vel_z
  0x14   | COUNTERS  | R      | [15:0] collision counter
  0x18   | CYCLES    | R      | [31:0] simulation cycle counter
"""

# Base Address assigned in Vivado Address Editor for M_AXI_GP0
AXI_BASE_ADDR: int = 0x43C00000

# Register Byte Offsets
REG_CONTROL: int   = 0x00
REG_DEPTH_CFG: int = 0x04
REG_CURRENT: int   = 0x08
REG_STATUS: int    = 0x0C
REG_POSITION: int  = 0x10
REG_COUNTERS: int  = 0x14
REG_CYCLES: int    = 0x18

REGISTER_NAMES = {
    REG_CONTROL: "CONTROL",
    REG_DEPTH_CFG: "DEPTH_CFG",
    REG_CURRENT: "CURRENT",
    REG_STATUS: "STATUS",
    REG_POSITION: "POSITION",
    REG_COUNTERS: "COUNTERS",
    REG_CYCLES: "CYCLES",
}

# -----------------------------------------------------------------------------
# CONTROL Register Bit Definitions (0x00)
# -----------------------------------------------------------------------------
CTRL_START_BIT: int          = 0
CTRL_STOP_BIT: int           = 1
CTRL_RESET_BIT: int          = 2
CTRL_DISTURB_STROBE_BIT: int = 3
CTRL_DISTURB_TYPE_SHIFT: int = 4
CTRL_DISTURB_TYPE_MASK: int  = 0x3
CTRL_SET_DEPTH_WE_BIT: int   = 6

# -----------------------------------------------------------------------------
# STATUS Register Bit Definitions (0x0C)
# -----------------------------------------------------------------------------
STATUS_STATE_MASK: int          = 0x0F
STATUS_COLLISION_BIT: int       = 4
STATUS_RECOVERY_BIT: int        = 5
STATUS_TARGET_REACHED_BIT: int  = 6
STATUS_OBJECT_TYPE_SHIFT: int   = 7
STATUS_OBJECT_TYPE_MASK: int    = 0x03

# -----------------------------------------------------------------------------
# Bitfield Packing Helpers
# -----------------------------------------------------------------------------
def pack_control(
    start: bool = False,
    stop: bool = False,
    reset: bool = False,
    disturb_strobe: bool = False,
    disturb_type: int = 0,
    set_depth_we: bool = False
) -> int:
    """Packs control flags and fields into a 32-bit CONTROL register word."""
    word = 0
    if start:
        word |= (1 << CTRL_START_BIT)
    if stop:
        word |= (1 << CTRL_STOP_BIT)
    if reset:
        word |= (1 << CTRL_RESET_BIT)
    if disturb_strobe:
        word |= (1 << CTRL_DISTURB_STROBE_BIT)
    word |= ((disturb_type & CTRL_DISTURB_TYPE_MASK) << CTRL_DISTURB_TYPE_SHIFT)
    if set_depth_we:
        word |= (1 << CTRL_SET_DEPTH_WE_BIT)
    return word & 0xFFFFFFFF


def pack_depth_cfg(set_depth_units: int, target_depth_units: int) -> int:
    """
    Packs set_depth and target_depth (scaled integer units) into 32-bit DEPTH_CFG.
    Bits [15:0]  = set_depth (signed 16-bit)
    Bits [31:16] = target_depth (signed 16-bit)
    """
    set_u16 = set_depth_units & 0xFFFF
    target_u16 = target_depth_units & 0xFFFF
    return ((target_u16 << 16) | set_u16) & 0xFFFFFFFF


def unpack_depth_cfg(word: int):
    """
    Unpacks 32-bit DEPTH_CFG into (set_depth_units, target_depth_units).
    Interprets both as signed 16-bit integers.
    """
    raw_set = word & 0xFFFF
    raw_target = (word >> 16) & 0xFFFF

    set_depth = raw_set - 65536 if raw_set >= 32768 else raw_set
    target_depth = raw_target - 65536 if raw_target >= 32768 else raw_target
    return set_depth, target_depth


def pack_current(current_pct: int) -> int:
    """
    Packs signed 8-bit current strength (-100 to +100) into 32-bit word.
    """
    return current_pct & 0xFF


def unpack_current(word: int) -> int:
    """Unpacks signed 8-bit current strength from 32-bit word."""
    raw = word & 0xFF
    return raw - 256 if raw >= 128 else raw
