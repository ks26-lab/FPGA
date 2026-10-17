"""Authoritative bit encoder module for fpga_interface protocol."""

import json
from pathlib import Path
from typing import Optional, Union, Dict, Any

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "protocol.json"


def load_protocol(protocol_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load and parse the protocol.json contract file."""
    path = Path(protocol_path) if protocol_path else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Protocol configuration file not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def encode_integer(val: int, width: int = 8, signed: bool = False) -> str:
    """
    Convert an integer value into a fixed-width binary bit string.

    Args:
        val: Integer value to encode.
        width: Configured bit width.
        signed: True for two's complement signed integer, False for unsigned.

    Returns:
        Deterministic binary bit string (e.g. '00011001').

    Raises:
        TypeError: If val or width is not an integer.
        ValueError: If width < 1 or if val is out of bounds for the bit width.
    """
    if not isinstance(val, int) or isinstance(val, bool):
        raise TypeError(f"Value must be an integer, got {type(val).__name__}")
    if not isinstance(width, int) or width <= 0:
        raise ValueError(f"Bit width must be a positive integer, got {width}")

    if signed:
        min_val = -(1 << (width - 1))
        max_val = (1 << (width - 1)) - 1
        if not (min_val <= val <= max_val):
            raise ValueError(
                f"Value {val} is out of bounds for {width}-bit signed integer [{min_val}, {max_val}]"
            )
        # Two's complement representation
        if val < 0:
            val = (1 << width) + val
    else:
        min_val = 0
        max_val = (1 << width) - 1
        if not (min_val <= val <= max_val):
            raise ValueError(
                f"Value {val} is out of bounds for {width}-bit unsigned integer [{min_val}, {max_val}]"
            )

    bit_string = bin(val)[2:].zfill(width)
    return bit_string


def encode_from_protocol(
    val: int,
    signal_name: str = "input",
    protocol_path: Optional[Union[str, Path]] = None,
) -> str:
    """Encode an integer value using the signal specification from protocol.json."""
    protocol = load_protocol(protocol_path)
    signals = protocol.get("signals", {})
    if signal_name not in signals:
        raise KeyError(f"Signal '{signal_name}' not defined in protocol contract")

    spec = signals[signal_name]
    width = spec.get("width", 8)
    signed = spec.get("signed", False)

    return encode_integer(val, width=width, signed=signed)
