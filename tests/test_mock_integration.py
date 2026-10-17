"""
tests.test_mock_integration
============================
End-to-end integration test validating the entire communication pipeline:
CLI -> Parser -> FPGADriver -> MockAXI -> Telemetry -> Renderer.
"""

import unittest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fpga_interface.python.command_parser import CommandParser
from fpga_interface.python.fpga_driver import FPGADriver
from fpga_interface.python.axi_interface import MockAXIInterface
from fpga_interface.python.underwater_probe_cli import render_3panel_screen


class TestMockIntegration(unittest.TestCase):

    def setUp(self):
        self.mock_axi = MockAXIInterface()
        self.driver = FPGADriver(axi=self.mock_axi)

    def tearDown(self):
        self.driver.close()

    def test_full_operational_workflow(self):
        # 1. Reset command
        cmd_reset = CommandParser.parse("reset")
        self.assertEqual(cmd_reset["command"], "RESET")
        t_reset = self.driver.reset()
        self.assertEqual(t_reset.state, "IDLE")
        self.assertAlmostEqual(t_reset.depth, 50.0)
        self.assertAlmostEqual(t_reset.target_depth, 80.0)
        self.assertEqual(t_reset.collision_count, 0)

        # 2. Set Depth command
        cmd_depth = CommandParser.parse("set depth 45")
        self.driver.set_depth(cmd_depth["value"])
        t1 = self.driver.get_telemetry()
        self.assertAlmostEqual(t1.depth, 45.0)

        # 3. Set Target command
        cmd_target = CommandParser.parse("target 85")
        self.driver.set_target(cmd_target["value"])
        t2 = self.driver.get_telemetry()
        self.assertAlmostEqual(t2.target_depth, 85.0)

        # 4. Set Current command
        cmd_current = CommandParser.parse("current +25")
        self.driver.set_current(cmd_current["value"])
        t3 = self.driver.get_telemetry()
        self.assertEqual(t3.current_strength, 25)

        # 5. Start simulation
        cmd_start = CommandParser.parse("start")
        self.driver.start()
        time.sleep(0.3)  # Allow mock hardware ticks to advance

        t4 = self.driver.get_telemetry()
        self.assertIn(t4.state, ["MOVING_TO_TARGET", "TARGET_REACHED"])
        self.assertGreater(t4.simulation_cycles, 0)

        # 6. Inject Disturbance: WHALE
        cmd_disturb = CommandParser.parse("disturb whale")
        self.driver.disturb(cmd_disturb["type"])
        time.sleep(0.15)  # Allow mock hardware tick to register collision

        t5 = self.driver.get_telemetry()
        self.assertEqual(t5.collision_count, 1)
        self.assertEqual(t5.active_object, "WHALE")

        # 7. Render 3-panel screen test
        screen = render_3panel_screen(t5, self.driver.mode_name, self.driver.is_hardware)
        self.assertIn("UNDERWATER ENVIRONMENT", screen)
        self.assertIn("STATUS READOUT", screen)
        self.assertIn("DEPTH SCALE", screen)
        self.assertIn("WHALE", screen)

        # 8. Reset confirmation
        self.driver.reset()
        t_final = self.driver.get_telemetry()
        self.assertEqual(t_final.state, "IDLE")
        self.assertAlmostEqual(t_final.depth, 50.0)


if __name__ == "__main__":
    unittest.main()
