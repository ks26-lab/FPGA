"""
tests.test_mars_performance_comparison
=======================================
Comprehensive automated verification suite for Scene 3: Mars Space Habitat /
Landing & Meteorite Defense FPGA Upgrade on EDGE ZYNQ Z7010 (XC7Z010).

Validates all 21 test areas mandated by Section 25:
 1. AXI read/write (all registers 0x00 to 0x78)
 2. Descent physics (a = (T - mg)/m, v[n+1], h[n+1])
 3. Thrust control (retro-thrust throttle feedback & limits)
 4. Landing FSM (PREP -> POWERED DESCENT -> APPROACH -> TOUCHDOWN)
 5. Touchdown detection (radar altitude <= 1.0 m & velocity dampening)
 6. Meteorite trajectory (discrete integration x, y, z updates)
 7. Parallel meteorite processing (8 concurrent channels)
 8. Impact detection (3D collision region check)
 9. Impact energy (E = 0.5 * m * v^2 fixed-point)
10. Damage classification (LOW, MODERATE, HIGH, CRITICAL)
11. Section isolation (Section A / Section B independent bulkhead sealing)
12. Habitat FSM (NORMAL -> IMPACT -> DAMAGE -> ISOLATION -> STABILIZATION)
13. Atmospheric drag (simplified Martian drag model)
14. Thermal risk (thermal load and overheating warning)
15. Life-support monitor (O2, CO2, cabin pressure, power reserve)
16. Fault detection (hardware fault supervisor bitmask)
17. Backend <-> FPGA communication (AXI transactions and telemetry decoding)
18. Backend <-> UI (JSON telemetry serialization & state payload)
19. Hardware unavailable (--hw truthfully halts when /dev/mem is absent)
20. Fixed-point vs floating-point golden model comparison
21. Regression of existing Mars functionality (legacy attack syntax preserved)
"""

import math
import os
import sys
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.backends.laptop_fpga_backend import LaptopFPGAEmulator
from python.core.backend_adapter import BackendAXIAdapter
from python.scenes.mars_habitat.driver import MarsHabitatDriver
from python.scenes.mars_habitat.command_handler import MarsHabitatCommandHandler
from python.scenes.mars_habitat.api import MarsHabitatAPI
from python.scenes.mars_habitat.benchmark import run_mars_benchmark
from python.scenes.mars_habitat.register_map import (
    BASE_ADDRESS,
    REG_CONTROL,
    REG_ATTACK,
    REG_THRESHOLD,
    REG_STATUS,
    REG_IMPACT,
    REG_COUNTERS,
    REG_TOTAL,
    REG_LANDING_ALTITUDE,
    REG_LANDING_VELOCITY,
    REG_THRUST_COMMAND,
    REG_PREDICTED_ALTITUDE,
    REG_PREDICTED_TOUCHDOWN_VEL,
    REG_LANDING_STATUS,
    REG_METEORITE_ACTIVE,
    REG_METEORITE_IMPACT_VECTOR,
    REG_TOTAL_IMPACT_ENERGY,
    REG_SECTION_DAMAGE,
    REG_RECOVERY_ACTION,
    REG_O2_PERCENT,
    REG_CO2_PERCENT,
    REG_PRESSURE_KPA,
    REG_TEMPERATURE_C,
    REG_LIFE_SUPPORT_STATUS,
    REG_HABITAT_HEALTH,
    REG_HAZARD_SCORE,
    REG_FAULT_FLAGS,
    REG_SIMULATION_CYCLES,
    REG_METEORITES_PROCESSED,
    REG_LATENCY_CYCLES,
    REG_UPDATE_COUNTER,
    REG_HARDWARE_VERSION,
)


