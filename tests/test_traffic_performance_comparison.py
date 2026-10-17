"""
tests.test_traffic_performance_comparison
=========================================
Automated tests validating Section 13 Performance Comparison requirements:
- Measured FPGA update latency vs Software update latency
- Measured throughput (updates/sec and vehicles/sec)
- Queue calculation latency
- Signal decision latency
- Speedup factor calculation
"""

import unittest
from python.scenes.traffic.benchmark import run_traffic_benchmark
from python.scenes.traffic.driver import TrafficDriver
from python.scenes.traffic.api import TrafficAPI
from python.core.axi_interface import MockAXIInterface


class TestTrafficPerformanceComparison(unittest.TestCase):
    """Validates measured performance metrics between FPGA PL and Software PS."""

    def test_run_traffic_benchmark_metrics(self):
        bm = run_traffic_benchmark(iterations=200)

        self.assertIn("software", bm)
        self.assertIn("fpga_hardware", bm)
        self.assertIn("performance_gain", bm)

        sw = bm["software"]
        hw = bm["fpga_hardware"]
        gain = bm["performance_gain"]

        # Ensure all required metrics are present and non-zero
        self.assertGreater(sw["latency_us_per_update"], 0)
        self.assertGreater(sw["throughput_updates_sec"], 0)
        self.assertGreater(sw["throughput_vehicles_sec"], 0)
        self.assertGreater(sw["queue_calc_latency_us"], 0)
        self.assertGreater(sw["optimizer_latency_us"], 0)

        self.assertGreater(hw["clock_frequency_mhz"], 0)
        self.assertGreater(hw["latency_cycles"], 0)
        self.assertGreater(hw["throughput_updates_sec"], 0)
        self.assertGreater(hw["throughput_vehicles_sec"], 0)

        # Hardware latency should be significantly lower than software latency
        self.assertGreater(sw["latency_us_per_update"], hw["latency_us_per_update"])
        self.assertGreater(gain["speedup_factor"], 1.0)
        self.assertGreater(gain["latency_reduction_pct"], 50.0)

    def test_traffic_api_performance_and_counters(self):
        axi = MockAXIInterface()
        driver = TrafficDriver(axi=axi)
        api = TrafficAPI(driver=driver)

        perf = api.get_traffic_performance_counters()
        self.assertIn("fsm_cycles", perf)
        self.assertIn("vehicle_cycles", perf)
        self.assertIn("optimizer_cycles", perf)
        self.assertIn("total_updates", perf)
        self.assertEqual(perf["parallel_channels"], 16)

        state = api.get_traffic_state()
        self.assertIn("mode", state)
        self.assertIn("signal_phase", state)
        self.assertIn("queues", state)
        self.assertIn("average_speed", state)
        self.assertIn("stopped_vehicles", state)
        self.assertIn("congestion_score", state)
        self.assertIn("hardware", state)
        self.assertEqual(state["hardware"]["connected"], False)

        # Test POST configuration
        cfg_resp = api.update_traffic_configuration({"intersection_id": 1, "queue_ns": 30, "queue_ew": 20, "min_green_s": 15, "max_green_s": 50})
        self.assertEqual(cfg_resp["status"], "success")

        # Test POST scenario
        scen_resp = api.post_vehicle_scenario({"north": 20, "south": 15, "east": 10, "west": 8})
        self.assertEqual(scen_resp["status"], "success")

        # Test POST emergency
        emg_resp = api.post_emergency_event("EAST")
        self.assertEqual(emg_resp["status"], "success")
        self.assertEqual(emg_resp["corridor_direction"], "EAST")

        # Test clear emergency
        clr_resp = api.clear_emergency()
        self.assertEqual(clr_resp["status"], "success")

        # Test GET status & execution mode
        st = api.get_fpga_status()
        self.assertIn("base_address", st)
        self.assertIn("fault_flags", st)

        m = api.get_execution_mode()
        self.assertEqual(m["mode"], "emulator")



if __name__ == "__main__":
    unittest.main()
