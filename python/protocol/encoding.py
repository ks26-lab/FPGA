"""
python.protocol.encoding
========================
Numeric conversion, fixed-point bit packing, and signed two's complement helpers.
"""

from typing import Tuple


def float_to_fixed16(value: float, scale: float = 10.0) -> int:
    """Converts a float to a scaled signed 16-bit integer."""
    val = int(round(value * scale))
    if val < -32768:
        val = -32768
    elif val > 32767:
        val = 32767
    return val & 0xFFFF


def fixed16_to_float(raw_u16: int, scale: float = 10.0) -> float:
    """Converts raw 16-bit word to signed float using scale."""
    val = raw_u16 & 0xFFFF
    signed_val = val - 65536 if val >= 32768 else val
    return round(signed_val / scale, 2)


def pack_two_i16(low_val: int, high_val: int) -> int:
    """Packs two signed 16-bit integers into a single 32-bit unsigned word."""
    return ((high_val & 0xFFFF) << 16) | (low_val & 0xFFFF)


def unpack_two_i16(word: int) -> Tuple[int, int]:
    """Unpacks a 32-bit word into two signed 16-bit integers (low, high)."""
    raw_low = word & 0xFFFF
    raw_high = (word >> 16) & 0xFFFF
    low = raw_low - 65536 if raw_low >= 32768 else raw_low
    high = raw_high - 65536 if raw_high >= 32768 else raw_high
    return low, high


def pack_four_u8(b0: int, b1: int, b2: int, b3: int) -> int:
    """Packs four 8-bit bytes into a 32-bit unsigned word."""
    return ((b3 & 0xFF) << 24) | ((b2 & 0xFF) << 16) | ((b1 & 0xFF) << 8) | (b0 & 0xFF)


def unpack_four_u8(word: int) -> Tuple[int, int, int, int]:
    """Unpacks a 32-bit word into four 8-bit bytes (b0, b1, b2, b3)."""
    return (word & 0xFF), ((word >> 8) & 0xFF), ((word >> 16) & 0xFF), ((word >> 24) & 0xFF)


def unpack_i8(val: int) -> int:
    """Converts unsigned 8-bit byte to signed integer (-128 to 127)."""
    raw = val & 0xFF
    return raw - 256 if raw >= 128 else raw
