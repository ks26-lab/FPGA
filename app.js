/**
 * FPGA Project Control Panel — Experimental Testbed Core Logic
 * 
 * Strict Hardware Mapping:
 * Only real inputs, logic, and outputs defined for each FPGA project.
 * Flow: USER COMMAND -> FPGA INPUT -> FPGA LOGIC -> FPGA OUTPUT -> VISUAL REPRESENTATION
 */

// =============================================================================
// PROJECT DEFINITIONS (Exact FPGA Inputs, Processing Logic, and Outputs)
// =============================================================================

const PROJECTS = {
  TRAFFIC: {
    id: "TRAFFIC",
    name: "SMART CITY TRAFFIC GRID",
    desc: "EDGE ZYNQ Z7010 FPGA 16-VEHICLE PARALLEL ACCELERATOR",
    image: "C:/Users/karti/.gemini/antigravity-ide/brain/77403d67-de93-430a-ad8f-69bfb3fae9ec/traffic_signal_project_1791213984487.jpg",
    inputs: {
      rst_n: { type: "switch", label: "rst_n", desc: "Active-Low Reset Pin", val: 1 },
      adaptive_mode: { type: "switch", label: "adaptive_mode", desc: "Autonomous FPGA Adaptive Optimization", val: 1 },
      density_preset: { type: "bus_select", options: ["LOW (5 veh)", "MEDIUM (15 veh)", "HIGH (35 veh)", "GRIDLOCK (60 veh)"], label: "density_preset", desc: "Arrival Rate Generator", val: "MEDIUM (15 veh)" },
      emergency_override: { type: "switch", label: "emergency_override", desc: "Priority Corridor Preemption Switch", val: 0 },
      emergency_dir: { type: "bus_select", options: ["NORTH (00)", "SOUTH (01)", "EAST (10)", "WEST (11)"], label: "emergency_dir [1:0]", desc: "Corridor Target Direction", val: "NORTH (00)" },
      ped_request: { type: "binary", label: "ped_request", desc: "Pedestrian Walk Pushbutton", val: 0 },
      selected_vehicle: { type: "bus_select", options: ["V0 (North 0)", "V1 (North 1)", "V2 (North 2)", "V3 (North 3)", "V4 (South 0)", "V5 (South 1)", "V6 (South 2)", "V7 (South 3)", "V8 (East 0)", "V9 (East 1)", "V10 (East 2)", "V11 (East 3)", "V12 (West 0)", "V13 (West 1)", "V14 (West 2)", "V15 (West 3)"], label: "selected_vehicle", desc: "Telemetry Channel Inspector", val: "V0 (North 0)" }
    },
    outputs: {
      ns_lights: { type: "led_cluster_traffic", label: "ns_lights [2:0]", desc: "North-South Cluster (R/Y/G)", val: "GREEN" },
      ew_lights: { type: "led_cluster_traffic", label: "ew_lights [2:0]", desc: "East-West Cluster (R/Y/G)", val: "RED" },
      timer_7seg: { type: "seven_seg", label: "timer_7seg [6:0]", desc: "Remaining Green Interval (s)", val: 24 },
      fsm_state: { type: "badge", label: "fsm_state [2:0]", desc: "FPGA FSM State Code", val: "S_NS_GREEN (001)" },
      congestion_score: { type: "badge", label: "congestion_score [7:0]", desc: "Congestion Rating (0-100%)", val: "38% (NORMAL)" },
      approach_queues: { type: "badge", label: "queues [31:0]", desc: "N / S / E / W Queue Depths", val: "N:12 S:10 E:8 W:6 (Tot:36)" },
      parallel_engines: { type: "badge", label: "parallel_engines", desc: "16 Hardware Vehicle Channels", val: "16 ACTIVE (4x4 Matrix)" },
      fault_supervisor: { type: "badge", label: "fault_flags [15:0]", desc: "Safety Interlock Supervisor", val: "NOMINAL (MUTEX LOCKED)" }
    },
    // Internal hardware vehicle state (16 channels)
    _vehicles: [
      { id: 0, lane: "NORTH", x: 180, v: 12.0, a: 0.0, brake: 0 },
      { id: 1, lane: "NORTH", x: 140, v: 11.5, a: 0.0, brake: 0 },
      { id: 2, lane: "NORTH", x: 90,  v: 10.0, a: 0.0, brake: 0 },
      { id: 3, lane: "NORTH", x: 30,  v: 8.5,  a: 0.0, brake: 0 },
      { id: 4, lane: "SOUTH", x: 175, v: 11.8, a: 0.0, brake: 0 },
      { id: 5, lane: "SOUTH", x: 130, v: 10.5, a: 0.0, brake: 0 },
      { id: 6, lane: "SOUTH", x: 80,  v: 9.0,  a: 0.0, brake: 0 },
      { id: 7, lane: "SOUTH", x: 20,  v: 7.0,  a: 0.0, brake: 0 },
      { id: 8, lane: "EAST",  x: 185, v: 13.0, a: 0.0, brake: 0 },
      { id: 9, lane: "EAST",  x: 145, v: 12.0, a: 0.0, brake: 0 },
      { id: 10, lane: "EAST", x: 95,  v: 11.0, a: 0.0, brake: 0 },
      { id: 11, lane: "EAST", x: 35,  v: 9.5,  a: 0.0, brake: 0 },
      { id: 12, lane: "WEST", x: 170, v: 11.0, a: 0.0, brake: 0 },
      { id: 13, lane: "WEST", x: 125, v: 10.0, a: 0.0, brake: 0 },
      { id: 14, lane: "WEST", x: 75,  v: 8.0,  a: 0.0, brake: 0 },
      { id: 15, lane: "WEST", x: 15,  v: 6.5,  a: 0.0, brake: 0 }
    ],
    evaluate: function() {
      if (this.inputs.rst_n.val === 0) {
        this.outputs.ns_lights.val = "RED";
        this.outputs.ew_lights.val = "RED";
        this.outputs.timer_7seg.val = 0;
        this.outputs.fsm_state.val = "S_RESET (000)";
        this.outputs.congestion_score.val = "0% (RESET)";
        this.outputs.fault_supervisor.val = "RESET TRIP";
        return;
      }

      // Density calculation
      let qN = 12, qS = 10, qE = 8, qW = 6;
      const dPreset = this.inputs.density_preset.val;
      if (dPreset.includes("LOW")) { qN = 5; qS = 4; qE = 3; qW = 2; }
      else if (dPreset.includes("HIGH")) { qN = 35; qS = 30; qE = 22; qW = 18; }
      else if (dPreset.includes("GRIDLOCK")) { qN = 60; qS = 55; qE = 48; qW = 42; }
      const qTot = qN + qS + qE + qW;
      const congPct = Math.min(100, Math.round((qTot / 160) * 100));

      this.outputs.approach_queues.val = `N:${qN} S:${qS} E:${qE} W:${qW} (Tot:${qTot})`;
      this.outputs.congestion_score.val = `${congPct}% (${congPct > 70 ? 'HEAVY' : (congPct > 40 ? 'NORMAL' : 'LOW')})`;

      // Emergency preemption corridor
      if (this.inputs.emergency_override.val === 1) {
        const isEW = this.inputs.emergency_dir.val.includes("EAST") || this.inputs.emergency_dir.val.includes("WEST");
        this.outputs.ns_lights.val = isEW ? "RED" : "GREEN";
        this.outputs.ew_lights.val = isEW ? "GREEN" : "RED";
        this.outputs.timer_7seg.val = 30;
        this.outputs.fsm_state.val = "S_EMERGENCY (110)";
        this.outputs.fault_supervisor.val = "EMERGENCY CORRIDOR GRANTED";
        return;
      }

      // Pedestrian Walk
      if (this.inputs.ped_request.val === 1) {
        this.outputs.ns_lights.val = "RED";
        this.outputs.ew_lights.val = "RED";
        this.outputs.timer_7seg.val = 10;
        this.outputs.fsm_state.val = "S_PED_WALK (101)";
        this.outputs.fault_supervisor.val = "ALL-RED MUTEX ACTIVE";
        return;
      }

      // Dynamic Green Splits
      const qNS = qN + qS;
      const qEW = qE + qW;
      let gNS = Math.max(10, Math.min(45, Math.round((qNS / Math.max(1, qNS + qEW)) * 55)));
      let gEW = Math.max(10, Math.min(45, Math.round((qEW / Math.max(1, qNS + qEW)) * 55)));

      if (qEW > qNS * 1.5) {
        this.outputs.ns_lights.val = "RED";
        this.outputs.ew_lights.val = "GREEN";
        this.outputs.timer_7seg.val = gEW;
        this.outputs.fsm_state.val = "S_EW_GREEN (011)";
      } else {
        this.outputs.ns_lights.val = "GREEN";
        this.outputs.ew_lights.val = "RED";
        this.outputs.timer_7seg.val = gNS;
        this.outputs.fsm_state.val = "S_NS_GREEN (001)";
      }
      this.outputs.fault_supervisor.val = "NOMINAL (MUTEX LOCKED)";
    },
    renderVisualOverlay: function() {
      const qTot = this.outputs.approach_queues.val;
      const fsm = this.outputs.fsm_state.val;
      const cong = this.outputs.congestion_score.val;
      const timer = this.outputs.timer_7seg.val;
      const isEmg = this.inputs.emergency_override.val === 1;
      const emgDir = this.inputs.emergency_dir.val;

      // Parse selected vehicle ID
      const vehMatch = this.inputs.selected_vehicle.val.match(/V(\d+)/);
      const vId = vehMatch ? parseInt(vehMatch[1], 10) : 0;
      const vInfo = this._vehicles[vId] || this._vehicles[0];

      return `
        <div style="font-size:10px; font-family:var(--font-mono); color:#e6edf3; display:grid; grid-template-columns: 1fr 1fr; gap:8px; max-width:620px; background:rgba(10,14,20,0.85); padding:8px; border:1px solid #1e2638; border-radius:4px;">
          <!-- Panel 1: Intersection Visual -->
          <div style="border-right:1px solid #1e2638; padding-right:8px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">1. INTERSECTION TOPOLOGY</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>NS SIGNAL:</span>
              <span style="font-weight:700; color:${getColorHex(this.outputs.ns_lights.val)}">${this.outputs.ns_lights.val}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>EW SIGNAL:</span>
              <span style="font-weight:700; color:${getColorHex(this.outputs.ew_lights.val)}">${this.outputs.ew_lights.val}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>REMAINING:</span>
              <span style="color:#ffb800; font-weight:700;">${timer}s</span>
            </div>
            <div style="font-size:9px; color:#8b949e; margin-top:4px; line-height:1.2;">
              APPROACHES: [N: 4 CH] [S: 4 CH] [E: 4 CH] [W: 4 CH]<br/>
              QUEUES: ${qTot}
            </div>
          </div>

          <!-- Panel 2: FPGA Hardware Telemetry -->
          <div>
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">2. FPGA TELEMETRY & HARDWARE</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>FPGA MODE:</span>
              <span style="color:#00ff88; font-weight:700;">AUTHORITATIVE PL</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>FSM STATE:</span>
              <span style="color:#58a6ff;">${fsm}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>LATENCY:</span>
              <span>18 clock cycles (180 ns)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>CONGESTION:</span>
              <span style="font-weight:700; color:${cong.includes('HEAVY') ? '#ff3344' : '#00ff88'};">${cong}</span>
            </div>
          </div>

          <!-- Panel 3: Emergency & Pedestrian -->
          <div style="border-right:1px solid #1e2638; padding-right:8px; border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">3. EMERGENCY & PRIORITY</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>STATUS:</span>
              <span style="color:${isEmg ? '#ff3344' : '#8b949e'}; font-weight:700;">${isEmg ? 'CORRIDOR ACTIVE' : 'NOMINAL'}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>DIRECTION:</span>
              <span>${isEmg ? emgDir : 'STANDBY'}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>OVERRIDE:</span>
              <span>${isEmg ? 'PREEMPTION LOCK' : 'ADAPTIVE SPLIT'}</span>
            </div>
          </div>

          <!-- Panel 4: Selected Vehicle Engine -->
          <div style="border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">4. VEHICLE KINEMATICS (CH ${vId})</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>LANE/APPROACH:</span>
              <span style="color:#79c0ff;">${vInfo.lane} (Lane 1)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>POSITION / VEL:</span>
              <span>${vInfo.x} m / ${vInfo.v} m/s</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>SAFETY STATUS:</span>
              <span style="color:#00ff88;">d_safe > 15m (SAFE)</span>
            </div>
          </div>
        </div>
      `;
    }
  },

  ROVER: {
    id: "ROVER",
    name: "MARS ROVER",
    desc: "MOTOR DRIVE & STEERING PWM CONTROLLER",
    image: "C:/Users/karti/.gemini/antigravity-ide/brain/77403d67-de93-430a-ad8f-69bfb3fae9ec/mars_rover_project_1791213943927.jpg",
    inputs: {
      rst_n: { type: "switch", label: "rst_n", desc: "Active-Low Reset Pin", val: 1 },
      drive_enable: { type: "switch", label: "drive_enable", desc: "H-Bridge Gate Driver Enable", val: 1 },
      dir_select: { type: "bus_select", options: ["00 (FWD)", "01 (REV)", "10 (PIVOT_L)", "11 (PIVOT_R)"], label: "dir_select [1:0]", desc: "Direction Register", val: "00 (FWD)" },
      speed_duty: { type: "bus_range", min: 0, max: 255, label: "speed_duty [7:0]", desc: "8-bit PWM Counter Top", val: 180 },
      obstacle_detect: { type: "binary", label: "obstacle_detect", desc: "Proximity Sensor Trip Pin", val: 0 }
    },
    outputs: {
      left_motor_pwm: { type: "badge", label: "left_motor_pwm", desc: "Left Motor PWM Output", val: "70.6% @ 20kHz" },
      right_motor_pwm: { type: "badge", label: "right_motor_pwm", desc: "Right Motor PWM Output", val: "70.6% @ 20kHz" },
      left_dir_out: { type: "badge", label: "left_dir_out", desc: "Left Bridge Direction Pin", val: "CW (0)" },
      right_dir_out: { type: "badge", label: "right_dir_out", desc: "Right Bridge Direction Pin", val: "CW (0)" },
      brake_active: { type: "led", color: "red", label: "brake_active", desc: "Emergency Brake Clamp LED", val: 0 },
      duty_7seg: { type: "seven_seg", label: "duty_7seg [6:0]", desc: "Active Duty Cycle Readout (%)", val: 71 }
    },
    evaluate: function() {
      if (this.inputs.rst_n.val === 0 || this.inputs.drive_enable.val === 0) {
        this.outputs.left_motor_pwm.val = "0.0% (DISABLED)";
        this.outputs.right_motor_pwm.val = "0.0% (DISABLED)";
        this.outputs.brake_active.val = 1;
        this.outputs.duty_7seg.val = 0;
        return;
      }
      if (this.inputs.obstacle_detect.val === 1) {
        // Obstacle interlock
        this.outputs.left_motor_pwm.val = "0.0% (HALT)";
        this.outputs.right_motor_pwm.val = "0.0% (HALT)";
        this.outputs.brake_active.val = 1;
        this.outputs.duty_7seg.val = 0;
        return;
      }
      this.outputs.brake_active.val = 0;
      const dutyPct = Math.round((this.inputs.speed_duty.val / 255) * 100);
      this.outputs.duty_7seg.val = dutyPct;
      
      const dir = this.inputs.dir_select.val;
      if (dir.includes("00")) {
        this.outputs.left_dir_out.val = "CW (0)";
        this.outputs.right_dir_out.val = "CW (0)";
        this.outputs.left_motor_pwm.val = `${dutyPct}% @ 20kHz`;
        this.outputs.right_motor_pwm.val = `${dutyPct}% @ 20kHz`;
      } else if (dir.includes("01")) {
        this.outputs.left_dir_out.val = "CCW (1)";
        this.outputs.right_dir_out.val = "CCW (1)";
        this.outputs.left_motor_pwm.val = `${dutyPct}% @ 20kHz`;
        this.outputs.right_motor_pwm.val = `${dutyPct}% @ 20kHz`;
      } else if (dir.includes("10")) {
        this.outputs.left_dir_out.val = "CCW (1)";
        this.outputs.right_dir_out.val = "CW (0)";
        this.outputs.left_motor_pwm.val = `${dutyPct}% @ 20kHz`;
        this.outputs.right_motor_pwm.val = `${dutyPct}% @ 20kHz`;
      } else {
        this.outputs.left_dir_out.val = "CW (0)";
        this.outputs.right_dir_out.val = "CCW (1)";
        this.outputs.left_motor_pwm.val = `${dutyPct}% @ 20kHz`;
        this.outputs.right_motor_pwm.val = `${dutyPct}% @ 20kHz`;
      }
    },
    renderVisualOverlay: function() {
      return `
        <div style="font-size:11px; font-family:var(--font-mono); color:#fff; display:flex; flex-direction:column; gap:6px;">
          <div style="color:var(--text-cyan); font-weight:600; border-bottom:1px solid #2d3848; padding-bottom:4px;">DRIVE BRIDGE OUTPUT</div>
          <div>L-MOTOR PWM: <span style="color:var(--text-cyan); font-weight:700;">${this.outputs.left_motor_pwm.val}</span></div>
          <div>R-MOTOR PWM: <span style="color:var(--text-cyan); font-weight:700;">${this.outputs.right_motor_pwm.val}</span></div>
          <div>BRAKE CLAMP: <span style="font-weight:700; color:${this.outputs.brake_active.val ? '#ff3344' : '#00ff88'}">${this.outputs.brake_active.val ? 'ENGAGED' : 'RELEASED'}</span></div>
          <div>DUTY READOUT: <span style="color:#ff3344; font-weight:700;">${this.outputs.duty_7seg.val}%</span></div>
        </div>
      `;
    }
  },

  ANDROID: {
    id: "ANDROID",
    name: "ANDROID",
    desc: "ROBOTIC JOINT SERVO & ACTUATOR CONTROLLER",
    image: "C:/Users/karti/.gemini/antigravity-ide/brain/77403d67-de93-430a-ad8f-69bfb3fae9ec/android_fpga_project_1791213918511.jpg",
    inputs: {
      rst_n: { type: "switch", label: "rst_n", desc: "Master Reset Pin", val: 1 },
      joint_enable: { type: "switch", label: "joint_enable", desc: "Actuator Power Rail Gate", val: 1 },
      actuator_select: { type: "bus_select", options: ["00 (HEAD)", "01 (SHOULDER)", "10 (ELBOW)", "11 (WRIST)"], label: "actuator_select [1:0]", desc: "Joint Axis Decoder", val: "01 (SHOULDER)" },
      target_pos: { type: "bus_range", min: 0, max: 180, label: "target_pos [7:0]", desc: "8-bit Angular Position (0-180°)", val: 90 },
      calib_mode: { type: "switch", label: "calib_mode", desc: "Index Sensor Calibration Flag", val: 0 }
    },
    outputs: {
      servo_pwm_out: { type: "badge", label: "servo_pwm_out", desc: "50Hz Precision Pulse Width", val: "1500 us (50Hz)" },
      pos_reached_led: { type: "led", color: "green", label: "pos_reached_led", desc: "Target Angle Tolerance Lock", val: 1 },
      fault_led: { type: "led", color: "red", label: "fault_led", desc: "Tracking / Overcurrent Trip", val: 0 },
      angle_7seg: { type: "seven_seg", label: "angle_7seg [6:0]", desc: "Current Joint Angle (°)", val: 90 }
    },
    evaluate: function() {
      if (this.inputs.rst_n.val === 0 || this.inputs.joint_enable.val === 0) {
        this.outputs.servo_pwm_out.val = "0 us (OFF)";
        this.outputs.pos_reached_led.val = 0;
        this.outputs.fault_led.val = 0;
        this.outputs.angle_7seg.val = 0;
        return;
      }
      if (this.inputs.calib_mode.val === 1) {
        this.outputs.servo_pwm_out.val = "1000 us (ZERO_INDEX)";
        this.outputs.pos_reached_led.val = 1;
        this.outputs.fault_led.val = 0;
        this.outputs.angle_7seg.val = 0;
        return;
      }
      const deg = parseInt(this.inputs.target_pos.val, 10);
      const pulseWidthUs = Math.round(1000 + (deg / 180) * 1000);
      this.outputs.servo_pwm_out.val = `${pulseWidthUs} us (50Hz)`;
      this.outputs.angle_7seg.val = deg;
      this.outputs.pos_reached_led.val = 1;
      this.outputs.fault_led.val = deg > 175 ? 1 : 0;
    },
    renderVisualOverlay: function() {
      return `
        <div style="font-size:11px; font-family:var(--font-mono); color:#fff; display:flex; flex-direction:column; gap:6px;">
          <div style="color:var(--text-cyan); font-weight:600; border-bottom:1px solid #2d3848; padding-bottom:4px;">ACTUATOR STATUS</div>
          <div>SERVO PWM  : <span style="color:var(--text-cyan); font-weight:700;">${this.outputs.servo_pwm_out.val}</span></div>
          <div>LOCK STATUS: <span style="font-weight:700; color:${this.outputs.pos_reached_led.val ? '#00ff88' : '#ff3344'}">${this.outputs.pos_reached_led.val ? 'LOCKED' : 'SEEKING'}</span></div>
          <div>FAULT ALARM: <span style="font-weight:700; color:${this.outputs.fault_led.val ? '#ff3344' : '#545d68'}">${this.outputs.fault_led.val ? 'OVERTRAVEL' : 'NOMINAL'}</span></div>
          <div>ANGLE ANGLE: <span style="color:#ff3344; font-weight:700;">${this.outputs.angle_7seg.val}°</span></div>
        </div>
      `;
    }
  },

  MARS: {
    id: "MARS",
    name: "MARS SPACE HABITAT & LANDING DEFENSE",
    desc: "EDGE ZYNQ Z7010 FPGA REAL-TIME DESCENT DYNAMICS & 8-CHANNEL METEORITE ENGINE",
    image: "C:/Users/karti/.gemini/antigravity-ide/brain/486275dd-e9e2-4460-967c-1e8c5ef04ba4/mars_habitat_project_1791306821523.jpg",
    inputs: {
      rst_n: { type: "switch", label: "rst_n", desc: "Master Reset Pin", val: 1 },
      op_mode: { type: "bus_select", options: ["FPGA HARDWARE MODE (Authoritative PL)", "SOFTWARE SIMULATION MODE"], label: "op_mode", desc: "Hardware Execution Authority", val: "FPGA HARDWARE MODE (Authoritative PL)" },
      landing_enable: { type: "switch", label: "landing_enable", desc: "Descent Dynamics & Throttle Closed-Loop", val: 1 },
      spacecraft_mass: { type: "bus_range", min: 500, max: 2500, label: "mass [kg]", desc: "Lander Wet Mass (m)", val: 1200 },
      retro_thrust_cmd: { type: "bus_range", min: 0, max: 100, label: "retro_thrust [%]", desc: "Manual Throttle Bias / Cap", val: 65 },
      meteor_parallel_en: { type: "switch", label: "meteor_parallel_en", desc: "8-Channel Parallel Hardware Engines", val: 1 },
      selected_meteor: { type: "bus_select", options: ["CH 0 (Normal)", "CH 1 (Fast)", "CH 2 (Heavy)", "CH 3 (Section A Vector)", "CH 4 (Section B Vector)", "CH 5 (Glancing)", "CH 6 (High Kinetic)", "CH 7 (Critical Swarm)"], label: "meteor_channel", desc: "Active Meteorite Telemetry Selector", val: "CH 0 (Normal)" },
      threat_scenario: { type: "bus_select", options: ["NOMINAL (Scattered Dust)", "SECTOR A DIRECT INGRESS", "SECTOR B CRITICAL BREACH", "8-CHANNEL SIMULTANEOUS SWARM"], label: "threat_scenario", desc: "Meteorite Ingress Threat Profile", val: "NOMINAL (Scattered Dust)" },
      isolation_override: { type: "bus_select", options: ["AUTO HARDWARE ISOLATION", "FORCE SECTION A SEAL", "FORCE SECTION B SEAL", "ALL SECTIONS OPEN"], label: "isolation_ctrl", desc: "Hull Bulkhead Isolation Override", val: "AUTO HARDWARE ISOLATION" }
    },
    outputs: {
      landing_stage: { type: "badge", label: "landing_stage [3:0]", desc: "FSM Landing Stage", val: "POWERED DESCENT (0001)" },
      landing_altitude: { type: "seven_seg", label: "altitude [15:0]", desc: "Radar Altitude h (m)", val: 420 },
      descent_velocity: { type: "badge", label: "velocity [15:0]", desc: "Vertical Velocity v (m/s)", val: "-14.2 m/s" },
      thrust_telemetry: { type: "badge", label: "thrust_n [15:0]", desc: "Adaptive Retro-Thrust T (N)", val: "5,820 N (58.2%)" },
      touchdown_flag: { type: "badge", label: "touchdown", desc: "Touchdown Sensor State", val: "IN DESCENT" },
      active_meteorites: { type: "badge", label: "active_meteors [7:0]", desc: "8-Channel Active Bitmask", val: "0xFF (8 ACTIVE)" },
      impact_energy: { type: "badge", label: "impact_energy [31:0]", desc: "Total Kinetic Energy E=½mv²", val: "142.5 kJ" },
      section_a_status: { type: "badge", label: "section_A_status", desc: "Section A Hull Integrity & Seal", val: "SEALED / NOMINAL (96%)" },
      section_b_status: { type: "badge", label: "section_B_status", desc: "Section B Hull Integrity & Seal", val: "SEALED / NOMINAL (94%)" },
      life_support: { type: "badge", label: "life_support [31:0]", desc: "O2 / Pressure / Health", val: "O2: 21.0% | P: 101.3 kPa" },
      fault_supervisor: { type: "badge", label: "fault_flags [15:0]", desc: "Hardware Safety Supervisor", val: "0x0000 (NOMINAL)" }
    },
    _meteors: [
      { id: 0, x: 120, y: 85, z: 450, vx: -12, vy: -8, vz: -45, mass: 2.5, radius: 0.15, active: true, impact: false, section: "A", energy_kj: 2.7, severity: "LOW" },
      { id: 1, x: -80, y: 110, z: 520, vx: 8, vy: -10, vz: -55, mass: 3.8, radius: 0.20, active: true, impact: false, section: "B", energy_kj: 6.2, severity: "MODERATE" },
      { id: 2, x: 45, y: -95, z: 380, vx: -5, vy: 9, vz: -60, mass: 5.2, radius: 0.25, active: true, impact: false, section: "A", energy_kj: 9.8, severity: "MODERATE" },
      { id: 3, x: -110, y: -70, z: 610, vx: 11, vy: 7, vz: -70, mass: 1.8, radius: 0.12, active: true, impact: false, section: "B", energy_kj: 4.6, severity: "LOW" },
      { id: 4, x: 200, y: 150, z: 750, vx: -18, vy: -14, vz: -80, mass: 8.5, radius: 0.35, active: true, impact: false, section: "A", energy_kj: 29.8, severity: "HIGH" },
      { id: 5, x: -160, y: 180, z: 820, vx: 15, vy: -16, vz: -85, mass: 4.0, radius: 0.22, active: true, impact: false, section: "B", energy_kj: 15.6, severity: "HIGH" },
      { id: 6, x: 90, y: -140, z: 490, vx: -9, vy: 13, vz: -50, mass: 6.1, radius: 0.28, active: true, impact: false, section: "A", energy_kj: 8.4, severity: "MODERATE" },
      { id: 7, x: -30, y: 40, z: 290, vx: 3, vy: -4, vz: -35, mass: 12.0, radius: 0.40, active: true, impact: false, section: "B", energy_kj: 7.7, severity: "HIGH" }
    ],
    evaluate: function() {
      if (this.inputs.rst_n.val === 0) {
        this.outputs.landing_stage.val = "RESET (0000)";
        this.outputs.landing_altitude.val = 0;
        this.outputs.descent_velocity.val = "0.0 m/s";
        this.outputs.thrust_telemetry.val = "0 N (0.0%)";
        this.outputs.touchdown_flag.val = "RESET STATE";
        this.outputs.active_meteorites.val = "0x00 (0 ACTIVE)";
        this.outputs.impact_energy.val = "0.0 kJ";
        this.outputs.section_a_status.val = "OFFLINE (RESET)";
        this.outputs.section_b_status.val = "OFFLINE (RESET)";
        this.outputs.life_support.val = "OFFLINE";
        this.outputs.fault_supervisor.val = "0x0001 (RESET ASSERTED)";
        return;
      }

      const isLandingEn = this.inputs.landing_enable.val === 1;
      const mass = parseFloat(this.inputs.spacecraft_mass.val);
      const thrustPct = parseFloat(this.inputs.retro_thrust_cmd.val);
      const gMars = 3.721; // m/s^2

      // Discrete-time descent dynamics
      let alt = 420.0;
      let vel = -14.2;
      let accel = 0.0;
      let thrustN = 0.0;
      let fsmStage = "POWERED DESCENT (0001)";
      let tdState = "IN DESCENT";

      if (isLandingEn) {
        const maxThrust = 10000.0; // 10 kN max retro-engine
        thrustN = (thrustPct / 100.0) * maxThrust;
        const netForce = thrustN - (mass * gMars);
        accel = netForce / mass; // a = (T - mg)/m
        accel = Math.max(-10.0, Math.min(10.0, accel));

        // Simulated current altitude based on mass and thrust balance
        if (thrustPct > 70) {
          vel = -4.5;
          alt = 85.0;
          fsmStage = "APPROACH (0010)";
        } else if (thrustPct >= 45) {
          vel = -14.2;
          alt = 420.0;
          fsmStage = "POWERED DESCENT (0001)";
        } else {
          vel = -28.6;
          alt = 1250.0;
          fsmStage = "PREP / FREE-FALL (0000)";
        }

        if (alt <= 2.0 || thrustPct === 0) {
          tdState = "TOUCHDOWN CONFIRMED";
          fsmStage = "TOUCHDOWN (0011)";
        }
      } else {
        thrustN = 0.0;
        accel = -gMars;
        vel = -25.0;
        alt = 1500.0;
        fsmStage = "STANDBY (0000)";
        tdState = "THRUST DISABLED";
      }

      this.outputs.landing_stage.val = fsmStage;
      this.outputs.landing_altitude.val = Math.round(alt);
      this.outputs.descent_velocity.val = `${vel.toFixed(1)} m/s (acc: ${accel >= 0 ? '+' : ''}${accel.toFixed(2)} m/s²)`;
      this.outputs.thrust_telemetry.val = `${Math.round(thrustN).toLocaleString()} N (${((thrustN / 10000) * 100).toFixed(1)}%)`;
      this.outputs.touchdown_flag.val = tdState;

      // 8-channel meteorite threat evaluation
      const scenario = this.inputs.threat_scenario.val;
      const meteorEn = this.inputs.meteor_parallel_en.val === 1;
      let totalEnergyKj = 0;
      let activeMask = 0;
      let secADamage = 4; // base 4% nominal
      let secBDamage = 6; // base 6% nominal

      this._meteors.forEach((m, idx) => {
        m.active = meteorEn;
        if (meteorEn) activeMask |= (1 << idx);

        if (scenario.includes("SECTOR A") && (idx === 0 || idx === 2 || idx === 4)) {
          m.impact = true;
          secADamage += Math.round(m.energy_kj * 1.5);
        } else if (scenario.includes("SECTOR B") && (idx === 1 || idx === 3 || idx === 7)) {
          m.impact = true;
          secBDamage += Math.round(m.energy_kj * 1.8);
        } else if (scenario.includes("SWARM")) {
          m.impact = true;
          secADamage += Math.round(m.energy_kj * 0.8);
          secBDamage += Math.round(m.energy_kj * 0.8);
        } else {
          m.impact = false;
        }

        const vTotSq = m.vx * m.vx + m.vy * m.vy + m.vz * m.vz;
        m.energy_kj = parseFloat(((0.5 * m.mass * vTotSq) / 1000).toFixed(1));
        totalEnergyKj += m.energy_kj;

        if (m.energy_kj < 5.0) m.severity = "LOW";
        else if (m.energy_kj < 15.0) m.severity = "MODERATE";
        else if (m.energy_kj < 25.0) m.severity = "HIGH";
        else m.severity = "CRITICAL";
      });

      secADamage = Math.min(100, secADamage);
      secBDamage = Math.min(100, secBDamage);

      this.outputs.active_meteorites.val = `0x${activeMask.toString(16).toUpperCase().padStart(2, '0')} (${meteorEn ? '8 ACTIVE' : 'DISABLED'})`;
      this.outputs.impact_energy.val = `${totalEnergyKj.toFixed(1)} kJ (8 CHANNELS)`;

      // Bulkhead isolation FSM
      const isoOverride = this.inputs.isolation_override.val;
      let secAState = "SEALED / NOMINAL";
      let secBState = "SEALED / NOMINAL";

      if (isoOverride.includes("SECTION A") || secADamage >= 40) {
        secAState = secADamage >= 80 ? "CRITICAL BREACH / ISOLATED" : "BULKHEAD ISOLATED";
      } else {
        secAState = secADamage >= 25 ? "MINOR DAMAGE (ACTIVE)" : "NOMINAL";
      }

      if (isoOverride.includes("SECTION B") || secBDamage >= 40) {
        secBState = secBDamage >= 80 ? "CRITICAL BREACH / ISOLATED" : "BULKHEAD ISOLATED";
      } else {
        secBState = secBDamage >= 25 ? "MINOR DAMAGE (ACTIVE)" : "NOMINAL";
      }

      this.outputs.section_a_status.val = `${secAState} (${100 - secADamage}% HP)`;
      this.outputs.section_b_status.val = `${secBState} (${100 - secBDamage}% HP)`;

      // Life support computation
      const o2 = Math.max(14.0, 21.0 - (secADamage + secBDamage) * 0.05).toFixed(1);
      const press = Math.max(70.0, 101.3 - (secADamage + secBDamage) * 0.2).toFixed(1);
      this.outputs.life_support.val = `O2: ${o2}% | P: ${press} kPa | COMPOSITE: ${Math.round(100 - (secADamage + secBDamage) / 2)}%`;

      // Fault flags
      let faultBits = 0x0000;
      if (Math.abs(vel) > 20.0 && alt < 500) faultBits |= 0x0002; // Excessive descent velocity
      if (secADamage >= 60 || secBDamage >= 60) faultBits |= 0x0004; // Structural hull breach
      if (parseFloat(press) < 85.0) faultBits |= 0x0008; // Cabin depressurization

      this.outputs.fault_supervisor.val = faultBits === 0 ? "0x0000 (NOMINAL)" : `0x${faultBits.toString(16).toUpperCase().padStart(4, '0')} (LIMIT TRIP)`;
    },
    renderVisualOverlay: function() {
      const mode = this.inputs.op_mode.val;
      const isHw = mode.includes("HARDWARE");
      const alt = this.outputs.landing_altitude.val;
      const velText = this.outputs.descent_velocity.val;
      const thrustText = this.outputs.thrust_telemetry.val;
      const fsmStage = this.outputs.landing_stage.val;
      const tdState = this.outputs.touchdown_flag.val;

      const chMatch = this.inputs.selected_meteor.val.match(/CH (\d+)/);
      const chId = chMatch ? parseInt(chMatch[1], 10) : 0;
      const selM = this._meteors[chId] || this._meteors[0];

      return `
        <div style="font-size:10px; font-family:var(--font-mono); color:#e6edf3; display:grid; grid-template-columns: 1fr 1fr; gap:8px; max-width:680px; background:rgba(10,14,20,0.92); padding:10px; border:1px solid #1e2638; border-radius:6px;">
          <!-- Master Mode Header Banner -->
          <div style="grid-column: 1 / -1; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e2638; padding-bottom:6px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${isHw ? '#00ff88' : '#ffb800'}; box-shadow:0 0 8px ${isHw ? '#00ff88' : '#ffb800'};"></span>
              <span style="font-weight:700; color:${isHw ? '#00ff88' : '#ffb800'}; letter-spacing:0.5px;">
                ${isHw ? 'FPGA HARDWARE MODE (AUTHORITATIVE PL)' : 'SOFTWARE SIMULATION MODE'}
              </span>
            </div>
            <div style="font-size:9px; color:#8b949e;">
              EDGE ZYNQ Z7010 (XC7Z010) @ AXI 0x43C20000
            </div>
          </div>

          <!-- Panel A: Landing Visualization -->
          <div style="border-right:1px solid #1e2638; padding-right:8px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">A. LANDING VISUALIZATION</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>SPACECRAFT ALTITUDE:</span>
              <span style="color:#ffb800; font-weight:700;">${alt} m (RADAR)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>DESCENT VELOCITY:</span>
              <span style="color:${velText.includes('-2') ? '#ff3344' : '#58a6ff'}; font-weight:700;">${velText}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>RETRO-THRUST:</span>
              <span style="color:#00ff88; font-weight:700;">${thrustText}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>LANDING FSM:</span>
              <span style="color:#79c0ff; font-weight:700;">${fsmStage}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>TOUCHDOWN STATE:</span>
              <span style="color:${tdState.includes('CONFIRMED') ? '#00ff88' : '#ffb800'}; font-weight:700;">${tdState}</span>
            </div>
          </div>

          <!-- Panel B: Landing Telemetry -->
          <div>
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">B. LANDING TELEMETRY (DYNAMICS)</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>DYNAMICS EQUATION:</span>
              <span style="color:#8b949e;">a = (T - mg) / m</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>MARS GRAVITY (g):</span>
              <span style="color:#e6edf3;">3.721 m/s² (FIXED-POINT)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>DESCENT RISK:</span>
              <span style="color:${this.outputs.fault_supervisor.val.includes('0x0002') ? '#ff3344' : '#00ff88'}; font-weight:700;">
                ${this.outputs.fault_supervisor.val.includes('0x0002') ? 'HIGH VELOCITY HAZARD' : 'NOMINAL DESCENT'}
              </span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>LANDING STATUS:</span>
              <span style="color:#00ff88; font-weight:700;">CLOSED-LOOP ADAPTIVE</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>TOUCHDOWN SENSOR:</span>
              <span style="color:#58a6ff;">h &lt; 1.0 m &amp; |v| &lt; 2.0 m/s</span>
            </div>
          </div>

          <!-- Panel C: Meteorite Field (8-Channel Parallel Hardware Engines) -->
          <div style="border-right:1px solid #1e2638; padding-right:8px; border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">C. 8-CH PARALLEL METEORITE FIELD</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>INSPECTED CHANNEL:</span>
              <span style="color:#ffb800; font-weight:700;">CH ${chId} (${selM.section} TGT, ${selM.mass} kg)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>POSITION [X, Y, Z]:</span>
              <span style="color:#e6edf3;">[${selM.x}, ${selM.y}, ${selM.z}] m</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>VELOCITY [Vx,Vy,Vz]:</span>
              <span style="color:#e6edf3;">[${selM.vx}, ${selM.vy}, ${selM.vz}] m/s</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>ACTIVE / IMPACT:</span>
              <span style="color:${selM.impact ? '#ff3344' : '#00ff88'}; font-weight:700;">
                ${selM.active ? 'ACTIVE' : 'IDLE'} | ${selM.impact ? 'COLLISION' : 'EN ROUTE'}
              </span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>ACTIVE CHANNELS:</span>
              <span style="color:#79c0ff; font-weight:700;">${this.outputs.active_meteorites.val}</span>
            </div>
          </div>

          <!-- Panel D: Impact Monitor -->
          <div style="border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">D. IMPACT KINETIC ENERGY ENGINE</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>CH ${chId} KINETIC ENERGY:</span>
              <span style="color:#ffb800; font-weight:700;">${selM.energy_kj} kJ (E = ½mv²)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>IMPACT SEVERITY:</span>
              <span style="color:${selM.severity === 'CRITICAL' ? '#ff3344' : (selM.severity === 'HIGH' ? '#ffb800' : '#00ff88')}; font-weight:700;">
                ${selM.severity}
              </span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>TOTAL IMPACT ENERGY:</span>
              <span style="color:#79c0ff; font-weight:700;">${this.outputs.impact_energy.val}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>AFFECTED TARGET:</span>
              <span style="color:#e6edf3;">HABITAT SECTOR ${selM.section}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>RADAR COLLISION THRESH:</span>
              <span style="color:#8b949e;">r &le; 10.0 m (3D EUCLIDEAN)</span>
            </div>
          </div>

          <!-- Panel E: Habitat Status -->
          <div style="border-right:1px solid #1e2638; padding-right:8px; border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">E. HABITAT DAMAGE & ISOLATION FSM</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>SECTION A STATUS:</span>
              <span style="color:${this.outputs.section_a_status.val.includes('CRITICAL') ? '#ff3344' : (this.outputs.section_a_status.val.includes('ISOLATED') ? '#ffb800' : '#00ff88')}; font-weight:700;">
                ${this.outputs.section_a_status.val}
              </span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>SECTION B STATUS:</span>
              <span style="color:${this.outputs.section_b_status.val.includes('CRITICAL') ? '#ff3344' : (this.outputs.section_b_status.val.includes('ISOLATED') ? '#ffb800' : '#00ff88')}; font-weight:700;">
                ${this.outputs.section_b_status.val}
              </span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>ISOLATION COMMAND:</span>
              <span style="color:#79c0ff;">${this.inputs.isolation_override.val}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>INTER-SECTOR LINK:</span>
              <span style="color:${this.outputs.section_a_status.val.includes('ISOLATED') || this.outputs.section_b_status.val.includes('ISOLATED') ? '#ffb800' : '#00ff88'}; font-weight:700;">
                ${this.outputs.section_a_status.val.includes('ISOLATED') || this.outputs.section_b_status.val.includes('ISOLATED') ? 'LINK ISOLATED (AIRTIGHT)' : 'PRESSURIZED LINK OPEN'}
              </span>
            </div>
          </div>

          <!-- Panel F: Life Support & Environmental -->
          <div style="border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">F. LIFE SUPPORT & ENVIRONMENT</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>LIFE SUPPORT:</span>
              <span style="color:#00ff88; font-weight:700;">${this.outputs.life_support.val}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>CABIN ENVIRONMENT:</span>
              <span style="color:#e6edf3;">T: 21.4°C | CO2: 0.04%</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>ATMOSPHERIC DRAG:</span>
              <span style="color:#8b949e;">&rho; = 0.020 kg/m³ | Cd = 1.05</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>THERMAL RISK:</span>
              <span style="color:#00ff88; font-weight:700;">NOMINAL (LOAD &lt; 15 kW)</span>
            </div>
          </div>

          <!-- Panel G: FPGA Hardware Telemetry -->
          <div style="grid-column: 1 / -1; border-top:1px solid #1e2638; padding-top:6px; display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
            <div>
              <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">G. FPGA STATUS & FAULT SUPERVISOR</div>
              <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                <span>FPGA LINK:</span>
                <span style="color:${isHw ? '#00ff88' : '#79c0ff'}; font-weight:700;">${isHw ? 'ONLINE (AXI4-LITE MEM)' : 'EMULATED INTERFACE'}</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                <span>CORE VERSION:</span>
                <span style="color:#ffb800; font-weight:700;">0x4D415253 ("MARS" v2.0)</span>
              </div>
            </div>
            <div>
              <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                <span>PIPELINE LATENCY:</span>
                <span style="color:#ffb800; font-weight:700;">18 cycles (180 ns @ 100MHz)</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                <span>UPDATE RATE:</span>
                <span style="color:#00ff88; font-weight:700;">100 Hz (DETERMINISTIC PL)</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                <span>FAULT SUPERVISOR:</span>
                <span style="color:${this.outputs.fault_supervisor.val.includes('0x0000') ? '#00ff88' : '#ff3344'}; font-weight:700;">
                  ${this.outputs.fault_supervisor.val}
                </span>
              </div>
            </div>
          </div>
        </div>
      `;
    }
  },

  SOLAR: {
    id: "SOLAR",
    name: "SOLAR TRACKING GIMBAL",
    desc: "EDGE ZYNQ Z7010 FPGA 4-PANEL PARALLEL VECTOR & POWER ENGINE",
    image: "C:/Users/karti/.gemini/antigravity-ide/brain/486275dd-e9e2-4460-967c-1e8c5ef04ba4/solar_gimbal_project_1791305820333.jpg",
    inputs: {
      rst_n: { type: "switch", label: "rst_n", desc: "Active-Low Reset Pin", val: 1 },
      track_en: { type: "switch", label: "track_en", desc: "Hardware Tracking Closed-Loop Strobe", val: 1 },
      sun_azimuth: { type: "bus_range", min: 0, max: 360, label: "sun_azimuth [15:0]", desc: "Sun Target Azimuth (°)", val: 180 },
      sun_elevation: { type: "bus_range", min: 0, max: 90, label: "sun_elevation [15:0]", desc: "Sun Target Elevation (°)", val: 45 },
      panel_azimuth: { type: "bus_range", min: 0, max: 360, label: "panel_azimuth [15:0]", desc: "Gimbal Current Azimuth (°)", val: 175 },
      panel_elevation: { type: "bus_range", min: 0, max: 90, label: "panel_elevation [15:0]", desc: "Gimbal Current Elevation (°)", val: 40 },
      deadband: { type: "bus_select", options: ["0.5° (TIGHT)", "1.0° (NORMAL)", "2.0° (WIDE)"], label: "deadband [15:0]", desc: "Tracking Deadband Tolerance", val: "0.5° (TIGHT)" },
      multi_panel_en: { type: "switch", label: "multi_panel_en", desc: "4-Channel Parallel Array Engine", val: 1 },
      selected_channel: { type: "bus_select", options: ["PANEL 0 (Master)", "PANEL 1 (+1.0° Offset)", "PANEL 2 (+2.0° Offset)", "PANEL 3 (+3.0° Offset)"], label: "selected_channel", desc: "Array Channel Inspector", val: "PANEL 0 (Master)" }
    },
    outputs: {
      az_action: { type: "badge", label: "az_action", desc: "Azimuth Stepper Direction", val: "CW STEP (+5.0°)" },
      el_action: { type: "badge", label: "el_action", desc: "Elevation Stepper Direction", val: "UP STEP (+5.0°)" },
      incident_angle: { type: "badge", label: "incident_angle [15:0]", desc: "Arccos Incidence (θ)", val: "7.07° (cos θ = 0.992)" },
      single_power: { type: "seven_seg", label: "single_power [15:0]", desc: "Channel 0 Effective Power (W)", val: 5622 },
      total_array_power: { type: "badge", label: "total_power [31:0]", desc: "4-Panel Array Aggregated Power", val: "21,780 W (4 CHANNELS)" },
      dot_product: { type: "badge", label: "dot_product [31:0]", desc: "Cartesian Dot Product (N · S)", val: "+0.9924 (Q16.16)" },
      fsm_state: { type: "badge", label: "fsm_state [3:0]", desc: "FPGA State Machine", val: "S_TRACK (0011)" },
      tracking_quality: { type: "badge", label: "quality_score [15:0]", desc: "Hardware Alignment Quality", val: "98% (ALIGN NOMINAL)" },
      fault_supervisor: { type: "badge", label: "fault_flags [15:0]", desc: "Safety Supervisor", val: "NOMINAL (NO LIMIT TRIPS)" }
    },
    _panels: [
      { id: 0, offset_az: 0.0, offset_el: 0.0, power_w: 5622, theta_deg: 7.07, active: true },
      { id: 1, offset_az: 1.0, offset_el: 0.0, power_w: 5540, theta_deg: 8.01, active: true },
      { id: 2, offset_az: 0.0, offset_el: 1.0, power_w: 5410, theta_deg: 9.32, active: true },
      { id: 3, offset_az: 1.5, offset_el: 1.5, power_w: 5208, theta_deg: 11.20, active: true }
    ],
    evaluate: function() {
      if (this.inputs.rst_n.val === 0) {
        this.outputs.az_action.val = "RESET HOLD";
        this.outputs.el_action.val = "RESET HOLD";
        this.outputs.incident_angle.val = "0.0° (RESET)";
        this.outputs.single_power.val = 0;
        this.outputs.total_array_power.val = "0 W (OFFLINE)";
        this.outputs.dot_product.val = "0.0000";
        this.outputs.fsm_state.val = "S_RESET (0000)";
        this.outputs.tracking_quality.val = "0% (RESET)";
        this.outputs.fault_supervisor.val = "RESET ASSERTED";
        return;
      }

      const sAz = parseFloat(this.inputs.sun_azimuth.val);
      const sEl = parseFloat(this.inputs.sun_elevation.val);
      const pAz = parseFloat(this.inputs.panel_azimuth.val);
      const pEl = parseFloat(this.inputs.panel_elevation.val);

      // Section 9: Modulo-360 Azimuth Wrap-around normalization [-180, +180]
      let rawDiff = sAz - pAz;
      if (rawDiff > 180.0) rawDiff -= 360.0;
      else if (rawDiff < -180.0) rawDiff += 360.0;
      const azErr = rawDiff;
      const elErr = sEl - pEl;

      // Deadband check
      let db = 0.5;
      if (this.inputs.deadband.val.includes("1.0")) db = 1.0;
      else if (this.inputs.deadband.val.includes("2.0")) db = 2.0;

      const azHold = Math.abs(azErr) <= db;
      const elHold = Math.abs(elErr) <= db;
      const isLocked = azHold && elHold;

      const azDir = azHold ? "HOLD" : (azErr > 0 ? "CW STEP" : "CCW STEP");
      const elDir = elHold ? "HOLD" : (elErr > 0 ? "UP STEP" : "DOWN STEP");
      this.outputs.az_action.val = `${azDir} (${azErr >= 0 ? '+' : ''}${azErr.toFixed(1)}°)`;
      this.outputs.el_action.val = `${elDir} (${elErr >= 0 ? '+' : ''}${elErr.toFixed(1)}°)`;

      // 3D Cartesian Sun Vector (Sx, Sy, Sz)
      const sAzRad = (sAz * Math.PI) / 180.0;
      const sElRad = (sEl * Math.PI) / 180.0;
      const sx = Math.cos(sElRad) * Math.cos(sAzRad);
      const sy = Math.cos(sElRad) * Math.sin(sAzRad);
      const sz = Math.sin(sElRad);

      // 3D Cartesian Panel Normal Vector (Nx, Ny, Nz)
      const pAzRad = (pAz * Math.PI) / 180.0;
      const pElRad = (pEl * Math.PI) / 180.0;
      const nx = Math.cos(pElRad) * Math.cos(pAzRad);
      const ny = Math.cos(pElRad) * Math.sin(pAzRad);
      const nz = Math.sin(pElRad);

      // 3D Dot Product (D = Nx*Sx + Ny*Sy + Nz*Sz) clamped to [-1, 1]
      const dot = Math.max(-1.0, Math.min(1.0, nx * sx + ny * sy + nz * sz));
      this.outputs.dot_product.val = `${dot >= 0 ? '+' : ''}${dot.toFixed(4)} (Q16.16)`;

      // Arccos Incident Angle (theta = acos(D))
      const thetaRad = Math.acos(dot);
      const thetaDeg = (thetaRad * 180.0) / Math.PI;
      const cosClamp = Math.max(0.0, dot);
      this.outputs.incident_angle.val = `${thetaDeg.toFixed(2)}° (cos θ = ${cosClamp.toFixed(3)})`;

      // Solar Power Engine: P = I0 * A * eta * max(0, cos(theta)) = 5665 * cosClamp
      const peakPower = 5665.0; // 1361 * 18.5 * 0.225
      const singlePwr = Math.round(peakPower * cosClamp);
      this.outputs.single_power.val = singlePwr;

      // 4-Panel Parallel Array Engine
      const multiEn = this.inputs.multi_panel_en.val === 1;
      let totArrayPwr = 0;
      this._panels.forEach((p, idx) => {
        const pAzOffset = ((pAz + p.offset_az + 360.0) % 360.0) * (Math.PI / 180.0);
        const pElOffset = Math.max(0.0, Math.min(90.0, pEl + p.offset_el)) * (Math.PI / 180.0);
        const pNx = Math.cos(pElOffset) * Math.cos(pAzOffset);
        const pNy = Math.cos(pElOffset) * Math.sin(pAzOffset);
        const pNz = Math.sin(pElOffset);
        const pDot = Math.max(-1.0, Math.min(1.0, pNx * sx + pNy * sy + pNz * sz));
        const pTheta = (Math.acos(pDot) * 180.0) / Math.PI;
        const pPwr = Math.round(peakPower * Math.max(0.0, pDot));
        p.theta_deg = parseFloat(pTheta.toFixed(2));
        p.power_w = pPwr;
        p.active = multiEn || (idx === 0);
        if (p.active) totArrayPwr += pPwr;
      });

      this.outputs.total_array_power.val = `${totArrayPwr.toLocaleString()} W (${multiEn ? '4 CHANNELS' : '1 CH ACTIVE'})`;

      // Tracking quality & quality score
      const totErr = Math.sqrt(azErr * azErr + elErr * elErr);
      const qualityPct = isLocked ? 100 : Math.max(0, Math.min(100, Math.round(100 - (totErr * totErr) / 20.25)));
      this.outputs.tracking_quality.val = `${qualityPct}% (${isLocked ? 'ALIGN LOCKED' : (qualityPct > 80 ? 'NOMINAL' : 'COARSE')})`;

      // State
      this.outputs.fsm_state.val = isLocked ? "S_LOCKED (0010)" : "S_TRACK (0011)";

      // Fault supervisor
      if (pEl < 0 || pEl > 90 || sEl < 0) {
        this.outputs.fault_supervisor.val = "TRIP: ANGLE LIMIT FAULT";
      } else {
        this.outputs.fault_supervisor.val = "NOMINAL (NO LIMIT TRIPS)";
      }
    },
    renderVisualOverlay: function() {
      const sAz = parseFloat(this.inputs.sun_azimuth.val);
      const sEl = parseFloat(this.inputs.sun_elevation.val);
      const pAz = parseFloat(this.inputs.panel_azimuth.val);
      const pEl = parseFloat(this.inputs.panel_elevation.val);

      let rawDiff = sAz - pAz;
      if (rawDiff > 180.0) rawDiff -= 360.0;
      else if (rawDiff < -180.0) rawDiff += 360.0;
      const azErr = rawDiff;
      const elErr = sEl - pEl;
      const totErr = Math.sqrt(azErr * azErr + elErr * elErr);

      const sAzRad = (sAz * Math.PI) / 180.0;
      const sElRad = (sEl * Math.PI) / 180.0;
      const sx = Math.cos(sElRad) * Math.cos(sAzRad);
      const sy = Math.cos(sElRad) * Math.sin(sAzRad);
      const sz = Math.sin(sElRad);

      const pAzRad = (pAz * Math.PI) / 180.0;
      const pElRad = (pEl * Math.PI) / 180.0;
      const nx = Math.cos(pElRad) * Math.cos(pAzRad);
      const ny = Math.cos(pElRad) * Math.sin(pAzRad);
      const nz = Math.sin(pElRad);

      const dot = Math.max(-1.0, Math.min(1.0, nx * sx + ny * sy + nz * sz));
      const cosClamp = Math.max(0.0, dot);
      const thetaDeg = (Math.acos(dot) * 180.0) / Math.PI;

      const pwr = this.outputs.single_power.val;
      const arrayPwr = this.outputs.total_array_power.val;
      const pwrLoss = Math.max(0.0, 5665.0 - pwr);

      const chMatch = this.inputs.selected_channel.val.match(/PANEL (\d+)/);
      const chId = chMatch ? parseInt(chMatch[1], 10) : 0;
      const chInfo = this._panels[chId] || this._panels[0];

      return `
        <div style="font-size:10px; font-family:var(--font-mono); color:#e6edf3; display:grid; grid-template-columns: 1fr 1fr; gap:8px; max-width:640px; background:rgba(10,14,20,0.88); padding:8px; border:1px solid #1e2638; border-radius:4px;">
          <!-- Panel A: Solar / Gimbal Visualization -->
          <div style="border-right:1px solid #1e2638; padding-right:8px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">A. SOLAR & GIMBAL ORIENTATION</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>SUN DIRECTION:</span>
              <span style="color:#ffb800; font-weight:700;">AZ ${sAz.toFixed(1)}° / EL ${sEl.toFixed(1)}°</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>PANEL NORMAL:</span>
              <span style="color:#58a6ff; font-weight:700;">AZ ${pAz.toFixed(1)}° / EL ${pEl.toFixed(1)}°</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>ALIGNMENT STATUS:</span>
              <span style="color:${Math.abs(azErr) <= 0.5 && Math.abs(elErr) <= 0.5 ? '#00ff88' : '#ffb800'}; font-weight:700;">
                ${Math.abs(azErr) <= 0.5 && Math.abs(elErr) <= 0.5 ? '● LOCKED (TIGHT)' : '○ SLEWING TO TARGET'}
              </span>
            </div>
            <div style="font-size:9px; color:#8b949e; margin-top:4px; line-height:1.2;">
              MODULO-360 NORMALIZATION: [${rawDiff >= 0 ? '+' : ''}${rawDiff.toFixed(1)}°]<br/>
              DEADBAND: ${this.inputs.deadband.val}
            </div>
          </div>

          <!-- Panel B: Tracking Telemetry -->
          <div>
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">B. TRACKING ERROR ENGINE</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>AZIMUTH ERROR:</span>
              <span style="font-weight:700; color:${Math.abs(azErr) <= 0.5 ? '#00ff88' : '#79c0ff'}">${azErr >= 0 ? '+' : ''}${azErr.toFixed(1)}°</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>ELEVATION ERROR:</span>
              <span style="font-weight:700; color:${Math.abs(elErr) <= 0.5 ? '#00ff88' : '#79c0ff'}">${elErr >= 0 ? '+' : ''}${elErr.toFixed(1)}°</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>TOTAL ERROR:</span>
              <span style="color:#ffb800; font-weight:700;">${totErr.toFixed(2)}° (√(eA²+eE²))</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>TRACKING QUALITY:</span>
              <span style="color:#00ff88; font-weight:700;">${this.outputs.tracking_quality.val}</span>
            </div>
          </div>

          <!-- Panel C: Solar Power Engine -->
          <div style="border-right:1px solid #1e2638; padding-right:8px; border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">C. PHOTOVOLTAIC POWER ENGINE</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>IRRADIANCE (I0):</span>
              <span>1361.0 W/m² (AM0/AM1.5)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>INCIDENT ANGLE:</span>
              <span style="color:#ffb800; font-weight:700;">θ = ${thetaDeg.toFixed(2)}°</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>THEORETICAL PEAK:</span>
              <span>5665 W (η = 22.5%)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>EFFECTIVE POWER:</span>
              <span style="color:#00ff88; font-weight:700;">${pwr} W (${arrayPwr})</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>MISALIGN LOSS:</span>
              <span style="color:${pwrLoss > 500 ? '#ff3344' : '#8b949e'};">${pwrLoss.toFixed(1)} W</span>
            </div>
          </div>

          <!-- Panel D: Vector Data (Engineering/Debug) -->
          <div style="border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">D. 3D CARTESIAN VECTORS (DEBUG)</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:1px; font-size:9px;">
              <span>SUN VEC (S):</span>
              <span>[${sx.toFixed(3)}, ${sy.toFixed(3)}, ${sz.toFixed(3)}]</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:1px; font-size:9px;">
              <span>PANEL NORM (N):</span>
              <span>[${nx.toFixed(3)}, ${ny.toFixed(3)}, ${nz.toFixed(3)}]</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:1px; font-size:9px;">
              <span>DOT PRODUCT (D):</span>
              <span style="color:#79c0ff; font-weight:700;">${dot >= 0 ? '+' : ''}${dot.toFixed(4)} (N · S)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:1px; font-size:9px;">
              <span>COS INCIDENCE:</span>
              <span>${cosClamp.toFixed(3)} [Q16.16: 0x${Math.round(cosClamp * 65536).toString(16).toUpperCase()}]</span>
            </div>
          </div>

          <!-- Panel E: Actuator Status -->
          <div style="border-right:1px solid #1e2638; padding-right:8px; border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">E. ACTUATOR CONTROLLER & LIMITS</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>AZ STEPPER:</span>
              <span style="font-weight:700; color:#58a6ff;">${this.outputs.az_action.val}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>EL STEPPER:</span>
              <span style="font-weight:700; color:#58a6ff;">${this.outputs.el_action.val}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>RATE LIMIT:</span>
              <span>10.0°/s MAX SLEW</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>SAFETY INTERLOCK:</span>
              <span style="color:#00ff88; font-weight:700;">${this.outputs.fault_supervisor.val}</span>
            </div>
          </div>

          <!-- Panel F: FPGA Hardware Telemetry -->
          <div style="border-top:1px solid #1e2638; padding-top:6px;">
            <div style="color:var(--text-cyan); font-weight:700; margin-bottom:4px; font-size:10px;">F. FPGA PL COMPUTATION ENGINE</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>FPGA MODE:</span>
              <span style="color:#00ff88; font-weight:700;">AUTHORITATIVE PL</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>TARGET BOARD:</span>
              <span>EDGE ZYNQ Z7010 (XC7Z010)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>PIPELINE LATENCY:</span>
              <span style="color:#ffb800; font-weight:700;">18 cycles (180 ns @ 100MHz)</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>PARALLEL CHANNELS:</span>
              <span style="color:#79c0ff; font-weight:700;">4 HARDWARE PIPELINES (CH ${chId}: ${chInfo.power_w}W, θ=${chInfo.theta_deg}°)</span>
            </div>
          </div>
        </div>
      `;
    }
  }
};

