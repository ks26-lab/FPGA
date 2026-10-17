"""
python.scenes.solar_gimbal.driver
=================================
Dedicated hardware driver for Solar Gimbal Autonomous Tracking scene.
Interacts with the FPGA via AXI4-Lite at base address 0x43C30000.
"""

import math
from typing import Dict, Any, Optional

from python.core.fpga_driver import BaseFPGADriver
from python.core.axi_interface import AXIInterface, MockAXIInterface
from python.protocol.encoding import float_to_fixed16
from python.scenes.solar_gimbal.register_map import (
    BASE_ADDRESS,
    REG_CONTROL,
    REG_SUN_POS,
    REG_PANEL_POS,
    REG_STATUS,
    REG_ERROR,
    REG_ACTUATORS,
    REG_CYCLES,
    REG_SUN_VECTOR_X,
    REG_SUN_VECTOR_Y,
    REG_SUN_VECTOR_Z,
    REG_PANEL_NORMAL_X,
    REG_PANEL_NORMAL_Y,
    REG_PANEL_NORMAL_Z,
    REG_DOT_PRODUCT,
    REG_INCIDENT_ANGLE,
    REG_ESTIMATED_POWER,
    REG_FILTERED_SUN,
    REG_PREDICTED_SUN,
    REG_ANGULAR_VELOCITY,
    REG_CONTROL_LIMITS,
    REG_FAULT_FLAGS,
    REG_VECTOR_CYCLES,
    REG_UPDATE_COUNTER,
    REG_PANEL0_DATA,
    REG_PANEL1_DATA,
    REG_PANEL2_DATA,
    REG_PANEL3_DATA,
    REG_TOTAL_ARRAY_POWER,
    REG_PANELS_ACTIVE_MASK,
    REG_TRACKING_QUALITY,
    REG_HARDWARE_VERSION,
    BENCHMARK_IRRADIANCE_W_M2,
    PANEL_AREA_M2,
    PANEL_EFFICIENCY_PCT,
    PEAK_POWER_WATTS
)
from python.scenes.solar_gimbal.telemetry import decode_solar_telemetry


