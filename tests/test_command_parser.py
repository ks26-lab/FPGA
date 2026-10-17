"""
tests.test_command_parser
=========================
Unit tests for the underwater probe CLI command parser.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fpga_interface.python.command_parser import CommandParser, CommandParseError


class TestCommandParser(unittest.TestCase):

    def test_valid_set_depth(self):
        cmd = CommandParser.parse("set depth 50")
        self.assertEqual(cmd["command"], "SET_DEPTH")
        self.assertEqual(cmd["value"], 50.0)

        cmd2 = CommandParser.parse("set depth 74.5")
        self.assertEqual(cmd2["command"], "SET_DEPTH")
        self.assertEqual(cmd2["value"], 74.5)

    def test_valid_target(self):
        cmd = CommandParser.parse("target 80")
        self.assertEqual(cmd["command"], "SET_TARGET")
        self.assertEqual(cmd["value"], 80.0)

        cmd2 = CommandParser.parse("target 120.25")
        self.assertEqual(cmd2["command"], "SET_TARGET")
        self.assertEqual(cmd2["value"], 120.25)

    def test_valid_current(self):
        cmd_pos = CommandParser.parse("current +20")
        self.assertEqual(cmd_pos["command"], "SET_CURRENT")
        self.assertEqual(cmd_pos["value"], 20)

        cmd_neg = CommandParser.parse("current -30")
        self.assertEqual(cmd_neg["command"], "SET_CURRENT")
        self.assertEqual(cmd_neg["value"], -30)

        cmd_zero = CommandParser.parse("current 0")
        self.assertEqual(cmd_zero["command"], "SET_CURRENT")
        self.assertEqual(cmd_zero["value"], 0)

    def test_valid_disturb(self):
        for obj in ["whale", "fish", "garbage", "WHALE", "FiSh"]:
            cmd = CommandParser.parse(f"disturb {obj}")
            self.assertEqual(cmd["command"], "DISTURB")
            self.assertEqual(cmd["type"], obj.upper())

    def test_lifecycle_commands(self):
        self.assertEqual(CommandParser.parse("start")["command"], "START")
        self.assertEqual(CommandParser.parse("stop")["command"], "STOP")
        self.assertEqual(CommandParser.parse("reset")["command"], "RESET")
        self.assertEqual(CommandParser.parse("status")["command"], "STATUS")
        self.assertEqual(CommandParser.parse("help")["command"], "HELP")
        self.assertEqual(CommandParser.parse("exit")["command"], "EXIT")
        self.assertEqual(CommandParser.parse("quit")["command"], "EXIT")

    def test_poll_command(self):
        cmd_default = CommandParser.parse("poll")
        self.assertEqual(cmd_default["command"], "POLL")
        self.assertEqual(cmd_default["interval"], 0.5)

        cmd_custom = CommandParser.parse("poll 1.2")
        self.assertEqual(cmd_custom["command"], "POLL")
        self.assertAlmostEqual(cmd_custom["interval"], 1.2)

    def test_invalid_set_depth(self):
        # Non-numeric
        with self.assertRaises(CommandParseError):
            CommandParser.parse("set depth abc")
        # Missing parameter
        with self.assertRaises(CommandParseError):
            CommandParser.parse("set depth")
        # Out of bounds
        with self.assertRaises(CommandParseError):
            CommandParser.parse("set depth -10")
        with self.assertRaises(CommandParseError):
            CommandParser.parse("set depth 1500")

    def test_invalid_current(self):
        with self.assertRaises(CommandParseError):
            CommandParser.parse("current +500")
        with self.assertRaises(CommandParseError):
            CommandParser.parse("current -200")
        with self.assertRaises(CommandParseError):
            CommandParser.parse("current fast")
        with self.assertRaises(CommandParseError):
            CommandParser.parse("current")

    def test_invalid_disturb(self):
        with self.assertRaises(CommandParseError):
            CommandParser.parse("disturb elephant")
        with self.assertRaises(CommandParseError):
            CommandParser.parse("disturb none")
        with self.assertRaises(CommandParseError):
            CommandParser.parse("disturb")

    def test_unknown_command(self):
        with self.assertRaises(CommandParseError):
            CommandParser.parse("fly to the moon")


if __name__ == "__main__":
    unittest.main()
