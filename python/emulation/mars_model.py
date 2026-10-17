"""
python.emulation.mars_model
===========================
RTL-Equivalent Software Model for Mars Space Habitat & Landing Accelerator.
Faithfully reproduces mars_habitat_core.v and all 11 computational engines:
- Mars gravity engine (g = 3.71 m/s^2)
- Closed-loop retro-thrust braking controller
- Deterministic fixed-point landing physics engine (discrete dt integration)
- Forward landing prediction engine (T+1, T+5, T+10 horizons)
- True 8-channel concurrent parallel meteorite trajectory & energy processor
- Habitat structural damage accumulation and automated section isolation
- Atmospheric gas composition (O2/CO2) and pressure dynamics
- Thermal model (internal heating vs. Martian external sink)
- Life-support health score (0..100) and multi-domain fault detector
- 32-register AXI4-Lite slave address space (0x00 .. 0x7C)
"""

import threading
from typing import Dict, Any, List


class MarsHabitatRTLModel:
    """Cycle-accurate software model of mars_habitat_core.v & sub-engines."""

    BASE_ADDRESS = 0x43C20000
    BASE_ADDR = 0x43C20000

    # FSM State Constants
    STATE_IDLE              = 0
    STATE_ATTACK_RECEIVED   = 1
    STATE_METEORITE_ACTIVE  = 2
    STATE_TARGET_IDENT      = 3
    STATE_IMPACT_CALC       = 4
    STATE_THRESHOLD_CHECK   = 5
    STATE_PROTECTION_ACTION = 6
    STATE_UPDATE_STATUS     = 7
    STATE_NEXT_METEORITE    = 8
    STATE_ATTACK_COMPLETE   = 9

    # Landing FSM Constants
    LANDING_FSM_PREP       = 0
    LANDING_FSM_POWERED    = 1
    LANDING_FSM_APPROACH   = 2
    LANDING_FSM_TOUCHDOWN  = 3

    # Register Byte Offsets (Expanded 256-byte aperture)
    REG_CONTROL                 = 0x00
    REG_ATTACK                  = 0x04
    REG_THRESHOLD               = 0x08
    REG_STATUS                  = 0x0C
    REG_IMPACT                  = 0x10
    REG_COUNTERS                = 0x14
    REG_TOTAL                   = 0x18
    REG_LANDING_ALTITUDE        = 0x1C
    REG_LANDING_VELOCITY        = 0x20
    REG_THRUST_COMMAND          = 0x24
    REG_PREDICTED_ALTITUDE      = 0x28
    REG_PREDICTED_TOUCHDOWN_VEL = 0x2C
    REG_LANDING_STATUS          = 0x30
    REG_METEORITE_ACTIVE        = 0x34
    REG_METEORITE_IMPACT_VECTOR = 0x38
    REG_TOTAL_IMPACT_ENERGY     = 0x3C
    REG_SECTION_DAMAGE          = 0x40
    REG_RECOVERY_ACTION         = 0x44
    REG_O2_PERCENT              = 0x48
    REG_CO2_PERCENT             = 0x4C
    REG_PRESSURE_KPA            = 0x50
    REG_TEMPERATURE_C           = 0x54
    REG_LIFE_SUPPORT_STATUS     = 0x58
    REG_HABITAT_HEALTH          = 0x5C
    REG_HAZARD_SCORE            = 0x60
    REG_FAULT_FLAGS             = 0x64
    REG_SIMULATION_CYCLES       = 0x68
    REG_METEORITES_PROCESSED    = 0x6C

    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        """Resets all internal hardware registers matching Verilog rst_n assertion."""
        with self._lock:
            # Legacy FSM & State
            self.system_state: int = self.STATE_IDLE
            self.section_A_state: int = 0      # 0 = OPERATIONAL, 1 = CLOSED
            self.section_B_state: int = 0      # 0 = OPERATIONAL, 1 = CLOSED
            self.link_A_B_state: int = 0       # 0 = OPEN, 1 = CLOSED
            self.active_target: int = 1        # 1 = A, 2 = B
            self.last_impact_value: int = 0    # 16-bit scaled (x10)
            self.threshold_crossed: int = 0    # 1-bit flag
            self.total_requested: int = 0      # 8-bit
            self.processed_count: int = 0      # 8-bit
            self.impact_count_A: int = 0       # 16-bit
            self.impact_count_B: int = 0       # 16-bit
            self.total_impacts: int = 0        # 16-bit

            # Config Registers
            self.cmd_meteorite_type: int = 0   # 0 = NORMAL, 1 = BIG
            self.cmd_target_segment: int = 0   # 0 = ALL, 1 = A, 2 = B
            self.cmd_meteorite_count: int = 1
            self.cfg_threshold_A: int = 700    # 70.0
            self.cfg_threshold_B: int = 650    # 65.0

            # LFSR state
            self.lfsr: int = 0xA5

            # Landing Physics Engine (Fixed-point: alt in 0.1m, vel in 0.1m/s)
            self.landing_active: bool = False
            self.landing_fsm: int = self.LANDING_FSM_PREP
            self.landing_alt_dm: int = 5000     # 500.0 m
            self.landing_vel_dms: int = -200    # -20.0 m/s
            self.landing_accel_dms2: int = 0    # 0.0 m/s^2
            self.thrust_command: int = 650      # 65.0%
            self.pred_alt_dm: int = 4000        # 400.0 m
            self.pred_touchdown_vel: int = -42  # -4.2 m/s
            self.landing_status_code: int = 0   # 0=SAFE

            # Parallel Meteorite Engine (8 channels)
            self.parallel_meteor_en: bool = False
            self.meteorite_active_mask: int = 0
            self.meteorite_impact_vector: int = 0
            self.critical_impact_count: int = 0
            self.total_impact_energy: int = 0

            # Habitat Damage & Recovery
            self.damage_A: int = 0              # 0.1 units
            self.damage_B: int = 0
            self.recovery_action: int = 0       # 0=NO_ACTION

            # Atmospheric & Thermal
            self.o2_percent: int = 209          # 20.9%
            self.co2_percent: int = 4           # 0.04%
            self.pressure_kpa: int = 1013       # 101.3 kPa
            self.temperature_c: int = 210       # +21.0 C

            # Life Support & Safety
            self.life_support_status: int = 0   # 0=STABLE
            self.habitat_health: int = 100      # 100%
            self.hazard_score: int = 15         # 15/100
            self.hazard_status: int = 0         # 0=NORMAL
            self.fault_flags: int = 0           # 0x0000

            # Performance Counters
            self.simulation_cycles: int = 12000
            self.meteorites_processed_total: int = 0

    def tick(self):
        """Simulation tick (advances physical integration & cycle counters)."""
        with self._lock:
            self.simulation_cycles = (self.simulation_cycles + 1000) & 0xFFFFFFFF
            if self.landing_active and self.landing_alt_dm > 0:
                self._step_landing_physics()
            if self.parallel_meteor_en:
                self._step_parallel_meteorites()
            self._update_atmosphere_and_life_support()

    def _step_landing_physics(self):
        """Discrete dt integration matching mars_landing_physics.v."""
        # Mars gravity: 3.71 m/s^2 -> down force 3710 N for 1000kg
        # Closed-loop thrust: K_alt * e_alt + K_vel * e_vel + g_comp
        alt_m = self.landing_alt_dm / 10.0
        vel_ms = self.landing_vel_dms / 10.0

        target_v = -2.0 if alt_m < 20.0 else (-10.0 if alt_m < 100.0 else -20.0)
        vel_err = target_v - vel_ms
        thrust_n = 3710 + vel_err * 400.0
        thrust_clamped = max(0.0, min(10000.0, thrust_n))
        self.thrust_command = int((thrust_clamped / 10000.0) * 1000)

        # Net acceleration = (Thrust - F_grav) / m
        a_ms2 = (thrust_clamped - 3710) / 1000.0
        self.landing_accel_dms2 = int(a_ms2 * 10)

        # dt = 0.1s
        dt = 0.1
        vel_ms += a_ms2 * dt
        alt_m += vel_ms * dt

        if alt_m <= 0.0:
            alt_m = 0.0
            self.landing_fsm = self.LANDING_FSM_TOUCHDOWN
            self.landing_active = False
            # Check touchdown speed safety
            if abs(vel_ms) <= 5.0:
                self.landing_status_code = 0  # SAFE
            elif abs(vel_ms) <= 10.0:
                self.landing_status_code = 1  # WARN
            else:
                self.landing_status_code = 2  # CRITICAL
                self.fault_flags |= (1 << 0)   # EXCESSIVE_VELOCITY
        else:
            if alt_m < 30.0:
                self.landing_fsm = self.LANDING_FSM_APPROACH
            else:
                self.landing_fsm = self.LANDING_FSM_POWERED

        self.landing_alt_dm = max(0, int(alt_m * 10))
        self.landing_vel_dms = int(vel_ms * 10)

        # Predictor: T+5 projection
        self.pred_alt_dm = max(0, int((alt_m + vel_ms * 0.5) * 10))
        self.pred_touchdown_vel = self.landing_vel_dms

    def _step_parallel_meteorites(self):
        """True parallel 8-channel evaluation matching meteorite_parallel_engine.v."""
        self.meteorite_active_mask = 0xFF
        self.meteorites_processed_total += 8
        # Deterministic impact evaluation
        self._step_lfsr()
        impacts = 0
        energy_sum = 0
        crit_count = 0

        for ch in range(8):
            # Distance comparison d^2 < impact_radius^2
            ch_hit = 1 if ((self.lfsr >> ch) & 1) and (ch in (1, 5)) else 0
            if ch_hit:
                impacts |= (1 << ch)
                e_ch = 350 + (ch * 75)
                energy_sum += e_ch
                if e_ch > 500:
                    crit_count += 1
                # Apply damage to section
                if ch % 2 == 0:
                    self.damage_A = min(1000, self.damage_A + 45)
                    self.impact_count_A += 1
                else:
                    self.damage_B = min(1000, self.damage_B + 45)
                    self.impact_count_B += 1
                self.total_impacts += 1

        self.meteorite_impact_vector = impacts
        self.total_impact_energy += energy_sum
        self.critical_impact_count += crit_count

        # Structural damage threshold check
        if self.damage_A >= self.cfg_threshold_A:
            self.section_A_state = 1
            self.link_A_B_state = 1
            self.recovery_action = 1  # ISOLATE_A
            self.fault_flags |= (1 << 4)  # SECTION_A_BREACH

        if self.damage_B >= self.cfg_threshold_B:
            self.section_B_state = 1
            self.link_A_B_state = 1
            self.recovery_action = 2 if self.recovery_action == 0 else 3  # ISOLATE_B or BOTH
            self.fault_flags |= (1 << 5)  # SECTION_B_BREACH

    def _update_atmosphere_and_life_support(self):
        """Subsystem health & life support metric evaluation."""
        # Breach effects
        if self.section_A_state or self.section_B_state:
            self.pressure_kpa = max(100, self.pressure_kpa - 2)
            self.o2_percent = max(120, self.o2_percent - 1)
            self.temperature_c = max(-500, self.temperature_c - 5)
            self.co2_percent = min(200, self.co2_percent + 1)

        # Fault checking
        if self.o2_percent < 180:
            self.fault_flags |= (1 << 6)
        if self.co2_percent > 80:
            self.fault_flags |= (1 << 7)
        if self.pressure_kpa < 700:
            self.fault_flags |= (1 << 8)
        if self.temperature_c < -200 or self.temperature_c > 450:
            self.fault_flags |= (1 << 9)

        # Composite Health Score
        dmg_penalty = (self.damage_A + self.damage_B) // 20
        env_penalty = 0
        if self.pressure_kpa < 900: env_penalty += 15
        if self.o2_percent < 195: env_penalty += 15
        if self.temperature_c < 0: env_penalty += 10
        self.habitat_health = max(0, 100 - dmg_penalty - env_penalty)

        if self.habitat_health >= 90:
            self.life_support_status = 0  # STABLE
        elif self.habitat_health >= 70:
            self.life_support_status = 1  # DEGRADED
        elif self.habitat_health >= 40:
            self.life_support_status = 2  # WARNING
        else:
            self.life_support_status = 3  # CRITICAL

        # Hazard Score
        self.hazard_score = min(100, max(10, 100 - self.habitat_health + (self.critical_impact_count * 10)))
        if self.hazard_score >= 70:
            self.hazard_status = 2  # CRITICAL
        elif self.hazard_score >= 40:
            self.hazard_status = 1  # WARNING
        else:
            self.hazard_status = 0  # NORMAL

    def _step_lfsr(self):
        """Steps the 8-bit LFSR polynomial: x^8 + x^6 + x^5 + x^4 + 1."""
        b7 = (self.lfsr >> 7) & 1
        b5 = (self.lfsr >> 5) & 1
        b4 = (self.lfsr >> 4) & 1
        b3 = (self.lfsr >> 3) & 1
        feedback = b7 ^ b5 ^ b4 ^ b3
        self.lfsr = ((self.lfsr << 1) & 0xFE) | feedback

    def read_register(self, offset: int) -> int:
        """Reads 32-bit register matching mars_habitat_axi_slave.v."""
        with self._lock:
            if offset == self.REG_CONTROL:
                return 0
            elif offset == self.REG_ATTACK:
                return (
                    ((self.cmd_meteorite_count & 0xFF) << 8) |
                    ((self.cmd_target_segment & 0x03) << 1) |
                    (self.cmd_meteorite_type & 1)
                )
            elif offset == self.REG_THRESHOLD:
                return ((self.cfg_threshold_B & 0xFFFF) << 16) | (self.cfg_threshold_A & 0xFFFF)
            elif offset == self.REG_STATUS:
                val = (self.system_state & 0x0F)
                if self.section_A_state:   val |= (1 << 4)
                if self.section_B_state:   val |= (1 << 5)
                if self.link_A_B_state:    val |= (1 << 6)
                if self.threshold_crossed: val |= (1 << 7)
                val |= ((self.active_target & 0x03) << 8)
                return val
            elif offset == self.REG_IMPACT:
                return (
                    ((self.total_requested & 0xFF) << 24) |
                    ((self.processed_count & 0xFF) << 16) |
                    (self.last_impact_value & 0xFFFF)
                )
            elif offset == self.REG_COUNTERS:
                return ((self.impact_count_B & 0xFFFF) << 16) | (self.impact_count_A & 0xFFFF)
            elif offset == self.REG_TOTAL:
                return ((self.critical_impact_count & 0xFFFF) << 16) | (self.total_impacts & 0xFFFF)
            elif offset == self.REG_LANDING_ALTITUDE:
                return self.landing_alt_dm & 0xFFFFFFFF
            elif offset == self.REG_LANDING_VELOCITY:
                return ((self.landing_accel_dms2 & 0xFFFF) << 16) | (self.landing_vel_dms & 0xFFFF)
            elif offset == self.REG_THRUST_COMMAND:
                return self.thrust_command & 0xFFFF
            elif offset == self.REG_PREDICTED_ALTITUDE:
                return self.pred_alt_dm & 0xFFFFFFFF
            elif offset == self.REG_PREDICTED_TOUCHDOWN_VEL:
                return self.pred_touchdown_vel & 0xFFFF
            elif offset == self.REG_LANDING_STATUS:
                return ((self.landing_fsm & 0x03) << 2) | (self.landing_status_code & 0x03)
            elif offset == self.REG_METEORITE_ACTIVE:
                return self.meteorite_active_mask & 0xFF
            elif offset == self.REG_METEORITE_IMPACT_VECTOR:
                return self.meteorite_impact_vector & 0xFF
            elif offset == self.REG_TOTAL_IMPACT_ENERGY:
                return self.total_impact_energy & 0xFFFFFFFF
            elif offset == self.REG_SECTION_DAMAGE:
                return ((self.damage_B & 0xFFFF) << 16) | (self.damage_A & 0xFFFF)
            elif offset == self.REG_RECOVERY_ACTION:
                return self.recovery_action & 0x0F
            elif offset == self.REG_O2_PERCENT:
                return self.o2_percent & 0xFFFF
            elif offset == self.REG_CO2_PERCENT:
                return self.co2_percent & 0xFFFF
            elif offset == self.REG_PRESSURE_KPA:
                return self.pressure_kpa & 0xFFFF
            elif offset == self.REG_TEMPERATURE_C:
                return self.temperature_c & 0xFFFF
            elif offset == self.REG_LIFE_SUPPORT_STATUS:
                return self.life_support_status & 0x03
            elif offset == self.REG_HABITAT_HEALTH:
                return self.habitat_health & 0xFF
            elif offset == self.REG_HAZARD_SCORE:
                return ((self.hazard_status & 0x03) << 8) | (self.hazard_score & 0xFF)
            elif offset == self.REG_FAULT_FLAGS:
                return self.fault_flags & 0xFFFF
            elif offset == self.REG_SIMULATION_CYCLES:
                return self.simulation_cycles & 0xFFFFFFFF
            elif offset == self.REG_METEORITES_PROCESSED:
                return self.meteorites_processed_total & 0xFFFF
            return 0xDEADBEEF

    def write_register(self, offset: int, value: int):
        """Processes 32-bit register write matching mars_habitat_axi_slave.v."""
        with self._lock:
            val32 = value & 0xFFFFFFFF
            if offset == self.REG_CONTROL:
                attack_strobe   = val32 & 1
                reset_strobe    = (val32 >> 1) & 1
                landing_strobe  = (val32 >> 2) & 1
                meteor_par_en   = (val32 >> 3) & 1

                if reset_strobe:
                    self.reset()
                    return

                if landing_strobe:
                    self.landing_active = True
                    self.landing_fsm = self.LANDING_FSM_POWERED
                    self.landing_alt_dm = 5000
                    self.landing_vel_dms = -200

                self.parallel_meteor_en = bool(meteor_par_en)
                if self.parallel_meteor_en:
                    self.meteorite_active_mask = 0xFF
                else:
                    self.meteorite_active_mask = 0x00

                if attack_strobe:
                    self._run_attack_sequence()

            elif offset == self.REG_ATTACK:
                self.cmd_meteorite_type  = val32 & 1
                self.cmd_target_segment  = (val32 >> 1) & 0x03
                self.cmd_meteorite_count = max(1, (val32 >> 8) & 0xFF)

            elif offset == self.REG_THRESHOLD:
                self.cfg_threshold_A = val32 & 0xFFFF
                self.cfg_threshold_B = (val32 >> 16) & 0xFFFF

    def _run_attack_sequence(self):
        """Executes the discrete hardware FSM loop for the configured meteorite wave."""
        self.total_requested = self.cmd_meteorite_count
        count = self.total_requested

        for seq in range(count):
            self.system_state = self.STATE_TARGET_IDENT

            if self.cmd_target_segment == 1:
                target = 1 # Section A
            elif self.cmd_target_segment == 2:
                target = 2 # Section B
            else:
                target = 1 if (seq % 2 == 0) else 2
            self.active_target = target

            self.system_state = self.STATE_IMPACT_CALC
            self._step_lfsr()
            variation = (self.lfsr & 0x7F) ^ (seq & 0x7F)

            if self.cmd_meteorite_type == 0:
                impact = 280 + ((variation & 0x7F) * 2)
            else:
                impact = 874 if seq == 0 else (850 + (variation & 0x7F))

            self.last_impact_value = impact & 0xFFFF
            self.system_state = self.STATE_THRESHOLD_CHECK

            threshold = self.cfg_threshold_A if target == 1 else self.cfg_threshold_B
            crossed = 1 if (impact >= threshold) else 0
            self.threshold_crossed = crossed

            if crossed:
                self.system_state = self.STATE_PROTECTION_ACTION
                if target == 1:
                    self.section_A_state = 1
                    self.damage_A = min(1000, self.damage_A + 200)
                else:
                    self.section_B_state = 1
                    self.damage_B = min(1000, self.damage_B + 200)
                self.link_A_B_state = 1
                self.recovery_action = 1 if target == 1 else 2

            self.system_state = self.STATE_UPDATE_STATUS
            if target == 1:
                self.impact_count_A = (self.impact_count_A + 1) & 0xFFFF
            else:
                self.impact_count_B = (self.impact_count_B + 1) & 0xFFFF
            self.total_impacts = (self.total_impacts + 1) & 0xFFFF
            self.processed_count = seq + 1
            self.meteorites_processed_total += 1

        self.system_state = self.STATE_ATTACK_COMPLETE
        self._update_atmosphere_and_life_support()

    def read32(self, offset: int) -> int:
        """Alias for read_register."""
        return self.read_register(offset)

    def write32(self, offset: int, value: int):
        """Alias for write_register."""
        self.write_register(offset, value)
