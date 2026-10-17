"""
python.scenes.solar_gimbal.telemetry
====================================
Telemetry decoding for Solar Tracking Gimbal core.
Extracts 3D Cartesian vectors, dot-product, incident angle, photovoltaic power,
predictive tracking, 4-panel parallel array, and safety faults calculated in FPGA PL.
"""

import time
import math
from typing import Dict, Any, List

from python.protocol.encoding import fixed16_to_float
from python.scenes.solar_gimbal.register_map import (
    STATE_NAMES,
    FAULT_BITS,
    NUMBER_OF_PANELS
)


def _q16_16_to_float(raw: int) -> float:
    """Converts 32-bit two's complement Q16.16 integer to Python float."""
    signed_val = raw if raw < 0x80000000 else raw - 0x100000000
    return round(signed_val / 65536.0, 4)


def _signed16(val: int) -> int:
    """Converts 16-bit unsigned int to signed int."""
    val &= 0xFFFF
    return val if val < 0x8000 else val - 0x10000


def decode_solar_telemetry(
    status_reg: int,
    sun_pos_reg: int,
    panel_pos_reg: int,
    error_reg: int,
    actuator_reg: int,
    cycles_reg: int,
    is_hardware: bool,
    # Extended Mathematical Engine Registers (Defaults maintain 100% backward compatibility)
    sun_vec_x_reg: int = 0,
    sun_vec_y_reg: int = 0,
    sun_vec_z_reg: int = 0,
    panel_norm_x_reg: int = 0,
    panel_norm_y_reg: int = 0,
    panel_norm_z_reg: int = 0,
    dot_product_reg: int = 0,
    incident_angle_reg: int = 0,
    power_reg: int = 0,
    filtered_sun_reg: int = 0,
    predicted_sun_reg: int = 0,
    angular_velocity_reg: int = 0,
    fault_flags_reg: int = 0,
    vector_cycles_reg: int = 0,
    update_counter_reg: int = 0,
    p0_data_reg: int = 0,
    p1_data_reg: int = 0,
    p2_data_reg: int = 0,
    p3_data_reg: int = 0,
    total_power_reg: int = 0,
    active_mask_reg: int = 0x0F,
    tracking_quality_reg: int = 0,
    version_reg: int = 0x501A7010
) -> Dict[str, Any]:
    """Decodes raw 32-bit registers into Solar Gimbal telemetry envelope."""
    state_code = status_reg & 0x0F
    locked = bool((status_reg >> 4) & 1)
    az_dir_code = (status_reg >> 5) & 1
    el_dir_code = (status_reg >> 6) & 1
    az_hold = bool((status_reg >> 7) & 1)
    el_hold = bool((status_reg >> 8) & 1)

    az_dir_str = "HOLD" if az_hold else ("CLOCKWISE" if az_dir_code else "COUNTER_CLOCKWISE")
    el_dir_str = "HOLD" if el_hold else ("UP" if el_dir_code else "DOWN")

    sun_az = fixed16_to_float(sun_pos_reg & 0xFFFF, scale=10.0)
    sun_el = fixed16_to_float((sun_pos_reg >> 16) & 0xFFFF, scale=10.0)

    panel_az = fixed16_to_float(panel_pos_reg & 0xFFFF, scale=10.0)
    panel_el = fixed16_to_float((panel_pos_reg >> 16) & 0xFFFF, scale=10.0)

    az_err = fixed16_to_float(error_reg & 0xFFFF, scale=10.0)
    el_err = fixed16_to_float((error_reg >> 16) & 0xFFFF, scale=10.0)

    act_az = fixed16_to_float(actuator_reg & 0xFFFF, scale=10.0)
    act_el = fixed16_to_float((actuator_reg >> 16) & 0xFFFF, scale=10.0)

    state_str = STATE_NAMES.get(state_code, f"STATE_{state_code}")

    # Decode 3D Vectors (Q16.16)
    sun_vec = {
        "x": _q16_16_to_float(sun_vec_x_reg),
        "y": _q16_16_to_float(sun_vec_y_reg),
        "z": _q16_16_to_float(sun_vec_z_reg),
    }
    panel_norm = {
        "x": _q16_16_to_float(panel_norm_x_reg),
        "y": _q16_16_to_float(panel_norm_y_reg),
        "z": _q16_16_to_float(panel_norm_z_reg),
    }

    # Incident angle & dot product
    cos_theta = _q16_16_to_float(dot_product_reg)
    incident_angle_deg = round((incident_angle_reg & 0xFFFF) / 10.0, 2)
    cos_incidence_ratio = round(((incident_angle_reg >> 16) & 0xFFFF) / 1000.0, 3)

    # Power estimation
    estimated_power_w = float(power_reg & 0xFFFF)
    power_efficiency_pct = round(((power_reg >> 16) & 0xFFFF) / 10.0, 1)

    # Filtered & Predicted Sun Position
    filtered_az = fixed16_to_float(filtered_sun_reg & 0xFFFF, scale=10.0)
    filtered_el = fixed16_to_float((filtered_sun_reg >> 16) & 0xFFFF, scale=10.0)
    pred_az = fixed16_to_float(predicted_sun_reg & 0xFFFF, scale=10.0)
    pred_el = fixed16_to_float((predicted_sun_reg >> 16) & 0xFFFF, scale=10.0)

    omega_az = round(_signed16(angular_velocity_reg & 0xFFFF) / 10.0, 2)
    omega_el = round(_signed16((angular_velocity_reg >> 16) & 0xFFFF) / 10.0, 2)

    # Fault Flags
    fault_flags = fault_flags_reg & 0xFFFF
    active_faults: List[str] = []
    for bit_idx, fault_name in FAULT_BITS.items():
        if (fault_flags >> bit_idx) & 1:
            active_faults.append(fault_name)

    # 4-Panel Parallel Array
    panel_raws = [p0_data_reg, p1_data_reg, p2_data_reg, p3_data_reg]
    panels_data = []
    for idx, raw in enumerate(panel_raws):
        p_pwr = float(raw & 0xFFFF)
        p_inc = round(((raw >> 16) & 0xFFFF) / 10.0, 2)
        p_active = bool((active_mask_reg >> idx) & 1)
        panels_data.append({
            "panel_id": idx,
            "power_w": p_pwr,
            "incident_angle_deg": p_inc,
            "active": p_active
        })

    active_panel_count = bin(active_mask_reg & 0x0F).count("1")
    total_power = float(total_power_reg) if total_power_reg > 0 else (estimated_power_w * active_panel_count)

    authoritative_engine = "FPGA (Hardware Authoritative)" if is_hardware else "FPGA (Laptop Emulated RTL)"

    data_payload = {
        # Legacy fields
        "sun_azimuth": sun_az,
        "sun_elevation": sun_el,
        "panel_azimuth": panel_az,
        "panel_elevation": panel_el,
        "azimuth_error": az_err,
        "elevation_error": el_err,
        "azimuth_direction": az_dir_str,
        "elevation_direction": el_dir_str,
        "actuator_azimuth": act_az,
        "actuator_elevation": act_el,
        "tracking_locked": locked,
        "cycle_counter": cycles_reg,
        # Upgraded Vector Math & Physics fields
        "sun_vector": sun_vec,
        "panel_normal": panel_norm,
        "dot_product": cos_theta,
        "incident_angle": incident_angle_deg,
        "cos_incidence": cos_incidence_ratio,
        "estimated_power": estimated_power_w,
        "power_efficiency": power_efficiency_pct,
        "az_hold": az_hold,
        "el_hold": el_hold,
        # Filtering & Prediction
        "filtered_azimuth": filtered_az,
        "filtered_elevation": filtered_el,
        "predicted_azimuth": pred_az,
        "predicted_elevation": pred_el,
        "angular_velocity_az": omega_az,
        "angular_velocity_el": omega_el,
        # 4-Panel Parallel Array
        "panels": panels_data,
        "panels_active_count": active_panel_count,
        "total_array_power": total_power,
        # Safety & Performance
        "fault_flags": fault_flags,
        "fault_list": active_faults,
        "vector_cycles": vector_cycles_reg,
        "update_counter": update_counter_reg,
        "authoritative": authoritative_engine,
        # Upgraded Optimization & Quality Metrics
        "total_tracking_error_deg": round(math.sqrt(az_err**2 + el_err**2), 2),
        "tracking_error_sq": round(az_err**2 + el_err**2, 2),
        "tracking_quality_pct": (tracking_quality_reg >> 16) & 0xFFFF if tracking_quality_reg > 0 else (100 if locked else max(0, int(100 - (az_err**2 + el_err**2) / 20.25))),
        "power_loss_w": float(tracking_quality_reg & 0xFFFF) if tracking_quality_reg > 0 else max(0.0, 5665.0 - estimated_power_w),
        "hardware_version": f"0x{version_reg:08X}"
    }

    envelope = {
        "scene": "solar_gimbal",
        "timestamp": time.time(),
        "hardware": is_hardware,
        "state": state_str,
        "state_str": state_str,
        "data": data_payload
    }

    # Flatten fields to envelope for direct access (e.g. telem["azimuth_error"])
    for k, v in data_payload.items():
        if k not in envelope:
            envelope[k] = v

    return envelope