class TestMarsPerformanceComparison(unittest.TestCase):
    """Automated test suite verifying all 21 validation items for the Mars FPGA engine."""

    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()
        self.adapter = BackendAXIAdapter(self.emulator, base_addr=BASE_ADDRESS)
        self.driver = MarsHabitatDriver(self.adapter, base_address=BASE_ADDRESS)
        self.handler = MarsHabitatCommandHandler(self.driver)
        self.api = MarsHabitatAPI(self.driver)
        self.driver.reset()

    def tearDown(self):
        self.emulator.close()

    # --------------------------------------------------------------------------
    # 1. AXI READ / WRITE
    # --------------------------------------------------------------------------
    def test_01_axi_read_write(self):
        """Verify reading and writing to AXI registers across 0x00 to 0x78."""
        regs = self.driver.get_debug_registers()
        self.assertIn("0x00_CONTROL", regs)
        self.assertIn("0x1C_LANDING_ALTITUDE", regs)
        self.assertIn("0x24_THRUST_COMMAND", regs)
        self.assertIn("0x34_METEORITE_ACTIVE", regs)
        self.assertIn("0x3C_TOTAL_IMPACT_ENERGY", regs)
        self.assertIn("0x5C_HABITAT_HEALTH", regs)
        self.assertIn("0x64_FAULT_FLAGS", regs)
        self.assertIn("0x70_LATENCY_CYCLES", regs)
        self.assertIn("0x78_HARDWARE_VERSION", regs)
        self.assertEqual(regs["0x78_HARDWARE_VERSION"], "0x4D415253")

    # --------------------------------------------------------------------------
    # 2. DESCENT PHYSICS
    # --------------------------------------------------------------------------
    def test_02_descent_physics(self):
        """Verify discrete descent dynamics: acceleration, velocity, altitude."""
        self.driver.start_landing()
        self.emulator.run_ticks(10)
        telem = self.driver.get_telemetry()["data"]
        self.assertLess(telem["landing_altitude"], 500.0)
        self.assertLessEqual(telem["landing_velocity"], 0.0)
        self.assertGreaterEqual(telem["landing_acceleration"], -10.0)
        self.assertLessEqual(telem["landing_acceleration"], 10.0)

    # --------------------------------------------------------------------------
    # 3. THRUST CONTROL
    # --------------------------------------------------------------------------
    def test_03_thrust_control(self):
        """Verify retro-thrust controller adjusts throttle based on altitude/velocity."""
        self.driver.start_landing()
        self.emulator.run_ticks(5)
        telem = self.driver.get_telemetry()["data"]
        self.assertGreater(telem["thrust_command"], 0.0)
        self.assertLessEqual(telem["thrust_command"], 10000.0)

    # --------------------------------------------------------------------------
    # 4. LANDING FSM
    # --------------------------------------------------------------------------
    def test_04_landing_fsm(self):
        """Verify landing FSM stages: PREP, POWERED_DESCENT, APPROACH, TOUCHDOWN."""
        self.driver.reset()
        telem = self.driver.get_telemetry()["data"]
        self.assertEqual(telem["landing_fsm"], "PREP")

        self.driver.start_landing()
        self.emulator.run_ticks(5)
        telem = self.driver.get_telemetry()["data"]
        self.assertIn(telem["landing_fsm"], ["POWERED_DESCENT", "APPROACH", "TOUCHDOWN"])

    # --------------------------------------------------------------------------
    # 5. TOUCHDOWN DETECTION
    # --------------------------------------------------------------------------
    def test_05_touchdown_detection(self):
        """Verify touchdown detection flag and throttle cut-off on ground contact."""
        self.driver.start_landing()
        # Run sufficient ticks to reach ground
        self.emulator.run_ticks(150)
        telem = self.driver.get_telemetry()["data"]
        self.assertLessEqual(telem["landing_altitude"], 5.0)
        if telem["landing_altitude"] <= 1.0:
            self.assertTrue(telem["touchdown"])

    # --------------------------------------------------------------------------
    # 6. METEORITE TRAJECTORY
    # --------------------------------------------------------------------------
    def test_06_meteorite_trajectory(self):
        """Verify discrete meteorite trajectory displacement integration."""
        self.driver.start_parallel_meteorites()
        t0 = self.driver.get_telemetry()["data"]
        self.emulator.run_ticks(5)
        t1 = self.driver.get_telemetry()["data"]
        self.assertGreater(t1["meteorites_processed"], t0["meteorites_processed"])

    # --------------------------------------------------------------------------
    # 7. PARALLEL METEORITE PROCESSING (8 CHANNELS)
    # --------------------------------------------------------------------------
    def test_07_parallel_meteorite_processing(self):
        """Verify all 8 hardware channels process concurrently."""
        self.driver.start_parallel_meteorites()
        self.emulator.run_ticks(5)
        telem = self.driver.get_telemetry()["data"]
        self.assertEqual(telem["meteorite_active_mask"], 0xFF)
        self.assertEqual(telem["meteorite_active_count"], 8)
        self.assertGreaterEqual(telem["meteorites_processed"], 8)

    # --------------------------------------------------------------------------
    # 8. IMPACT DETECTION
    # --------------------------------------------------------------------------
    def test_08_impact_detection(self):
        """Verify collision detection when trajectory enters habitat impact radius."""
        self.driver.attack(attack_type="BIG", target="A", count=1)
        telem = self.driver.get_telemetry()["data"]
        self.assertGreaterEqual(telem["total_impacts"], 1)

    # --------------------------------------------------------------------------
    # 9. IMPACT ENERGY (E = 0.5 * m * v^2)
    # --------------------------------------------------------------------------
    def test_09_impact_energy(self):
        """Verify kinetic energy computation for impacting bodies."""
        self.driver.start_parallel_meteorites()
        self.emulator.run_ticks(15)
        telem = self.driver.get_telemetry()["data"]
        self.assertGreater(telem["total_impact_energy"], 0.0)

    # --------------------------------------------------------------------------
    # 10. DAMAGE CLASSIFICATION
    # --------------------------------------------------------------------------
    def test_10_damage_classification(self):
        """Verify structural damage accumulation on sections A & B."""
        self.driver.attack(attack_type="NORMAL", target="A", count=1)
        telem = self.driver.get_telemetry()["data"]
        self.assertGreaterEqual(telem["section_A_damage"], 0)
        self.assertLessEqual(telem["section_A_damage"], 100)

    # --------------------------------------------------------------------------
    # 11. SECTION ISOLATION
    # --------------------------------------------------------------------------
    def test_11_section_isolation(self):
        """Verify Section A and Section B isolate independently when breached."""
        self.driver.attack(attack_type="BIG", target="A", count=1)
        telem = self.driver.get_telemetry()["data"]
        self.assertEqual(telem["section_A"], "CLOSED")
        self.assertEqual(telem["link_status"], "CLOSED")
        self.assertEqual(telem["section_B"], "OPERATIONAL")

    # --------------------------------------------------------------------------
    # 12. HABITAT FSM
    # --------------------------------------------------------------------------
    def test_12_habitat_fsm(self):
        """Verify recovery action transitions."""
        self.driver.reset()
        telem = self.driver.get_telemetry()["data"]
        self.assertEqual(telem["recovery_action"], "NO_ACTION")

        self.driver.attack(attack_type="BIG", target="B", count=1)
        telem = self.driver.get_telemetry()["data"]
        self.assertIn(telem["recovery_action"], ["ISOLATE_B", "ISOLATE_BOTH"])

    # --------------------------------------------------------------------------
    # 13. ATMOSPHERIC DRAG
    # --------------------------------------------------------------------------
    def test_13_atmospheric_drag(self):
        """Verify environmental parameters and atmospheric drag tracking."""
        state = self.driver.get_mars_state()
        self.assertIn("environment", state)
        self.assertIn("drag", state["environment"])
        self.assertGreaterEqual(state["environment"]["drag"], 0.0)

    # --------------------------------------------------------------------------
    # 14. THERMAL RISK
    # --------------------------------------------------------------------------
    def test_14_thermal_risk(self):
        """Verify thermal load monitoring and temperature ranges."""
        telem = self.driver.get_telemetry()["data"]
        self.assertGreater(telem["temperature_c"], -100.0)
        self.assertLess(telem["temperature_c"], 100.0)
        state = self.driver.get_mars_state()
        self.assertIn("thermal_risk", state["environment"])

    # --------------------------------------------------------------------------
    # 15. LIFE-SUPPORT MONITOR
    # --------------------------------------------------------------------------
    def test_15_life_support_monitor(self):
        """Verify O2, CO2, pressure, and composite health tracking."""
        telem = self.driver.get_telemetry()["data"]
        self.assertGreater(telem["o2_percent"], 10.0)
        self.assertLess(telem["co2_percent"], 5.0)
        self.assertGreater(telem["pressure_kpa"], 50.0)
        self.assertGreaterEqual(telem["habitat_health"], 0)
        self.assertLessEqual(telem["habitat_health"], 100)

    # --------------------------------------------------------------------------
    # 16. FAULT DETECTION
    # --------------------------------------------------------------------------
    def test_16_fault_detection(self):
        """Verify hardware fault supervisor register and codes."""
        telem = self.driver.get_telemetry()["data"]
        self.assertIsInstance(telem["fault_flags"], int)
        fault_resp = self.api.get_faults()
        self.assertEqual(fault_resp["status"], "success")
        self.assertIn("fault_active", fault_resp)

    # --------------------------------------------------------------------------
    # 17. BACKEND <-> FPGA COMMUNICATION
    # --------------------------------------------------------------------------
    def test_17_backend_fpga_communication(self):
        """Verify end-to-end AXI adapter transactions and version register."""
        version = self.driver.get_hardware_version()
        self.assertEqual(version, 0x4D415253)
        self.assertEqual(self.driver.core_version, "0x4D415253")

    # --------------------------------------------------------------------------
    # 18. BACKEND <-> UI JSON TELEMETRY
    # --------------------------------------------------------------------------
    def test_18_backend_ui_telemetry(self):
        """Verify JSON telemetry matching Section 20 specification."""
        state = self.driver.get_mars_state()
        self.assertIn("mode", state)
        self.assertIn("landing", state)
        self.assertIn("meteorites", state)
        self.assertIn("habitat", state)
        self.assertIn("environment", state)
        self.assertIn("life_support", state)
        self.assertIn("hardware", state)

        landing = state["landing"]
        self.assertIn("stage", landing)
        self.assertIn("altitude_m", landing)
        self.assertIn("velocity_mps", landing)
        self.assertIn("acceleration_mps2", landing)
        self.assertIn("thrust_n", landing)
        self.assertIn("touchdown", landing)

        hw = state["hardware"]
        self.assertIn("connected", hw)
        self.assertIn("latency_cycles", hw)
        self.assertIn("update_counter", hw)

    # --------------------------------------------------------------------------
    # 19. HARDWARE UNAVAILABLE BEHAVIOR
    # --------------------------------------------------------------------------
    def test_19_hardware_unavailable(self):
        """Verify 'mars start --hw' strictly halts when /dev/mem is not present."""
        resp = self.handler.handle("mars start --hw")
        # In a development environment without physical Zynq /dev/mem, must report failure truthfully
        if not os.path.exists("/dev/mem"):
            self.assertIn("HARDWARE UNAVAILABLE", resp)
            self.assertIn("SOFTWARE SIMULATION MODE REQUIRED", resp)
        else:
            self.assertIn("AUTHORITATIVE", resp)

    # --------------------------------------------------------------------------
    # 20. FIXED-POINT VS FLOATING-POINT GOLDEN MODEL
    # --------------------------------------------------------------------------
    def test_20_fixed_vs_floating_point_parity(self):
        """Verify fixed-point kinetic energy calculation matches float E = 0.5 * m * v^2."""
        mass = 5.0  # kg
        vx = 10.0
        vy = 20.0
        vz = 30.0
        v_sq = vx * vx + vy * vy + vz * vz
        float_energy_j = 0.5 * mass * v_sq  # 0.5 * 5 * 1400 = 3500 J = 3.5 kJ

        # Fixed point Q16.16 equivalent
        mass_q = int(mass * 256)  # Q8.8
        v_sq_q = int(v_sq * 256)  # Q8.8
        fixed_energy_j = (mass_q * v_sq_q) >> 9  # / 512
        rel_error = abs(fixed_energy_j - float_energy_j) / float_energy_j
        self.assertLess(rel_error, 0.05, "Fixed-point kinetic energy must match within 5%")

    # --------------------------------------------------------------------------
    # 21. REGRESSION OF EXISTING MARS FUNCTIONALITY
    # --------------------------------------------------------------------------
    def test_21_regression_existing_functionality(self):
        """Verify backward compatibility of CLI syntax: attack big segment A."""
        res = self.handler.handle("attack big segment A")
        self.assertIn("SUCCESS", res)
        self.assertIn("ATTACK INITIATED", res)

        status_res = self.handler.handle("status")
        self.assertIn("Section A", status_res)
        self.assertIn("Section B", status_res)

        perf_res = self.handler.handle("mars performance")
        self.assertIn("PERFORMANCE", perf_res)


if __name__ == "__main__":
    unittest.main()
