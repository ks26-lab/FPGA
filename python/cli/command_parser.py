"""
python.cli.command_parser
=========================
Parses and validates user CLI command inputs.
"""

from typing import Tuple, List, Optional
from python.protocol.errors import CommandParseError


class UniversalCommandParser:
    """Parses raw terminal input into structured command tokens."""

    @staticmethod
    def parse_line(raw_input: str) -> Tuple[str, List[str]]:
        """
        Tokenizes raw line input.
        Returns: (command_name, args_list)
        """
        stripped = raw_input.strip()
        if not stripped:
            return "", []

        tokens = stripped.split()
        cmd = tokens[0].lower()
        args = tokens[1:]
        return cmd, args