let currentProject = PROJECTS.TRAFFIC;

// =============================================================================
// CINEMATIC BOOT INTRO SEQUENCE (5-10 Seconds)
// =============================================================================

const BOOT_LOG_LINES = [
  "[0.000s] HARDWARE BENCH: VDD_CORE = 1.00V, VDD_IO = 3.30V [OK]",
  "[0.840s] PLL LOCK: 50.000 MHz MASTER REFERENCE CLOCK VERIFIED",
  "[1.750s] LOADING SYNTHESIZED BITSTREAM: JTAG_SCAN_CHAIN -> CONFIG_SRAM",
  "[2.820s] CONFIGURING INTERFACE BUS PROTOCOL (8-BIT DETERMINISTIC PROTOCOL.JSON)",
  "[3.950s] MAPPING FPGA REGISTERS: TRAFFIC, MARS_ROVER, ANDROID, MARS_PDU",
  "[5.100s] SYNCHRONIZING HARDWARE INPUT PINS AND OUTPUT LED DRIVERS",
  "[6.250s] TIMING ANALYSIS: ZERO SETUP/HOLD SLACK VIOLATIONS (FMAX = 142 MHz)",
  "[7.100s] SYSTEM TESTBED READY: TRANSFERRING CONTROL TO EXPERIMENTAL CONSOLE..."
];

