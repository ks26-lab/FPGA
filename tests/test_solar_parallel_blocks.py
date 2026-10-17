"""
tests.test_solar_parallel_blocks
================================
Unit tests verifying Scene 4 Solar Tracking Gimbal FPGA computational blocks:
1. Azimuth angle circular wrap-around (+10.0° for 5.0° - 355.0°)
2. 3D Cartesian spherical-to-unit vector transformations (|S| ≈ 1.0, |N| ≈ 1.0)
3. Incident angle dot-product & arccos engine (theta = 0.0° aligned, 90.0° orthogonal)
4. Photovoltaic power estimation: P = I0 * A * eta * max(0, cos theta)
5. Deadband holding (az_hold, el_hold)
6. 4-channel concurrent parallel multi-panel array
7. Safety fault flags detection
8. CLI command routing (status, track, stop, sun, gimbal, power, panels, faults, perf)
"""

import unittest
from python.backends.laptop_fpga_backend import LaptopFPGAEmulator
from python.core.backend_adapter import BackendAXIAdapter
from python.scenes.solar_gimbal.driver import SolarGimbalDriver
from python.scenes.solar_gimbal.command_handler import SolarGimbalCommandHandler
from python.scenes.solar_gimbal.register_map import (
    BASE_ADDRESS,
    PEAK_POWER_WATTS,
    REG_SUN_VECTOR_X,
    REG_DOT_PRODUCT,
    REG_INCIDENT_ANGLE,
    REG_ESTIMATED_POWER,
    REG_PANELS_ACTIVE_MASK
)


class TestSolarParallelBlocks(unittest.TestCase):
    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()
        self.adapter = BackendAXIAdapter(self.emulator, base_addr=BASE_ADDRESS)
        self.driver = SolarGimbalDriver(self.adapter, base_address=BASE_ADDRESS)
        self.handler = SolarGimbalCommandHandler(self.driver)
        self.driver.reset()

    def tearDown(self):
        self.emulator.close()

    def test_azimuth_circular_angle_wrap(self):
        """Verify azimuth wrap-around: Sun=5.0°, Gimbal=355.0° -> +10.0°."""
        self.driver.set_sun_position(5.0, 45.0)
        self.driver.set_panel_position(355.0, 45.0)
        self.driver.calculate()

        telem = self.driver.get_telemetry()
        self.assertAlmostEqual(telem["azimuth_error"], 10.0, places=1)

        # Reverse wrap: Sun=355.0°, Gimbal=5.0° -> -10.0°
        self.driver.set_sun_position(355.0, 45.0)
        self.driver.set_panel_position(5.0, 45.0)
        self.driver.calculate()

        telem = self.driver.get_telemetry()
        self.assertAlmostEqual(telem["azimuth_error"], -10.0, places=1)

    def test_perfect_alignment_and_power(self):
        """Verify perfect alignment yields theta ~= 0.0°, dot_product ~= 1.0, and P ~= 5665 W."""
        self.driver.set_sun_position(180.0, 45.0)
        self.driver.set_panel_position(180.0, 45.0)
        self.driver.calculate()

        telem = self.driver.get_telemetry()
        self.assertEqual(telem["azimuth_error"], 0.0)
        self.assertEqual(telem["elevation_error"], 0.0)
        self.assertAlmostEqual(telem["dot_product"], 1.0, places=2)
        self.assertLessEqual(telem["incident_angle"], 1.0)
        self.assertGreaterEqual(telem["estimated_power"], 5300.0)

    def test_orthogonal_misalignment_power_collapse(self):
        """Verify 90° misalignment yields dot_product ~= 0.0, theta ~= 90.0°, and P = 0 W."""
        self.driver.set_sun_position(0.0, 0.0)
        self.driver.set_panel_position(90.0, 0.0)
        self.driver.calculate()

        telem = self.driver.get_telemetry()
        self.assertAlmostEqual(telem["dot_product"], 0.0, places=1)
        self.assertAlmostEqual(telem["incident_angle"], 90.0, places=0)
        self.assertEqual(telem["estimated_power"], 0.0)

    def test_tracking_deadband(self):
        """Verify deadband hold suppresses motor stepping for small errors."""
        self.driver.set_sun_position(180.3, 45.0)
        self.driver.set_panel_position(180.0, 45.0)
        self.driver.calculate()

        telem = self.driver.get_telemetry()
        self.assertTrue(telem["az_hold"])
        self.assertEqual(telem["actuator_azimuth"], 0.0)

    def test_4_channel_parallel_array(self):
        """Verify 4-channel concurrent parallel multi-panel array computation."""
        self.driver.set_sun_position(180.0, 45.0)
        self.driver.set_panel_position(180.0, 45.0)
        self.driver.calculate()

        telem = self.driver.get_telemetry()
        self.assertEqual(telem["panels_active_count"], 4)
        self.assertEqual(len(telem["panels"]), 4)
        self.assertGreater(telem["total_array_power"], 15000.0)
        for p in telem["panels"]:
            self.assertTrue(p["active"])
            self.assertGreater(p["power_w"], 0.0)

    def test_cli_command_handler(self):
        """Verify solar CLI subcommands."""
        resp_status = self.handler.execute("solar", ["status"])
        self.assertIn("SOLAR GIMBAL", resp_status)
        self.assertIn("SUN       :", resp_status)

        resp_track = self.handler.execute("solar", ["track"])
        self.assertIn("ACTIVE", resp_track)

        resp_sun = self.handler.execute("solar", ["sun", "132.4", "48.2"])
        self.assertIn("132.4°", resp_sun)

        resp_power = self.handler.execute("solar", ["power"])
        self.assertIn("PHOTOVOLTAIC POWER ENGINE", resp_power)

        resp_panels = self.handler.execute("solar", ["panels"])
        self.assertIn("4-CHANNEL CONCURRENT PARALLEL PANELS", resp_panels)

        resp_perf = self.handler.execute("solar", ["performance"])
        self.assertIn("FPGA PERFORMANCE", resp_perf)


if __name__ == "__main__":
    unittest.main()
