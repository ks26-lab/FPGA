"""
python.scenes.mars_habitat.telemetry
====================================
Telemetry decoding for Mars Space Habitat & Landing Accelerator FPGA core.
Decodes authoritative 32-register telemetry directly from FPGA AXI registers.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from python.protocol.encoding import fixed16_to_float
from python.scenes.mars_habitat.register_map import (
    STATE_NAMES,
    LANDING_FSM_NAMES,
    LANDING_STATUS_NAMES,
    RECOVERY_ACTION_NAMES,
    LIFE_SUPPORT_STATUS_NAMES,
    HAZARD_STATUS_NAMES,
    FAULT_FLAG_BITS
)


def _to_signed_16(val: int) -> int:
    """Converts 16-bit unsigned integer to signed integer."""
    u16 = val & 0xFFFF
    return u16 - 0x10000 if u16 >= 0x8000 else u16


def decode_mars_telemetry(
    status_reg: int,
    impact_reg: int,
    counters_reg: int,
    total_reg: int,
    thresh_reg: int,
    attack_reg: int,
    is_hardware: bool,
    extended_regs: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Decodes raw 32-bit registers into standard Mars telemetry envelope.
    Maintains 100% backward compatibility with legacy fields while adding
    authoritative FPGA landing, 8-channel meteorite, damage, atmospheric,
    and life-support metrics.
    """
    ext = extended_regs or {}

    # Legacy status register
    state_code = status_reg & 0x0F
    sec_a_closed = bool((status_reg >> 4) & 1)
    sec_b_closed = bool((status_reg >> 5) & 1)
    link_closed = bool((status_reg >> 6) & 1)
    threshold_crossed = bool((status_reg >> 7) & 1)
    active_target_code = (status_reg >> 8) & 0x03

    target_map = {0: "ALL", 1: "A", 2: "B"}
    active_target_str = target_map.get(active_target_code, "UNKNOWN")

    raw_impact = impact_reg & 0xFFFF
    processed_count = (impact_reg >> 16) & 0xFF
    total_requested = (impact_reg >> 24) & 0xFF
    last_impact = fixed16_to_float(raw_impact, scale=10.0)

    impacts_a = counters_reg & 0xFFFF
    impacts_b = (counters_reg >> 16) & 0xFFFF
    total_impacts = total_reg & 0xFFFF
    critical_impacts = (total_reg >> 16) & 0xFFFF

    raw_thresh_a = thresh_reg & 0xFFFF
    raw_thresh_b = (thresh_reg >> 16) & 0xFFFF
    thresh_a = fixed16_to_float(raw_thresh_a, scale=10.0)
    thresh_b = fixed16_to_float(raw_thresh_b, scale=10.0)

    attack_type_code = attack_reg & 1
    attack_type_str = "BIG" if attack_type_code == 1 else "NORMAL"
    state_str = STATE_NAMES.get(state_code, f"STATE_{state_code}")

    # Upgraded Landing Telemetry (from ext or defaults)
    landing_alt_raw = ext.get("landing_altitude", 0)
    landing_alt = round(landing_alt_raw / 10.0, 1)

    vel_accel_raw = ext.get("landing_velocity", 0)
    landing_vel = round(_to_signed_16(vel_accel_raw & 0xFFFF) / 10.0, 1)
    landing_accel = round(_to_signed_16((vel_accel_raw >> 16) & 0xFFFF) / 10.0, 1)

    thrust_raw = ext.get("thrust_command", 0) & 0xFFFF
    thrust_pct = round(thrust_raw / 10.0, 1)

    pred_alt_raw = ext.get("predicted_altitude", 0)
    pred_alt = round(pred_alt_raw / 10.0, 1)

    pred_touch_raw = ext.get("predicted_touchdown_vel", 0)
    pred_touch_vel = round(_to_signed_16(pred_touch_raw & 0xFFFF) / 10.0, 1)

    landing_stat_raw = ext.get("landing_status", 0)
    landing_stat_code = landing_stat_raw & 0x03
    landing_fsm_code = (landing_stat_raw >> 2) & 0x03
    landing_status_str = LANDING_STATUS_NAMES.get(landing_stat_code, "SAFE")
    landing_fsm_str = LANDING_FSM_NAMES.get(landing_fsm_code, "PREP")

    # Upgraded Meteorite Telemetry
    meteor_active_mask = ext.get("meteorite_active", 0) & 0xFF
    meteor_active_count = bin(meteor_active_mask).count('1')
    meteor_impact_vec = ext.get("meteorite_impact_vector", 0) & 0xFF
    crit_impact_cnt = ext.get("critical_impact_count", critical_impacts)
    total_impact_energy = ext.get("total_impact_energy", 0)

    # Damage & Recovery Telemetry
    damage_reg = ext.get("section_damage", 0)
    damage_A = round((damage_reg & 0xFFFF) / 10.0, 1)
    damage_B = round(((damage_reg >> 16) & 0xFFFF) / 10.0, 1)

    recovery_raw = ext.get("recovery_action", 0) & 0x0F
    recovery_str = RECOVERY_ACTION_NAMES.get(recovery_raw, "NO_ACTION")

    # Atmospheric & Thermal Telemetry
    o2_raw = ext.get("o2_percent", 209) & 0xFFFF
    o2_pct = round(o2_raw / 10.0, 1)

    co2_raw = ext.get("co2_percent", 4) & 0xFFFF
    co2_pct = round(co2_raw / 100.0, 2)

    pres_raw = ext.get("pressure_kpa", 1013) & 0xFFFF
    pressure_kpa = round(pres_raw / 10.0, 1)

    temp_raw = ext.get("temperature_c", 210) & 0xFFFF
    temp_c = round(_to_signed_16(temp_raw) / 10.0, 1)

    # Life Support & Health Telemetry
    ls_stat_raw = ext.get("life_support_status", 0) & 0x03
    ls_status_str = LIFE_SUPPORT_STATUS_NAMES.get(ls_stat_raw, "STABLE")

    health_score = ext.get("habitat_health", 100) & 0xFF

    hazard_reg = ext.get("hazard_score", 0)
    hazard_score = hazard_reg & 0xFF
    hazard_status_code = (hazard_reg >> 8) & 0x03
    hazard_status_str = HAZARD_STATUS_NAMES.get(hazard_status_code, "NORMAL")

    fault_flags = ext.get("fault_flags", 0) & 0xFFFF
    active_faults = [
        name for bit, name in FAULT_FLAG_BITS.items()
        if (fault_flags & (1 << bit)) != 0
    ]

    sim_cycles = ext.get("simulation_cycles", 0)
    meteorites_processed_total = ext.get("meteorites_processed", processed_count)

    return {
        "scene": "mars_habitat",
        "timestamp": time.time(),
        "hardware": is_hardware,
        "state": state_str,
        "data": {
            # Legacy Fields Preserved
            "section_A": "CLOSED" if sec_a_closed else "OPERATIONAL",
            "section_B": "CLOSED" if sec_b_closed else "OPERATIONAL",
            "link_status": "CLOSED" if link_closed else "OPEN",
            "section_A_closed": sec_a_closed,
            "section_B_closed": sec_b_closed,
            "link_closed": link_closed,
            "threshold_crossed": threshold_crossed,
            "active_target": active_target_str,
            "last_impact": last_impact,
            "threshold_A": thresh_a,
            "threshold_B": thresh_b,
            "processed_count": processed_count,
            "total_requested": total_requested,
            "impacts_A": impacts_a,
            "impacts_B": impacts_b,
            "total_impacts": total_impacts,
            "last_attack_type": attack_type_str,

            # Upgraded Landing Physics
            "landing_altitude": landing_alt,
            "landing_velocity": landing_vel,
            "landing_acceleration": landing_accel,
            "thrust_command": thrust_pct,
            "predicted_altitude": pred_alt,
            "predicted_touchdown_velocity": pred_touch_vel,
            "landing_status": landing_status_str,
            "landing_fsm": landing_fsm_str,

            # Upgraded Parallel Meteorite Engine
            "meteorite_active_mask": meteor_active_mask,
            "meteorite_active_count": meteor_active_count,
            "meteorite_impact_vector": meteor_impact_vec,
            "critical_impact_count": crit_impact_cnt,
            "total_impact_energy": total_impact_energy,

            # Habitat Damage & Recovery
            "damage_A": damage_A,
            "damage_B": damage_B,
            "recovery_action": recovery_str,

            # Atmospheric & Thermal Status
            "o2_percent": o2_pct,
            "co2_percent": co2_pct,
            "pressure_kpa": pressure_kpa,
            "temperature_c": temp_c,

            # Life Support & Safety Supervision
            "life_support_status": ls_status_str,
            "habitat_health": health_score,
            "hazard_score": hazard_score,
            "hazard_status": hazard_status_str,
            "fault_flags": fault_flags,
            "faults": active_faults,

            # FPGA Performance Counters
            "touchdown": landing_alt <= 0.1 or landing_fsm_str == "TOUCHDOWN",
            "latency_cycles": ext.get("latency_cycles", 18),
            "update_counter": ext.get("update_counter", sim_cycles),
            "core_version": f"0x{ext.get('hardware_version', 0x4D415253):08X}",
            "simulation_cycles": sim_cycles,
            "meteorites_processed": meteorites_processed_total
        }
    }
