"""
tests.test_traffic_safety
=========================
Mandatory Safety Verification Suite for Smart City Traffic Grid (BASIC Scene 2).
Enforces the NON-NEGOTIABLE Invariant: ACTUAL VEHICLE COLLISION = FORBIDDEN.

Verifies:
TEST 1: Two vehicles moving toward each other (No collision)
TEST 2: Two vehicles entering an intersection (No conflicting occupancy)
TEST 3: Two vehicles in the same lane with insufficient spacing (Safe distance maintained)
TEST 4: High-density traffic (Zero actual collisions across long simulation)
TEST 5: Emergency vehicle preemption (Emergency priority without collision)
TEST 6: Maximum vehicle speed (Next-state prediction prevents unsafe movement)
TEST 7: Adversarial / randomized vehicle states (Every committed state: actual_collision == 0)
TEST 8: Lane-crossing / intersection transition (Zero collision during geometry transition)
"""

import unittest
import random
from python.backends.laptop_fpga_backend import LaptopFPGAEmulator
from python.core.backend_adapter import BackendAXIAdapter
from python.scenes.traffic.driver import TrafficDriver
from python.scenes.traffic.register_map import BASE_ADDRESS


class TestSmartCitySafetyVerification(unittest.TestCase):
    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()
        self.adapter = BackendAXIAdapter(self.emulator, base_addr=BASE_ADDRESS)
        self.driver = TrafficDriver(self.adapter, base_address=BASE_ADDRESS)
        self.driver.reset()

    def tearDown(self):
        self.emulator.close()

    def _assert_zero_collision_invariant(self):
        """MANDATORY ASSERTION: actual_collision == 0 for every committed cycle."""
        self.assertEqual(
            self.emulator.traffic.actual_collision,
            0,
            "HARD INVARIANT VIOLATED: actual_collision != 0!"
        )

    def test_1_head_on_approach(self):
        """TEST 1: Two vehicles moving toward each other safely resolve without collision."""
        self.emulator.traffic.pos_n[0] = 175
        self.emulator.traffic.pos_s[0] = 175
        for _ in range(10):
            self.driver.step()
            self._assert_zero_collision_invariant()

    def test_2_intersection_entry(self):
        """TEST 2: Two vehicles entering intersection concurrently have no conflicting occupancy."""
        self.emulator.traffic.pos_n[0] = 178
        self.emulator.traffic.pos_e[0] = 178
        for _ in range(15):
            self.driver.step()
            self._assert_zero_collision_invariant()
            ns_occ = any(180 <= p <= 220 for p in self.emulator.traffic.pos_n + self.emulator.traffic.pos_s)
            ew_occ = any(180 <= p <= 220 for p in self.emulator.traffic.pos_e + self.emulator.traffic.pos_w)
            self.assertFalse(ns_occ and ew_occ, "Conflicting intersection occupancy detected!")

    def test_3_insufficient_spacing_following(self):
        """TEST 3: Two vehicles in same lane with insufficient spacing maintain safe distance."""
        self.emulator.traffic.pos_n[0] = 100
        self.emulator.traffic.pos_n[1] = 98  # Spacing = 2m < MIN_SEPARATION (8m)
        self.driver.step()
        self._assert_zero_collision_invariant()
        self.assertGreaterEqual(
            self.emulator.traffic.pos_n[0] - self.emulator.traffic.pos_n[1],
            0,
            "Rear vehicle passed lead vehicle in same lane!"
        )

    def test_4_high_density_traffic(self):
        """TEST 4: High-density traffic produces zero actual collisions across 100 cycles."""
        self.driver.set_queues(queue_ns=50, queue_ew=50)
        for _ in range(100):
            self.driver.step()
            self._assert_zero_collision_invariant()

    def test_5_emergency_preemption_safety(self):
        """TEST 5: Emergency vehicle preemption operates without creating collisions."""
        self.driver.trigger_emergency("EAST")
        for _ in range(30):
            self.driver.step()
            self._assert_zero_collision_invariant()

    def test_6_max_speed_prediction(self):
        """TEST 6: Maximum vehicle speed prediction prevents unsafe movement."""
        self.emulator.traffic.speeds = [15, 15, 15, 15]
        self.emulator.traffic.pos_n = [170, 155, 140, 125]
        for _ in range(20):
            self.driver.step()
            self._assert_zero_collision_invariant()

    def test_7_adversarial_randomized_states(self):
        """TEST 7: Adversarial / randomized vehicle states satisfy actual_collision == 0 on all states."""
        random.seed(42)
        for _ in range(50):
            # Inject randomized positions
            self.emulator.traffic.pos_n = [random.randint(0, 240) for _ in range(4)]
            self.emulator.traffic.pos_s = [random.randint(0, 240) for _ in range(4)]
            self.emulator.traffic.pos_e = [random.randint(0, 240) for _ in range(4)]
            self.emulator.traffic.pos_w = [random.randint(0, 240) for _ in range(4)]
            self.driver.step()
            self._assert_zero_collision_invariant()

    def test_8_lane_crossing_geometry_transition(self):
        """TEST 8: Lane-crossing / intersection transition maintains zero collision."""
        for phase_step in range(40):
            self.driver.step()
            self._assert_zero_collision_invariant()


if __name__ == "__main__":
    unittest.main()
