"""CLI input parser module for fpga_interface."""

from typing import Dict, Any


def parse_value(raw_value: str) -> Dict[str, Any]:
    """
    Parse a raw string into a structured value dictionary.

    Example:
        Input: "25"
        Output: {"value": 25, "type": "integer"}

    Raises:
        ValueError: If input cannot be parsed as a supported type.
    """
    cleaned = raw_value.strip()
    if not cleaned:
        raise ValueError("Empty input received")

    # Check for integer format
    try:
        val = int(cleaned, 10)
        return {
            "value": val,
            "type": "integer"
        }
    except ValueError:
        pass

    raise ValueError(f"Unsupported or malformed value: '{cleaned}' (expected integer)")


def parse_command(raw_line: str) -> Dict[str, Any]:
    """
    Parse a raw CLI command line into structured data.

    Supported formats:
        - "set input 25" -> {"command": "set_input", "target": "input", "value": 25, "type": "integer"}
        - "25"           -> {"command": "set_input", "target": "input", "value": 25, "type": "integer"}
        - "encode"       -> {"command": "encode"}
        - "send"         -> {"command": "send"}
        - "read"         -> {"command": "read"}
        - "status"       -> {"command": "status"}
        - "exit" / "quit"-> {"command": "exit"}
        - "help"         -> {"command": "help"}

    Raises:
        ValueError: On malformed input or unrecognized commands.
    """
    line = raw_line.strip()
    if not line:
        return {"command": "noop"}

    tokens = line.split()
    cmd = tokens[0].lower()

    if cmd in ("exit", "quit", "q"):
        return {"command": "exit"}

    if cmd in ("help", "?"):
        return {"command": "help"}

    if cmd == "encode":
        return {"command": "encode"}

    if cmd == "send":
        # Supports optional argument: "send" or "send 25"
        if len(tokens) == 2:
            parsed_val = parse_value(tokens[1])
            return {
                "command": "send",
                "target": "input",
                "value": parsed_val["value"],
                "type": parsed_val["type"]
            }
        elif len(tokens) == 1:
            return {"command": "send"}
        else:
            raise ValueError(f"Malformed send command: expected 'send' or 'send <value>', got '{line}'")

    if cmd == "read":
        return {"command": "read"}

    if cmd == "status":
        return {"command": "status"}

    if cmd == "set":
        # Form: set input <value>
        if len(tokens) == 3 and tokens[1].lower() == "input":
            parsed_val = parse_value(tokens[2])
            return {
                "command": "set_input",
                "target": "input",
                "value": parsed_val["value"],
                "type": parsed_val["type"]
            }
        elif len(tokens) == 2:
            parsed_val = parse_value(tokens[1])
            return {
                "command": "set_input",
                "target": "input",
                "value": parsed_val["value"],
                "type": parsed_val["type"]
            }
        else:
            raise ValueError(f"Malformed set command: expected 'set input <value>', got '{line}'")

    # If the user directly enters a number like "25"
    try:
        parsed_val = parse_value(tokens[0])
        if len(tokens) == 1:
            return {
                "command": "set_input",
                "target": "input",
                "value": parsed_val["value"],
                "type": parsed_val["type"]
            }
    except ValueError:
        pass

    raise ValueError(f"Unrecognized command or malformed input: '{line}'")
