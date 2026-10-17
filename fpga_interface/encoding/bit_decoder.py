"""Authoritative bit decoder module for fpga_interface protocol."""

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


def decode_integer(bit_str: str, width: Optional[int] = 8, signed: bool = False) -> int:
    """
    Convert a binary bit string back into an integer value.

    Args:
        bit_str: Binary string of '0's and '1's (e.g. '00011001').
        width: Expected bit width. If specified, bit string length must match.
        signed: True for two's complement signed integer, False for unsigned.

    Returns:
        Decoded integer value.

    Raises:
        TypeError: If bit_str is not a string.
        ValueError: If bit_str is malformed, has invalid width, or invalid characters.
    """
    if not isinstance(bit_str, str):
        raise TypeError(f"Bit string must be str, got {type(bit_str).__name__}")

    cleaned = bit_str.strip()
    if not cleaned:
        raise ValueError("Bit string cannot be empty")

    if not all(c in ('0', '1') for c in cleaned):
        raise ValueError(f"Malformed bit string: '{cleaned}' contains non-binary characters")

    bit_len = len(cleaned)
    if width is not None:
        if bit_len != width:
            raise ValueError(
                f"Bit string length {bit_len} does not match expected width {width}"
            )

    unsigned_val = int(cleaned, 2)
    if signed:
        # If the MSB is 1, it's negative in two's complement
        if cleaned[0] == '1':
            return unsigned_val - (1 << bit_len)
        return unsigned_val

    return unsigned_val


def decode_from_protocol(
    bit_str: str,
    signal_name: str = "output",
    protocol_path: Optional[Union[str, Path]] = None,
) -> int:
    """Decode a binary bit string using the signal specification from protocol.json."""
    protocol = load_protocol(protocol_path)
    signals = protocol.get("signals", {})
    if signal_name not in signals:
        raise KeyError(f"Signal '{signal_name}' not defined in protocol contract")

    spec = signals[signal_name]
    width = spec.get("width", 8)
    signed = spec.get("signed", False)

    return decode_integer(bit_str, width=width, signed=signed)
