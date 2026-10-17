"""
tests.test_mars_parallel_blocks
===============================
Comprehensive verification test suite verifying all 11 FPGA computational blocks,
8-channel parallel meteorite processing, closed-loop landing dynamics,
and 32-register AXI telemetry decoding on the Mars Space Habitat & Landing scene.
"""

import unittest
import sys
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.backends.laptop_fpga_backend import LaptopFPGAEmulator
from python.core.backend_adapter import BackendAXIAdapter
from python.scenes.mars_habitat.driver import MarsHabitatDriver
from python.scenes.mars_habitat.command_handler import MarsHabitatCommandHandler


class TestMarsParallelBlocks(unittest.TestCase):

    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()
        self.adapter = BackendAXIAdapter(self.emulator, base_addr=0x43C20000)
        self.driver = MarsHabitatDriver(self.adapter, base_address=0x43C20000)
        self.handler = MarsHabitatCommandHandler(self.driver)
        self.driver.reset()

    def tearDown(self):
        self.emulator.close()

    def test_block1_registers_reset_initialization(self):
        """Block A & B: Verify reset state on 0x43C20000."""
        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertEqual(d["section_A"], "OPERATIONAL")
        self.assertEqual(d["section_B"], "OPERATIONAL")
        self.assertEqual(d["link_status"], "OPEN")
        self.assertEqual(d["landing_altitude"], 500.0)
        self.assertEqual(d["habitat_health"], 100)
        self.assertEqual(d["fault_flags"], 0x0000)
        self.assertEqual(d["total_impacts"], 0)

    def test_block2_landing_physics_and_retro_thrust(self):
        """Block C & D: Closed-loop powered landing descent & retro-thrust braking."""
        self.driver.start_landing()
        self.emulator.run_ticks(10)

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertLess(d["landing_altitude"], 500.0, "Altitude must decrease during descent")
        self.assertGreater(d["thrust_command"], 0.0, "Retro-thrust must fire to decelerate")
        self.assertIn(d["landing_status"], ["SAFE", "WARNING"])
        self.assertIn(d["landing_fsm"], ["POWERED_DESCENT", "APPROACH", "TOUCHDOWN"])

    def test_block3_parallel_meteorite_engine(self):
        """Block G & J: 8-Channel concurrent parallel meteorite engine."""
        self.driver.start_parallel_meteorites()
        self.emulator.run_ticks(5)

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertEqual(d["meteorite_active_mask"], 0xFF, "All 8 channels must be active concurrently")
        self.assertEqual(d["meteorite_active_count"], 8)
        self.assertGreaterEqual(d["meteorites_processed"], 8)

    def test_block4_legacy_attack_compatibility(self):
        """Verify 100% backward compatibility with legacy attack big segment A command."""
        self.driver.attack(attack_type="BIG", target="A", count=1)
        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertEqual(d["section_A"], "CLOSED", "Section A must be closed after BIG attack")
        self.assertEqual(d["link_status"], "CLOSED", "Link must be closed for isolation")
        self.assertEqual(d["section_B"], "OPERATIONAL", "Section B must remain operational")
        self.assertTrue(d["threshold_crossed"])
        self.assertEqual(d["last_attack_type"], "BIG")

    def test_block5_structural_damage_and_recovery(self):
        """Block K, L & P: Structural damage accumulation and automated breach isolation."""
        self.driver.start_parallel_meteorites()
        self.emulator.run_ticks(15)

        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertGreater(d["total_impact_energy"], 0.0)
        self.assertIn(d["recovery_action"], ["NO_ACTION", "ISOLATE_A", "ISOLATE_B", "ISOLATE_BOTH"])

    def test_block6_atmospheric_and_thermal_dynamics(self):
        """Block M, N & O: Oxygen, CO2, pressure and temperature modeling."""
        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertGreater(d["o2_percent"], 10.0, "O2 level must be realistic percentage")
        self.assertLess(d["co2_percent"], 5.0, "CO2 level must be within tracking bound")
        self.assertGreater(d["pressure_kpa"], 50.0, "Cabin pressure must be tracked")

    def test_block7_life_support_health_and_hazard(self):
        """Block Q, R: 0-100 Habitat Health score and predictive hazard engine."""
        telem = self.driver.get_telemetry()
        d = telem["data"]
        self.assertGreaterEqual(d["habitat_health"], 0)
        self.assertLessEqual(d["habitat_health"], 100)
        self.assertIn(d["life_support_status"], ["STABLE", "DEGRADED", "WARNING", "CRITICAL"])
        self.assertIn(d["hazard_status"], ["NORMAL", "WARNING", "CRITICAL"])

    def test_block8_cli_commands(self):
        """Verify all CLI commands in MarsHabitatCommandHandler."""
        out_land = self.handler.execute("landing", ["status"])
        self.assertIn("LANDING", out_land)
        self.assertIn("Altitude", out_land)

        out_met = self.handler.execute("meteorites", [])
        self.assertIn("ACTIVE METEORITES", out_met)

        out_hab = self.handler.execute("habitat", ["status"])
        self.assertIn("SECTION A", out_hab)
        self.assertIn("O2", out_hab)

        out_ls = self.handler.execute("life", ["support"])
        self.assertIn("LIFE SUPPORT SUBSYSTEM", out_ls)

        out_haz = self.handler.execute("hazards", [])
        self.assertIn("PREDICTIVE HAZARD STATUS", out_haz)

        out_perf = self.handler.execute("performance", [])
        self.assertIn("FPGA HARDWARE PERFORMANCE COUNTERS", out_perf)

        out_fault = self.handler.execute("faults", [])
        self.assertIn("FPGA FAULT DETECTOR", out_fault)

    def test_block9_debug_registers_dump(self):
        """Verify full 32-register hex dump."""
        dbg = self.driver.get_debug_registers()
        self.assertEqual(dbg["scene"], "mars_habitat")
        self.assertIn("0x00_CONTROL", dbg)
        self.assertIn("0x1C_LANDING_ALTITUDE", dbg)
        self.assertIn("0x34_METEORITE_ACTIVE", dbg)
        self.assertIn("0x5C_HABITAT_HEALTH", dbg)
        self.assertIn("0x6C_METEORITES_PROCESSED", dbg)


if __name__ == "__main__":
    unittest.main()
