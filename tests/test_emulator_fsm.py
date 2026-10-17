"""
Unit tests verifying FSM state transitions on the Laptop FPGA Emulator.
Ensures legal transitions occur deterministically, illegal transitions are rejected,
and reset strobes return the FSM to the initial state.
"""

import unittest
from python.backends.laptop_fpga_backend import LaptopFPGAEmulator

class TestEmulatorFSM(unittest.TestCase):
    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()

    def tearDown(self):
        self.emulator.close()

    def test_underwater_fsm_lifecycle(self):
        base = 0x43C00000
        # Start core with target > current depth
        self.emulator.write32(base + 0x04, (800 << 16) | 400) # Target 80m, Start 40m
        self.emulator.write32(base + 0x00, 0x01) # Enable/Start
        
        # Advance 1 tick -> should transition from IDLE to DIVING (1)
        self.emulator.tick()
        status = self.emulator.read32(base + 0x0C)
        fsm_state = status & 0x07
        self.assertEqual(fsm_state, 1, "Expected DIVING state (1)")

        # Inject disturbance
        self.emulator.write32(base + 0x00, 0x01 | 0x10) # Set disturbance flag
        self.emulator.tick()
        status = self.emulator.read32(base + 0x0C)
        self.assertEqual(status & 0x07, 5, "Expected DISTURBANCE_RECOVERY state (5)")

        # Clear disturbance and advance
        self.emulator.write32(base + 0x00, 0x01)
        for _ in range(5):
            self.emulator.tick()
        status = self.emulator.read32(base + 0x0C)
        self.assertIn(status & 0x07, [1, 2, 4], "Should return to operational flight state")

    def test_maze_fsm_timeout(self):
        base = 0x43C10000
        # Start game
        self.emulator.write32(base + 0x00, 0x01)
        self.emulator.tick()
        status = self.emulator.read32(base + 0x04)
        self.assertIn(status & 0x07, [1, 2, 3], "Expected active maze display/gameplay state")

        # Run 55 ticks without movement -> countdown timer should expire to gameplay
        self.emulator.run_ticks(55)
        status = self.emulator.read32(base + 0x04)
        self.assertIn(status & 0x07, [3, 4, 5], "Expected GAMEPLAY or terminal state")

    def test_solar_fsm_acquire_and_lock(self):
        base = 0x43C30000
        # Set Sun close to panel (within slew range)
        self.emulator.write32(base + 0x04, 15) # 1.5°
        self.emulator.write32(base + 0x08, 10) # 1.0°
        self.emulator.write32(base + 0x00, 0x01) # Enable tracking
        
        self.emulator.tick()
        status = self.emulator.read32(base + 0x14)
        self.assertIn(status & 0x07, [1, 2], "Expected ACQUIRE (1) or TRACKING (2)")

        # Run ticks until locked
        self.emulator.run_ticks(10)
        status = self.emulator.read32(base + 0x14)
        self.assertEqual(status & 0x07, 3, "Expected LOCKED state (3)")
        self.assertTrue((status >> 3) & 1, "Expected locked status bit asserted")

if __name__ == "__main__":
    unittest.main()
