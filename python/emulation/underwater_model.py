"""
Underwater Dynamic Probe Software RTL Model.
Faithfully emulates underwater_probe_core.v and all 8 parallel FPGA processing blocks.
Strictly replicates fixed-point arithmetic, limits, FSM transitions, and 32-register AXI map.
"""

from typing import Dict, Any, List

class UnderwaterRTLModel:
    BASE_ADDR = 0x43C00000

    # Register Offsets
    REG_CONTROL            = 0x00
    REG_DEPTH_CFG          = 0x04
    REG_CURRENT            = 0x08
    REG_STATUS             = 0x0C
    REG_CURRENT_DEPTH      = 0x10
    REG_TARGET_DEPTH       = 0x14
    REG_VELOCITY           = 0x18
    REG_DEPTH_ERROR        = 0x1C
    REG_FILTERED_DEPTH     = 0x20
    REG_FILTERED_VELOCITY  = 0x24
    REG_DRAG_FORCE         = 0x28
    REG_RELATIVE_VELOCITY  = 0x2C
    REG_P_TERM             = 0x30
    REG_I_TERM             = 0x34
    REG_D_TERM             = 0x38
    REG_CONTROL_OUTPUT     = 0x3C
    REG_THRUST_COMMAND     = 0x40
    REG_THRUST_DELTA       = 0x44
    REG_IMPACT_ENERGY      = 0x48
    REG_IMPACT_SEVERITY    = 0x4C
    REG_RECOVERY_THRUST    = 0x50
    REG_POST_COL_VELOCITY  = 0x54
    REG_PREDICTED_DEPTH_1  = 0x58
    REG_PREDICTED_DEPTH_3  = 0x5C
    REG_PREDICTED_DEPTH_5  = 0x60
    REG_CONTROL_COST       = 0x64
    REG_OPTIMIZATION_ACT   = 0x68
    REG_FAULT_FLAGS        = 0x6C
    REG_SIMULATION_CYCLES  = 0x70
    REG_PHYSICS_UPDATES    = 0x74
    REG_COLLISION_COUNT    = 0x78
    REG_RECOVERY_COUNT     = 0x7C

    # FSM States
    STATE_IDLE               = 0
    STATE_MOVING_TO_TARGET   = 1
    STATE_DISTURBED          = 2
    STATE_COLLISION_DETECTED = 3
    STATE_DISPLACEMENT       = 4
    STATE_RECOVERY           = 5
    STATE_TARGET_REACHED     = 6

    def __init__(self):
        self.reset()

    def reset(self):
        self.control = 0
        self.current_depth = 500   # 50.0m
        self.target_depth = 800    # 80.0m
        self.current_strength = 20 # +20%
        self.state = self.STATE_IDLE
        self.velocity = 0
        self.displacement_x = 0
        self.collision = False
        self.recovery = False
        self.target_reached = False
        self.active_object = 0
        self.collision_count = 0
        self.recovery_count = 0
        self.sim_cycles = 0
        self.physics_updates = 0

        # Filter buffers
        self.depth_taps = [500, 500, 500, 500]
        self.ema_vel = 0

        # PID state
        self.prev_error = 0
        self.integral_acc = 0
        self.prev_thrust = 500
        self.thrust_command = 500
        self.thrust_delta = 0
        self.p_term = 0
        self.i_term = 0
        self.d_term = 0
        self.control_output = 0

        # Physics & Forces
        self.depth_error = 0
        self.drag_force = 0
        self.relative_velocity = 0
        self.impact_energy = 0
        self.impact_severity = 0
        self.recovery_thrust = 500
        self.post_col_velocity = 0
        self.predicted_d1 = 500
        self.predicted_d3 = 500
        self.predicted_d5 = 500
        self.control_cost = 0
        self.optimization_action = 0
        self.fault_flags = 0
        self.recovery_step = 0

    def read32(self, offset: int) -> int:
        if offset == self.REG_CONTROL:
            return 0
        elif offset == self.REG_DEPTH_CFG:
            return ((self.target_depth & 0xFFFF) << 16) | (self.current_depth & 0xFFFF)
        elif offset == self.REG_CURRENT:
            return self.current_strength & 0xFF
        elif offset == self.REG_STATUS:
            return (self.state & 0x0F) | (int(self.collision) << 4) | (int(self.recovery) << 5) | \
                   (int(self.target_reached) << 6) | ((self.active_object & 0x03) << 7)
        elif offset == self.REG_CURRENT_DEPTH:
            return self.current_depth & 0xFFFF
        elif offset == self.REG_TARGET_DEPTH:
            return self.target_depth & 0xFFFF
        elif offset == self.REG_VELOCITY:
            return self.velocity & 0xFF
        elif offset == self.REG_DEPTH_ERROR:
            return self.depth_error & 0xFFFF
        elif offset == self.REG_FILTERED_DEPTH:
            return (sum(self.depth_taps) // 4) & 0xFFFF
        elif offset == self.REG_FILTERED_VELOCITY:
            return self.ema_vel & 0xFF
        elif offset == self.REG_DRAG_FORCE:
            return self.drag_force & 0xFFFF
        elif offset == self.REG_RELATIVE_VELOCITY:
            return self.relative_velocity & 0xFFFF
        elif offset == self.REG_P_TERM:
            return self.p_term & 0xFFFF
        elif offset == self.REG_I_TERM:
            return self.i_term & 0xFFFF
        elif offset == self.REG_D_TERM:
            return self.d_term & 0xFFFF
        elif offset == self.REG_CONTROL_OUTPUT:
            return self.control_output & 0xFFFF
        elif offset == self.REG_THRUST_COMMAND:
            return self.thrust_command & 0xFFFF
        elif offset == self.REG_THRUST_DELTA:
            return self.thrust_delta & 0xFFFF
        elif offset == self.REG_IMPACT_ENERGY:
            return self.impact_energy & 0xFFFF
        elif offset == self.REG_IMPACT_SEVERITY:
            return self.impact_severity & 0x07
        elif offset == self.REG_RECOVERY_THRUST:
            return self.recovery_thrust & 0xFFFF
        elif offset == self.REG_POST_COL_VELOCITY:
            return self.post_col_velocity & 0xFF
        elif offset == self.REG_PREDICTED_DEPTH_1:
            return self.predicted_d1 & 0xFFFF
        elif offset == self.REG_PREDICTED_DEPTH_3:
            return self.predicted_d3 & 0xFFFF
        elif offset == self.REG_PREDICTED_DEPTH_5:
            return self.predicted_d5 & 0xFFFF
        elif offset == self.REG_CONTROL_COST:
            return self.control_cost & 0xFFFF
        elif offset == self.REG_OPTIMIZATION_ACT:
            return self.optimization_action & 0x03
        elif offset == self.REG_FAULT_FLAGS:
            return self.fault_flags & 0xFF
        elif offset == self.REG_SIMULATION_CYCLES:
            return self.sim_cycles & 0xFFFFFFFF
        elif offset == self.REG_PHYSICS_UPDATES:
            return self.physics_updates & 0xFFFFFFFF
        elif offset == self.REG_COLLISION_COUNT:
            return self.collision_count & 0xFFFF
        elif offset == self.REG_RECOVERY_COUNT:
            return self.recovery_count & 0xFFFF
        return 0

    def write32(self, offset: int, value: int):
        val = value & 0xFFFFFFFF
        if offset == self.REG_CONTROL:
            self.control = val
            if val & 0x01: # Start
                if self.state == self.STATE_IDLE:
                    self.state = self.STATE_MOVING_TO_TARGET
            if val & 0x02: # Stop
                self.state = self.STATE_IDLE
            if val & 0x04: # Reset
                self.reset()
            if val & 0x08: # Disturb strobe
                d_type = (val >> 4) & 0x03
                self.trigger_disturbance(d_type)
            if val & 0x40: # set_depth_we
                # applied in REG_DEPTH_CFG
                pass
        elif offset == self.REG_DEPTH_CFG:
            set_d = val & 0xFFFF
            tgt_d = (val >> 16) & 0xFFFF
            if set_d > 0x7FFF: set_d -= 0x10000
            if tgt_d > 0x7FFF: tgt_d -= 0x10000
            self.current_depth = set_d
            self.target_depth = tgt_d
        elif offset == self.REG_CURRENT:
            c = val & 0xFF
            self.current_strength = c if c < 0x80 else c - 0x100

    def trigger_disturbance(self, obj_type: int):
        if self.state != self.STATE_IDLE:
            self.active_object = obj_type
            self.collision = True
            self.collision_count += 1
            self.post_col_velocity = self.velocity
            self.state = self.STATE_COLLISION_DETECTED

            mass = 5 if obj_type == 1 else (25 if obj_type == 2 else 200)
            v_sq = self.relative_velocity * self.relative_velocity
            e_calc = (mass * v_sq) // 200
            self.impact_energy = min(65535, e_calc)
            if e_calc < 50: self.impact_severity = 1
            elif e_calc < 250: self.impact_severity = 2
            elif e_calc < 800: self.impact_severity = 3
            else: self.impact_severity = 4

    def tick(self):
        self.sim_cycles = (self.sim_cycles + 1) & 0xFFFFFFFF
        if self.state == self.STATE_IDLE:
            self.velocity = 0
            self.collision = False
            self.recovery = False
            self.target_reached = False
            return

        self.physics_updates = (self.physics_updates + 1) & 0xFFFFFFFF
        self.depth_error = self.target_depth - self.current_depth
        v_curr = self.current_strength >> 4
        self.relative_velocity = self.velocity - v_curr

        # 1. Quadratic Drag Calculation: K_drag = 0.25 (factor 4 >> 4)
        quad = self.relative_velocity * abs(self.relative_velocity)
        self.drag_force = max(-1000, min(1000, (quad * 4) >> 4))

        # 2. PID Control Calculation
        self.p_term = (self.depth_error * 20) >> 4
        self.integral_acc = max(-50000, min(50000, self.integral_acc + self.depth_error))
        self.i_term = (self.integral_acc * 4) >> 8
        d_err = self.depth_error - self.prev_error
        self.prev_error = self.depth_error
        self.d_term = (d_err * 12) >> 2

        dist_comp = -(self.current_strength * 2)
        self.control_output = self.p_term + self.i_term + self.d_term + dist_comp
        new_thrust = max(0, min(1500, 500 + self.control_output))
        self.thrust_delta = new_thrust - self.thrust_command
        self.thrust_command = new_thrust

        # 3. Acceleration & Velocity Integration
        net_f = (self.recovery_thrust if self.recovery else (self.thrust_command - 500)) - self.drag_force
        v_step = net_f >> 5
        self.velocity = max(-15, min(15, self.velocity + v_step + v_curr))

        # 4. Discrete Depth Update
        self.current_depth = max(0, min(10000, self.current_depth + self.velocity))

        # 5. Filters
        self.depth_taps.pop(0)
        self.depth_taps.append(self.current_depth)
        self.ema_vel = ((self.ema_vel * 3) + self.velocity) >> 2

        # 6. Future Depth Prediction
        accel = net_f >> 5
        self.predicted_d1 = max(0, min(10000, self.current_depth + self.velocity + (accel >> 1)))
        self.predicted_d3 = max(0, min(10000, self.current_depth + (self.velocity * 3) + (accel << 2)))
        self.predicted_d5 = max(0, min(10000, self.current_depth + (self.velocity * 5) + (accel * 12)))

        # 7. Energy Optimizer
        self.control_cost = (abs(self.depth_error) * 2) + (abs(self.velocity) * 4) + (abs(self.thrust_command - 500) >> 2)
        if (self.depth_error > 20 and self.velocity < -2) or (self.depth_error < -20 and self.velocity > 2):
            self.optimization_action = 1 # INCREASE
        elif abs(self.depth_error) < 5 and abs(self.velocity) > 8:
            self.optimization_action = 2 # DECREASE
        else:
            self.optimization_action = 0 # HOLD

        # 8. Fault Detection
        f = 0
        if self.current_depth <= 0 or self.current_depth >= 10000: f |= (1 << 0)
        if abs(self.depth_error) > 2000: f |= (1 << 1)
        if abs(self.velocity) > 12: f |= (1 << 2)
        if self.thrust_command >= 1500 or self.thrust_command <= 0: f |= (1 << 3)
        if abs(self.current_strength) > 90: f |= (1 << 4)
        if self.collision and abs(self.velocity) > 10: f |= (1 << 5)
        if abs(self.integral_acc) >= 50000: f |= (1 << 6)
        self.fault_flags = f

        # 9. FSM State Updates
        if self.state == self.STATE_MOVING_TO_TARGET:
            if abs(self.depth_error) <= 5:
                self.target_reached = True
                self.state = self.STATE_TARGET_REACHED

        elif self.state == self.STATE_COLLISION_DETECTED:
            if self.active_object == 1:
                self.current_depth -= 8
                self.recovery_thrust = 580
            elif self.active_object == 2:
                self.current_depth += 14
                self.recovery_thrust = 420
            elif self.active_object == 3:
                self.current_depth -= 32
                self.recovery_thrust = 750
            self.recovery_step = 8
            self.state = self.STATE_DISPLACEMENT

        elif self.state == self.STATE_DISPLACEMENT:
            self.collision = False
            self.recovery = True
            self.recovery_count += 1
            self.state = self.STATE_RECOVERY

        elif self.state == self.STATE_RECOVERY:
            self.recovery = True
            if self.recovery_step > 1:
                self.recovery_step -= 1
            else:
                self.recovery_step = 0
                self.recovery = False
                self.active_object = 0
                self.recovery_thrust = 500
                self.state = self.STATE_MOVING_TO_TARGET

        elif self.state == self.STATE_TARGET_REACHED:
            self.target_reached = True
            if abs(self.depth_error) > 8:
                self.target_reached = False
                self.state = self.STATE_MOVING_TO_TARGET
