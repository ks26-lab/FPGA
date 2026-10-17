"""
tests.test_telemetry_decoder
============================
Unit tests for decoding raw FPGA register reads into the Telemetry dataclass.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fpga_interface.python.telemetry_decoder import decode_telemetry, Telemetry


class TestTelemetryDecoder(unittest.TestCase):

    def test_nominal_decoding(self):
        # Construct known raw register values:
        # 1. STATUS (0x0C):
        #    state = 1 (MOVING_TO_TARGET, bits [3:0])
        #    collision = 0 (bit 4)
        #    recovery = 0 (bit 5)
        #    target_reached = 0 (bit 6)
        #    active_object = 0 (NONE, bits [8:7])
        raw_status = 0x01

        # 2. POSITION (0x10):
        #    depth = 515 (51.5 m, bits [15:0])
        #    disp_x = 12 (lateral offset, bits [23:16])
        #    vel_z = 5 (0.5 m/s, bits [31:24])
        #    raw_position = (5 << 24) | (12 << 16) | 515
        raw_position = (5 << 24) | (12 << 16) | 515

        # 3. COUNTERS (0x14):
        #    collision_count = 2 (bits [15:0])
        raw_counters = 2

        # 4. CYCLES (0x18):
        #    sim_cycle_counter = 15432
        raw_cycles = 15432

        # 5. DEPTH_CFG (0x04):
        #    set_depth = 500 (50.0m), target_depth = 800 (80.0m)
        raw_depth_cfg = (800 << 16) | 500

        # 6. CURRENT (0x08):
        #    current = +20%
        raw_current = 20

        t: Telemetry = decode_telemetry(
            raw_status=raw_status,
            raw_position=raw_position,
            raw_counters=raw_counters,
            raw_cycles=raw_cycles,
            raw_depth_cfg=raw_depth_cfg,
            raw_current=raw_current
        )

        self.assertAlmostEqual(t.depth, 51.5)
        self.assertAlmostEqual(t.target_depth, 80.0)
        self.assertAlmostEqual(t.set_depth, 50.0)
        self.assertEqual(t.current_strength, 20)
        self.assertAlmostEqual(t.displacement_x, 12.0)
        self.assertAlmostEqual(t.velocity_z, 0.5)
        self.assertEqual(t.state, "MOVING_TO_TARGET")
        self.assertEqual(t.state_code, 1)
        self.assertFalse(t.collision)
        self.assertFalse(t.recovery)
        self.assertFalse(t.target_reached)
        self.assertEqual(t.active_object, "NONE")
        self.assertEqual(t.collision_count, 2)
        self.assertEqual(t.simulation_cycles, 15432)

    def test_collision_whale_decoding(self):
        # Collision with WHALE:
        # state = 3 (COLLISION_DETECTED)
        # collision = 1 (bit 4 => 0x10)
        # active_object = 3 (WHALE, bits [8:7] => 3 << 7 = 0x180)
        # raw_status = 0x180 | 0x10 | 0x03 = 0x193
        raw_status = 0x193

        # disp_x = -24 (signed 8-bit => 232)
        # vel_z = -10 (-1.0 m/s => 246)
        # depth = 780 (78.0m)
        raw_position = (246 << 24) | (232 << 16) | 780

        raw_counters = 5
        raw_cycles = 20000

        t = decode_telemetry(raw_status, raw_position, raw_counters, raw_cycles)

        self.assertEqual(t.state, "COLLISION_DETECTED")
        self.assertTrue(t.collision)
        self.assertEqual(t.active_object, "WHALE")
        self.assertAlmostEqual(t.depth, 78.0)
        self.assertAlmostEqual(t.displacement_x, -24.0)
        self.assertAlmostEqual(t.velocity_z, -1.0)
        self.assertEqual(t.collision_count, 5)


if __name__ == "__main__":
    unittest.main()
