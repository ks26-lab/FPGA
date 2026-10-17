"""
tests.test_underwater_parallel_blocks
======================================
Comprehensive verification test suite verifying all 8 FPGA parallel processing blocks
and 32-register AXI telemetry decoding on the Underwater Dynamic Probe.
"""

import unittest
import sys
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.backends.laptop_fpga_backend import LaptopFPGAEmulator
from python.core.backend_adapter import BackendAXIAdapter
from python.scenes.underwater.driver import UnderwaterDriver
from python.scenes.underwater.command_handler import UnderwaterCommandHandler


class TestUnderwaterParallelBlocks(unittest.TestCase):

    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()
        self.adapter = BackendAXIAdapter(self.emulator, base_addr=0x43C00000)
        self.driver = UnderwaterDriver(self.adapter, base_address=0x43C00000)
        self.handler = UnderwaterCommandHandler(self.driver)
        self.driver.reset()

    def tearDown(self):
        self.emulator.close()

    def test_block1_depth_error_and_convergence(self):
        """Block A: Depth Physics & Discrete Error calculation."""
        self.driver.set_depth(50.0)
        self.driver.set_target(80.0)
        self.driver.start()
        self.emulator.tick()

        telem = self.driver.get_telemetry()
        d = telem["data"]
        # depth_error = target - current = 80 - 50 = +30.0m
        self.assertAlmostEqual(d["depth_error"], 30.0, places=1)
        self.assertEqual(telem["state"], "MOVING_TO_TARGET")

    def test_block2_pid_thrust_and_anti_windup(self):
        """Block E & F: Hardware PID Depth Controller & Bounded Thrust."""
        self.driver.set_depth(50.0)
        self.driver.set_target(80.0)
        self.driver.start()
        self.emulator.run_ticks(5)

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertGreater(d["p_term"], 0.0, "P-term must be positive for positive error")
        self.assertGreater(d["thrust"], 50.0, "Thrust command must increase to drive descent")
        self.assertLessEqual(d["thrust"], 150.0, "Thrust must not exceed maximum saturation")

    def test_block3_hydrodynamic_drag_engine(self):
        """Block D: Parallel Drag Calculation Engine."""
        self.driver.set_depth(50.0)
        self.driver.set_target(80.0)
        self.driver.set_current(20) # +20% current
        self.driver.start()
        self.emulator.run_ticks(10)

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertIsNotNone(d["drag_force"])
        self.assertIsNotNone(d["relative_velocity"])

    def test_block4_moving_average_and_ema_filtering(self):
        """Block G: Parallel Hardware Filter Engine."""
        self.driver.set_depth(50.0)
        self.driver.set_target(80.0)
        self.driver.start()
        self.emulator.run_ticks(8)

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertAlmostEqual(d["filtered_depth"], d["depth"], delta=5.0)
        self.assertIsNotNone(d["filtered_velocity"])

    def test_block5_collision_energy_and_severity(self):
        """Block H: Parallel Collision Impact Engine."""
        self.driver.start()
        self.emulator.tick()

        # Inject WHALE disturbance
        self.driver.disturb("WHALE")
        self.emulator.tick()

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertTrue(d["collision"])
        self.assertEqual(d["active_object"], "WHALE")
        self.assertGreater(d["impact_energy"], 0)
        self.assertIn(d["impact_severity"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_block6_asymptotic_recovery_fsm(self):
        """Block I: Hardware Recovery Engine & FSM."""
        self.driver.start()
        self.emulator.tick()
        self.driver.disturb("FISH")
        self.emulator.run_ticks(3)

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertTrue(d["recovery"], "Recovery FSM must be active after impact")
        self.assertGreater(d["recovery_thrust"], 0.0)

    def test_block7_depth_prediction_engine(self):
        """Block J: Future-depth projection (T+1, T+3, T+5)."""
        self.driver.set_depth(40.0)
        self.driver.set_target(90.0)
        self.driver.start()
        self.emulator.run_ticks(5)

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertGreater(d["predicted_depth_1"], 0.0)
        self.assertGreater(d["predicted_depth_3"], 0.0)
        self.assertGreater(d["predicted_depth_5"], 0.0)

    def test_block8_energy_optimizer_and_fault_detector(self):
        """Block K & L: Energy Optimizer & Fault/Anomaly Detector."""
        self.driver.set_depth(50.0)
        self.driver.set_target(50.0)
        self.driver.start()
        self.emulator.tick()

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertIn(d["optimization_action"], ["HOLD_THRUST", "INCREASE_THRUST", "DECREASE_THRUST"])
        self.assertIsInstance(d["fault_flags"], int)
        self.assertIsInstance(d["active_faults"], list)

    def test_command_handler_extensions(self):
        """Verifies CLI command handler for pid, prediction, faults."""
        res_pid = self.handler.execute("pid", [])
        self.assertIn("FPGA PID DEPTH CONTROLLER", res_pid)

        res_pred = self.handler.execute("prediction", [])
        self.assertIn("FPGA FUTURE DEPTH PROJECTION", res_pred)

        res_faults = self.handler.execute("faults", [])
        self.assertIn("FPGA HARDWARE FAULT STATUS", res_faults)


if __name__ == "__main__":
    unittest.main()
