"""
fpga_interface.python.telemetry_decoder
=======================================
Decodes raw 32-bit AXI register values read from the FPGA hardware into
a clean, strongly-typed Python Telemetry object.
"""

from dataclasses import dataclass
from typing import Optional

from fpga_interface.python.protocol import (
    DEPTH_SCALE,
    VELOCITY_SCALE,
    STATE_CODE_TO_NAME,
    DISTURB_CODE_TO_NAME,
)
from fpga_interface.python.register_map import (
    STATUS_STATE_MASK,
    STATUS_COLLISION_BIT,
    STATUS_RECOVERY_BIT,
    STATUS_TARGET_REACHED_BIT,
    STATUS_OBJECT_TYPE_SHIFT,
    STATUS_OBJECT_TYPE_MASK,
    unpack_depth_cfg,
    unpack_current,
)


@dataclass
class Telemetry:
    """Strongly-typed snapshot of live FPGA simulation state."""
    depth: float                 # Current probe depth in meters
    target_depth: float          # Desired target depth in meters
    set_depth: float             # Configured preset depth in meters
    current_strength: int        # Water current percentage (-100% to +100%)
    displacement_x: float        # Lateral offset from center (- = left, + = right)
    velocity_z: float            # Vertical rate of change in m/s
    state: str                   # FSM state string (e.g. "MOVING_TO_TARGET")
    state_code: int              # Raw FSM state code (0..6)
    collision: bool              # True if collision impulse detected
    recovery: bool               # True if asymptotic recovery is active
    target_reached: bool         # True if within target tolerance
    active_object: str           # "NONE", "FISH", "GARBAGE", "WHALE"
    active_object_code: int      # 0..3
    collision_count: int         # Total lifetime collisions on FPGA
    simulation_cycles: int       # Total hardware simulation ticks

    # Raw register dump for diagnostic transparency
    raw_status: int
    raw_position: int
    raw_counters: int
    raw_cycles: int
    raw_depth_cfg: int
    raw_current: int


def _to_signed_16(val_u16: int) -> int:
    """Converts 16-bit unsigned integer to signed integer."""
    val = val_u16 & 0xFFFF
    return val - 65536 if val >= 32768 else val


def _to_signed_8(val_u8: int) -> int:
    """Converts 8-bit unsigned integer to signed integer."""
    val = val_u8 & 0xFF
    return val - 256 if val >= 128 else val


def decode_telemetry(
    raw_status: int,
    raw_position: int,
    raw_counters: int,
    raw_cycles: int,
    raw_depth_cfg: int = 0,
    raw_current: int = 0
) -> Telemetry:
    """
    Decodes raw 32-bit register reads from underwater_probe_axi_slave.v:
      - raw_status    (0x0C)
      - raw_position  (0x10)
      - raw_counters  (0x14)
      - raw_cycles    (0x18)
      - raw_depth_cfg (0x04)
      - raw_current   (0x08)
    """
    # 1. Decode STATUS Register (0x0C)
    state_code = raw_status & STATUS_STATE_MASK
    state_name = STATE_CODE_TO_NAME.get(state_code, f"UNKNOWN_{state_code}")
    collision = bool((raw_status >> STATUS_COLLISION_BIT) & 1)
    recovery = bool((raw_status >> STATUS_RECOVERY_BIT) & 1)
    target_reached = bool((raw_status >> STATUS_TARGET_REACHED_BIT) & 1)
    obj_code = (raw_status >> STATUS_OBJECT_TYPE_SHIFT) & STATUS_OBJECT_TYPE_MASK
    active_object = DISTURB_CODE_TO_NAME.get(obj_code, "NONE")

    # 2. Decode POSITION Register (0x10)
    # [15:0]  = current_depth (signed 16-bit, scaled x10)
    # [23:16] = displacement_x (signed 8-bit)
    # [31:24] = velocity_z (signed 8-bit, 0.1 m/s)
    raw_depth_u16 = raw_position & 0xFFFF
    raw_disp_u8 = (raw_position >> 16) & 0xFF
    raw_vel_u8 = (raw_position >> 24) & 0xFF

    depth_m = _to_signed_16(raw_depth_u16) / DEPTH_SCALE
    disp_x = float(_to_signed_8(raw_disp_u8))
    vel_z = _to_signed_8(raw_vel_u8) / VELOCITY_SCALE

    # 3. Decode COUNTERS Register (0x14)
    # [15:0] = collision_counter
    collision_count = raw_counters & 0xFFFF

    # 4. Decode CYCLES Register (0x18)
    simulation_cycles = raw_cycles & 0xFFFFFFFF

    # 5. Decode Configuration Mirrors (0x04 & 0x08)
    set_units, target_units = unpack_depth_cfg(raw_depth_cfg)
    set_depth_m = set_units / DEPTH_SCALE
    target_depth_m = target_units / DEPTH_SCALE
    current_pct = unpack_current(raw_current)

    return Telemetry(
        depth=round(depth_m, 2),
        target_depth=round(target_depth_m, 2),
        set_depth=round(set_depth_m, 2),
        current_strength=current_pct,
        displacement_x=disp_x,
        velocity_z=round(vel_z, 2),
        state=state_name,
        state_code=state_code,
        collision=collision,
        recovery=recovery,
        target_reached=target_reached,
        active_object=active_object,
        active_object_code=obj_code,
        collision_count=collision_count,
        simulation_cycles=simulation_cycles,
        raw_status=raw_status,
        raw_position=raw_position,
        raw_counters=raw_counters,
        raw_cycles=raw_cycles,
        raw_depth_cfg=raw_depth_cfg,
        raw_current=raw_current,
    )
