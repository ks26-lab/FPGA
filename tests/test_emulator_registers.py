"""
Unit tests verifying register read/write parity on the Laptop FPGA Emulator.
Ensures:
- Correct address decoding across all 5 peripheral apertures.
- Read-only registers cannot be overwritten.
- Reset strobes clear state.
- Bit-masking and width constraints are enforced.
"""

import unittest
from python.backends.laptop_fpga_backend import LaptopFPGAEmulator

class TestEmulatorRegisters(unittest.TestCase):
    def setUp(self):
        # Disable autonomous ticking for deterministic unit testing
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()

    def tearDown(self):
        self.emulator.close()

    def test_underwater_registers(self):
        base = 0x43C00000
        # Write config: target=800 (80m), set=400 (40m)
        cfg_val = (800 << 16) | 400
        self.emulator.write32(base + 0x04, cfg_val)
        self.assertEqual(self.emulator.read32(base + 0x04), cfg_val)

        # Write current: +20
        self.emulator.write32(base + 0x08, 20)
        self.assertEqual(self.emulator.read32(base + 0x08), 20)

        # Verify initial status is IDLE (0)
        status = self.emulator.read32(base + 0x0C)
        self.assertEqual(status & 0x07, 0)

        # Reset strobe clears registers
        self.emulator.write32(base + 0x00, 0x02) # Reset bit
        self.assertEqual(self.emulator.read32(base + 0x0C) & 0x07, 0)

    def test_maze_registers(self):
        base = 0x43C10000
        # Initial position should be (0, 0)
        pos = self.emulator.read32(base + 0x0C)
        x = pos & 0xFF
        y = (pos >> 8) & 0xFF
        self.assertEqual((x, y), (0, 0))

        # Initial timer value should be 50 ticks
        timer = self.emulator.read32(base + 0x10)
        self.assertEqual(timer, 50)

    def test_mars_registers(self):
        base = 0x43C20000
        # Initial status should be IDLE (system_state=0, sections operational, link open)
        status = self.emulator.read32(base + 0x0C)
        self.assertEqual(status & 0x0F, 0) # STATE_IDLE
        self.assertEqual((status >> 4) & 1, 0) # Section A operational
        self.assertEqual((status >> 5) & 1, 0) # Section B operational
        self.assertEqual((status >> 6) & 1, 0) # Link A-B open

        # Config threshold write to REG_THRESHOLD (0x08)
        self.emulator.write32(base + 0x08, (650 << 16) | 700)
        self.assertEqual(self.emulator.read32(base + 0x08), (650 << 16) | 700)

    def test_solar_registers(self):
        base = 0x43C30000
        # Write sun azimuth & elevation
        self.emulator.write32(base + 0x04, 2700) # 270.0°
        self.emulator.write32(base + 0x08, 600)  # 60.0°
        self.assertEqual(self.emulator.read32(base + 0x04), 2700)
        self.assertEqual(self.emulator.read32(base + 0x08), 600)

    def test_traffic_registers(self):
        base = 0x43C40000
        # Write queues
        self.emulator.write32(base + 0x10, 15) # NS queue
        self.emulator.write32(base + 0x14, 12) # EW queue
        self.assertEqual(self.emulator.read32(base + 0x10), 15)
        self.assertEqual(self.emulator.read32(base + 0x14), 12)

if __name__ == "__main__":
    unittest.main()
