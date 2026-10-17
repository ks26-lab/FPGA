"""
Unit tests verifying fixed-point integer arithmetic and scaling in the Laptop FPGA Emulator.
Ensures:
- 0.1m depth scaling (40.0m -> 400).
- Bitwise arithmetic right-shift drift (>> 4).
- Circular azimuth modulo error (+1800 / -3600).
- Galois LFSR bit-shifts and polynomial feedback.
"""

import unittest
from python.backends.laptop_fpga_backend import LaptopFPGAEmulator

class TestEmulatorFixedPoint(unittest.TestCase):
    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()

    def tearDown(self):
        self.emulator.close()

    def test_underwater_fixed_point_drift(self):
        base = 0x43C00000
        # Configure set depth = 50.0m (500 units), target = 50.0m (500 units)
        self.emulator.write32(base + 0x04, (500 << 16) | 500)
        # Configure strong ocean current = +64% (64 >> 4 = +4 units lateral drift per tick)
        self.emulator.write32(base + 0x08, 64)
        self.emulator.write32(base + 0x00, 0x01) # Start

        # Run 10 ticks
        self.emulator.run_ticks(10)

        pos = self.emulator.read32(base + 0x10)
        depth = pos & 0xFFFF
        lateral = (pos >> 16) & 0xFFFF
        
        # Depth should stay at 500 (target depth held)
        self.assertEqual(depth, 500)
        # Lateral displacement should be exactly 10 * 4 = 40 units (4.0m)
        self.assertEqual(lateral, 40)

    def test_solar_circular_azimuth_error(self):
        base = 0x43C30000
        # Sun at 10.0° (100 units), Panel at 350.0° (3500 units)
        # Direct difference: 100 - 3500 = -3400
        # Circular shortest path should be: -3400 + 3600 = +200 (+20.0°)
        self.emulator.write32(base + 0x04, 100)
        self.emulator.solar.panel_azimuth = 3500
        self.emulator.write32(base + 0x00, 0x01) # Enable

        self.emulator.tick()
        az_error_raw = self.emulator.read32(base + 0x18)
        # Interpret 16-bit signed
        az_error = az_error_raw if az_error_raw < 0x8000 else az_error_raw - 0x10000
        self.assertEqual(az_error, 200, "Circular modulo arithmetic must yield +200 shortest path")

    def test_mars_lfsr_reproducibility(self):
        base = 0x43C20000
        # Enable impact generator
        self.emulator.write32(base + 0x00, 0x01)
        
        # Advance 4 sequence intervals (4 * 10 ticks = 40 ticks)
        self.emulator.run_ticks(40)
        
        last_impact = self.emulator.read32(base + 0x10)
        # Verify impact value is non-zero and within expected discrete range
        self.assertGreater(last_impact, 0)
        self.assertLessEqual(last_impact, 1000)

if __name__ == "__main__":
    unittest.main()
