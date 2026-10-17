"""
python.scenes.traffic.register_map
==================================
AXI register definitions for Smart City Traffic Management peripheral.
Base Address: 0x43C40000 (M_AXI_GP0)
Aperture: 256 bytes (0x00 - 0x7C)
"""

BASE_ADDRESS = 0x43C40000

# ==============================================================================
# Legacy Registers (0x00 - 0x14) - Fully Preserved
# ==============================================================================
REG_CONTROL           = 0x00  # [W]   Bit 0: step, Bit 1: reset, Bit 2: override_en, Bit 3: override_phase, Bit 4: auto, Bit 5: emg, Bit 8: ped, Bit 9: stress
REG_CONFIG            = 0x04  # [R/W] [7:0]: intersection_id, [15:8]: queue_ns, [23:16]: queue_ew, [31:24]: priority
REG_TIMING_CFG        = 0x08  # [R/W] [15:0]: min_green_s, [31:16]: max_green_s
REG_STATUS            = 0x0C  # [R]   [3:0]: phase, Bit 4: alert, Bit 5: override, [15:8]: fsm_code
REG_TELEMETRY         = 0x10  # [R]   [7:0]: green_rem_s, [15:8]: cong_score, [23:16]: clr_ns, [31:24]: clr_ew
REG_CYCLES            = 0x14  # [R]   [31:0]: simulation_ticks

# ==============================================================================
# Upgraded Computational Engine & 16-Vehicle Registers (0x18 - 0x78)
# ==============================================================================
REG_APPROACH_QUEUES_NS= 0x18  # [R]   [7:0]: queue_n, [23:16]: queue_s
REG_APPROACH_QUEUES_EW= 0x1C  # [R]   [7:0]: queue_e, [23:16]: queue_w
REG_TOTAL_QUEUES      = 0x20  # [R]   [9:0]: queue_total, [23:16]: queue_ns_sum, [31:24]: queue_ew_sum
REG_DYNAMIC_SPLITS    = 0x24  # [R]   [7:0]: calc_green_ns_s, [23:16]: calc_green_ew_s
REG_WAIT_TIMES        = 0x28  # [R]   [15:0]: ns_wait_time_s, [31:16]: ew_wait_time_s
REG_PREDICTED_QUEUES  = 0x2C  # [R]   [8:0]: pred_queue_ns, [24:16]: pred_queue_ew
REG_CONGESTION_LEVELS = 0x30  # [R]   [2:0]: n_cong, [6:4]: s_cong, [10:8]: e_cong, [14:12]: w_cong, [23:16]: score, [31:24]: global
REG_EMERGENCY_STATUS  = 0x34  # [R]   [0]: emg_req, [2:1]: emg_dir, [4]: corridor_active, [7:5]: curr_node, [10:8]: next_node, [15:11]: events
REG_PEDESTRIAN_STATUS = 0x38  # [R]   [0]: ped_walk_active, [7:1]: ped_time_rem, [15:8]: ped_serviced_count
REG_FAULT_FLAGS       = 0x3C  # [R]   16-bit hardware safety supervisor fault flags bitmask
REG_FAULT_COUNT       = 0x40  # [R]   [15:0]: fault_count, [31:16]: collision_events
REG_VEHICLE_OCCUPANCY = 0x44  # [R]   [15:0]: vehicle_active_mask, [31:16]: brake_required_mask
REG_VEH_POS_NORTH     = 0x48  # [R]   [7:0]=V0, [15:8]=V1, [23:16]=V2, [31:24]=V3
REG_VEH_POS_SOUTH     = 0x4C  # [R]   [7:0]=V4, [15:8]=V5, [23:16]=V6, [31:24]=V7
REG_VEH_POS_EAST      = 0x50  # [R]   [7:0]=V8, [15:8]=V9, [23:16]=V10,[31:24]=V11
REG_VEH_POS_WEST      = 0x54  # [R]   [7:0]=V12,[15:8]=V13,[23:16]=V14,[31:24]=V15
REG_VEH_SPEEDS        = 0x58  # [R]   [7:0]: avg_v_n, [15:8]: avg_v_s, [23:16]: avg_v_e, [31:24]: avg_v_w
REG_STARVATION_FLAGS  = 0x5C  # [R/W] [0]: ns_starving, [1]: ew_starving, [31:16]: starvation_limit_s
REG_FSM_CYCLES        = 0x60  # [R]   32-bit FSM execution cycles
REG_QUEUE_CYCLES      = 0x64  # [R]   32-bit queue update cycles
REG_VEHICLE_CYCLES    = 0x68  # [R]   32-bit parallel vehicle engine cycles
REG_OPTIMIZER_CYCLES  = 0x6C  # [R]   32-bit optimization cycles
REG_UPDATE_COUNTER    = 0x70  # [R]   32-bit cumulative updates
REG_THROUGHPUT        = 0x74  # [R]   32-bit throughput metric
REG_ADAPTIVE_WEIGHTS  = 0x78  # [R/W] [7:0]: w_queue, [15:8]: w_wait, [23:16]: w_pred, [31:24]: w_emg

# ==============================================================================
# FSM State & Classification Maps
# ==============================================================================
SIGNAL_PHASES = {
    0: "NS_GREEN",
    1: "NS_YELLOW",
    2: "ALL_RED",
    3: "EW_GREEN",
    4: "EW_YELLOW",
    5: "PEDESTRIAN",
    6: "EMERGENCY"
}

CONGESTION_LEVEL_NAMES = {
    0: "LOW",
    1: "NORMAL",
    2: "HIGH",
    3: "HEAVY",
    4: "GRIDLOCK"
}

# Project Traffic Density Thresholds
DENSITY_THRESHOLDS = {
    "LOW": 10,
    "NORMAL": 22,
    "HIGH": 42,
    "HEAVY": 65,
    "GRIDLOCK": 85
}

FAULT_BITS = {
    0: "CONFLICTING_GREEN",
    1: "PEDESTRIAN_CONFLICT",
    2: "QUEUE_OVERFLOW",
    3: "TIMER_OVERFLOW",
    4: "INVALID_FSM_STATE",
    5: "COLLISION_RISK_DETECTED",
    6: "EMERGENCY_DISAGREEMENT"
}