function initCinematicIntro() {
  const overlay = document.getElementById("cinematic-intro");
  const logEl = document.getElementById("intro-terminal-log");
  const barEl = document.getElementById("intro-progress-bar");
  const stageEl = document.getElementById("intro-stage-label");
  const percentEl = document.getElementById("intro-percent-label");
  const skipBtn = document.getElementById("skip-intro-btn");
  const controlPanel = document.getElementById("control-panel");

  let step = 0;
  let progress = 0;
  const totalSteps = BOOT_LOG_LINES.length;
  let isFinished = false;

  function finishIntro() {
    if (isFinished) return;
    isFinished = true;
    overlay.classList.add("fade-out");
    setTimeout(() => {
      overlay.classList.add("hidden");
      controlPanel.classList.remove("hidden");
    }, 800);
  }

  skipBtn.addEventListener("click", finishIntro);
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") finishIntro();
  });

  const interval = setInterval(() => {
    if (step < totalSteps) {
      logEl.textContent += BOOT_LOG_LINES[step] + "\n";
      logEl.scrollTop = logEl.scrollHeight;
      step++;
      progress = Math.min(100, Math.round((step / totalSteps) * 100));
      barEl.style.width = progress + "%";
      percentEl.textContent = progress + "%";
      stageEl.textContent = BOOT_LOG_LINES[step - 1].slice(9, 45) + "...";
    } else {
      clearInterval(interval);
      setTimeout(finishIntro, 900);
    }
  }, 850); // 850ms * 8 lines = ~6.8 seconds total intro time
}

