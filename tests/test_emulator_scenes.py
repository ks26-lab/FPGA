"""
Integration tests executing all five scenes through their standard SceneDrivers
backed by the Laptop FPGA Emulator.
Ensures scene drivers operate correctly without knowing whether hardware is present.
"""

import unittest
from python.backends.laptop_fpga_backend import LaptopFPGAEmulator
from python.core.backend_adapter import BackendAXIAdapter
from python.scenes.underwater import UnderwaterDriver
from python.scenes.maze import MazeDriver
from python.scenes.mars_habitat import MarsHabitatDriver
from python.scenes.solar_gimbal import SolarGimbalDriver
from python.scenes.traffic import TrafficDriver

class TestEmulatorScenes(unittest.TestCase):
    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()

    def tearDown(self):
        self.emulator.close()

    def test_underwater_scene_driver(self):
        adapter = BackendAXIAdapter(self.emulator, base_addr=0x43C00000)
        driver = UnderwaterDriver(adapter, base_address=0x43C00000)
        driver.reset()

        driver.set_depth(40.0)
        driver.set_target(80.0)
        driver.set_current(20)
        driver.start()

        self.emulator.run_ticks(15)

        telem = driver.get_telemetry()
        self.assertIn("depth", telem)
        self.assertIn("state_str", telem)
        self.assertFalse(driver.is_hardware)
        self.assertEqual(driver.mode_name, "LAPTOP FPGA EMULATION")

    def test_maze_scene_driver(self):
        adapter = BackendAXIAdapter(self.emulator, base_addr=0x43C10000)
        driver = MazeDriver(adapter, base_address=0x43C10000)
        driver.reset()
        driver.start_game()

        # Try valid move right from (0,0) -> based on maze ROM (0,0) wall mask is 0b1101 (LEFT, DOWN, UP)
        # RIGHT is unblocked -> move right
        driver.move("right")
        self.emulator.tick()

        telem = driver.get_telemetry()
        self.assertEqual(telem["player_pos"], (1, 0))

    def test_mars_scene_driver(self):
        adapter = BackendAXIAdapter(self.emulator, base_addr=0x43C20000)
        driver = MarsHabitatDriver(adapter, base_address=0x43C20000)
        driver.reset()
        driver.start()

        self.emulator.run_ticks(30)
        telem = driver.get_telemetry()
        self.assertIn("seg_a_health", telem)
        self.assertIn("seg_b_health", telem)

    def test_solar_scene_driver(self):
        adapter = BackendAXIAdapter(self.emulator, base_addr=0x43C30000)
        driver = SolarGimbalDriver(adapter, base_address=0x43C30000)
        driver.reset()
        driver.set_target_azimuth(180.0)
        driver.set_target_elevation(45.0)
        driver.start_tracking()

        self.emulator.run_ticks(20)
        telem = driver.get_telemetry()
        self.assertIn("azimuth_error", telem)
        self.assertIn("elevation_error", telem)

    def test_traffic_scene_driver(self):
        adapter = BackendAXIAdapter(self.emulator, base_addr=0x43C40000)
        driver = TrafficDriver(adapter, base_address=0x43C40000)
        driver.reset()
        driver.start()
        driver.set_queues(10, 5)

        self.emulator.run_ticks(35) # Should advance phase through NS_GREEN to YELLOW/RED
        telem = driver.get_telemetry()
        self.assertIn("phase_name", telem)
        self.assertIn("ns_light", telem)

if __name__ == "__main__":
    unittest.main()
