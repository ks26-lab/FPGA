"""
python.protocol package
"""

from python.protocol.enums import SceneType, ExecutionMode, HardwareStatus
from python.protocol.errors import (
    FPGACommunicationError,
    HardwareUnavailableError,
    CommandParseError,
    InvalidRegisterError,
    SceneNotSelectedError,
)
from python.protocol.encoding import (
    float_to_fixed16,
    fixed16_to_float,
    pack_two_i16,
    unpack_two_i16,
    pack_four_u8,
    unpack_four_u8,
    unpack_i8,
)

__all__ = [
    "SceneType",
    "ExecutionMode",
    "HardwareStatus",
    "FPGACommunicationError",
    "HardwareUnavailableError",
    "CommandParseError",
    "InvalidRegisterError",
    "SceneNotSelectedError",
    "float_to_fixed16",
    "fixed16_to_float",
    "pack_two_i16",
    "unpack_two_i16",
    "pack_four_u8",
    "unpack_four_u8",
    "unpack_i8",
]
