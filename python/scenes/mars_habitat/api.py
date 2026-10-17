"""
python.scenes.mars_habitat.api
==============================
Backend API routing and structured endpoints for Mars Space Habitat & Landing Accelerator.
Fulfills all requirements of Section 20 of the specification:
  GET  /mars/state
  GET  /mars/telemetry
  GET  /mars/landing
  GET  /mars/meteorites
  GET  /mars/habitat
  GET  /mars/faults
  GET  /mars/fpga
  GET  /mars/performance
  POST /mars/configure
  POST /mars/launch
  POST /mars/meteorite
  POST /mars/abort
"""

from typing import Dict, Any
from python.scenes.mars_habitat.driver import MarsHabitatDriver
from python.scenes.mars_habitat.benchmark import run_mars_benchmark


class MarsHabitatAPI:
    """REST API service layer for Mars Space Habitat & Landing scene."""

    def __init__(self, driver: MarsHabitatDriver):
        self.driver = driver

    # --------------------------------------------------------------------------
    # GET Endpoints
    # --------------------------------------------------------------------------
    def get_mars_state(self) -> Dict[str, Any]:
        """GET /mars/state - Complete structured JSON state matching Section 20."""
        return self.driver.get_mars_state()

    def get_mars_telemetry(self) -> Dict[str, Any]:
        """GET /mars/telemetry - Decoded 32-register raw and physical telemetry."""
        return self.driver.get_telemetry()

    def get_landing_telemetry(self) -> Dict[str, Any]:
        """GET /mars/landing - Focused landing trajectory & retro-thrust telemetry."""
        state = self.driver.get_mars_state()
        return {
            "status": "success",
            "landing": state["landing"],
            "environment": state["environment"],
            "hardware": state["hardware"]
        }

    def get_meteorite_telemetry(self) -> Dict[str, Any]:
        """GET /mars/meteorites - 8-channel parallel meteorite field telemetry."""
        state = self.driver.get_mars_state()
        return {
            "status": "success",
            "meteorites": state["meteorites"],
            "hardware": state["hardware"]
        }

    def get_habitat_telemetry(self) -> Dict[str, Any]:
        """GET /mars/habitat - Habitat structural integrity, damage, and life-support."""
        state = self.driver.get_mars_state()
        return {
            "status": "success",
            "habitat": state["habitat"],
            "life_support": state["life_support"],
            "hardware": state["hardware"]
        }

    def get_fault_telemetry(self) -> Dict[str, Any]:
        """GET /mars/faults - Hardware safety supervisor and fault bitmask."""
        t = self.driver.get_telemetry()["data"]
        return {
            "status": "success",
            "fault_flags": f"0x{t.get('fault_flags', 0):04X}",
            "active_faults": t.get("faults", []),
            "recovery_action": t.get("recovery_action", "NO_ACTION")
        }

    def get_fpga_status(self) -> Dict[str, Any]:
        """GET /mars/fpga - Hardware connection status, base address, and version."""
        t = self.driver.get_telemetry()["data"]
        return {
            "status": "success",
            "connected": self.driver.is_hardware,
            "mode": "fpga" if self.driver.is_hardware else "emulator",
            "base_address": f"0x{self.driver.base_address:08X}",
            "core_version": t.get("core_version", "0x4D415253"),
            "latency_cycles": t.get("latency_cycles", 18),
            "simulation_cycles": t.get("simulation_cycles", 0)
        }

    def get_performance(self) -> Dict[str, Any]:
        """GET /mars/performance - Measured FPGA vs Software benchmark."""
        return run_mars_benchmark(iterations=100)

    # --------------------------------------------------------------------------
    # POST Endpoints
    # --------------------------------------------------------------------------
    def configure_system(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """POST /mars/configure - Updates thresholds or attack parameters."""
        th_a = config.get("threshold_A")
        th_b = config.get("threshold_B")
        if th_a is not None and th_b is not None:
            self.driver.set_thresholds(float(th_a), float(th_b))

        return {
            "status": "success",
            "message": "Mars Habitat configuration updated."
        }

    def launch(self) -> Dict[str, Any]:
        """POST /mars/launch - Triggers powered landing descent."""
        self.driver.launch()
        return {
            "status": "success",
            "message": "Powered descent initiated in FPGA PL."
        }

    def trigger_meteorite(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST /mars/meteorite - Spawns meteorite batch or enables parallel engine."""
        atk_type = payload.get("type", "NORMAL")
        target = payload.get("target", "ALL")
        count = int(payload.get("count", 1))
        self.driver.attack(attack_type=atk_type, target=target, count=count)

        return {
            "status": "success",
            "message": f"Spawned {atk_type} meteorite attack on Target {target} ({count} items)."
        }

    def abort(self) -> Dict[str, Any]:
        """POST /mars/abort - Aborts descent or halts simulation."""
        self.driver.abort()
        return {
            "status": "success",
            "message": "Descent aborted; hardware controller stabilized in safe state."
        }
