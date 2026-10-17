"""
fpga_interface.python.command_parser
====================================
Parses and strictly validates human-readable CLI input commands into
structured Python dictionaries before communicating with the FPGA driver.

Commands:
  set depth <val>   - Set current probe depth in meters [0..1000]
  target <val>      - Set target depth in meters [0..1000]
  current <val>     - Set water current percentage [-100..+100]
  disturb <type>    - Inject disturbance (fish, garbage, whale)
  start             - Start probe movement simulation
  stop              - Stop probe movement simulation
  reset             - Assert FPGA reset
  status            - Display current telemetry status readout
  poll [sec]        - Start continuous telemetry display loop
  help              - Display command reference
  exit / quit       - Terminate CLI
"""

from typing import Dict, Any, Tuple
from fpga_interface.python.protocol import (
    MIN_DEPTH_M,
    MAX_DEPTH_M,
    MIN_CURRENT_PCT,
    MAX_CURRENT_PCT,
    DISTURB_NAME_TO_CODE,
)


class CommandParseError(ValueError):
    """Raised when a CLI command is malformed or parameters are invalid."""
    pass


class CommandParser:
    """Validates and converts text commands into structured command packets."""

    @staticmethod
    def parse(raw_line: str) -> Dict[str, Any]:
        """
        Parses raw user input string into a structured dictionary.
        Raises CommandParseError on syntax or validation errors.
        """
        line = raw_line.strip()
        if not line:
            return {"command": "NOP"}

        tokens = line.split()
        cmd = tokens[0].lower()

        # ---------------------------------------------------------------------
        # 1. SET DEPTH: 'set depth <value>'
        # ---------------------------------------------------------------------
        if cmd == "set":
            if len(tokens) < 3:
                raise CommandParseError(
                    "Malformed syntax. Expected: 'set depth <meters>' (e.g. 'set depth 50')"
                )
            subcmd = tokens[1].lower()
            if subcmd != "depth":
                raise CommandParseError(
                    f"Unknown parameter '{tokens[1]}'. Expected 'set depth <meters>'"
                )
            raw_val = tokens[2]
            try:
                depth_val = float(raw_val)
            except ValueError:
                raise CommandParseError(
                    f"Invalid depth value '{raw_val}'. Must be a number between {MIN_DEPTH_M} and {MAX_DEPTH_M} m."
                )

            if not (MIN_DEPTH_M <= depth_val <= MAX_DEPTH_M):
                raise CommandParseError(
                    f"Depth {depth_val} m out of range [{MIN_DEPTH_M}, {MAX_DEPTH_M}] m."
                )

            return {
                "command": "SET_DEPTH",
                "value": float(depth_val)
            }

        # ---------------------------------------------------------------------
        # 2. TARGET DEPTH: 'target <value>'
        # ---------------------------------------------------------------------
        elif cmd == "target":
            if len(tokens) < 2:
                raise CommandParseError(
                    "Missing target depth value. Usage: 'target <depth_in_meters>' (e.g. 'target 80')"
                )
            raw_val = tokens[1]
            try:
                target_val = float(raw_val)
            except ValueError:
                raise CommandParseError(
                    f"Invalid target depth '{raw_val}'. Must be a number between {MIN_DEPTH_M} and {MAX_DEPTH_M} m."
                )

            if not (MIN_DEPTH_M <= target_val <= MAX_DEPTH_M):
                raise CommandParseError(
                    f"Target depth {target_val} m out of range [{MIN_DEPTH_M}, {MAX_DEPTH_M}] m."
                )

            return {
                "command": "SET_TARGET",
                "value": float(target_val)
            }

        # ---------------------------------------------------------------------
        # 3. CURRENT STRENGTH: 'current <signed_int>'
        # ---------------------------------------------------------------------
        elif cmd == "current":
            if len(tokens) < 2:
                raise CommandParseError(
                    "Missing current percentage. Usage: 'current <+/-percentage>' (e.g. 'current +20')"
                )
            raw_val = tokens[1]
            # Strip optional '+' sign
            clean_val = raw_val[1:] if raw_val.startswith('+') else raw_val
            try:
                current_val = int(clean_val)
            except ValueError:
                raise CommandParseError(
                    f"Invalid current value '{raw_val}'. Must be an integer between {MIN_CURRENT_PCT}% and {MAX_CURRENT_PCT}%."
                )

            if not (MIN_CURRENT_PCT <= current_val <= MAX_CURRENT_PCT):
                raise CommandParseError(
                    f"Current strength {current_val}% out of range [{MIN_CURRENT_PCT}, {MAX_CURRENT_PCT}]%."
                )

            return {
                "command": "SET_CURRENT",
                "value": int(current_val)
            }

        # ---------------------------------------------------------------------
        # 4. DISTURB: 'disturb <type>'
        # ---------------------------------------------------------------------
        elif cmd == "disturb":
            if len(tokens) < 2:
                valid_types = ", ".join([k.lower() for k in DISTURB_NAME_TO_CODE.keys() if k != "NONE"])
                raise CommandParseError(
                    f"Missing disturbance type. Usage: 'disturb <type>'. Allowed: {valid_types}"
                )
            raw_type = tokens[1].strip().upper()
            if raw_type not in DISTURB_NAME_TO_CODE or raw_type == "NONE":
                valid_types = ", ".join([k.lower() for k in DISTURB_NAME_TO_CODE.keys() if k != "NONE"])
                raise CommandParseError(
                    f"Invalid disturbance type '{tokens[1]}'. Allowed types: {valid_types}."
                )

            return {
                "command": "DISTURB",
                "type": raw_type
            }

        # ---------------------------------------------------------------------
        # 5. CONTROL & LIFECYCLE COMMANDS
        # ---------------------------------------------------------------------
        elif cmd == "start":
            return {"command": "START"}

        elif cmd == "stop":
            return {"command": "STOP"}

        elif cmd == "reset":
            return {"command": "RESET"}

        elif cmd == "status":
            return {"command": "STATUS"}

        elif cmd == "poll":
            interval = 0.5
            if len(tokens) >= 2:
                try:
                    interval = max(0.1, float(tokens[1]))
                except ValueError:
                    raise CommandParseError(f"Invalid polling interval '{tokens[1]}'. Must be seconds (e.g. 'poll 0.5').")
            return {"command": "POLL", "interval": interval}

        elif cmd == "help":
            return {"command": "HELP"}

        elif cmd in ("exit", "quit"):
            return {"command": "EXIT"}

        else:
            raise CommandParseError(
                f"Unknown command '{tokens[0]}'. Type 'help' for list of valid commands."
            )