// =============================================================================
// DOM RENDERING & CONTROL PANEL STATE
// =============================================================================

function renderDock() {
  const dock = document.getElementById("project-dock");
  dock.innerHTML = "";

  Object.values(PROJECTS).forEach((proj) => {
    const tile = document.createElement("div");
    tile.className = `dock-tile ${proj.id === currentProject.id ? 'active' : ''}`;
    tile.innerHTML = `
      <div class="tile-ident">
        <span class="tile-indicator"></span>
        <span class="tile-name">${proj.name}</span>
      </div>
      <span class="tile-status">${proj.id === currentProject.id ? 'SELECTED' : 'DOCKED'}</span>
    `;
    tile.addEventListener("click", () => switchProject(proj.id));
    dock.appendChild(tile);
  });
}

function switchProject(projId) {
  if (!PROJECTS[projId]) return;
  currentProject = PROJECTS[projId];
  currentProject.evaluate();

  document.getElementById("active-target-id").textContent = currentProject.id;
  document.getElementById("active-target-desc").textContent = currentProject.desc;
  const imgEl = document.getElementById("project-image");
  imgEl.onerror = () => {
    imgEl.onerror = null;
    imgEl.src = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450"><rect width="800" height="450" fill="%23040810"/><defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="%23162235" stroke-width="1"/></pattern></defs><rect width="800" height="450" fill="url(%23grid)"/><circle cx="400" cy="225" r="140" fill="none" stroke="%2300e5ff" stroke-width="1.5" stroke-dasharray="6,6" opacity="0.6"/><circle cx="400" cy="225" r="90" fill="none" stroke="%2300ff88" stroke-width="1.5" opacity="0.4"/><line x1="160" y1="225" x2="640" y2="225" stroke="%231f334d" stroke-width="1"/><line x1="400" y1="65" x2="400" y2="385" stroke="%231f334d" stroke-width="1"/><text x="400" y="215" font-family="monospace" font-size="20" fill="%2300e5ff" font-weight="bold" text-anchor="middle" letter-spacing="2">${currentProject.id} HARDWARE BENCH</text><text x="400" y="245" font-family="monospace" font-size="12" fill="%238b949e" text-anchor="middle">${currentProject.desc}</text><text x="400" y="275" font-family="monospace" font-size="11" fill="%2300ff88" text-anchor="middle">[REAL-TIME AXI REGISTER MAPPING ACTIVE]</text></svg>`;
  };
  imgEl.src = currentProject.image;

  renderDock();
  renderInputs();
  renderOutputs();
  renderVisualOverlay();
  pulseSignalFlow();

  logCLI(`[SWITCH] Active hardware target set to FPGA://${currentProject.id}.`, "sys-msg");
}

