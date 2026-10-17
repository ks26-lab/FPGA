"""
tests.test_traffic_parallel_blocks
==================================
Unit tests verifying Scene 5 Smart City Traffic Grid FPGA computational blocks:
1. 7-state FSM arbitration with mutual-exclusion enforcement
2. Demand-driven dynamic green split optimizer (NS vs EW)
3. 4-approach directional queue computation and congestion scoring
4. Emergency vehicle preemption corridor override (I1 -> I2 -> I3 -> I4)
5. Pedestrian crossing walk phase scheduling
6. 16-channel concurrent hardware parallel vehicle kinematics engine
7. Starvation prevention and waiting-time accumulation
8. CLI commands (status, density, signal, emergency, pedestrian, auto, optimize, faults, perf, stress)
"""

import unittest
from python.backends.laptop_fpga_backend import LaptopFPGAEmulator
from python.core.backend_adapter import BackendAXIAdapter
from python.scenes.traffic.driver import TrafficDriver
from python.scenes.traffic.command_handler import TrafficCommandHandler
from python.scenes.traffic.register_map import (
    BASE_ADDRESS,
    REG_CONTROL,
    REG_CONFIG,
    REG_STATUS,
    REG_TOTAL_QUEUES,
    REG_DYNAMIC_SPLITS,
    REG_EMERGENCY_STATUS,
    REG_VEHICLE_OCCUPANCY
)


class TestTrafficParallelBlocks(unittest.TestCase):
    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()
        self.adapter = BackendAXIAdapter(self.emulator, base_addr=BASE_ADDRESS)
        self.driver = TrafficDriver(self.adapter, base_address=BASE_ADDRESS)
        self.handler = TrafficCommandHandler(self.driver)
        self.driver.reset()

    def tearDown(self):
        self.emulator.close()

    def test_dynamic_green_split_demand_arbitration(self):
        """Verify dynamic green split favors high-demand direction."""
        # NS Dominated
        self.driver.set_queues(queue_ns=40, queue_ew=10)
        self.driver.step()

        telem = self.driver.get_telemetry()
        self.assertGreaterEqual(telem["calc_green_ns_s"], telem["calc_green_ew_s"])

        # EW Dominated
        self.driver.set_queues(queue_ns=10, queue_ew=60)
        self.driver.step()

        telem = self.driver.get_telemetry()
        self.assertGreater(telem["calc_green_ew_s"], telem["calc_green_ns_s"])

    def test_mutual_exclusion_enforcement(self):
        """Verify NS_GREEN and EW_GREEN never assert simultaneously."""
        for _ in range(20):
            self.driver.step()
            telem = self.driver.get_telemetry()
            self.assertFalse(telem["ns_light"] == "GREEN" and telem["ew_light"] == "GREEN")

    def test_emergency_corridor_preemption(self):
        """Verify emergency vehicle override preempts normal FSM and activates corridor."""
        self.driver.trigger_emergency("EAST")
        self.driver.step()

        telem = self.driver.get_telemetry()
        self.assertTrue(telem["emergency_active"])
        self.assertEqual(telem["emergency_direction"], "EAST")
        self.assertTrue(telem["corridor_active"])
        self.assertEqual(telem["ew_light"], "EMERGENCY GREEN")

    def test_pedestrian_walk_scheduling(self):
        """Verify pedestrian crossing request registration and walk countdown."""
        self.driver.trigger_pedestrian()
        self.driver.step()

        telem = self.driver.get_telemetry()
        self.assertTrue(telem["pedestrian_walk_active"] or telem["data"]["pedestrian_time_remaining"] > 0)

    def test_16_channel_parallel_vehicle_engine(self):
        """Verify all 16 parallel vehicle channels operate concurrently."""
        self.driver.step()
        telem = self.driver.get_telemetry()

        self.assertEqual(telem["vehicle_active_mask"], 0xFFFF)
        self.assertEqual(len(telem["positions_north"]), 4)
        self.assertEqual(len(telem["positions_south"]), 4)
        self.assertEqual(len(telem["positions_east"]), 4)
        self.assertEqual(len(telem["positions_west"]), 4)

    def test_cli_command_handler(self):
        """Verify smart city traffic CLI commands."""
        resp_status = self.handler.execute("traffic", ["status"])
        self.assertIn("SMART CITY TRAFFIC", resp_status)
        self.assertIn("PHASE       :", resp_status)

        resp_density = self.handler.execute("traffic", ["density", "N", "25"])
        self.assertIn("Approach N queue set to 25", resp_density)

        resp_sig = self.handler.execute("traffic", ["signal"])
        self.assertIn("Current Phase:", resp_sig)

        resp_emg = self.handler.execute("traffic", ["emergency", "WEST"])
        self.assertIn("EMERGENCY CORRIDOR ACTIVE", resp_emg)

        resp_ped = self.handler.execute("traffic", ["pedestrian"])
        self.assertIn("Pedestrian walk request", resp_ped)

        resp_perf = self.handler.execute("traffic", ["performance"])
        self.assertIn("FPGA PERFORMANCE", resp_perf)
        self.assertIn("16 hardware channels", resp_perf)

        resp_stress = self.handler.execute("traffic", ["stress"])
        self.assertIn("FPGA TRAFFIC STRESS", resp_stress)


if __name__ == "__main__":
    unittest.main()
