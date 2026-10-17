"""
tests.test_scene_drivers
========================
Tests all 5 scene drivers for register packing, commands, and telemetry decoding.
"""

import unittest
import sys
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.core.axi_interface import MockAXIInterface
from python.scenes.underwater import UnderwaterDriver
from python.scenes.maze import MazeDriver
from python.scenes.mars_habitat import MarsHabitatDriver
from python.scenes.solar_gimbal import SolarGimbalDriver
from python.scenes.traffic import TrafficDriver


class TestSceneDrivers(unittest.TestCase):

    def test_underwater_driver(self):
        axi = MockAXIInterface(base_addr=0x43C00000)
        driver = UnderwaterDriver(axi)

        # Baseline
        t = driver.get_telemetry()
        self.assertEqual(t["scene"], "underwater")
        self.assertEqual(t["data"]["depth"], 50.0)
        self.assertEqual(t["data"]["target_depth"], 80.0)

        # Set depth 40m
        driver.set_depth(40.0)
        t = driver.get_telemetry()
        self.assertEqual(t["data"]["depth"], 40.0)

        # Set target 100m
        driver.set_target(100.0)
        t = driver.get_telemetry()
        self.assertEqual(t["data"]["target_depth"], 100.0)

        # Disturb whale
        driver.disturb("WHALE")
        t = driver.get_telemetry()
        self.assertTrue(t["data"]["collision"])
        self.assertEqual(t["data"]["active_object"], "WHALE")
        self.assertEqual(t["data"]["collision_count"], 1)

        # Debug registers
        dbg = driver.get_debug_registers()
        self.assertIn("0x43C00000", dbg["base_address"])
        self.assertIn("CONTROL", dbg)

    def test_maze_driver(self):
        axi = MockAXIInterface(base_addr=0x43C10000)
        driver = MazeDriver(axi)

        # Baseline
        t = driver.get_telemetry()
        self.assertEqual(t["scene"], "maze")
        self.assertEqual(t["data"]["player_x"], 0)
        self.assertEqual(t["data"]["player_y"], 0)

        # Start game
        driver.start()
        t = driver.get_telemetry()
        self.assertEqual(t["state"], "GAMEPLAY")

        # Move right (legal from (0,0) according to maze ROM)
        driver.move_right()
        t = driver.get_telemetry()
        self.assertEqual(t["data"]["player_x"], 1)
        self.assertEqual(t["data"]["player_y"], 0)
        self.assertFalse(t["data"]["collision"])
        self.assertEqual(t["data"]["valid_moves"], 1)

        # Try to move UP from row 0 (hits boundary wall)
        driver.move_up()
        t = driver.get_telemetry()
        self.assertEqual(t["data"]["player_x"], 1)
        self.assertEqual(t["data"]["player_y"], 0)
        self.assertTrue(t["data"]["collision"])
        self.assertEqual(t["data"]["collision_count"], 1)

        # Inspect cell ROM
        walls = driver.read_maze_cell(0)
        self.assertEqual(walls, 0b1101)

    def test_mars_habitat_driver(self):
        axi = MockAXIInterface(base_addr=0x43C20000)
        driver = MarsHabitatDriver(axi)

        # Baseline
        t = driver.get_telemetry()
        self.assertEqual(t["scene"], "mars_habitat")
        self.assertEqual(t["data"]["section_A"], "OPERATIONAL")
        self.assertEqual(t["data"]["section_B"], "OPERATIONAL")
        self.assertEqual(t["data"]["link_status"], "OPEN")

        # Launch normal attack (impact ~ 28.0 < threshold 70.0)
        driver.attack(attack_type="NORMAL", target="A", count=5)
        t = driver.get_telemetry()
        self.assertEqual(t["data"]["section_A"], "OPERATIONAL")
        self.assertEqual(t["data"]["link_status"], "OPEN")
        self.assertEqual(t["data"]["total_impacts"], 5)

        # Launch big attack on Section A (impact 87.4 >= threshold 70.0)
        driver.attack(attack_type="BIG", target="A", count=1)
        t = driver.get_telemetry()
        self.assertEqual(t["data"]["section_A"], "CLOSED")
        self.assertEqual(t["data"]["link_status"], "CLOSED")
        self.assertEqual(t["data"]["section_B"], "OPERATIONAL")
        self.assertTrue(t["data"]["threshold_crossed"])

    def test_solar_gimbal_driver(self):
        axi = MockAXIInterface(base_addr=0x43C30000)
        driver = SolarGimbalDriver(axi)

        # Set Sun: 135.0 Az, 42.0 El; Panel: 90.0 Az, 30.0 El
        driver.set_sun_position(135.0, 42.0)
        driver.set_panel_position(90.0, 30.0)
        driver.calculate()

        t = driver.get_telemetry()
        self.assertEqual(t["scene"], "solar_gimbal")
        self.assertAlmostEqual(t["data"]["azimuth_error"], 45.0, places=1)
        self.assertAlmostEqual(t["data"]["elevation_error"], 12.0, places=1)
        self.assertEqual(t["data"]["azimuth_direction"], "CLOCKWISE")
        self.assertEqual(t["data"]["elevation_direction"], "UP")
        self.assertFalse(t["data"]["tracking_locked"])

        # Align to within 0.2 deg -> tracking locked
        driver.set_panel_position(135.1, 42.1)
        driver.calculate()
        t = driver.get_telemetry()
        self.assertTrue(t["data"]["tracking_locked"])
        self.assertEqual(t["state"], "TRACKING_LOCKED")

    def test_traffic_driver(self):
        axi = MockAXIInterface(base_addr=0x43C40000)
        driver = TrafficDriver(axi)

        # Baseline
        t = driver.get_telemetry()
        self.assertEqual(t["scene"], "traffic")
        self.assertEqual(t["data"]["signal_phase"], "NS_GREEN")

        # Step simulation
        driver.step()
        t = driver.get_telemetry()
        self.assertEqual(t["data"]["green_time_remaining_s"], 19)

        # Manual override
        driver.manual_override("EW")
        t = driver.get_telemetry()
        self.assertEqual(t["data"]["signal_phase"], "EW_GREEN")
        self.assertTrue(t["data"]["override_active"])

        # Clear override
        driver.clear_override()
        driver.step()
        t = driver.get_telemetry()
        self.assertFalse(t["data"]["override_active"])


if __name__ == "__main__":
    unittest.main()
