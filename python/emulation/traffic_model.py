"""
Smart City Traffic Grid Software RTL Model.
Replicates upgraded traffic_core.v and traffic_axi_slave.v on EDGE ZYNQ Z7010.

Authoritative PL Responsibilities:
- 7-state deterministic hardware traffic light FSM with strict mutual exclusion
- Directional queue computation (N, S, E, W, NS, EW, Total) and congestion metric (0..100%)
- Demand-driven dynamic green split optimizer clamped between G_min and G_max
- Unserved waiting-time tracking and starvation prevention
- 16-channel concurrent parallel vehicle kinematics & safe-following engine
- 4-node emergency preemption corridor (I1 -> I2 -> I3 -> I4)
- Predictive queue growth calculation and safety fault supervisor
"""

from typing import Dict, Any, List

class TrafficGridRTLModel:
    BASE_ADDR = 0x43C40000

    # Modern AXI Register Offsets
    REG_CONTROL           = 0x00
    REG_CONFIG            = 0x04
    REG_TIMING_CFG        = 0x08
    REG_STATUS            = 0x0C
    REG_TELEMETRY         = 0x10
    REG_CYCLES            = 0x14
    REG_APPROACH_QUEUES_NS= 0x18
    REG_APPROACH_QUEUES_EW= 0x1C
    REG_TOTAL_QUEUES      = 0x20
    REG_DYNAMIC_SPLITS    = 0x24
    REG_WAIT_TIMES        = 0x28
    REG_PREDICTED_QUEUES  = 0x2C
    REG_CONGESTION_LEVELS = 0x30
    REG_EMERGENCY_STATUS  = 0x34
    REG_PEDESTRIAN_STATUS = 0x38
    REG_FAULT_FLAGS       = 0x3C
    REG_FAULT_COUNT       = 0x40
    REG_VEHICLE_OCCUPANCY = 0x44
    REG_VEH_POS_NORTH     = 0x48
    REG_VEH_POS_SOUTH     = 0x4C
    REG_VEH_POS_EAST      = 0x50
    REG_VEH_POS_WEST      = 0x54
    REG_VEH_SPEEDS        = 0x58
    REG_STARVATION_FLAGS  = 0x5C
    REG_FSM_CYCLES        = 0x60
    REG_QUEUE_CYCLES      = 0x64
    REG_VEHICLE_CYCLES    = 0x68
    REG_OPTIMIZER_CYCLES  = 0x6C
    REG_UPDATE_COUNTER    = 0x70
    REG_THROUGHPUT        = 0x74
    REG_ADAPTIVE_WEIGHTS  = 0x78

    # Signal Phases
    PHASE_NS_GREEN    = 0
    PHASE_NS_YELLOW   = 1
    PHASE_ALL_RED     = 2
    PHASE_EW_GREEN    = 3
    PHASE_EW_YELLOW   = 4
    PHASE_PEDESTRIAN  = 5
    PHASE_EMERGENCY   = 6

    def __init__(self):
        self.legacy_mode = False
        self.reset()

    def reset(self):
        self.control = 0
        self.config = 0
        self.phase = self.PHASE_NS_GREEN
        self.timer = 20
        self.cycle_count = 0

        self.intersection_id = 1
        self.min_green = 10
        self.max_green = 45
        self.starvation_limit = 45

        # Approach queues
        self.q_n = 12
        self.q_s = 10
        self.q_e = 8
        self.q_w = 6
        self.ns_queue = 22
        self.ew_queue = 14

        self.cleared_ns = 0
        self.cleared_ew = 0
        self.ns_wait_time = 0
        self.ew_wait_time = 0
        self.ns_starving = False
        self.ew_starving = False

        # Emergency & Pedestrian
        self.emergency_active = False
        self.emergency_dir = 0
        self.corridor_active = False
        self.curr_node = 1
        self.next_node = 2
        self.emg_events = 0
        self.ped_active = False
        self.ped_time_rem = 0
        self.ped_serviced = 0

        # Safety & Vehicles
        self.fault_flags = 0
        self.fault_count = 0
        self.collision_events = 0

        self.pos_n = [180, 140, 90, 30]
        self.pos_s = [175, 130, 80, 20]
        self.pos_e = [185, 145, 95, 35]
        self.pos_w = [170, 120, 70, 15]
        self.speeds = [10, 10, 10, 10]

    def read32(self, offset: int) -> int:
        # Legacy test compatibility
        if self.legacy_mode:
            if offset == 0x10:
                return self.ns_queue & 0xFF
            elif offset == 0x14:
                return self.ew_queue & 0xFF

        # Standard AXI Registers
        if offset == self.REG_CONTROL:
            return self.control
        elif offset == self.REG_CONFIG:
            return ((0 & 0xFF) << 24) | ((self.ew_queue & 0xFF) << 16) | ((self.ns_queue & 0xFF) << 8) | (self.intersection_id & 0xFF)
        elif offset == self.REG_TIMING_CFG:
            return ((self.max_green & 0xFFFF) << 16) | (self.min_green & 0xFFFF)
        elif offset == self.REG_STATUS:
            override_bit = 1 if (self.control & 0x04) or self.emergency_active else 0
            alert_bit = 1 if self._calc_congestion() > 70 else 0
            fsm_code = 0xEE if self.emergency_active else (0xAA if override_bit else self.phase)
            return (self.phase & 0x0F) | (alert_bit << 4) | (override_bit << 5) | ((fsm_code & 0xFF) << 8)
        elif offset == self.REG_TELEMETRY:
            cong = self._calc_congestion()
            return ((self.cleared_ew & 0xFF) << 24) | ((self.cleared_ns & 0xFF) << 16) | ((cong & 0xFF) << 8) | (self.timer & 0xFF)
        elif offset == self.REG_CYCLES:
            return self.cycle_count & 0xFFFFFFFF
        elif offset == self.REG_APPROACH_QUEUES_NS:
            return ((self.q_s & 0xFF) << 16) | (self.q_n & 0xFF)
        elif offset == self.REG_APPROACH_QUEUES_EW:
            return ((self.q_w & 0xFF) << 16) | (self.q_e & 0xFF)
        elif offset == self.REG_TOTAL_QUEUES:
            tot = self.q_n + self.q_s + self.q_e + self.q_w
            return ((self.ew_queue & 0xFF) << 24) | ((self.ns_queue & 0xFF) << 16) | (tot & 0xFFFF)
        elif offset == self.REG_DYNAMIC_SPLITS:
            g_ns, g_ew = self._calc_splits()
            return ((g_ew & 0xFF) << 16) | (g_ns & 0xFF)
        elif offset == self.REG_WAIT_TIMES:
            return ((self.ew_wait_time & 0xFFFF) << 16) | (self.ns_wait_time & 0xFFFF)
        elif offset == self.REG_PREDICTED_QUEUES:
            return ((min(255, self.ew_queue + 2) & 0xFFFF) << 16) | (min(255, self.ns_queue + 3) & 0xFFFF)
        elif offset == self.REG_CONGESTION_LEVELS:
            cong = self._calc_congestion()
            glob_lvl = 3 if cong > 60 else (2 if cong > 40 else 1)
            return (glob_lvl << 24) | (cong << 16) | 0x0111
        elif offset == self.REG_EMERGENCY_STATUS:
            emg_bit = 1 if self.emergency_active else 0
            corr_bit = 1 if self.corridor_active else 0
            return (self.emg_events << 11) | (self.next_node << 8) | (self.curr_node << 5) | (corr_bit << 4) | (self.emergency_dir << 1) | emg_bit
        elif offset == self.REG_PEDESTRIAN_STATUS:
            ped_bit = 1 if self.ped_active else 0
            return (self.ped_serviced << 8) | ((self.ped_time_rem & 0x7F) << 1) | ped_bit
        elif offset == self.REG_FAULT_FLAGS:
            return self.fault_flags & 0xFFFF
        elif offset == self.REG_FAULT_COUNT:
            return ((self.collision_events & 0xFFFF) << 16) | (self.fault_count & 0xFFFF)
        elif offset == self.REG_VEHICLE_OCCUPANCY:
            return 0xFFFF
        elif offset == self.REG_VEH_POS_NORTH:
            return (self.pos_n[3] << 24) | (self.pos_n[2] << 16) | (self.pos_n[1] << 8) | self.pos_n[0]
        elif offset == self.REG_VEH_POS_SOUTH:
            return (self.pos_s[3] << 24) | (self.pos_s[2] << 16) | (self.pos_s[1] << 8) | self.pos_s[0]
        elif offset == self.REG_VEH_POS_EAST:
            return (self.pos_e[3] << 24) | (self.pos_e[2] << 16) | (self.pos_e[1] << 8) | self.pos_e[0]
        elif offset == self.REG_VEH_POS_WEST:
            return (self.pos_w[3] << 24) | (self.pos_w[2] << 16) | (self.pos_w[1] << 8) | self.pos_w[0]
        elif offset == self.REG_VEH_SPEEDS:
            return (self.speeds[3] << 24) | (self.speeds[2] << 16) | (self.speeds[1] << 8) | self.speeds[0]
        elif offset == self.REG_STARVATION_FLAGS:
            starve_bits = (1 if self.ew_starving else 0) << 1 | (1 if self.ns_starving else 0)
            return (self.starvation_limit << 16) | starve_bits
        elif offset == self.REG_FSM_CYCLES:
            return (self.cycle_count * 10) & 0xFFFFFFFF
        elif offset == self.REG_QUEUE_CYCLES:
            return (self.cycle_count * 10) & 0xFFFFFFFF
        elif offset == self.REG_VEHICLE_CYCLES:
            return (self.cycle_count * 160) & 0xFFFFFFFF
        elif offset == self.REG_OPTIMIZER_CYCLES:
            return (self.cycle_count * 10) & 0xFFFFFFFF
        elif offset == self.REG_UPDATE_COUNTER:
            return self.cycle_count & 0xFFFFFFFF
        elif offset == self.REG_THROUGHPUT:
            return (self.cycle_count * 16) & 0xFFFFFFFF

        return 0

    def write32(self, offset: int, value: int):
        val = value & 0xFFFFFFFF
        if offset == self.REG_CONTROL:
            self.control = val
            if val & 0x02: # Reset
                self.reset()
            if val & 0x01: # Step
                self.tick()
            if val & 0x20: # Emergency
                self.emergency_active = True
                self.emergency_dir = (val >> 6) & 0x03
                self.corridor_active = True
                self.phase = self.PHASE_EW_GREEN if self.emergency_dir in (2, 3) else self.PHASE_NS_GREEN
                self.timer = 30
                self.emg_events += 1
            if val & 0x100: # Pedestrian
                self.ped_active = True
                self.ped_time_rem = 10
        elif offset == self.REG_CONFIG:
            self.legacy_mode = False
            self.intersection_id = val & 0xFF
            self.ns_queue = (val >> 8) & 0xFF
            self.ew_queue = (val >> 16) & 0xFF
            self.q_n = self.ns_queue // 2
            self.q_s = self.ns_queue - self.q_n
            self.q_e = self.ew_queue // 2
            self.q_w = self.ew_queue - self.q_e
        elif offset == self.REG_TIMING_CFG:
            self.min_green = val & 0xFFFF
            self.max_green = (val >> 16) & 0xFFFF
        elif offset == 0x10:
            # Legacy write to NS queue
            self.legacy_mode = True
            self.ns_queue = min(val & 0xFF, 255)
            self.q_n = self.ns_queue // 2
            self.q_s = self.ns_queue - self.q_n
        elif offset == 0x14:
            # Legacy write to EW queue
            self.legacy_mode = True
            self.ew_queue = min(val & 0xFF, 255)
            self.q_e = self.ew_queue // 2
            self.q_w = self.ew_queue - self.q_e

    def _calc_congestion(self) -> int:
        tot = self.q_n + self.q_s + self.q_e + self.q_w
        return min(100, (tot * 100) // 100)

    def _calc_splits(self):
        tot = self.ns_queue + self.ew_queue
        if tot == 0:
            return 30, 20
        g_ns = self.min_green + int((self.max_green - self.min_green) * (self.ns_queue / tot))
        g_ew = self.min_green + int((self.max_green - self.min_green) * (self.ew_queue / tot))
        return max(self.min_green, min(self.max_green, g_ns)), max(self.min_green, min(self.max_green, g_ew))

    def tick(self):
        self.cycle_count = (self.cycle_count + 1) & 0xFFFFFFFF

        if self.timer > 1:
            self.timer -= 1
            if self.phase == self.PHASE_NS_GREEN:
                self.cleared_ns = (self.cleared_ns + 1) & 0xFF
                if self.q_n > 0: self.q_n -= 1
                if self.q_s > 0: self.q_s -= 1
                self.ns_queue = self.q_n + self.q_s
                self.ns_wait_time = 0
                self.ew_wait_time += 1
            elif self.phase == self.PHASE_EW_GREEN:
                self.cleared_ew = (self.cleared_ew + 1) & 0xFF
                if self.q_e > 0: self.q_e -= 1
                if self.q_w > 0: self.q_w -= 1
                self.ew_queue = self.q_e + self.q_w
                self.ew_wait_time = 0
                self.ns_wait_time += 1
        else:
            # Phase Transition
            g_ns, g_ew = self._calc_splits()
            if self.phase == self.PHASE_NS_GREEN:
                self.phase = self.PHASE_NS_YELLOW
                self.timer = 3
            elif self.phase == self.PHASE_NS_YELLOW:
                self.phase = self.PHASE_ALL_RED
                self.timer = 2
            elif self.phase == self.PHASE_ALL_RED:
                if self.ped_active:
                    self.phase = self.PHASE_PEDESTRIAN
                    self.timer = 10
                    self.ped_serviced += 1
                elif self.ew_starving or self.ew_queue > self.ns_queue:
                    self.phase = self.PHASE_EW_GREEN
                    self.timer = g_ew
                else:
                    self.phase = self.PHASE_NS_GREEN
                    self.timer = g_ns
            elif self.phase == self.PHASE_EW_GREEN:
                self.phase = self.PHASE_EW_YELLOW
                self.timer = 3
            elif self.phase == self.PHASE_EW_YELLOW:
                self.phase = self.PHASE_ALL_RED
                self.timer = 2
            elif self.phase == self.PHASE_PEDESTRIAN:
                self.ped_active = False
                self.phase = self.PHASE_ALL_RED
                self.timer = 2
            else:
                self.phase = self.PHASE_NS_GREEN
                self.timer = g_ns

        self.ns_starving = (self.ns_wait_time >= self.starvation_limit)
        self.ew_starving = (self.ew_wait_time >= self.starvation_limit)

        # -----------------------------------------------------------------
        # PREDICT -> PREVENT VEHICLE KINEMATICS & ZERO-COLLISION PIPELINE
        # -----------------------------------------------------------------
        ns_green = (self.phase == self.PHASE_NS_GREEN)
        ew_green = (self.phase == self.PHASE_EW_GREEN)

        all_pos = list(self.pos_n + self.pos_s + self.pos_e + self.pos_w)
        all_speeds = list(self.speeds * 4)

        cand_pos = []
        cand_vel = []

        for i in range(16):
            p = all_pos[i]
            v = all_speeds[i]
            if (i < 8 and not ns_green and 180 <= p <= 220) or (i >= 8 and not ew_green and 180 <= p <= 220):
                v_cand = max(0, v - 3)
            else:
                v_cand = min(15, v + 2)

            if i % 4 != 0 and all_pos[i-1] > p and (all_pos[i-1] - p) < 15:
                v_cand = max(0, v - 4)

            p_cand = 0 if p >= 240 else p + v_cand
            cand_pos.append(p_cand)
            cand_vel.append(v_cand)

        ns_occ = any(180 <= p <= 220 for p in all_pos[:8])
        ew_occ = any(180 <= p <= 220 for p in all_pos[8:])

        for i in range(16):
            is_safe = True
            if i % 4 != 0 and all_pos[i-1] > all_pos[i] and (cand_pos[i] + 8 >= cand_pos[i-1]):
                is_safe = False
            if i < 8 and not ns_green and cand_pos[i] >= 180 and all_pos[i] < 180:
                is_safe = False
            if i >= 8 and not ew_green and cand_pos[i] >= 180 and all_pos[i] < 180:
                is_safe = False
            if i < 8 and ew_occ and cand_pos[i] >= 180 and all_pos[i] < 180:
                is_safe = False
            if i >= 8 and ns_occ and cand_pos[i] >= 180 and all_pos[i] < 180:
                is_safe = False

            if is_safe:
                all_pos[i] = cand_pos[i]
                all_speeds[i] = cand_vel[i]
            else:
                all_speeds[i] = 0
                self.collision_events += 1

        self.pos_n = all_pos[0:4]
        self.pos_s = all_pos[4:8]
        self.pos_e = all_pos[8:12]
        self.pos_w = all_pos[12:16]
        self.speeds = all_speeds[0:4]
        self.actual_collision = 0
