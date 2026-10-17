"""
tests.test_universal_parser
============================
Tests for UniversalCommandParser.
"""

import unittest
import sys
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.cli.command_parser import UniversalCommandParser


class TestUniversalCommandParser(unittest.TestCase):

    def test_empty_and_whitespace(self):
        cmd, args = UniversalCommandParser.parse_line("")
        self.assertEqual(cmd, "")
        self.assertEqual(args, [])

        cmd, args = UniversalCommandParser.parse_line("    \t  ")
        self.assertEqual(cmd, "")
        self.assertEqual(args, [])

    def test_global_commands(self):
        cmd, args = UniversalCommandParser.parse_line("scene underwater")
        self.assertEqual(cmd, "scene")
        self.assertEqual(args, ["underwater"])

        cmd, args = UniversalCommandParser.parse_line("status")
        self.assertEqual(cmd, "status")
        self.assertEqual(args, [])

        cmd, args = UniversalCommandParser.parse_line("debug registers")
        self.assertEqual(cmd, "debug")
        self.assertEqual(args, ["registers"])

    def test_underwater_commands(self):
        cmd, args = UniversalCommandParser.parse_line("set depth 45.5")
        self.assertEqual(cmd, "set")
        self.assertEqual(args, ["depth", "45.5"])

        cmd, args = UniversalCommandParser.parse_line("disturb whale")
        self.assertEqual(cmd, "disturb")
        self.assertEqual(args, ["whale"])

    def test_maze_commands(self):
        cmd, args = UniversalCommandParser.parse_line("start")
        self.assertEqual(cmd, "start")
        self.assertEqual(args, [])

        cmd, args = UniversalCommandParser.parse_line("right")
        self.assertEqual(cmd, "right")
        self.assertEqual(args, [])

        cmd, args = UniversalCommandParser.parse_line("inspect 12")
        self.assertEqual(cmd, "inspect")
        self.assertEqual(args, ["12"])

    def test_mars_commands(self):
        cmd, args = UniversalCommandParser.parse_line("attack big segment A")
        self.assertEqual(cmd, "attack")
        self.assertEqual(args, ["big", "segment", "A"])

        cmd, args = UniversalCommandParser.parse_line("threshold A 75.0")
        self.assertEqual(cmd, "threshold")
        self.assertEqual(args, ["A", "75.0"])

    def test_solar_commands(self):
        cmd, args = UniversalCommandParser.parse_line("sun azimuth 120.0")
        self.assertEqual(cmd, "sun")
        self.assertEqual(args, ["azimuth", "120.0"])

        cmd, args = UniversalCommandParser.parse_line("calculate")
        self.assertEqual(cmd, "calculate")
        self.assertEqual(args, [])

    def test_traffic_commands(self):
        cmd, args = UniversalCommandParser.parse_line("queue ns 25")
        self.assertEqual(cmd, "queue")
        self.assertEqual(args, ["ns", "25"])

        cmd, args = UniversalCommandParser.parse_line("override ew")
        self.assertEqual(cmd, "override")
        self.assertEqual(args, ["ew"])


if __name__ == "__main__":
    unittest.main()
