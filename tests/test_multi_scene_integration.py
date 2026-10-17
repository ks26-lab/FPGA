"""
tests.test_multi_scene_integration
==================================
End-to-end integration tests simulating a full user session across all 5 scenes.
"""

import unittest
import sys
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.core.runtime import SystemRuntime
from python.cli.renderer import CLIRenderer


class TestMultiSceneIntegration(unittest.TestCase):

    def setUp(self):
        self.runtime = SystemRuntime(force_mock=True, single_bitstream=False)

    def tearDown(self):
        self.runtime.shutdown()

    def test_full_session_flow(self):
        mgr = self.runtime.scene_mgr

        # 1. Underwater Scene
        resp = mgr.select_scene("underwater")
        self.assertIn("Underwater Dynamic Probe", resp)
        self.assertIn("[FPGA]", resp)

        out = mgr.execute_command("set", ["depth", "40.0"])
        self.assertIn("40.0 m", out)

        out = mgr.execute_command("target", ["80.0"])
        self.assertIn("80.0 m", out)

        out = mgr.execute_command("current", ["+20"])
        self.assertIn("+20%", out)

        out = mgr.execute_command("start", [])
        self.assertIn("started", out)

        out = mgr.execute_command("disturb", ["whale"])
        self.assertIn("WHALE", out)

        telem_water = mgr.get_active_telemetry()
        rendered_water = CLIRenderer.render_telemetry(telem_water)
        self.assertIn("UNDERWATER PROBE STATUS", rendered_water)
        self.assertIn("40.0 m", rendered_water)
        self.assertIn("WHALE", rendered_water)

        dbg = mgr.get_active_debug_registers()
        rendered_dbg = CLIRenderer.render_debug_registers(dbg)
        self.assertIn("0x43C00000", rendered_dbg)

        # 2. Maze Scene
        resp = mgr.select_scene("maze")
        self.assertIn("Maze Runner", resp)

        mgr.execute_command("start", [])
        mgr.execute_command("right", [])
        mgr.execute_command("up", []) # Hits top boundary
        telem_maze = mgr.get_active_telemetry()
        rendered_maze = CLIRenderer.render_telemetry(telem_maze)
        self.assertIn("MAZE RUNNER STATUS", rendered_maze)
        self.assertIn("PLAYER POS (X,Y): (1, 0)", rendered_maze)
        self.assertIn("HIT WALL", rendered_maze)

        # 3. Mars Habitat Scene
        resp = mgr.select_scene("mars")
        self.assertIn("Mars Space Habitat", resp)

        mgr.execute_command("meteorites", ["10"])
        mgr.execute_command("attack", ["big", "segment", "A"])
        telem_mars = mgr.get_active_telemetry()
        rendered_mars = CLIRenderer.render_telemetry(telem_mars)
        self.assertIn("MARS HABITAT DEFENSE", rendered_mars)
        self.assertIn("SECTION A      : CLOSED", rendered_mars)
        self.assertIn("SECTION B      : OPERATIONAL", rendered_mars)
        self.assertIn("LINK A-B       : CLOSED", rendered_mars)

        # 4. Solar Scene
        resp = mgr.select_scene("solar")
        self.assertIn("Solar Gimbal", resp)

        mgr.execute_command("sun", ["azimuth", "180.0"])
        mgr.execute_command("sun", ["elevation", "60.0"])
        mgr.execute_command("panel", ["azimuth", "120.0"])
        mgr.execute_command("panel", ["elevation", "45.0"])
        mgr.execute_command("calculate", [])

        telem_solar = mgr.get_active_telemetry()
        rendered_solar = CLIRenderer.render_telemetry(telem_solar)
        self.assertIn("SOLAR TRACKING GIMBAL", rendered_solar)
        self.assertIn("+60.0°", rendered_solar)

        # 5. Traffic Scene
        resp = mgr.select_scene("traffic")
        self.assertIn("Traffic Management", resp)

        mgr.execute_command("queue", ["ns", "35"])
        mgr.execute_command("queue", ["ew", "10"])
        mgr.execute_command("step", [])

        telem_traffic = mgr.get_active_telemetry()
        rendered_traffic = CLIRenderer.render_telemetry(telem_traffic)
        self.assertIn("SMART CITY TRAFFIC GRID", rendered_traffic)
        self.assertIn("NS=35", rendered_traffic)


if __name__ == "__main__":
    unittest.main()
