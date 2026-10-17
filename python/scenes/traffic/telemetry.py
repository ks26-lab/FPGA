"""
python.scenes.traffic.telemetry
===============================
Telemetry decoding for Traffic Management FPGA core.
Decodes 4-way intersection FSM state, approach queue depths (N, S, E, W),
dynamic green splits, waiting times, prediction, 16 parallel vehicles,
emergency preemption corridor, and safety faults calculated in FPGA PL.
"""

import time
from typing import Dict, Any, List

from python.scenes.traffic.register_map import (
    SIGNAL_PHASES,
    CONGESTION_LEVEL_NAMES,
    FAULT_BITS
)


def decode_traffic_telemetry(
    status_reg: int,
    telemetry_reg: int,
    config_reg: int,
    timing_reg: int,
    cycles_reg: int,
    is_hardware: bool,
    # Extended registers (defaults maintain 100% backward compatibility)
    queues_ns_reg: int = 0,
    queues_ew_reg: int = 0,
    total_queues_reg: int = 0,
    dynamic_splits_reg: int = 0,
    wait_times_reg: int = 0,
    pred_queues_reg: int = 0,
    cong_levels_reg: int = 0,
    emergency_reg: int = 0,
    pedestrian_reg: int = 0,
    fault_flags_reg: int = 0,
    fault_count_reg: int = 0,
    vehicle_occ_reg: int = 0,
    veh_pos_n_reg: int = 0,
    veh_pos_s_reg: int = 0,
    veh_pos_e_reg: int = 0,
    veh_pos_w_reg: int = 0,
    veh_speeds_reg: int = 0,
    starvation_reg: int = 0,
    fsm_cycles_reg: int = 0,
    queue_cycles_reg: int = 0,
    vehicle_cycles_reg: int = 0,
    optimizer_cycles_reg: int = 0,
    update_counter_reg: int = 0
) -> Dict[str, Any]:
    """Decodes raw 32-bit registers into Traffic telemetry envelope."""
    phase_code = status_reg & 0x0F
    congestion_alert = bool((status_reg >> 4) & 1)
    override_active = bool((status_reg >> 5) & 1)
    fsm_code = (status_reg >> 8) & 0xFF

    phase_str = SIGNAL_PHASES.get(phase_code, f"PHASE_{phase_code}")

    green_rem_s = telemetry_reg & 0xFF
    cong_score = (telemetry_reg >> 8) & 0xFF
    cleared_ns = (telemetry_reg >> 16) & 0xFF
    cleared_ew = (telemetry_reg >> 24) & 0xFF

    intersection_id = config_reg & 0xFF
    queue_ns = (config_reg >> 8) & 0xFF
    queue_ew = (config_reg >> 16) & 0xFF
    priority = (config_reg >> 24) & 0xFF

    min_green_s = timing_reg & 0xFFFF
    max_green_s = (timing_reg >> 16) & 0xFFFF

    # Physical light indicators
    if phase_code == 0:
        ns_light = "GREEN"
        ew_light = "RED"
    elif phase_code == 1:
        ns_light = "YELLOW"
        ew_light = "RED"
    elif phase_code == 3:
        ns_light = "RED"
        ew_light = "GREEN"
    elif phase_code == 4:
        ns_light = "RED"
        ew_light = "YELLOW"
    elif phase_code == 5:
        ns_light = "RED (PED WALK)"
        ew_light = "RED (PED WALK)"
    elif phase_code == 6:
        ns_light = "EMERGENCY GREEN" if (emergency_reg & 0x06) <= 2 else "RED"
        ew_light = "EMERGENCY GREEN" if (emergency_reg & 0x06) > 2 else "RED"
    else:
        ns_light = "RED"
        ew_light = "RED"

    # Decode Approach Queues
    q_n = queues_ns_reg & 0xFF if queues_ns_reg > 0 else (queue_ns >> 1)
    q_s = (queues_ns_reg >> 16) & 0xFF if queues_ns_reg > 0 else (queue_ns >> 1)
    q_e = queues_ew_reg & 0xFF if queues_ew_reg > 0 else (queue_ew >> 1)
    q_w = (queues_ew_reg >> 16) & 0xFF if queues_ew_reg > 0 else (queue_ew >> 1)
    q_total = total_queues_reg & 0xFFFF if total_queues_reg > 0 else (queue_ns + queue_ew)

    # Dynamic splits & wait times
    g_split_ns = dynamic_splits_reg & 0xFF if dynamic_splits_reg > 0 else 30
    g_split_ew = (dynamic_splits_reg >> 16) & 0xFF if dynamic_splits_reg > 0 else 20
    ns_wait_s = wait_times_reg & 0xFFFF
    ew_wait_s = (wait_times_reg >> 16) & 0xFFFF
    ns_starving = bool(starvation_reg & 1)
    ew_starving = bool((starvation_reg >> 1) & 1)

    # Prediction
    pred_ns = pred_queues_reg & 0xFFFF
    pred_ew = (pred_queues_reg >> 16) & 0xFFFF

    # Congestion Levels
    n_lvl = CONGESTION_LEVEL_NAMES.get(cong_levels_reg & 0x07, "LOW")
    s_lvl = CONGESTION_LEVEL_NAMES.get((cong_levels_reg >> 4) & 0x07, "LOW")
    e_lvl = CONGESTION_LEVEL_NAMES.get((cong_levels_reg >> 8) & 0x07, "LOW")
    w_lvl = CONGESTION_LEVEL_NAMES.get((cong_levels_reg >> 12) & 0x07, "LOW")
    glob_lvl = CONGESTION_LEVEL_NAMES.get((cong_levels_reg >> 24) & 0x07, "NORMAL")

    # Emergency Corridor
    emg_active = bool(emergency_reg & 1)
    emg_dir_code = (emergency_reg >> 1) & 0x03
    emg_dir_str = ["NORTH", "SOUTH", "EAST", "WEST"][emg_dir_code]
    corridor_active = bool((emergency_reg >> 4) & 1)
    curr_node = (emergency_reg >> 5) & 0x07
    next_node = (emergency_reg >> 8) & 0x07
    emg_events = (emergency_reg >> 11) & 0x1F

    # Pedestrian
    ped_walk = bool(pedestrian_reg & 1)
    ped_time = (pedestrian_reg >> 1) & 0x7F
    ped_serviced = (pedestrian_reg >> 8) & 0xFF

    # Safety Faults
    raw_faults = fault_flags_reg & 0xFFFF
    active_faults: List[str] = []
    for bit_idx, name in FAULT_BITS.items():
        if (raw_faults >> bit_idx) & 1:
            active_faults.append(name)
    fault_count = fault_count_reg & 0xFFFF
    collision_events = (fault_count_reg >> 16) & 0xFFFF

    # 16 Parallel Vehicles
    veh_active = vehicle_occ_reg & 0xFFFF
    veh_brakes = (vehicle_occ_reg >> 16) & 0xFFFF
    v_pos_n = [veh_pos_n_reg & 0xFF, (veh_pos_n_reg >> 8) & 0xFF, (veh_pos_n_reg >> 16) & 0xFF, (veh_pos_n_reg >> 24) & 0xFF]
    v_pos_s = [veh_pos_s_reg & 0xFF, (veh_pos_s_reg >> 8) & 0xFF, (veh_pos_s_reg >> 16) & 0xFF, (veh_pos_s_reg >> 24) & 0xFF]
    v_pos_e = [veh_pos_e_reg & 0xFF, (veh_pos_e_reg >> 8) & 0xFF, (veh_pos_e_reg >> 16) & 0xFF, (veh_pos_e_reg >> 24) & 0xFF]
    v_pos_w = [veh_pos_w_reg & 0xFF, (veh_pos_w_reg >> 8) & 0xFF, (veh_pos_w_reg >> 16) & 0xFF, (veh_pos_w_reg >> 24) & 0xFF]
    avg_v_n = veh_speeds_reg & 0xFF
    avg_v_s = (veh_speeds_reg >> 8) & 0xFF
    avg_v_e = (veh_speeds_reg >> 16) & 0xFF
    avg_v_w = (veh_speeds_reg >> 24) & 0xFF

    auth_str = "FPGA (Hardware Authoritative)" if is_hardware else "FPGA (Laptop Emulated RTL)"

    data_payload = {
        # Legacy fields
        "intersection_id": intersection_id,
        "signal_phase": phase_str,
        "phase_name": phase_str,
        "ns_light": ns_light,
        "ew_light": ew_light,
        "green_time_remaining_s": green_rem_s,
        "congestion_score_pct": cong_score,
        "congestion_alert": congestion_alert,
        "override_active": override_active,
        "queue_ns": queue_ns,
        "queue_ew": queue_ew,
        "cleared_ns_vehicles": cleared_ns,
        "cleared_ew_vehicles": cleared_ew,
        "min_green_s": min_green_s,
        "max_green_s": max_green_s,
        "fsm_state_code": fsm_code,
        "simulation_ticks": cycles_reg,
        # Extended approach queues
        "queue_north": q_n,
        "queue_south": q_s,
        "queue_east": q_e,
        "queue_west": q_w,
        "queue_total": q_total,
        "queue_ns_sum": q_n + q_s,
        "queue_ew_sum": q_e + q_w,
        # Dynamic green splits & waiting times
        "calc_green_ns_s": g_split_ns,
        "calc_green_ew_s": g_split_ew,
        "ns_wait_time_s": ns_wait_s,
        "ew_wait_time_s": ew_wait_s,
        "ns_starving": ns_starving,
        "ew_starving": ew_starving,
        # Predictions & Congestion levels
        "pred_queue_ns": pred_ns,
        "pred_queue_ew": pred_ew,
        "n_congestion_level": n_lvl,
        "s_congestion_level": s_lvl,
        "e_congestion_level": e_lvl,
        "w_congestion_level": w_lvl,
        "global_congestion_level": glob_lvl,
        # Emergency Corridor
        "emergency_active": emg_active,
        "emergency_direction": emg_dir_str,
        "corridor_active": corridor_active,
        "current_emergency_node": curr_node,
        "next_emergency_node": next_node,
        "emergency_events": emg_events,
        # Pedestrian
        "pedestrian_walk_active": ped_walk,
        "pedestrian_time_remaining": ped_time,
        "pedestrian_serviced_count": ped_serviced,
        # Safety Faults
        "fault_flags": raw_faults,
        "fault_list": active_faults,
        "fault_count": fault_count,
        "collision_events": collision_events,
        # 16 Parallel Vehicles
        "vehicle_active_mask": veh_active,
        "brake_required_mask": veh_brakes,
        "positions_north": v_pos_n,
        "positions_south": v_pos_s,
        "positions_east": v_pos_e,
        "positions_west": v_pos_w,
        "speed_north_mps": avg_v_n,
        "speed_south_mps": avg_v_s,
        "speed_east_mps": avg_v_e,
        "speed_west_mps": avg_v_w,
        # Performance Counters
        "fsm_cycles": fsm_cycles_reg,
        "queue_cycles": queue_cycles_reg,
        "vehicle_cycles": vehicle_cycles_reg,
        "optimizer_cycles": optimizer_cycles_reg,
        "total_updates": update_counter_reg,
        "authoritative": auth_str
    }

    envelope = {
        "scene": "traffic",
        "timestamp": time.time(),
        "hardware": is_hardware,
        "state": phase_str,
        "phase_name": phase_str,
        "ns_light": ns_light,
        "ew_light": ew_light,
        "data": data_payload
    }

    # Flatten fields into envelope for direct access (e.g. telem["ns_light"], telem["phase_name"])
    for k, v in data_payload.items():
        if k not in envelope:
            envelope[k] = v

    return envelope
