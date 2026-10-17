"""
python.scenes.solar_gimbal.api
==============================
Authoritative Backend API interface for the Solar Tracking Gimbal FPGA scene.
Provides structured endpoints matching Section 18 of the Solar upgrade specification:
- GET solar state
- GET solar telemetry
- POST solar configuration
- POST sun position
- POST gimbal position
- GET FPGA status
- GET performance
- GET execution mode
"""

from typing import Dict, Any, Optional
from python.scenes.solar_gimbal.driver import SolarGimbalDriver


class SolarGimbalAPI:
    """Authoritative API layer interfacing client requests with the FPGA Solar Gimbal Driver."""

    def __init__(self, driver: SolarGimbalDriver):
        self.driver = driver

    def get_solar_state(self) -> Dict[str, Any]:
        """
        GET /api/solar/state
        Returns authoritative real-time state computed in FPGA PL.
        """
        return self.driver.get_solar_state()

    def get_solar_telemetry(self) -> Dict[str, Any]:
        """
        GET /api/solar/telemetry
        Returns full decoded telemetry envelope including 3D vectors, power, and 4 panels.
        """
        return self.driver.get_telemetry()

    def post_solar_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST /api/solar/configuration
        Configures deadbands, prediction horizon, filter shift, and tracking modes in hardware.
        """
        if "az_deadband" in config or "el_deadband" in config:
            az_db = float(config.get("az_deadband", 0.5))
            el_db = float(config.get("el_deadband", 0.5))
            self.driver.set_deadband(az_db, el_db)

        if "multi_panel_en" in config:
            self.driver.enable_multi_panel(bool(config["multi_panel_en"]))

        if "opt_power_en" in config:
            self.driver.enable_power_optimizer(bool(config["opt_power_en"]))

        if "tracking" in config:
            self.driver.enable_tracking(bool(config["tracking"]))

        self.driver.calculate()
        return {
            "status": "success",
            "message": "Updated FPGA Solar configuration parameters",
            "applied": config
        }

    def post_sun_position(self, azimuth: float, elevation: float) -> Dict[str, Any]:
        """
        POST /api/solar/sun
        Transmits target Sun coordinates to FPGA hardware.
        """
        self.driver.set_sun_position(azimuth, elevation)
        self.driver.calculate()
        return {
            "status": "success",
            "sun_azimuth": azimuth,
            "sun_elevation": elevation,
            "message": f"Target Sun position set to Az={azimuth:.1f}°, El={elevation:.1f}°"
        }

    def post_gimbal_position(self, azimuth: float, elevation: float) -> Dict[str, Any]:
        """
        POST /api/solar/gimbal
        Transmits Gimbal panel coordinates to FPGA hardware.
        """
        self.driver.set_panel_position(azimuth, elevation)
        self.driver.calculate()
        return {
            "status": "success",
            "panel_azimuth": azimuth,
            "panel_elevation": elevation,
            "message": f"Gimbal orientation set to Az={azimuth:.1f}°, El={elevation:.1f}°"
        }

    def get_fpga_status(self) -> Dict[str, Any]:
        """
        GET /api/solar/fpga
        Reports FPGA connection, base address, state, and safety supervisory flags.
        """
        telem = self.driver.get_telemetry()
        d = telem["data"]
        return {
            "connected": self.driver.is_hardware,
            "execution_mode": "fpga" if self.driver.is_hardware else "emulator",
            "base_address": f"0x{self.driver.base_address:08X}",
            "hardware_version": d.get("hardware_version", "0x501A7010"),
            "fsm_state": telem.get("state", "IDLE"),
            "tracking_locked": d.get("tracking_locked", False),
            "fault_flags": f"0x{d.get('fault_flags', 0):04X}",
            "fault_list": d.get("fault_list", []),
            "authoritative": d.get("authoritative", "PL")
        }

    def get_performance(self) -> Dict[str, Any]:
        """
        GET /api/solar/performance
        Reads hardware cycle and vector pipeline latency counters.
        """
        return self.driver.get_performance_metrics()

    def get_execution_mode(self) -> Dict[str, Any]:
        """
        GET /api/solar/mode
        Reports hardware vs software execution mode.
        """
        return {
            "mode": "fpga" if self.driver.is_hardware else "emulator",
            "is_hardware": self.driver.is_hardware,
            "platform_authority": "EDGE ZYNQ Z7010 PL" if self.driver.is_hardware else "Laptop Bit-Accurate RTL Emulator"
        }
