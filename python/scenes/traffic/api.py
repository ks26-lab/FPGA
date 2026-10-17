"""
python.scenes.traffic.api
=========================
Authoritative Backend API interface for the Smart City Traffic Grid FPGA scene.
Provides structured endpoints matching Section 6 of the Traffic upgrade specification:
- GET traffic state
- GET traffic telemetry
- POST/update traffic configuration
- POST vehicle scenario
- POST emergency event
- GET FPGA status
- GET traffic performance counters
- GET hardware/software execution mode
"""

import json
from typing import Dict, Any, Optional
from python.scenes.traffic.driver import TrafficDriver


class TrafficAPI:
    """Authoritative API layer interfacing client requests with the FPGA Traffic Driver."""

    def __init__(self, driver: TrafficDriver):
        self.driver = driver

    def get_traffic_state(self) -> Dict[str, Any]:
        """
        GET /api/traffic/state
        Returns authoritative real-time state computed in FPGA PL.
        """
        return self.driver.get_traffic_state()

    def get_traffic_telemetry(self) -> Dict[str, Any]:
        """
        GET /api/traffic/telemetry
        Returns full decoded telemetry envelope including 16 parallel vehicles.
        """
        return self.driver.get_telemetry()

    def update_traffic_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST /api/traffic/configuration
        Updates intersection queue allocations, priority, and timing limits in hardware.
        """
        int_id = config.get("intersection_id", 1)
        q_ns = config.get("queue_ns", 20)
        q_ew = config.get("queue_ew", 15)
        prio = config.get("priority", 0)
        self.driver.configure_intersection(int_id, q_ns, q_ew, prio)

        if "min_green_s" in config or "max_green_s" in config:
            min_g = config.get("min_green_s", 10)
            max_g = config.get("max_green_s", 45)
            self.driver.configure_timing(min_g, max_g)

        self.driver.step()
        return {
            "status": "success",
            "message": f"Updated hardware configuration for intersection {int_id}",
            "applied": config
        }

    def post_vehicle_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST /api/traffic/scenario
        Sets directional vehicle arrival queues (North, South, East, West).
        """
        qn = scenario.get("north", 10)
        qs = scenario.get("south", 10)
        qe = scenario.get("east", 8)
        qw = scenario.get("west", 6)
        self.driver.set_approach_queues(qn, qs, qe, qw)
        self.driver.step()

        return {
            "status": "success",
            "message": "Scenario injected into FPGA queue engine",
            "queues": {"north": qn, "south": qs, "east": qe, "west": qw}
        }

    def post_emergency_event(self, direction: str = "NORTH") -> Dict[str, Any]:
        """
        POST /api/traffic/emergency
        Asserts priority emergency corridor along specified approach.
        """
        dir_clean = direction.upper()
        if dir_clean not in ("NORTH", "SOUTH", "EAST", "WEST", "N", "S", "E", "W"):
            return {
                "status": "error",
                "message": f"Invalid direction '{direction}'. Must be NORTH, SOUTH, EAST, or WEST."
            }
        full_dir = {"N": "NORTH", "S": "SOUTH", "E": "EAST", "W": "WEST"}.get(dir_clean, dir_clean)
        self.driver.trigger_emergency(full_dir)
        self.driver.step()

        return {
            "status": "success",
            "emergency_active": True,
            "corridor_direction": full_dir,
            "message": f"Emergency vehicle preemption active on {full_dir} approach."
        }

    def clear_emergency(self) -> Dict[str, Any]:
        """
        POST /api/traffic/emergency/clear
        Restores autonomous adaptive scheduling.
        """
        self.driver.clear_override()
        self.driver.step()
        return {
            "status": "success",
            "emergency_active": False,
            "message": "Emergency corridor cleared; restored normal adaptive operation."
        }

    def get_fpga_status(self) -> Dict[str, Any]:
        """
        GET /api/traffic/fpga
        Reports FPGA connection, base address, FSM state, and safety supervisory flags.
        """
        telem = self.driver.get_telemetry()
        d = telem["data"]
        return {
            "connected": self.driver.is_hardware,
            "execution_mode": "fpga" if self.driver.is_hardware else "emulator",
            "base_address": f"0x{self.driver.base_address:08X}",
            "fsm_state_code": d.get("fsm_state_code", 0),
            "signal_phase": d.get("signal_phase", "NS_GREEN"),
            "fault_flags": f"0x{d.get('fault_flags', 0):04X}",
            "fault_count": d.get("fault_count", 0),
            "collision_hazards": d.get("collision_events", 0),
            "authoritative": d.get("authoritative", "PL")
        }

    def get_traffic_performance_counters(self) -> Dict[str, Any]:
        """
        GET /api/traffic/performance
        Reads dedicated hardware cycle and latency counters.
        """
        return self.driver.get_performance_metrics()

    def get_execution_mode(self) -> Dict[str, Any]:
        """
        GET /api/traffic/mode
        Reports hardware vs software execution mode.
        """
        return {
            "mode": "fpga" if self.driver.is_hardware else "emulator",
            "is_hardware": self.driver.is_hardware,
            "platform_authority": "EDGE ZYNQ Z7010 PL" if self.driver.is_hardware else "Laptop Bit-Accurate RTL Emulator"
        }
