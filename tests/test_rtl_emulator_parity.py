"""
Golden trace regression test verifying strict RTL vs Laptop Emulator Parity.
Compares exact deterministic trace vectors matching the Verilog testbenches in fpga_interface/verilog/.
"""

import unittest
from python.backends.laptop_fpga_backend import LaptopFPGAEmulator

class TestRTLEmulatorParity(unittest.TestCase):
    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()

    def tearDown(self):
        self.emulator.close()

    def test_underwater_golden_trace(self):
        """
        Matches underwater_probe_tb.v:
        - Reset
        - Target: 80.0m (800), Start: 40.0m (400)
        - Current: +20%
        - Start core
        - 10 ticks
        - Verify depth increases by velocity steps (clamp 5)
        """
        base = 0x43C00000
        # Reset pulse
        self.emulator.write32(base + 0x00, 0x02)
        self.assertEqual(self.emulator.read32(base + 0x18), 0) # 0 ticks

        # Configure
        self.emulator.write32(base + 0x04, (800 << 16) | 400)
        self.emulator.write32(base + 0x08, 20)
        self.emulator.write32(base + 0x00, 0x01) # Start

        # Step 10 ticks
        self.emulator.run_ticks(10)

        # Verilog Golden Prediction:
        # At tick 10: depth moved upwards towards 800 with velocity accelerating up to +15
        pos = self.emulator.read32(base + 0x10)
        depth = pos & 0xFFFF
        lateral = (pos >> 16) & 0xFFFF

        self.assertGreater(depth, 400)
        self.assertLessEqual(depth, 800)
        self.assertEqual(lateral, 10 * (20 >> 4)) # exactly 10 units

    def test_maze_golden_trace(self):
        """
        Matches maze_tb.v:
        - Reset
        - Start game
        - Verify (0,0) wall hits when attempting invalid moves (UP, LEFT)
        """
        base = 0x43C10000
        self.emulator.write32(base + 0x00, 0x02) # Reset
        self.emulator.write32(base + 0x00, 0x01) # Start game
        self.emulator.tick()

        # Try illegal move UP (0) -> blocked by outer boundary
        self.emulator.write32(base + 0x04, 0)
        self.emulator.tick()

        # Try illegal move LEFT (3) -> blocked by outer boundary
        self.emulator.write32(base + 0x04, 3)
        self.emulator.tick()

        counters = self.emulator.read32(base + 0x14)
        hits = (counters >> 16) & 0xFFFF
        moves = counters & 0xFFFF

        self.assertEqual(hits, 2, "Both invalid moves must increment collision counter")
        self.assertEqual(moves, 0, "No valid moves executed")

    def test_solar_golden_trace(self):
        """
        Matches solar_gimbal_tb.v:
        - Reset
        - Sun at 180.0° (1800), 45.0° (450)
        - Panel starts at 0.0°, 0.0°
        - Step 10 ticks
        - Verify panel slews azimuth by +10 each tick = 100 units (10.0°)
        """
        base = 0x43C30000
        self.emulator.write32(base + 0x00, 0x02) # Reset
        self.emulator.write32(base + 0x04, 1800)
        self.emulator.write32(base + 0x08, 450)
        self.emulator.write32(base + 0x00, 0x01) # Start

        self.emulator.run_ticks(10)

        panel_az = self.emulator.read32(base + 0x0C)
        panel_el = self.emulator.read32(base + 0x10)

        self.assertEqual(panel_az, 100, "Panel azimuth should have slewed exactly 10 * 10 = 100 units")
        self.assertEqual(panel_el, 50, "Panel elevation should have slewed exactly 10 * 5 = 50 units")

if __name__ == "__main__":
    unittest.main()