function renderInputs() {
  const container = document.getElementById("fpga-inputs-container");
  container.innerHTML = "";
  const countTag = document.getElementById("input-count-tag");
  const keys = Object.keys(currentProject.inputs);
  countTag.textContent = `${keys.length} PINS`;

  keys.forEach((key) => {
    const input = currentProject.inputs[key];
    const row = document.createElement("div");
    row.className = "io-item-row";

    let controlHtml = "";
    if (input.type === "switch") {
      controlHtml = `
        <label class="toggle-switch">
          <input type="checkbox" id="input-${key}" ${input.val ? "checked" : ""}>
          <span class="slider-track"></span>
        </label>
      `;
    } else if (input.type === "binary") {
      controlHtml = `
        <div class="binary-btn-group">
          <button type="button" class="binary-btn ${input.val === 0 ? 'active' : ''}" data-pin="${key}" data-val="0">0</button>
          <button type="button" class="binary-btn ${input.val === 1 ? 'active' : ''}" data-pin="${key}" data-val="1">1</button>
        </div>
      `;
    } else if (input.type === "bus_range") {
      controlHtml = `
        <div class="bus-slider-wrap">
          <input type="range" class="bus-range-slider" id="input-${key}" min="${input.min}" max="${input.max}" value="${input.val}">
          <span class="bus-numeric-val" id="val-${key}">${input.val}</span>
        </div>
      `;
    } else if (input.type === "bus_select") {
      controlHtml = `
        <select id="input-${key}" class="signal-state-badge" style="background:#090e15; border:1px solid #2d3848; color:var(--text-cyan); font-family:var(--font-mono); outline:none;">
          ${input.options.map(opt => `<option value="${opt}" ${input.val === opt ? 'selected' : ''}>${opt}</option>`).join('')}
        </select>
      `;
    }

    row.innerHTML = `
      <div class="io-meta">
        <div class="io-name">${input.label}</div>
        <div class="io-desc">${input.desc}</div>
      </div>
      <div class="io-control-wrap">${controlHtml}</div>
    `;
    container.appendChild(row);

    // Event binding
    if (input.type === "switch") {
      const cb = row.querySelector(`#input-${key}`);
      cb.addEventListener("change", (e) => {
        setFPGAInput(key, e.target.checked ? 1 : 0);
      });
    } else if (input.type === "binary") {
      const btns = row.querySelectorAll(".binary-btn");
      btns.forEach(btn => {
        btn.addEventListener("click", () => {
          setFPGAInput(key, parseInt(btn.dataset.val, 10));
        });
      });
    } else if (input.type === "bus_range") {
      const slider = row.querySelector(`#input-${key}`);
      slider.addEventListener("input", (e) => {
        document.getElementById(`val-${key}`).textContent = e.target.value;
        setFPGAInput(key, parseInt(e.target.value, 10));
      });
    } else if (input.type === "bus_select") {
      const sel = row.querySelector(`#input-${key}`);
      sel.addEventListener("change", (e) => {
        setFPGAInput(key, e.target.value);
      });
    }
  });
}