class SolarGimbalDriver(BaseFPGADriver):
    """Driver for Solar Gimbal on AXI peripheral 0x43C30000."""

    def __init__(self, axi: AXIInterface, base_address: int = BASE_ADDRESS):
        super().__init__(axi, scene_name="solar_gimbal", base_address=base_address)
        self._cur_sun_az: float = 180.0
        self._cur_sun_el: float = 45.0
        if isinstance(self.axi, MockAXIInterface):
            self._setup_mock_hooks()

    def _setup_mock_hooks(self):
        """Mock behavior replicating upgraded solar_gimbal_core.v logic."""
        mock = self.axi
        # Baseline registers
        mock.registers[REG_CONTROL] = 0
        mock.registers[REG_SUN_POS] = (450 << 16) | 1800
        mock.registers[REG_PANEL_POS] = (450 << 16) | 1800
        mock.registers[REG_STATUS] = 0
        mock.registers[REG_ERROR] = 0
        mock.registers[REG_ACTUATORS] = 0
        mock.registers[REG_CYCLES] = 0
        mock.registers[REG_SUN_VECTOR_X] = 0
        mock.registers[REG_SUN_VECTOR_Y] = 0
        mock.registers[REG_SUN_VECTOR_Z] = 0
        mock.registers[REG_PANEL_NORMAL_X] = 0
        mock.registers[REG_PANEL_NORMAL_Y] = 0
        mock.registers[REG_PANEL_NORMAL_Z] = 0
        mock.registers[REG_DOT_PRODUCT] = 65536
        mock.registers[REG_INCIDENT_ANGLE] = (1000 << 16) | 0
        mock.registers[REG_ESTIMATED_POWER] = (225 << 16) | int(PEAK_POWER_WATTS)
        mock.registers[REG_FILTERED_SUN] = (450 << 16) | 1800
        mock.registers[REG_PREDICTED_SUN] = (450 << 16) | 1800
        mock.registers[REG_ANGULAR_VELOCITY] = 0
        mock.registers[REG_CONTROL_LIMITS] = (5 << 16) | 5
        mock.registers[REG_FAULT_FLAGS] = 0
        mock.registers[REG_VECTOR_CYCLES] = 18
        mock.registers[REG_UPDATE_COUNTER] = 0
        mock.registers[REG_PANEL0_DATA] = (0 << 16) | int(PEAK_POWER_WATTS)
        mock.registers[REG_PANEL1_DATA] = (10 << 16) | int(PEAK_POWER_WATTS * 0.98)
        mock.registers[REG_PANEL2_DATA] = (20 << 16) | int(PEAK_POWER_WATTS * 0.95)
        mock.registers[REG_PANEL3_DATA] = (30 << 16) | int(PEAK_POWER_WATTS * 0.92)
        mock.registers[REG_TOTAL_ARRAY_POWER] = int(PEAK_POWER_WATTS * 3.85)
        mock.registers[REG_PANELS_ACTIVE_MASK] = 0x0F
        mock.registers[REG_TRACKING_QUALITY] = (100 << 16) | 0
        mock.registers[REG_HARDWARE_VERSION] = 0x501A7010

        def on_control_write(val: int):
            calc_strobe = val & 1
            reset_strobe = (val >> 1) & 1
            track_en = (val >> 2) & 1

            if reset_strobe:
                mock.registers[REG_STATUS] = 0
                mock.registers[REG_ERROR] = 0
                mock.registers[REG_ACTUATORS] = 0
                mock.registers[REG_FAULT_FLAGS] = 0
                return

            if calc_strobe or track_en:
                sun_pos = mock.registers.get(REG_SUN_POS, (450 << 16) | 1800)
                panel_pos = mock.registers.get(REG_PANEL_POS, (450 << 16) | 1800)

                s_az = sun_pos & 0xFFFF
                s_el = (sun_pos >> 16) & 0xFFFF
                p_az = panel_pos & 0xFFFF
                p_el = (panel_pos >> 16) & 0xFFFF

                # Circular modulo 360 wrap-around
                raw_az_diff = s_az - p_az
                if raw_az_diff > 1800:
                    az_err = raw_az_diff - 3600
                elif raw_az_diff < -1800:
                    az_err = raw_az_diff + 3600
                else:
                    az_err = raw_az_diff

                el_err = s_el - p_el

                az_dir = 1 if az_err >= 0 else 0
                el_dir = 1 if el_err >= 0 else 0
                az_hold = 1 if abs(az_err) <= 5 else 0
                el_hold = 1 if abs(el_err) <= 5 else 0
                locked = 1 if (az_hold and el_hold) else 0
                state_code = 2 if locked else 3

                status_val = (state_code & 0x0F) | (locked << 4) | (az_dir << 5) | (el_dir << 6) | (az_hold << 7) | (el_hold << 8)
                mock.registers[REG_STATUS] = status_val
                mock.registers[REG_ERROR] = ((el_err & 0xFFFF) << 16) | (az_err & 0xFFFF)

                act_az = 0 if az_hold else max(-100, min(100, az_err))
                act_el = 0 if el_hold else max(-50, min(50, el_err))
                mock.registers[REG_ACTUATORS] = ((act_el & 0xFFFF) << 16) | (act_az & 0xFFFF)

                # Vector Math Emulation
                s_az_rad = math.radians(s_az / 10.0)
                s_el_rad = math.radians(s_el / 10.0)
                p_az_rad = math.radians(p_az / 10.0)
                p_el_rad = math.radians(p_el / 10.0)

                sx = math.cos(s_el_rad) * math.cos(s_az_rad)
                sy = math.cos(s_el_rad) * math.sin(s_az_rad)
                sz = math.sin(s_el_rad)

                nx = math.cos(p_el_rad) * math.cos(p_az_rad)
                ny = math.cos(p_el_rad) * math.sin(p_az_rad)
                nz = math.sin(p_el_rad)

                dot = max(-1.0, min(1.0, nx * sx + ny * sy + nz * sz))
                dot_q16 = int(dot * 65536) & 0xFFFFFFFF
                mock.registers[REG_SUN_VECTOR_X] = int(sx * 65536) & 0xFFFFFFFF
                mock.registers[REG_SUN_VECTOR_Y] = int(sy * 65536) & 0xFFFFFFFF
                mock.registers[REG_SUN_VECTOR_Z] = int(sz * 65536) & 0xFFFFFFFF
                mock.registers[REG_PANEL_NORMAL_X] = int(nx * 65536) & 0xFFFFFFFF
                mock.registers[REG_PANEL_NORMAL_Y] = int(ny * 65536) & 0xFFFFFFFF
                mock.registers[REG_PANEL_NORMAL_Z] = int(nz * 65536) & 0xFFFFFFFF
                mock.registers[REG_DOT_PRODUCT] = dot_q16

                cos_clamp = max(0.0, dot)
                incident_deg = math.degrees(math.acos(dot)) if dot <= 1.0 else 0.0
                pwr = int(PEAK_POWER_WATTS * cos_clamp)
                mock.registers[REG_INCIDENT_ANGLE] = (int(dot * 1000) << 16) | int(incident_deg * 10)
                mock.registers[REG_ESTIMATED_POWER] = (225 << 16) | pwr
                mock.registers[REG_TOTAL_ARRAY_POWER] = int(pwr * 3.85)

                mock.registers[REG_CYCLES] = (mock.registers.get(REG_CYCLES, 0) + 1) & 0xFFFFFFFF
                mock.registers[REG_UPDATE_COUNTER] = (mock.registers.get(REG_UPDATE_COUNTER, 0) + 1) & 0xFFFFFFFF

        mock.write_hooks[REG_CONTROL] = on_control_write

    def set_sun_position(self, azimuth_deg: float, elevation_deg: float) -> None:
        """Sets sun azimuth and elevation registers."""
        self._cur_sun_az = azimuth_deg
        self._cur_sun_el = elevation_deg
        u_az = float_to_fixed16(azimuth_deg, scale=10.0)
        u_el = float_to_fixed16(elevation_deg, scale=10.0)
        self.write32(REG_SUN_POS, ((u_el & 0xFFFF) << 16) | (u_az & 0xFFFF))

    def set_panel_position(self, azimuth_deg: float, elevation_deg: float) -> None:
        """Sets panel azimuth and elevation registers."""
        u_az = float_to_fixed16(azimuth_deg, scale=10.0)
        u_el = float_to_fixed16(elevation_deg, scale=10.0)
        self.write32(REG_PANEL_POS, ((u_el & 0xFFFF) << 16) | (u_az & 0xFFFF))

    def set_target_azimuth(self, azimuth_deg: float) -> None:
        """Convenience method to set target azimuth."""
        self.set_sun_position(azimuth_deg, self._cur_sun_el)

    def set_target_elevation(self, elevation_deg: float) -> None:
        """Convenience method to set target elevation."""
        self.set_sun_position(self._cur_sun_az, elevation_deg)

    def calculate(self) -> None:
        """Sends calc_strobe to FPGA to perform tracking and vector mathematics."""
        self.write32(REG_CONTROL, 1)

    def enable_tracking(self, enable: bool = True) -> None:
        """Enables or disables continuous hardware tracking."""
        val = (1 << 2) | (1 << 3) if enable else 0
        self.write32(REG_CONTROL, val)

    def start_tracking(self) -> None:
        """Starts continuous hardware tracking."""
        self.enable_tracking(True)

    def start(self) -> None:
        """Alias for start_tracking."""
        self.start_tracking()

    def stop(self) -> None:
        """Disables hardware tracking."""
        self.enable_tracking(False)

    def reset(self) -> None:
        """Sends hardware reset strobe."""
        self.write32(REG_CONTROL, 2)

    def set_deadband(self, az_deadband_deg: float, el_deadband_deg: float) -> None:
        """Sets tracking deadbands (in degrees)."""
        az_db = int(round(az_deadband_deg * 10.0)) & 0xFFFF
        el_db = int(round(el_deadband_deg * 10.0)) & 0xFFFF
        self.write32(REG_CONTROL_LIMITS, (el_db << 16) | az_db)

    def enable_multi_panel(self, enable: bool = True) -> None:
        """Enables 4-channel parallel multi-panel calculation engine."""
        cur = self.read32(REG_CONTROL)
        new_val = (cur | (1 << 3)) if enable else (cur & ~(1 << 3))
        self.write32(REG_CONTROL, new_val)

    def enable_power_optimizer(self, enable: bool = True) -> None:
        """Enables perturb-and-observe MPPT power optimizer."""
        cur = self.read32(REG_CONTROL)
        new_val = (cur | (1 << 4)) if enable else (cur & ~(1 << 4))
        self.write32(REG_CONTROL, new_val)

    def get_telemetry(self) -> Dict[str, Any]:
        """Reads all 32 AXI registers and decodes full FPGA telemetry."""
        return decode_solar_telemetry(
            status_reg=self.read32(REG_STATUS),
            sun_pos_reg=self.read32(REG_SUN_POS),
            panel_pos_reg=self.read32(REG_PANEL_POS),
            error_reg=self.read32(REG_ERROR),
            actuator_reg=self.read32(REG_ACTUATORS),
            cycles_reg=self.read32(REG_CYCLES),
            is_hardware=self.is_hardware,
            sun_vec_x_reg=self.read32(REG_SUN_VECTOR_X),
            sun_vec_y_reg=self.read32(REG_SUN_VECTOR_Y),
            sun_vec_z_reg=self.read32(REG_SUN_VECTOR_Z),
            panel_norm_x_reg=self.read32(REG_PANEL_NORMAL_X),
            panel_norm_y_reg=self.read32(REG_PANEL_NORMAL_Y),
            panel_norm_z_reg=self.read32(REG_PANEL_NORMAL_Z),
            dot_product_reg=self.read32(REG_DOT_PRODUCT),
            incident_angle_reg=self.read32(REG_INCIDENT_ANGLE),
            power_reg=self.read32(REG_ESTIMATED_POWER),
            filtered_sun_reg=self.read32(REG_FILTERED_SUN),
            predicted_sun_reg=self.read32(REG_PREDICTED_SUN),
            angular_velocity_reg=self.read32(REG_ANGULAR_VELOCITY),
            fault_flags_reg=self.read32(REG_FAULT_FLAGS),
            vector_cycles_reg=self.read32(REG_VECTOR_CYCLES),
            update_counter_reg=self.read32(REG_UPDATE_COUNTER),
            p0_data_reg=self.read32(REG_PANEL0_DATA),
            p1_data_reg=self.read32(REG_PANEL1_DATA),
            p2_data_reg=self.read32(REG_PANEL2_DATA),
            p3_data_reg=self.read32(REG_PANEL3_DATA),
            total_power_reg=self.read32(REG_TOTAL_ARRAY_POWER),
            active_mask_reg=self.read32(REG_PANELS_ACTIVE_MASK),
            tracking_quality_reg=self.read32(REG_TRACKING_QUALITY),
            version_reg=self.read32(REG_HARDWARE_VERSION)
        )

    def get_solar_state(self) -> Dict[str, Any]:
        """Returns structured JSON state matching the authoritative FPGA Solar specification (Section 18)."""
        telem = self.get_telemetry()
        d = telem["data"]
        return {
            "mode": "fpga" if self.is_hardware else "emulator",
            "sun": {
                "azimuth": d.get("sun_azimuth", 0.0),
                "elevation": d.get("sun_elevation", 0.0)
            },
            "gimbal": {
                "azimuth": d.get("panel_azimuth", 0.0),
                "elevation": d.get("panel_elevation", 0.0)
            },
            "tracking": {
                "azimuth_error": d.get("azimuth_error", 0.0),
                "elevation_error": d.get("elevation_error", 0.0),
                "tracking_error": d.get("total_tracking_error_deg", 0.0),
                "status": "LOCKED" if d.get("tracking_locked") else ("DEADBAND_HOLD" if (d.get("az_hold") and d.get("el_hold")) else "SLEWING")
            },
            "solar": {
                "incident_angle": d.get("incident_angle", 0.0),
                "power_w": d.get("estimated_power", 0.0),
                "efficiency": d.get("power_efficiency", 0.0)
            },
            "actuator": {
                "azimuth_direction": d.get("azimuth_direction", "HOLD"),
                "elevation_direction": d.get("elevation_direction", "HOLD")
            },
            "hardware": {
                "connected": self.is_hardware,
                "latency_cycles": d.get("vector_cycles", 18),
                "update_counter": d.get("update_counter", 0)
            }
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Returns measured hardware cycle counts, latency, and throughput."""
        t = self.get_telemetry()["data"]
        return {
            "vector_cycles": t.get("vector_cycles", 18),
            "update_counter": t.get("update_counter", 0),
            "cycle_counter": t.get("cycle_counter", 0),
            "authoritative": t.get("authoritative", "PL"),
            "parallel_panels": 4,
            "hardware_connected": self.is_hardware
        }

    def get_debug_registers(self) -> Dict[str, Any]:
        """Dumps all 32 AXI registers as hex strings."""
        return {
            "scene": "solar_gimbal",
            "base_address": f"0x{self.base_address:08X}",
            "REG_CONTROL": f"0x{self.read32(REG_CONTROL):08X}",
            "REG_SUN_POS": f"0x{self.read32(REG_SUN_POS):08X}",
            "REG_PANEL_POS": f"0x{self.read32(REG_PANEL_POS):08X}",
            "REG_STATUS": f"0x{self.read32(REG_STATUS):08X}",
            "REG_ERROR": f"0x{self.read32(REG_ERROR):08X}",
            "REG_ACTUATORS": f"0x{self.read32(REG_ACTUATORS):08X}",
            "REG_CYCLES": f"0x{self.read32(REG_CYCLES):08X}",
            "REG_SUN_VECTOR_X": f"0x{self.read32(REG_SUN_VECTOR_X):08X}",
            "REG_SUN_VECTOR_Y": f"0x{self.read32(REG_SUN_VECTOR_Y):08X}",
            "REG_SUN_VECTOR_Z": f"0x{self.read32(REG_SUN_VECTOR_Z):08X}",
            "REG_PANEL_NORMAL_X": f"0x{self.read32(REG_PANEL_NORMAL_X):08X}",
            "REG_PANEL_NORMAL_Y": f"0x{self.read32(REG_PANEL_NORMAL_Y):08X}",
            "REG_PANEL_NORMAL_Z": f"0x{self.read32(REG_PANEL_NORMAL_Z):08X}",
            "REG_DOT_PRODUCT": f"0x{self.read32(REG_DOT_PRODUCT):08X}",
            "REG_INCIDENT_ANGLE": f"0x{self.read32(REG_INCIDENT_ANGLE):08X}",
            "REG_ESTIMATED_POWER": f"0x{self.read32(REG_ESTIMATED_POWER):08X}",
            "REG_FILTERED_SUN": f"0x{self.read32(REG_FILTERED_SUN):08X}",
            "REG_PREDICTED_SUN": f"0x{self.read32(REG_PREDICTED_SUN):08X}",
            "REG_ANGULAR_VELOCITY": f"0x{self.read32(REG_ANGULAR_VELOCITY):08X}",
            "REG_CONTROL_LIMITS": f"0x{self.read32(REG_CONTROL_LIMITS):08X}",
            "REG_FAULT_FLAGS": f"0x{self.read32(REG_FAULT_FLAGS):08X}",
            "REG_VECTOR_CYCLES": f"0x{self.read32(REG_VECTOR_CYCLES):08X}",
            "REG_UPDATE_COUNTER": f"0x{self.read32(REG_UPDATE_COUNTER):08X}",
            "REG_TOTAL_ARRAY_POWER": f"0x{self.read32(REG_TOTAL_ARRAY_POWER):08X}",
            "REG_PANELS_ACTIVE_MASK": f"0x{self.read32(REG_PANELS_ACTIVE_MASK):08X}",
            "REG_TRACKING_QUALITY": f"0x{self.read32(REG_TRACKING_QUALITY):08X}",
            "REG_HARDWARE_VERSION": f"0x{self.read32(REG_HARDWARE_VERSION):08X}"
        }
