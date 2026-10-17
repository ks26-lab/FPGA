"""
python.scenes.underwater.telemetry
==================================
Telemetry decoding and data structures for Underwater Dynamic Probe.
Strictly decodes FPGA hardware register values; does not perform simulation in Python.
"""

import time
from typing import Dict, Any, List

from python.protocol.encoding import fixed16_to_float, unpack_i8
from python.scenes.underwater.register_map import (
    STATE_NAMES,
    DISTURBANCE_NAMES,
    SEVERITY_NAMES,
    ACTION_NAMES,
    FAULT_BITS,
)


def decode_i16(raw: int) -> int:
    val = raw & 0xFFFF
    return val if val < 0x8000 else val - 0x10000


def decode_i8(raw: int) -> int:
    val = raw & 0xFF
    return val if val < 0x80 else val - 0x100


def decode_underwater_telemetry(
    status_reg: int,
    depth_cfg_reg: int,
    current_reg: int,
    current_depth_reg: int,
    target_depth_reg: int,
    velocity_reg: int,
    depth_error_reg: int,
    filtered_depth_reg: int,
    filtered_velocity_reg: int,
    drag_force_reg: int,
    relative_velocity_reg: int,
    p_term_reg: int,
    i_term_reg: int,
    d_term_reg: int,
    control_output_reg: int,
    thrust_command_reg: int,
    thrust_delta_reg: int,
    impact_energy_reg: int,
    impact_severity_reg: int,
    recovery_thrust_reg: int,
    post_col_velocity_reg: int,
    predicted_depth_1_reg: int,
    predicted_depth_3_reg: int,
    predicted_depth_5_reg: int,
    control_cost_reg: int,
    optimization_act_reg: int,
    fault_flags_reg: int,
    sim_cycles_reg: int,
    physics_updates_reg: int,
    collision_count_reg: int,
    recovery_count_reg: int,
    is_hardware: bool
) -> Dict[str, Any]:
    """Decodes all 32 FPGA registers into strongly-typed telemetry dictionary."""
    state_code = status_reg & 0x0F
    collision = bool((status_reg >> 4) & 1)
    recovery = bool((status_reg >> 5) & 1)
    target_reached = bool((status_reg >> 6) & 1)
    obj_code = (status_reg >> 7) & 0x03

    # Primary physics
    depth_m = decode_i16(current_depth_reg) / 10.0
    target_depth_m = decode_i16(target_depth_reg) / 10.0
    depth_error_m = decode_i16(depth_error_reg) / 10.0
    vel_ms = decode_i8(velocity_reg) / 10.0
    flt_depth_m = decode_i16(filtered_depth_reg) / 10.0
    flt_vel_ms = decode_i8(filtered_velocity_reg) / 10.0
    current_pct = decode_i8(current_reg)

    # Forces & PID
    drag_n = decode_i16(drag_force_reg) / 10.0
    rel_vel_ms = decode_i16(relative_velocity_reg) / 10.0
    p_term = decode_i16(p_term_reg) / 10.0
    i_term = decode_i16(i_term_reg) / 10.0
    d_term = decode_i16(d_term_reg) / 10.0
    ctrl_out = decode_i16(control_output_reg) / 10.0
    thrust_n = decode_i16(thrust_command_reg) / 10.0
    thrust_delta_n = decode_i16(thrust_delta_reg) / 10.0

    # Collision & Recovery
    impact_energy_j = impact_energy_reg & 0xFFFF
    severity_code = impact_severity_reg & 0x07
    rec_thrust_n = decode_i16(recovery_thrust_reg) / 10.0
    post_col_vel_ms = decode_i8(post_col_velocity_reg) / 10.0

    # Predictions
    pred_1_m = decode_i16(predicted_depth_1_reg) / 10.0
    pred_3_m = decode_i16(predicted_depth_3_reg) / 10.0
    pred_5_m = decode_i16(predicted_depth_5_reg) / 10.0

    # Optimization & Faults
    cost = control_cost_reg & 0xFFFF
    action_code = optimization_act_reg & 0x03
    fault_flags = fault_flags_reg & 0xFF

    active_faults: List[str] = []
    for bit, name in FAULT_BITS.items():
        if (fault_flags >> bit) & 1:
            active_faults.append(name)

    state_str = STATE_NAMES.get(state_code, f"STATE_{state_code}")
    obj_str = DISTURBANCE_NAMES.get(obj_code, "NONE")
    sev_str = SEVERITY_NAMES.get(severity_code, "NONE")
    act_str = ACTION_NAMES.get(action_code, "HOLD_THRUST")

    return {
        "scene": "underwater",
        "timestamp": time.time(),
        "hardware": is_hardware,
        "state": state_str,
        "data": {
            "depth": depth_m,
            "target_depth": target_depth_m,
            "depth_error": depth_error_m,
            "velocity": vel_ms,
            "filtered_depth": flt_depth_m,
            "filtered_velocity": flt_vel_ms,
            "current_strength": current_pct,
            "relative_velocity": rel_vel_ms,
            "drag_force": drag_n,
            "p_term": p_term,
            "i_term": i_term,
            "d_term": d_term,
            "control_output": ctrl_out,
            "thrust": thrust_n,
            "thrust_delta": thrust_delta_n,
            "collision": collision,
            "recovery": recovery,
            "target_reached": target_reached,
            "active_object": obj_str,
            "impact_energy": impact_energy_j,
            "impact_severity": sev_str,
            "recovery_thrust": rec_thrust_n,
            "post_collision_velocity": post_col_vel_ms,
            "predicted_depth_1": pred_1_m,
            "predicted_depth_3": pred_3_m,
            "predicted_depth_5": pred_5_m,
            "control_cost": cost,
            "optimization_action": act_str,
            "fault_flags": fault_flags,
            "active_faults": active_faults,
            "simulation_cycles": sim_cycles_reg,
            "physics_update_count": physics_updates_reg,
            "collision_count": collision_count_reg & 0xFFFF,
            "recovery_count": recovery_count_reg & 0xFFFF,
            "displacement_x": 0 # Maintained for legacy compatibility
        }
    }