function renderOutputs() {
  const container = document.getElementById("fpga-outputs-container");
  container.innerHTML = "";
  const countTag = document.getElementById("output-count-tag");
  const keys = Object.keys(currentProject.outputs);
  countTag.textContent = `${keys.length} PORTS`;

  keys.forEach((key) => {
    const output = currentProject.outputs[key];
    const row = document.createElement("div");
    row.className = "io-item-row";

    let visualHtml = "";
    if (output.type === "led") {
      visualHtml = `
        <div class="led-cluster">
          <span class="led-indicator ${output.color} ${output.val ? 'on' : ''}"></span>
          <span style="font-size:11px; font-weight:600; color:${output.val ? '#fff' : 'var(--text-dim)'};">${output.val ? 'HIGH (1)' : 'LOW (0)'}</span>
        </div>
      `;
    } else if (output.type === "led_cluster_traffic") {
      const isRed = output.val === "RED";
      const isYellow = output.val === "YELLOW";
      const isGreen = output.val === "GREEN";
      visualHtml = `
        <div class="led-cluster" style="background:#040608; padding:4px 8px; border:1px solid #1f2937;">
          <span class="led-indicator red ${isRed ? 'on' : ''}" title="RED"></span>
          <span class="led-indicator yellow ${isYellow ? 'on' : ''}" title="YELLOW"></span>
          <span class="led-indicator green ${isGreen ? 'on' : ''}" title="GREEN"></span>
          <span style="font-size:11px; font-weight:700; margin-left:6px; color:${getColorHex(output.val)}">${output.val}</span>
        </div>
      `;
    } else if (output.type === "led_cluster_4") {
      visualHtml = `
        <div class="led-cluster">
          ${output.val.map((v, i) => `
            <div style="display:flex; flex-direction:column; align-items:center; gap:2px;">
              <span class="led-indicator green ${v ? 'on' : ''}"></span>
              <span style="font-size:9px; color:var(--text-dim);">B${i}</span>
            </div>
          `).join('')}
        </div>
      `;
    } else if (output.type === "seven_seg") {
      visualHtml = render7SegmentHtml(output.val);
    } else if (output.type === "badge") {
      visualHtml = `<div class="signal-state-badge">${output.val}</div>`;
    }

    row.innerHTML = `
      <div class="io-meta">
        <div class="io-name">${output.label}</div>
        <div class="io-desc">${output.desc}</div>
      </div>
      <div class="io-control-wrap">${visualHtml}</div>
    `;
    container.appendChild(row);
  });
}

