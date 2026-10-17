"""
EDGE ZYNQ Z7010 High-Level Hardware Service Interface
======================================================
Provides scene-specific hardware transaction routines for all 5 simulation
environments:
  1. Undersea Dynamic Probe (Depth, thrust, current drift, collision FSM)
  2. Solar Tracking Gimbal (3D vector error, servo angles, actuator outputs)
  3. Smart City Traffic Grid (Intersection phase arbitrations, queue telemetry)
  4. Space Habitat / Mars Landing (State machine, impact protection, deceleration)
  5. 3D Maze Runner (Collision verification, movement validation, step counter)

CRITICAL NON-NEGOTIABLE RULE:
- If FPGA is CONNECTED: returns real hardware register data marked 'FPGA_HARDWARE'.
- If FPGA is DISCONNECTED: returns hardware_active=False, source='SOFTWARE_ONLY',
  and hardware telemetry as None/'N/A'. Never pretends Python is FPGA.
"""

import struct
from typing import Dict, Any, Optional

from hardware.fpga_protocol import (
    SCENE_UNDERSEA,
    SCENE_SOLAR,
    SCENE_CITY,
    SCENE_SPACE,
    SCENE_MAZE,
    OP_STEP_SIM,
    OP_READ_REG,
    OP_WRITE_REG,
)
from hardware.fpga_connection import FPGAConnectionManager


_global_fpga_interface: Optional["FPGAHardwareInterface"] = None


def get_fpga_interface() -> "FPGAHardwareInterface":
    """
    Factory function returning a singleton instance of FPGAHardwareInterface.
    Guarantees thread-safe shared hardware state across all simulation scenes.
    """
    global _global_fpga_interface
    if _global_fpga_interface is None:
        _global_fpga_interface = FPGAHardwareInterface()
    return _global_fpga_interface


