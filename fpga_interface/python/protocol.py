"""
fpga_interface.python.protocol
==============================
Defines data structures, numerical scaling constants, object encodings,
and conversion utilities for the Zynq Z7010 Underwater Probe simulation.

Numerical Representation (matching underwater_probe_core.v):
  - Depth values: 16-bit signed scaled integer (1 unit = 0.1 m, e.g. 537 = 53.7 m)
  - Current strength: 8-bit signed percentage (-100% to +100%)
  - Lateral offset X: 8-bit signed integer (-128 to +127, 0 = center line)
  - Probe Velocity Z: 8-bit signed rate (0.1 m/update tick)
"""

from typing import Union

# -----------------------------------------------------------------------------
# Scaling Constants
# -----------------------------------------------------------------------------
DEPTH_SCALE: float = 10.0        # 1 FPGA unit = 0.1 m (50.0 m -> 500)
VELOCITY_SCALE: float = 10.0     # 1 FPGA unit = 0.1 m/s (5.0 m/s -> 50)
DISPLACEMENT_SCALE: float = 1.0  # 1 FPGA unit = 1 lateral unit

# Operational Ranges
MIN_DEPTH_M: float = 0.0
MAX_DEPTH_M: float = 1000.0

MIN_CURRENT_PCT: int = -100
MAX_CURRENT_PCT: int = 100

# -----------------------------------------------------------------------------
# Disturbance Types (matching underwater_probe_core.v)
# -----------------------------------------------------------------------------
DISTURB_NONE: int = 0
DISTURB_FISH: int = 1
DISTURB_GARBAGE: int = 2
DISTURB_WHALE: int = 3

DISTURB_NAME_TO_CODE = {
    "NONE": DISTURB_NONE,
    "FISH": DISTURB_FISH,
    "GARBAGE": DISTURB_GARBAGE,
    "WHALE": DISTURB_WHALE,
}

DISTURB_CODE_TO_NAME = {
    DISTURB_NONE: "NONE",
    DISTURB_FISH: "FISH",
    DISTURB_GARBAGE: "GARBAGE",
    DISTURB_WHALE: "WHALE",
}

# -----------------------------------------------------------------------------
# FSM State Codes (matching underwater_probe_core.v)
# -----------------------------------------------------------------------------
STATE_IDLE: int = 0
STATE_MOVING_TO_TARGET: int = 1
STATE_DISTURBED: int = 2
STATE_COLLISION_DETECTED: int = 3
STATE_DISPLACEMENT: int = 4
STATE_RECOVERY: int = 5
STATE_TARGET_REACHED: int = 6

STATE_CODE_TO_NAME = {
    STATE_IDLE: "IDLE",
    STATE_MOVING_TO_TARGET: "MOVING_TO_TARGET",
    STATE_DISTURBED: "DISTURBED",
    STATE_COLLISION_DETECTED: "COLLISION_DETECTED",
    STATE_DISPLACEMENT: "DISPLACEMENT",
    STATE_RECOVERY: "RECOVERY",
    STATE_TARGET_REACHED: "TARGET_REACHED",
}

# -----------------------------------------------------------------------------
# Conversion Helpers
# -----------------------------------------------------------------------------
def depth_to_fpga_units(depth_m: Union[int, float]) -> int:
    """
    Converts real-world depth in meters to 16-bit scaled FPGA integer units.
    Example: 50.0 m -> 500 units, 80.0 m -> 800 units.
    """
    if not (MIN_DEPTH_M <= depth_m <= MAX_DEPTH_M):
        raise ValueError(
            f"Depth {depth_m} m out of valid range [{MIN_DEPTH_M}, {MAX_DEPTH_M}] m"
        )
    return int(round(float(depth_m) * DEPTH_SCALE))


def fpga_units_to_depth(units: int) -> float:
    """Converts 16-bit scaled FPGA integer units back to real-world meters."""
    return float(units) / DEPTH_SCALE


def validate_current(current_pct: int) -> int:
    """Validates water current strength percentage (-100% to +100%)."""
    if not (MIN_CURRENT_PCT <= current_pct <= MAX_CURRENT_PCT):
        raise ValueError(
            f"Current {current_pct}% out of range [{MIN_CURRENT_PCT}, {MAX_CURRENT_PCT}]%"
        )
    return int(current_pct)


def parse_disturb_type(name: str) -> int:
    """Validates and converts disturbance string name to FPGA 2-bit code."""
    upper = name.strip().upper()
    if upper not in DISTURB_NAME_TO_CODE or upper == "NONE":
        valid = ", ".join([k.lower() for k in DISTURB_NAME_TO_CODE.keys() if k != "NONE"])
        raise ValueError(f"Invalid disturbance type '{name}'. Must be one of: {valid}")
    return DISTURB_NAME_TO_CODE[upper]