function renderVisualOverlay() {
  const overlay = document.getElementById("visual-state-overlay");
  overlay.innerHTML = currentProject.renderVisualOverlay();
}

function getColorHex(colorName) {
  if (colorName === "RED") return "#ff3344";
  if (colorName === "YELLOW") return "#ffb800";
  if (colorName === "GREEN") return "#00ff88";
  return "#e6edf3";
}

// =============================================================================
// REALISTIC 7-SEGMENT HARDWARE DISPLAY RENDERER
// =============================================================================

const SEGMENT_MAP = {
  0: ["a", "b", "c", "d", "e", "f"],
  1: ["b", "c"],
  2: ["a", "b", "d", "e", "g"],
  3: ["a", "b", "c", "d", "g"],
  4: ["b", "c", "f", "g"],
  5: ["a", "c", "d", "f", "g"],
  6: ["a", "c", "d", "e", "f", "g"],
  7: ["a", "b", "c"],
  8: ["a", "b", "c", "d", "e", "f", "g"],
  9: ["a", "b", "c", "d", "f", "g"],
  "-": ["g"]
};

function render7SegmentHtml(value) {
  const str = Math.abs(parseInt(value, 10) || 0).toString().padStart(2, "0");
  const digits = str.slice(-2).split("");

  let html = `<div class="seven-seg-cluster">`;
  digits.forEach(d => {
    const activeSegs = SEGMENT_MAP[d] || [];
    html += `
      <div class="seven-seg-digit">
        <div class="seg seg-a ${activeSegs.includes("a") ? "on" : ""}"></div>
        <div class="seg seg-b ${activeSegs.includes("b") ? "on" : ""}"></div>
        <div class="seg seg-c ${activeSegs.includes("c") ? "on" : ""}"></div>
        <div class="seg seg-d ${activeSegs.includes("d") ? "on" : ""}"></div>
        <div class="seg seg-e ${activeSegs.includes("e") ? "on" : ""}"></div>
        <div class="seg seg-f ${activeSegs.includes("f") ? "on" : ""}"></div>
        <div class="seg seg-g ${activeSegs.includes("g") ? "on" : ""}"></div>
      </div>
    `;
  });
  html += `</div>`;
  return html;
}

