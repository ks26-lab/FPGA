"""
tests.test_scene_manager
========================
Tests for SceneManager and Scene selection / address mapping.
"""

import unittest
import sys
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.core.transport import TransportManager
from python.core.scene_manager import SceneManager
from python.protocol.enums import SceneType
from python.protocol.errors import SceneNotSelectedError


class TestSceneManager(unittest.TestCase):

    def setUp(self):
        self.transport_mgr = TransportManager(force_mock=True)
        self.mgr = SceneManager(self.transport_mgr, single_bitstream_mode=False)

    def tearDown(self):
        self.transport_mgr.close_all()

    def test_initial_state_none(self):
        self.assertIsNone(self.mgr.active_scene)
        with self.assertRaises(SceneNotSelectedError):
            self.mgr.get_active_telemetry()

    def test_select_all_scenes(self):
        # Undersea / Underwater
        resp = self.mgr.select_scene("underwater")
        self.assertEqual(self.mgr.active_scene, SceneType.UNDERWATER)
        self.assertIn("Underwater Dynamic Probe", resp)
        self.assertEqual(self.mgr.get_driver(SceneType.UNDERWATER).base_address, 0x43C00000)

        # Maze
        resp = self.mgr.select_scene("maze")
        self.assertEqual(self.mgr.active_scene, SceneType.MAZE)
        self.assertIn("Maze Runner", resp)
        self.assertEqual(self.mgr.get_driver(SceneType.MAZE).base_address, 0x43C10000)

        # Mars
        resp = self.mgr.select_scene("mars")
        self.assertEqual(self.mgr.active_scene, SceneType.MARS)
        self.assertIn("Mars Space Habitat", resp)
        self.assertEqual(self.mgr.get_driver(SceneType.MARS).base_address, 0x43C20000)

        # Solar
        resp = self.mgr.select_scene("solar")
        self.assertEqual(self.mgr.active_scene, SceneType.SOLAR)
        self.assertIn("Solar Gimbal", resp)
        self.assertEqual(self.mgr.get_driver(SceneType.SOLAR).base_address, 0x43C30000)

        # Traffic
        resp = self.mgr.select_scene("traffic")
        self.assertEqual(self.mgr.active_scene, SceneType.TRAFFIC)
        self.assertIn("Traffic Management", resp)
        self.assertEqual(self.mgr.get_driver(SceneType.TRAFFIC).base_address, 0x43C40000)

    def test_single_bitstream_mode(self):
        single_mgr = SceneManager(self.transport_mgr, single_bitstream_mode=True)
        for st in [SceneType.UNDERWATER, SceneType.MAZE, SceneType.MARS, SceneType.SOLAR, SceneType.TRAFFIC]:
            driver = single_mgr.get_driver(st)
            self.assertEqual(driver.base_address, 0x43C00000)

    def test_invalid_scene_name(self):
        with self.assertRaises(ValueError):
            self.mgr.select_scene("quantum_teleportation")


if __name__ == "__main__":
    unittest.main()
