"""Main CLI entry point for fpga_interface FPGA interface."""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure fpga_interface and its submodules are resolvable without colliding with root cli
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent

for p in [str(WORKSPACE_ROOT), str(PROJECT_ROOT), str(SCRIPT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from fpga_interface.cli.input_parser import parse_command, parse_value
    from fpga_interface.cli.output_formatter import (
        format_banner,
        format_input_set,
        format_encoded,
        format_hardware_bus,
        format_decoded,
        format_status,
        format_roundtrip_summary,
        format_error,
    )
    from fpga_interface.encoding.bit_encoder import encode_from_protocol
    from fpga_interface.encoding.bit_decoder import decode_from_protocol
except (ImportError, ModuleNotFoundError):
    from input_parser import parse_command, parse_value
    from output_formatter import (
        format_banner,
        format_input_set,
        format_encoded,
        format_hardware_bus,
        format_decoded,
        format_status,
        format_roundtrip_summary,
        format_error,
    )
    from encoding.bit_encoder import encode_from_protocol
    from encoding.bit_decoder import decode_from_protocol


def verilog_passthrough_interface(in_bits: str) -> str:
    """
    Software model of Verilog top.v pass-through test path.
    Data flow: in_bits -> input_interface -> internal_signal -> output_interface -> out_bits
    """
    # Direct pass-through matching top.v
    return in_bits


class CLIController:
    """Manages CLI state and dispatches commands between modules."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.input_value: Optional[int] = None
        self.encoded_bits: Optional[str] = None
        self.verilog_output_bits: Optional[str] = None
        self.decoded_value: Optional[int] = None

    def execute_line(self, line: str) -> Optional[str]:
        """Parse and execute a single line command. Returns message to print if any."""
        try:
            parsed = parse_command(line)
        except ValueError as err:
            return format_error(str(err))

        cmd = parsed.get("command")

        if cmd == "noop":
            return None

        if cmd == "exit":
            sys.exit(0)

        if cmd == "help":
            return (
                "Available commands:\n"
                "  set input <value>   - Set human-readable input value (e.g. 'set input 25')\n"
                "  <value>             - Shorthand to set input value\n"
                "  encode              - Encode input value to fixed-width binary bit string\n"
                "  send                - Transfer encoded bits through Verilog interface bus\n"
                "  read                - Read and decode output bits from Verilog interface\n"
                "  status              - Show current interface signals and states\n"
                "  exit                - Exit the CLI"
            )

        if cmd == "set_input":
            val = parsed["value"]
            self.input_value = val
            # Reset downstream pipeline stages on new input
            self.encoded_bits = None
            self.verilog_output_bits = None
            self.decoded_value = None
            return format_input_set(val, target=parsed.get("target", "input"))

        if cmd == "encode":
            if self.input_value is None:
                return format_error("No input value set. Use 'set input <val>' first.")
            try:
                self.encoded_bits = encode_from_protocol(self.input_value, signal_name="input")
                return format_encoded(self.encoded_bits, target="input")
            except Exception as err:
                return format_error(f"Encoding failed: {err}")

        if cmd == "send":
            # If value provided directly with send: e.g. "send 25"
            if "value" in parsed:
                self.input_value = parsed["value"]
                self.encoded_bits = encode_from_protocol(self.input_value, signal_name="input")

            if self.encoded_bits is None:
                if self.input_value is not None:
                    # Automatically encode if value is present
                    self.encoded_bits = encode_from_protocol(self.input_value, signal_name="input")
                else:
                    return format_error("Nothing to send. Set and encode an input value first.")

            # Route through Verilog interface boundary
            self.verilog_output_bits = verilog_passthrough_interface(self.encoded_bits)
            rx_msg = format_hardware_bus("rx", self.encoded_bits)
            tx_msg = format_hardware_bus("tx", self.verilog_output_bits)
            return f"{rx_msg}\n{tx_msg}"

        if cmd == "read":
            if self.verilog_output_bits is None:
                return format_error("No output bits received from Verilog. Use 'send' first.")
            try:
                self.decoded_value = decode_from_protocol(self.verilog_output_bits, signal_name="output")
                return format_decoded(self.decoded_value, bit_str=self.verilog_output_bits)
            except Exception as err:
                return format_error(f"Decoding failed: {err}")

        if cmd == "status":
            return format_status(
                self.input_value,
                self.encoded_bits,
                self.verilog_output_bits,
                self.decoded_value,
            )

        return format_error(f"Unhandled command: {cmd}")

    def run_roundtrip(self, value: int, raw_output: bool = False) -> int:
        """Execute full deterministic pipeline roundtrip: input -> encode -> Verilog -> decode."""
        self.input_value = value
        self.encoded_bits = encode_from_protocol(self.input_value, signal_name="input")
        self.verilog_output_bits = verilog_passthrough_interface(self.encoded_bits)
        self.decoded_value = decode_from_protocol(self.verilog_output_bits, signal_name="output")

        if raw_output:
            print(self.decoded_value)
        else:
            print(
                format_roundtrip_summary(
                    self.input_value,
                    self.encoded_bits,
                    self.encoded_bits,
                    self.verilog_output_bits,
                    self.decoded_value,
                )
            )
        return self.decoded_value

    def repl(self) -> None:
        """Interactive REPL loop."""
        print(format_banner())
        while True:
            try:
                line = input("> ")
                output = self.execute_line(line)
                if output:
                    print(output)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break


def main():
    parser = argparse.ArgumentParser(description="fpga_interface CLI Interface")
    parser.add_argument(
        "value",
        nargs="?",
        type=int,
        help="Run immediate round-trip on integer value (useful for MATLAB/scripts)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output only the raw decoded value (ideal for MATLAB system call parsing)",
    )
    parser.add_argument(
        "--exec",
        dest="exec_commands",
        type=str,
        help="Semicolon-separated list of commands to execute (e.g. 'set input 25; encode; send; read')",
    )

    args = parser.parse_args()
    controller = CLIController()

    if args.value is not None:
        controller.run_roundtrip(args.value, raw_output=args.raw)
        return

    if args.exec_commands:
        commands = args.exec_commands.split(";")
        for cmd in commands:
            cmd = cmd.strip()
            if cmd:
                print(f"> {cmd}")
                res = controller.execute_line(cmd)
                if res:
                    print(res)
        return

    # If piped input or interactive REPL
    if not sys.stdin.isatty():
        for line in sys.stdin:
            line = line.strip()
            if line:
                res = controller.execute_line(line)
                if res:
                    print(res)
        return

    controller.repl()


if __name__ == "__main__":
    main()
