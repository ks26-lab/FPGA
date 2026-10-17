"""
Unit tests verifying clock determinism and tick synchronization on the Laptop FPGA Emulator.
Ensures:
- Identical initial state + identical input + N ticks = identical output.
- Synchronous run_ticks(N) yields identical result to N individual tick() calls.
"""

import unittest
from python.backends.laptop_fpga_backend import LaptopFPGAEmulator

class TestEmulatorTick(unittest.TestCase):
    def test_deterministic_tick_execution(self):
        # Create two isolated emulators with identical parameters
        emu1 = LaptopFPGAEmulator(enable_autonomous_clock=False)
        emu2 = LaptopFPGAEmulator(enable_autonomous_clock=False)

        emu1.open()
        emu2.open()

        try:
            base = 0x43C00000
            # Identical inputs: Target 100m, Start 20m, Current +32%
            cfg = (1000 << 16) | 200
            emu1.write32(base + 0x04, cfg)
            emu2.write32(base + 0x04, cfg)

            emu1.write32(base + 0x08, 32)
            emu2.write32(base + 0x08, 32)

            emu1.write32(base + 0x00, 0x01) # Start
            emu2.write32(base + 0x00, 0x01) # Start

            # Emu1 runs 25 ticks via loop
            for _ in range(25):
                emu1.tick()

            # Emu2 runs 25 ticks via batch run_ticks
            emu2.run_ticks(25)

            # Compare all registers
            pos1 = emu1.read32(base + 0x10)
            pos2 = emu2.read32(base + 0x10)
            self.assertEqual(pos1, pos2, "Tick results must be 100% deterministic")

            status1 = emu1.read32(base + 0x0C)
            status2 = emu2.read32(base + 0x0C)
            self.assertEqual(status1, status2, "FSM state must be 100% deterministic")

            cycles1 = emu1.read32(base + 0x18)
            cycles2 = emu2.read32(base + 0x18)
            self.assertEqual(cycles1, cycles2, "Cycle counts must be identical")
            self.assertEqual(cycles1, 25)

        finally:
            emu1.close()
            emu2.close()

if __name__ == "__main__":
    unittest.main()