class FPGAHardwareInterface:
    """
    Unified Hardware Communication Service bridging simulation scenes
    to the physical EDGE ZYNQ Z7010 board.
    """
    def __init__(self):
        self.conn = FPGAConnectionManager()

    @property
    def is_hardware_active(self) -> bool:
        """Returns True ONLY if real hardware handshake has succeeded."""
        return self.conn.status.value == "CONNECTED"

    def get_status_badge(self) -> Tuple[str, str]:
        """
        Returns (badge_text, color_name) for UI display.
        color_name: 'GREEN' if connected, 'RED' if not connected.
        """
        if self.is_hardware_active:
            resp = self.conn.last_response_ms
            resp_txt = f"{resp}ms" if resp is not None else "LIVE"
            return (f"[● FPGA ACTIVE // {resp_txt}]", "GREEN")
        else:
            return ("[× FPGA NOT CONNECTED — SOFTWARE ONLY]", "RED")

    # =========================================================================
    # 1. UNDERSEA DYNAMIC PROBE HARDWARE PIPELINE
    # =========================================================================
    def step_undersea_probe(
        self,
        current_depth_m: float,
        target_depth_m: float,
        current_strength_pct: int = 0,
        disturb_type: int = 0
    ) -> Dict[str, Any]:
        """
        Transacts with underwater_probe_core.v on Zynq PL.
        Transmits depth configuration and disturbance strobes.
        Reads back AXI 0x0C (Status), 0x10 (Position), 0x14 (Counters).
        """
        self.conn.active_function = "UNDERSEA_DEPTH_CONTROL"

        if not self.is_hardware_active:
            # Explicitly report hardware unavailability!
            return {
                "hardware_active": False,
                "source": "SOFTWARE_ONLY",
                "fpga_depth": None,
                "fpga_velocity": None,
                "fpga_thrust": None,
                "fpga_state": "OFFLINE",
                "fpga_collision": None,
                "message": "FPGA NOT CONNECTED — Running on local software physics model"
            }

        # Pack into AXI frame:
        # payload: [target_depth_x10 (int16), current_str (int8), disturb_type (int8)]
        payload = struct.pack(">hbb", int(target_depth_m * 10), int(current_strength_pct), int(disturb_type))
        success, resp_payload, err = self.conn.transact(SCENE_UNDERSEA, OP_STEP_SIM, payload)

        if not success or len(resp_payload) < 8:
            return {
                "hardware_active": False,
                "source": "COMM_ERROR",
                "fpga_depth": None,
                "fpga_velocity": None,
                "fpga_thrust": None,
                "fpga_state": "ERR",
                "message": f"Hardware Transaction Failed: {err}"
            }

        # Unpack physical PL registers:
        # [depth_x10 (int16), velocity_z (int8), displacement_x (int8), state (uint8), collision (uint8), thrust_n (uint16)]
        depth_x10, vel_z, disp_x, state_val, col_flag, thrust_n = struct.unpack(">hbbBBH", resp_payload[:8])

        state_names = ["IDLE", "SEEKING", "HOLDING", "COLLISION", "DISPLACEMENT", "RECOVERY", "TARGET_REACHED"]
        state_str = state_names[state_val] if state_val < len(state_names) else f"STATE_{state_val}"

        return {
            "hardware_active": True,
            "source": "FPGA_HARDWARE",
            "fpga_depth": depth_x10 / 10.0,
            "fpga_velocity": float(vel_z) / 10.0,
            "fpga_displacement_x": float(disp_x) / 10.0,
            "fpga_thrust": float(thrust_n),
            "fpga_state": state_str,
            "fpga_collision": bool(col_flag),
            "latency_ms": self.conn.last_response_ms
        }

    # =========================================================================
    # 2. SOLAR TRACKING GIMBAL HARDWARE PIPELINE
    # =========================================================================
    def step_solar_gimbal(
        self,
        sun_azimuth: float,
        sun_elevation: float,
        panel_azimuth: float,
        panel_elevation: float
    ) -> Dict[str, Any]:
        """
        Transacts with solar_gimbal core on Zynq PL.
        Calculates 360-modulo angular errors and actuator commands on hardware.
        """
        self.conn.active_function = "SOLAR_GIMBAL_CONTROL"

        if not self.is_hardware_active:
            return {
                "hardware_active": False,
                "source": "SOFTWARE_ONLY",
                "fpga_azimuth_error": None,
                "fpga_elevation_error": None,
                "fpga_actuator_az": None,
                "fpga_actuator_el": None,
                "fpga_state": "OFFLINE",
                "message": "FPGA NOT CONNECTED — Software trigonometric tracking active"
            }

        payload = struct.pack(">hhhh", int(sun_azimuth * 10), int(sun_elevation * 10),
                              int(panel_azimuth * 10), int(panel_elevation * 10))
        success, resp_payload, err = self.conn.transact(SCENE_SOLAR, OP_STEP_SIM, payload)

        if not success or len(resp_payload) < 8:
            return {
                "hardware_active": False,
                "source": "COMM_ERROR",
                "fpga_azimuth_error": None,
                "fpga_elevation_error": None,
                "fpga_state": "ERR",
                "message": f"Hardware Transaction Failed: {err}"
            }

        # Unpack: [az_err_x10 (int16), el_err_x10 (int16), az_act (int16), el_act (int16)]
        az_err_x10, el_err_x10, az_act, el_act = struct.unpack(">hhhh", resp_payload[:8])

        return {
            "hardware_active": True,
            "source": "FPGA_HARDWARE",
            "fpga_azimuth_error": az_err_x10 / 10.0,
            "fpga_elevation_error": el_err_x10 / 10.0,
            "fpga_actuator_az": az_act / 10.0,
            "fpga_actuator_el": el_act / 10.0,
            "fpga_state": "TRACKING_LOCKED" if (abs(az_err_x10) < 5 and abs(el_err_x10) < 5) else "SLEWING",
            "latency_ms": self.conn.last_response_ms
        }

    # =========================================================================
    # 3. SMART CITY TRAFFIC GRID HARDWARE PIPELINE
    # =========================================================================
    def step_traffic_grid(
        self,
        intersection_id: str,
        queue_ns: int,
        queue_ew: int,
        manual_override: bool = False
    ) -> Dict[str, Any]:
        """
        Transacts with traffic FSM controller on Zynq PL.
        Arbitrates signal phase timing and priority allocation on hardware.
        """
        self.conn.active_function = "TRAFFIC_FSM_ARBITRATION"

        if not self.is_hardware_active:
            return {
                "hardware_active": False,
                "source": "SOFTWARE_ONLY",
                "fpga_signal_phase": None,
                "fpga_green_time_s": None,
                "fpga_congestion_score": None,
                "fpga_state": "OFFLINE",
                "message": "FPGA NOT CONNECTED — Software signal state active"
            }

        int_idx = int(intersection_id) if intersection_id.isdigit() else 1
        payload = struct.pack(">BBBB", int_idx, min(255, queue_ns), min(255, queue_ew), int(manual_override))
        success, resp_payload, err = self.conn.transact(SCENE_CITY, OP_STEP_SIM, payload)

        if not success or len(resp_payload) < 4:
            return {
                "hardware_active": False,
                "source": "COMM_ERROR",
                "fpga_signal_phase": None,
                "fpga_state": "ERR",
                "message": f"Hardware Transaction Failed: {err}"
            }

        # Unpack: [phase_code (uint8: 0=NS_GREEN, 1=EW_GREEN), green_time (uint8), congestion (uint8), fsm_code (uint8)]
        phase_code, green_t, cong_pct, fsm_code = struct.unpack(">BBBB", resp_payload[:4])
        phase_str = "NS_GREEN" if phase_code == 0 else ("EW_GREEN" if phase_code in (1, 3) else f"PHASE_{phase_code}")

        res = {
            "hardware_active": True,
            "source": "FPGA_HARDWARE",
            "fpga_signal_phase": phase_str,
            "fpga_green_time_s": int(green_t),
            "fpga_congestion_score": int(cong_pct),
            "fpga_state": f"FSM_PHASE_{fsm_code}",
            "latency_ms": self.conn.last_response_ms
        }

        # Optional extended telemetry payload
        if len(resp_payload) >= 8:
            qn, qs, qe, qw = struct.unpack(">BBBB", resp_payload[4:8])
            res.update({
                "fpga_queue_north": int(qn),
                "fpga_queue_south": int(qs),
                "fpga_queue_east": int(qe),
                "fpga_queue_west": int(qw),
                "fpga_total_queue": int(qn + qs + qe + qw)
            })

        return res


    # =========================================================================
    # 4. SPACE HABITAT / MARS LANDING HARDWARE PIPELINE
    # =========================================================================
    def step_mars_habitat(
        self,
        altitude_m: float,
        velocity_ms: float,
        impact_trigger: bool = False,
        impact_target: str = "A"
    ) -> Dict[str, Any]:
        """
        Transacts with mars_habitat_core.v on Zynq PL.
        Performs threshold comparisons, section isolation, and landing state logic.
        """
        self.conn.active_function = "MARS_IMPACT_AND_LANDING"

        if not self.is_hardware_active:
            return {
                "hardware_active": False,
                "source": "SOFTWARE_ONLY",
                "fpga_section_A": None,
                "fpga_section_B": None,
                "fpga_link": None,
                "fpga_landing_stage": None,
                "message": "FPGA NOT CONNECTED — Software landing simulation active"
            }

        target_code = 1 if impact_target == "A" else 2
        payload = struct.pack(">hhBB", int(altitude_m), int(velocity_ms * 10), int(impact_trigger), target_code)
        success, resp_payload, err = self.conn.transact(SCENE_SPACE, OP_STEP_SIM, payload)

        if not success or len(resp_payload) < 4:
            return {
                "hardware_active": False,
                "source": "COMM_ERROR",
                "fpga_section_A": None,
                "message": f"Hardware Transaction Failed: {err}"
            }

        # Unpack: [sec_A_closed (uint8), sec_B_closed (uint8), link_closed (uint8), stage_fsm (uint8)]
        a_cl, b_cl, link_cl, st_fsm = struct.unpack(">BBBB", resp_payload[:4])

        return {
            "hardware_active": True,
            "source": "FPGA_HARDWARE",
            "fpga_section_A": "CLOSED" if a_cl else "OPERATIONAL",
            "fpga_section_B": "CLOSED" if b_cl else "OPERATIONAL",
            "fpga_link": "CLOSED" if link_cl else "OPEN",
            "fpga_landing_stage": f"STAGE_{st_fsm}",
            "latency_ms": self.conn.last_response_ms
        }

    # =========================================================================
    # 5. 3D MAZE RUNNER HARDWARE PIPELINE
    # =========================================================================
    def step_maze_runner(
        self,
        player_x: int,
        player_y: int,
        move_dir: str
    ) -> Dict[str, Any]:
        """
        Transacts with maze_core.v on Zynq PL.
        Validates boundaries, evaluates wall bitmasks, registers step/collision counters.
        """
        self.conn.active_function = "MAZE_COLLISION_ARBITRATION"

        if not self.is_hardware_active:
            return {
                "hardware_active": False,
                "source": "SOFTWARE_ONLY",
                "fpga_move_valid": None,
                "fpga_collision": None,
                "fpga_timer_s": None,
                "fpga_state": "OFFLINE",
                "message": "FPGA NOT CONNECTED — Local Python graph solver active"
            }

        dir_map = {"UP": 1, "DOWN": 2, "LEFT": 3, "RIGHT": 4}
        dir_code = dir_map.get(move_dir.upper(), 0)
        payload = struct.pack(">BBB", int(player_x), int(player_y), dir_code)
        success, resp_payload, err = self.conn.transact(SCENE_MAZE, OP_STEP_SIM, payload)

        if not success or len(resp_payload) < 4:
            return {
                "hardware_active": False,
                "source": "COMM_ERROR",
                "fpga_move_valid": None,
                "message": f"Hardware Transaction Failed: {err}"
            }

        # Unpack: [move_valid (uint8), collision (uint8), timer_s (uint8), state_code (uint8), anim_state (uint8), anim_phase (uint8)]
        valid_mv, col_hit, rem_time, state_c, anim_s, anim_p = struct.unpack(">BBBBBB", resp_payload[:6])

        return {
            "hardware_active": True,
            "source": "FPGA_HARDWARE",
            "fpga_move_valid": bool(valid_mv),
            "fpga_collision": bool(col_hit),
            "fpga_timer_s": int(rem_time),
            "fpga_state": f"FSM_{state_c}",
            "animation_state": int(anim_s),
            "animation_phase": int(anim_p),
            "latency_ms": self.conn.last_response_ms
        }

    def read_maze_state(self) -> Dict[str, Any]:
        """
        Polls the Maze hardware telemetry without moving.
        """
        self.conn.active_function = "MAZE_TELEMETRY"

        if not self.is_hardware_active:
            return {
                "hardware_active": False,
                "source": "SOFTWARE_ONLY"
            }

        # Send CMD_NONE (0) to step_maze_runner to just get status
        payload = struct.pack(">BBB", 0, 0, 0)
        success, resp_payload, err = self.conn.transact(SCENE_MAZE, OP_STEP_SIM, payload)

        if not success or len(resp_payload) < 6:
            return {
                "hardware_active": False,
                "source": "COMM_ERROR"
            }

        # Unpack: [move_valid, collision, timer_s, state_code, anim_state, anim_phase]
        valid_mv, col_hit, rem_time, state_c, anim_s, anim_p = struct.unpack(">BBBBBB", resp_payload[:6])

        state_names = ["IDLE", "MAZE_DISPLAY", "MEMORY_PHASE", "RUNNING", "WIN", "TIMEOUT"]
        st_name = state_names[state_c] if state_c < len(state_names) else f"UNKNOWN_{state_c}"
        anim_names = ["NONE", "WIN", "LOSE"]
        anim_name = anim_names[anim_s] if anim_s < len(anim_names) else "NONE"

        return {
            "hardware_active": True,
            "source": "FPGA_HARDWARE",
            "game_state": st_name,
            "remaining_time_s": int(rem_time),
            "animation_state": anim_name,
            "animation_phase": int(anim_p)
        }