// =============================================================================
// CLI CONTROLLER & WORKFLOW INTERACTION MODEL
// =============================================================================

function pulseSignalFlow() {
  const steps = ["flow-cmd", "flow-in", "flow-logic", "flow-out", "flow-vis"];
  steps.forEach((id, idx) => {
    setTimeout(() => {
      const el = document.getElementById(id);
      if (el) {
        el.classList.add("pulse");
        setTimeout(() => el.classList.remove("pulse"), 400);
      }
    }, idx * 90);
  });
}

function setFPGAInput(pinName, value) {
  if (currentProject.inputs[pinName] !== undefined) {
    currentProject.inputs[pinName].val = value;
    currentProject.evaluate();
    renderOutputs();
    renderVisualOverlay();
    pulseSignalFlow();
  }
}

function logCLI(text, cssClass = "") {
  const display = document.getElementById("cli-history");
  const line = document.createElement("div");
  line.className = `cli-line ${cssClass}`;
  line.textContent = text;
  display.appendChild(line);
  display.scrollTop = display.scrollHeight;
}

function executeCLICommand(rawCommand) {
  const trimmed = rawCommand.trim();
  if (!trimmed) return;

  logCLI(`> ${trimmed}`, "user-cmd");
  pulseSignalFlow();

  const parts = trimmed.split(/\s+/);
  const cmd = parts[0].toLowerCase();

  if (cmd === "help") {
    logCLI(`[HELP] Valid commands for FPGA://${currentProject.id}:`, "sys-msg");
    logCLI(`  set <actual_input> <value>  - Sets value on defined FPGA pin`, "sys-msg");
    logCLI(`  run                         - Evaluates FPGA logic pipeline`, "sys-msg");
    logCLI(`  status                      - Displays all inputs and outputs`, "sys-msg");
    logCLI(`  switch <TRAFFIC|SOLAR|ROVER|ANDROID|MARS> - Switch active target`, "sys-msg");
    return;
  }

  if (cmd === "switch" && parts[1]) {
    const target = parts[1].toUpperCase();
    if (PROJECTS[target]) {
      switchProject(target);
    } else {
      logCLI(`[ERROR] Unknown target '${parts[1]}'. Available: TRAFFIC, SOLAR, ROVER, ANDROID, MARS`, "err-msg");
    }
    return;
  }

  if (cmd === "run") {
    currentProject.evaluate();
    renderOutputs();
    renderVisualOverlay();
    
    // Construct real output string
    const outStrings = Object.keys(currentProject.outputs).map(k => {
      const o = currentProject.outputs[k];
      return `${k}=${JSON.stringify(o.val)}`;
    });
    logCLI(`OUTPUT: ${outStrings.join(" | ")}`, "fpga-out");
    return;
  }

  if (cmd === "status") {
    logCLI(`--- FPGA://${currentProject.id} HARDWARE REGISTER STATUS ---`, "sys-msg");
    Object.keys(currentProject.inputs).forEach(k => {
      logCLI(`  INPUT  ${k.padEnd(18)} = ${currentProject.inputs[k].val}`, "sys-msg");
    });
    Object.keys(currentProject.outputs).forEach(k => {
      logCLI(`  OUTPUT ${k.padEnd(18)} = ${JSON.stringify(currentProject.outputs[k].val)}`, "fpga-out");
    });
    return;
  }

  if (cmd === "set") {
    if (parts.length < 3) {
      logCLI(`[ERROR] Malformed syntax. Expected: set <actual_input> <value>`, "err-msg");
      return;
    }
    const pin = parts[1];
    const rawVal = parts.slice(2).join(" ");

    if (currentProject.inputs[pin] === undefined) {
      logCLI(`[ERROR] Invalid FPGA input '${pin}'. Defined inputs for this design: ${Object.keys(currentProject.inputs).join(", ")}`, "err-msg");
      return;
    }

    let val = rawVal;
    if (!isNaN(rawVal)) {
      val = parseInt(rawVal, 10);
    }

    currentProject.inputs[pin].val = val;
    currentProject.evaluate();
    renderInputs();
    renderOutputs();
    renderVisualOverlay();

    // Construct response
    const outStrings = Object.keys(currentProject.outputs).map(k => {
      const o = currentProject.outputs[k];
      return `${k}=${JSON.stringify(o.val)}`;
    });
    logCLI(`OUTPUT: ${outStrings.join(" | ")}`, "fpga-out");
    return;
  }

  // Reject fictional or unrecognized commands strictly
  logCLI(`[ERROR] Unrecognized command '${trimmed}'. Fictional parameters/telemetry are not accepted by FPGA hardware. Type 'help'.`, "err-msg");
}

// =============================================================================
// AUTHORITATIVE HARDWARE STATE SYNCHRONIZATION
// =============================================================================

function syncHardwareStatus() {
  fetch('/api/hardware/status')
    .then(r => r.json())
    .then(data => {
      const modeVal = document.getElementById("mode-readout-val");
      const busVal = document.getElementById("bus-readout-val");
      const liveTag = document.getElementById("visual-live-tag");
      if (data && data.connection === "CONNECTED") {
        if (modeVal) {
          modeVal.textContent = "● FPGA HARDWARE ACTIVE";
          modeVal.className = "val active";
        }
        if (busVal) {
          busVal.textContent = "ACTIVE";
          busVal.className = "val active";
        }
        if (liveTag) liveTag.textContent = "● DIRECT HARDWARE FEED";
      } else {
        if (modeVal) {
          modeVal.textContent = "× SOFTWARE-ONLY MODE";
          modeVal.className = "val offline";
        }
        if (busVal) {
          busVal.textContent = "OFFLINE";
          busVal.className = "val offline";
        }
        if (liveTag) liveTag.textContent = "○ SOFTWARE TESTBED FEED";
      }
    })
    .catch(() => {
      const modeVal = document.getElementById("mode-readout-val");
      const busVal = document.getElementById("bus-readout-val");
      const liveTag = document.getElementById("visual-live-tag");
      if (modeVal) {
        modeVal.textContent = "× SOFTWARE-ONLY (STANDALONE WEB)";
        modeVal.className = "val offline";
      }
      if (busVal) {
        busVal.textContent = "OFFLINE";
        busVal.className = "val offline";
      }
      if (liveTag) liveTag.textContent = "○ SOFTWARE TESTBED FEED";
    });
}

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  initCinematicIntro();
  switchProject("TRAFFIC");
  syncHardwareStatus();

  const cliForm = document.getElementById("cli-form");
  const cliInput = document.getElementById("cli-input");
  cliForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const val = cliInput.value;
    cliInput.value = "";
    executeCLICommand(val);
  });
});
