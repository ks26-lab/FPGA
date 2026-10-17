"""CLI output formatter module for fpga_interface."""

from typing import Optional, Any


def format_banner() -> str:
    """Return the startup CLI banner."""
    return (
        "====================================================\n"
        " FPGA INTERFACE CLI (Iteration 1)\n"
        " Deterministic Protocol: CLI <-> Python <-> Verilog <-> MATLAB\n"
        " Type 'help' for commands or 'exit' to quit.\n"
        "===================================================="
    )


def format_input_set(value: Any, target: str = "input") -> str:
    """Format confirmation of input value being set."""
    return f"[{target.upper()}] Set to: {value}"


def format_encoded(bit_str: str, target: str = "input") -> str:
    """Format binary bit string representation of encoded input."""
    return f"[{target.upper()} ENCODED] Binary: {bit_str} (width: {len(bit_str)})"


def format_hardware_bus(direction: str, bit_str: str) -> str:
    """Format hardware boundary bus transfer."""
    return f"[VERILOG BUS {direction.upper()}] Bits: {bit_str}"


def format_decoded(value: Any, bit_str: Optional[str] = None) -> str:
    """Format human-readable output of decoded hardware result."""
    if bit_str:
        return f"[OUTPUT DECODED] Value: {value} (from binary: {bit_str})"
    return f"[OUTPUT DECODED] Value: {value}"


def format_status(
    input_value: Optional[int],
    encoded_bits: Optional[str],
    verilog_output_bits: Optional[str],
    decoded_value: Optional[int],
) -> str:
    """Format current interface state."""
    lines = [
        "--- Interface State ---",
        f" Current Input Value : {input_value if input_value is not None else '<unset>'}",
        f" Encoded Input Bits  : {encoded_bits if encoded_bits is not None else '<not encoded>'}",
        f" Verilog Output Bits : {verilog_output_bits if verilog_output_bits is not None else '<no data>'}",
        f" Decoded Result      : {decoded_value if decoded_value is not None else '<not read>'}",
        "-----------------------"
    ]
    return "\n".join(lines)


def format_roundtrip_summary(
    input_val: int,
    encoded_bits: str,
    verilog_in: str,
    verilog_out: str,
    decoded_val: int,
) -> str:
    """Format full round-trip verification report."""
    match = (input_val == decoded_val) and (encoded_bits == verilog_out)
    status_str = "PASS" if match else "FAIL"
    lines = [
        "================ ROUND-TRIP VERIFICATION ================",
        f" Input Value          : {input_val}",
        f" Python Encoded Bits  : {encoded_bits}",
        f" Verilog Input Bus    : {verilog_in}",
        f" Verilog Output Bus   : {verilog_out}",
        f" Python Decoded Value : {decoded_val}",
        f" Round-trip Status    : {status_str}",
        "========================================================="
    ]
    return "\n".join(lines)


def format_error(message: str) -> str:
    """Format an error message."""
    return f"[ERROR] {message}"
