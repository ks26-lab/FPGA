"""
python.cli.renderer
===================
Terminal ASCII renderer for universal FPGA CLI and scene-specific telemetry panels.
"""

from typing import Dict, Any, Optional
from python.protocol.enums import SceneType


class CLIRenderer:
    """Renders formatted ASCII screens and telemetry cards for PuTTY/Serial."""

    @staticmethod
    def render_banner(is_hardware: bool, transport_type: str = "AXI") -> str:
        if is_hardware:
            lines = [
                "========================================================",
                "       ZYNQ Z7010 MULTI-SCENE FPGA CONTROL SYSTEM       ",
                "========================================================",
                "SYSTEM",
                "--------------------------------------------------------",
                "Execution Backend : ZYNQ FPGA HARDWARE",
                "FPGA Hardware     : CONNECTED",
                "Computation Model : RTL",
                "Transport         : AXI4-Lite (/dev/mem)",
                "Processor         : ZYNQ ARM CORTEX-A9",
                "--------------------------------------------------------",
                "",
                "Available Scenes:",
                "  1. Solar Gimbal     (scene solar)",
                "  2. Maze Runner      (scene maze)",
                "  3. Mars Habitat     (scene mars)",
                "  4. Underwater Probe (scene underwater)",
                "  5. Traffic          (scene traffic)",
                "",
                "Type 'help' for commands.",
                "========================================================"
            ]
        else:
            lines = [
                "========================================================",
                "       ZYNQ Z7010 MULTI-SCENE FPGA CONTROL SYSTEM       ",
                "========================================================",
                "SYSTEM",
                "--------------------------------------------------------",
                "Execution Backend : LAPTOP FPGA EMULATION",
                "FPGA Hardware     : NOT CONNECTED",
                "Computation Model : RTL-equivalent Software Model",
                "Precision         : FPGA Fixed-Point Parity",
                "Timing Model      : Deterministic Tick Model",
                "Transport         : Memory-Mapped Register Model",
                "--------------------------------------------------------",
                "",
                "Available Scenes:",
                "  1. Solar Gimbal     (scene solar)",
                "  2. Maze Runner      (scene maze)",
                "  3. Mars Habitat     (scene mars)",
                "  4. Underwater Probe (scene underwater)",
                "  5. Traffic          (scene traffic)",
                "",
                "Type 'help' for commands.",
                "========================================================"
            ]
        return "\n".join(lines)

    @staticmethod
    def render_help(active_scene: Optional[SceneType] = None) -> str:
        lines = [
            "--------------------------------------------------------",
            "GLOBAL COMMANDS:",
            "  scene <name>        Switch scene (solar, maze, mars, underwater, traffic)",
            "  status              Query live FPGA telemetry from active scene",
            "  reset               Send hardware reset pulse to active scene core",
            "  debug registers     Inspect raw 32-bit AXI memory-mapped registers",
            "  debug on / off      Toggle debug trace mode",
            "  back                Deselect current scene",
            "  exit / quit         Close CLI and release AXI bus",
            "--------------------------------------------------------"
        ]

        if active_scene == SceneType.UNDERWATER:
            lines.extend([
                "UNDERWATER PROBE COMMANDS:",
                "  set depth <m>       Set starting probe depth in meters (0-1000m)",
                "  target <m>          Set target seeking depth (0-1000m)",
                "  current <+/-pct>    Set water current strength (-100% to +100%)",
                "  disturb <type>      Inject disturbance (whale, fish, garbage)",
                "  start               Start probe seeking movement",
                "  stop                Halt probe movement",
                "  prediction          Display FPGA future depth projections (T+1, T+3, T+5)",
                "  faults              Inspect FPGA anomaly and fault detection register",
                "  pid                 Display PID controller parameters and output",
                "--------------------------------------------------------"
            ])
        elif active_scene == SceneType.MAZE:
            lines.extend([
                "MAZE RUNNER COMMANDS:",
                "  start               Start game and initiate countdown timer",
                "  up / w              Move player UP",
                "  down / s            Move player DOWN",
                "  left / a            Move player LEFT",
                "  right / d           Move player RIGHT",
                "  path bfs            Trigger hardware BFS shortest path search",
                "  path astar          Trigger hardware A* path search",
                "  path status         Display FPGA pathfinding telemetry",
                "  maze stats          Display hardware topology & complexity score",
                "  agents [on|off]     Toggle/inspect 4-agent parallel engine",
                "  performance         Display FPGA hardware cycle counters",
                "  faults              Inspect FPGA anomaly and fault flags",
                "  inspect <0-63>      Read 4-bit wall bitmask from FPGA ROM",
                "--------------------------------------------------------"
            ])
        elif active_scene == SceneType.MARS:
            lines.extend([
                "MARS HABITAT COMMANDS:",
                "  meteorites <N>      Configure meteorite batch size (1-255)",
                "  attack normal [tgt] Launch normal meteorite wave (ALL, A, or B)",
                "  attack big [tgt]    Launch high-severity meteorite (tests isolation)",
                "  threshold <A|B> <V> Configure section impact threshold",
                "--------------------------------------------------------"
            ])
        elif active_scene == SceneType.SOLAR:
            lines.extend([
                "SOLAR GIMBAL COMMANDS:",
                "  sun azimuth <deg>   Set sun azimuth (0 - 360°)",
                "  sun elevation <deg> Set sun elevation (0 - 90°)",
                "  panel azimuth <deg> Set panel azimuth (0 - 360°)",
                "  panel elevation <d> Set panel elevation (0 - 90°)",
                "  calculate           Trigger FPGA circular tracking calculation",
                "--------------------------------------------------------"
            ])
        elif active_scene == SceneType.TRAFFIC:
            lines.extend([
                "TRAFFIC GRID COMMANDS:",
                "  queue ns <N>        Set North-South waiting vehicle queue",
                "  queue ew <N>        Set East-West waiting vehicle queue",
                "  intersection <1-4>  Select active intersection controller",
                "  override <ns|ew>    Manually force signal green phase",
                "  override auto       Restore autonomous adaptive FSM timing",
                "  step                Advance traffic simulation tick",
                "--------------------------------------------------------"
            ])
        return "\n".join(lines)

    @staticmethod
    def render_telemetry(telem: Dict[str, Any]) -> str:
        scene = telem.get("scene", "")
        data = telem.get("data", {})
        is_hw = telem.get("hardware", False)
        hw_tag = "[FPGA HARDWARE]" if is_hw else "[MOCK MODE]"

        if scene == "underwater":
            d = data.get("depth", 0.0)
            td = data.get("target_depth", 0.0)
            vel = data.get("velocity", 0.0)
            curr = data.get("current_strength", 0)
            col = "YES" if data.get("collision") else "NO"
            rec = "YES" if data.get("recovery") else "NO"
            d = data.get("depth", 0.0)
            td = data.get("target_depth", 0.0)
            d_err = data.get("depth_error", 0.0)
            vel = data.get("velocity", 0.0)
            flt_vel = data.get("filtered_velocity", 0.0)
            curr = data.get("current_strength", 0)
            drag = data.get("drag_force", 0.0)
            thrust = data.get("thrust", 0.0)
            pid_out = data.get("control_output", 0.0)
            col = "YES" if data.get("collision") else "NO"
            rec = "ACTIVE" if data.get("recovery") else "INACTIVE"
            tgt_rec = "YES" if data.get("target_reached") else "NO"
            obj = data.get("active_object", "NONE")
            cols = data.get("collision_count", 0)
            recs = data.get("recovery_count", 0)
            imp_e = data.get("impact_energy", 0)
            imp_sev = data.get("impact_severity", "NONE")
            p1 = data.get("predicted_depth_1", 0.0)
            p3 = data.get("predicted_depth_3", 0.0)
            p5 = data.get("predicted_depth_5", 0.0)
            cost = data.get("control_cost", 0)
            opt = data.get("optimization_action", "HOLD_THRUST").replace("_THRUST", "")
            faults = data.get("active_faults", [])
            fault_str = ",".join(faults) if faults else "NONE"
            cycles = data.get("simulation_cycles", 0)
            phys_updates = data.get("physics_update_count", 0)

            sign = "+" if curr >= 0 else ""
            err_sign = "+" if d_err >= 0 else ""
            lines = [
                f"┌── UNDERWATER PROBE STATUS {hw_tag} ──────┐",
                f"│ STATE          : {telem.get('state', ''):<26}│",
                f"│ CURRENT DEPTH  : {d:<5.1f} m                     │",
                f"│ TARGET DEPTH   : {td:<5.1f} m                     │",
                f"│ DEPTH ERROR    : {err_sign}{d_err:<5.1f} m                     │",
                f"│ VELOCITY       : {vel:<+5.1f} m/s (Filtered: {flt_vel:<+5.1f})   │",
                f"│ WATER CURRENT  : {sign}{curr}%                        │",
                f"│ HYDRO DRAG     : {drag:<+5.1f} N                     │",
                f"│ PID THRUST     : {thrust:<5.1f} N (Ctrl: {pid_out:<+5.1f})      │",
                "├───────────────────────────────────────────┤",
                "│ FPGA DEPTH PREDICTION                     │",
                f"│   T+1: {p1:<5.1f} m | T+3: {p3:<5.1f} m | T+5: {p5:<5.1f} m │",
                "├───────────────────────────────────────────┤",
                f"│ IMPACT / COLL  : {col:<3} ({obj:<7} {imp_e}J {imp_sev})   │",
                f"│ RECOVERY FSM   : {rec:<8} (Count: {recs:<3})           │",
                f"│ OPTIMIZER      : {opt:<8} (Cost: {cost:<4})           │",
                f"│ HARDWARE FAULT : {fault_str:<26}│",
                f"│ FPGA CYCLES    : {cycles:<12} (Updates: {phys_updates:<6})│",
                "└───────────────────────────────────────────┘"
            ]
            return "\n".join(lines)

        elif scene == "maze":
            px = data.get("player_x", 0)
            py = data.get("player_y", 0)
            gx = data.get("goal_x", 7)
            gy = data.get("goal_y", 7)
            col = "YES (HIT WALL)" if data.get("collision") else "NO"
            win = "★ GOAL REACHED! ★" if data.get("goal_reached") else "IN PROGRESS"
            tot = data.get("total_moves", 0)
            val = data.get("valid_moves", 0)
            c_cnt = data.get("collision_count", 0)
            t_rem = data.get("time_remaining_s", 0)

            algo = data.get("path_algorithm", "NONE")
            p_val = "FOUND" if data.get("path_valid") else "NONE"
            p_len = data.get("path_length", 0)
            nodes = data.get("nodes_explored", 0)
            cyc = data.get("path_cycles", 0)
            dist = data.get("current_distance", 0)
            eff = data.get("path_efficiency", 1.0)
            cplx = data.get("maze_complexity", 0.71)

            # Neighbor icons
            n_up = "↑" if data.get("valid_up") else "·"
            n_rt = "→" if data.get("valid_right") else "·"
            n_dn = "↓" if data.get("valid_down") else "·"
            n_lt = "←" if data.get("valid_left") else "·"
            neighbors = f"{n_up} {n_rt} {n_dn} {n_lt}"
            dead_end = "YES" if data.get("dead_end") else "NO"

            faults = data.get("active_faults", [])
            fault_str = ",".join(faults) if faults else "NONE"
            agents = data.get("active_agents", 0)
            ag_goals = data.get("agent_goal_count", 0)

            lines = [
                f"┌── MAZE RUNNER STATUS {hw_tag} ───────────┐",
                f"│ GAME STATE     : {telem.get('state', ''):<26}│",
                f"│ PLAYER POS (X,Y): ({px}, {py})                    │",
                f"│ GOAL POS   (X,Y): ({gx}, {gy})                    │",
                f"│ COLLISION      : {col:<26}│",
                f"│ GOAL STATUS    : {win:<26}│",
                f"│ TOTAL MOVES    : {tot:<6} (Valid: {val:<3})          │",
                f"│ TOTAL COLLIDE  : {c_cnt:<26}│",
                f"│ TIMER REMAINING: {t_rem} s                        │",
                "├───────────────────────────────────────────┤",
                "│ FPGA NAVIGATION ENGINE                    │",
                f"│   ALGORITHM    : {algo:<12} (Status: {p_val:<5})   │",
                f"│   PATH LENGTH  : {p_len:<6} Nodes Exp: {nodes:<4}      │",
                f"│   FPGA CYCLES  : {cyc:<6} Distance : {dist:<4}      │",
                f"│   EFFICIENCY   : {eff:<5.2f}  Complexity: {cplx:<4.2f}    │",
                f"│   NEIGHBORS    : [{neighbors}]  Dead End: {dead_end:<3}     │",
                f"│   AGENTS ACTIVE: {agents:<6} Goals Met: {ag_goals:<4}      │",
                f"│   HARDWARE FAULT: {fault_str:<25}│",
                "└───────────────────────────────────────────┘"
            ]
            return "\n".join(lines)

        elif scene == "mars_habitat":
            hw_mode = "HARDWARE (XC7Z010)" if telem.get("hardware") else "SOFTWARE EMULATION"
            sa = data.get("section_A", "OPERATIONAL")
            sb = data.get("section_B", "OPERATIONAL")
            link = "ISOLATED" if data.get("link_closed") else "OPEN"
            alt = data.get("landing_altitude", 0.0)
            vel = data.get("landing_velocity", 0.0)
            thrust = data.get("thrust_command", 0.0)
            pred_v = data.get("predicted_touchdown_velocity", 0.0)
            pred_status = data.get("landing_status", "SAFE")
            m_active = data.get("meteorite_active_count", 0)
            tot_imp = data.get("total_impacts", 0)
            crit_imp = data.get("critical_impact_count", 0)
            m_energy = data.get("total_impact_energy", 0.0)
            o2 = data.get("o2_percent", 20.9)
            co2 = data.get("co2_percent", 0.04)
            pres = data.get("pressure_kpa", 101.3)
            temp = data.get("temperature_c", 21.0)
            health = data.get("habitat_health", 100)
            cycles = data.get("simulation_cycles", 0)

            lander_y = "[LANDER]  ▼" if alt > 100.0 else ("[TOUCHDOWN]" if alt <= 0.0 else "[APPROACH] ▼")
            meteor_vis = "↓↓↓ METEORITES ACTIVE ↓↓↓" if m_active > 0 else "NOMINAL (NO THREAT)"

            c1_w = 27
            c2_w = 56

            lines = [
                f"┌{'─' * (c1_w + 2)}┬{'─' * (c2_w + 2)}┐",
                f"│ {'MARS SURFACE / HABITAT':<{c1_w}} │ {'FPGA SYSTEM ACCELERATOR':<{c2_w}} │",
                f"├{'─' * (c1_w + 2)}┼{'─' * (c2_w + 2)}┤",
                f"│ {lander_y:<{c1_w}} │ {f'MODE     : {hw_mode}':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {'        /▲\\':<{c1_w}} │ {'LANDING DYNAMICS (CLOSED-LOOP)':<{c2_w}} │",
                f"│ {'       / | \\':<{c1_w}} │ {f'ALTITUDE : {alt:>6.1f} m    VELOCITY : {vel:>+6.1f} m/s':<{c2_w}} │",
                f"│ {'      [HABITAT]':<{c1_w}} │ {f'THRUST   : {thrust:>5.1f} %    PREDICT  : {pred_status} ({pred_v:>+4.1f} m/s)':<{c2_w}} │",
                f"│ {f'A   : {sa}':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {f'B   : {sb}':<{c1_w}} │ {'PARALLEL METEORITE ENGINE (8-CHANNELS)':<{c2_w}} │",
                f"│ {f'LINK: {link}':<{c1_w}} │ {f'ACTIVE   : {m_active:<3}        IMPACTS  : {tot_imp:<4}':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {f'CRITICAL : {crit_imp:<3}        ENERGY   : {m_energy:<7.1f} J':<{c2_w}} │",
                f"│ {meteor_vis:<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {'── MARS REGOLITH ──':<{c1_w}} │ {'LIFE SUPPORT & THERMAL STATE':<{c2_w}} │",
                f"│ {f'HEALTH SCORE: {health:>3}%':<{c1_w}} │ {f'O2: {o2:>4.1f}%  CO2: {co2:>4.2f}%  P: {pres:>5.1f}kPa  T: {temp:>+5.1f}C':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {f'HEALTH   : {health:>3}%       FPGA CYCLES: {cycles:,}':<{c2_w}} │",
                f"└{'─' * (c1_w + 2)}┴{'─' * (c2_w + 2)}┘"
            ]
            return "\n".join(lines)

        elif scene == "solar_gimbal":
            s_az = data.get("sun_azimuth", 0.0)
            s_el = data.get("sun_elevation", 0.0)
            p_az = data.get("panel_azimuth", 0.0)
            p_el = data.get("panel_elevation", 0.0)
            az_err = data.get("azimuth_error", 0.0)
            el_err = data.get("elevation_error", 0.0)
            az_dir = data.get("azimuth_direction", "HOLD")
            el_dir = data.get("elevation_direction", "HOLD")
            act_az = data.get("actuator_azimuth", 0.0)
            act_el = data.get("actuator_elevation", 0.0)
            locked = "LOCKED (±0.5°)" if data.get("tracking_locked") else "SLEWING"

            inc_deg = data.get("incident_angle", 0.0)
            cos_th = data.get("cos_incidence", 1.0)
            power_w = data.get("estimated_power", 5665.0)
            tot_pwr = data.get("total_array_power", power_w * 4)
            cycles = data.get("vector_cycles", 18)
            panels_n = data.get("panels_active_count", 4)
            faults = data.get("fault_list", [])
            fault_str = ",".join(faults) if faults else "NONE"
            auth_str = "● AUTHORITATIVE" if telem.get("hardware") else "● EMULATED RTL"

            az_action = "HOLD" if data.get("az_hold") else ("→ STEP" if az_dir == "CLOCKWISE" else "← STEP")
            el_action = "HOLD" if data.get("el_hold") else ("↑ STEP" if el_dir == "UP" else "↓ STEP")

            c1_w = 26
            c2_w = 46

            # 3D Vector Alignment Visualization
            if abs(az_err) <= 2.0 and abs(el_err) <= 2.0:
                sun_art_1 = "       ☀ SUN          "
                sun_art_2 = "       │              "
                sun_art_3 = "       │ Sun Vector   "
                sun_art_4 = "       ↓              "
                sun_art_5 = "    ═════════ PANEL   "
                sun_art_6 = "       ║ GIMBAL AXIS  "
                align_tag = "[PERFECT ALIGNMENT]   "
            else:
                sun_art_1 = " ☀ SUN                "
                sun_art_2 = "   ╲                  "
                sun_art_3 = "    ╲ Sun Vector      "
                sun_art_4 = "     ↓                "
                sun_art_5 = "       ══════ PANEL   "
                sun_art_6 = "      ╱ GIMBAL AXIS   "
                align_tag = "[TRACKING IN PROGRESS]"

            lines = [
                f"┌{'─' * (c1_w + 2)}┬{'─' * (c2_w + 2)}┐",
                f"│ {'SOLAR TRACKING GIMBAL':<{c1_w}} │ {f'SOLAR TRACKING — FPGA ENGINE {hw_tag}':<{c2_w}} │",
                f"├{'─' * (c1_w + 2)}┼{'─' * (c2_w + 2)}┤",
                f"│ {sun_art_1:<{c1_w}} │ {f'Sun Azimuth       {s_az:>6.1f}°':<{c2_w}} │",
                f"│ {sun_art_2:<{c1_w}} │ {f'Sun Elevation     {s_el:>6.1f}°':<{c2_w}} │",
                f"│ {sun_art_3:<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {sun_art_4:<{c1_w}} │ {f'Gimbal Azimuth    {p_az:>6.1f}°':<{c2_w}} │",
                f"│ {sun_art_5:<{c1_w}} │ {f'Gimbal Elevation  {p_el:>6.1f}°':<{c2_w}} │",
                f"│ {sun_art_6:<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {align_tag:<{c1_w}} │ {f'AZ Error          {az_err:>+6.1f}°':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {f'EL Error          {el_err:>+6.1f}°':<{c2_w}} │",
                f"│ {f'Incidence: {inc_deg:>4.1f}°':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {f'Power: {power_w:>5.0f} W':<{c1_w}} │ {f'Incidence Angle   {inc_deg:>6.2f}° (cos θ = {cos_th:.3f})':<{c2_w}} │",
                f"│ {f'Array: {tot_pwr:>5.0f} W':<{c1_w}} │ {f'Estimated Power   {power_w:>6.0f} W (Array: {tot_pwr:>5.0f}W)':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {f'AZ Motor: {az_action}':<{c1_w}} │ {f'AZ Motor          {az_action}':<{c2_w}} │",
                f"│ {f'EL Motor: {el_action}':<{c1_w}} │ {f'EL Motor          {el_action}':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {f'Status: {locked}':<{c1_w}} │ {f'Panels Active     {panels_n}':<{c2_w}} │",
                f"│ {f'Fault: {fault_str}':<{c1_w}} │ {f'FPGA Cycles       {cycles}':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {f'Faults            {fault_str}':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {f'FPGA: {auth_str}':<{c1_w}} │ {f'FPGA: {auth_str}':<{c2_w}} │",
                f"└{'─' * (c1_w + 2)}┴{'─' * (c2_w + 2)}┘"
            ]
            return "\n".join(lines)

        elif scene == "traffic":
            iid = data.get("intersection_id", 1)
            ph = data.get("signal_phase", "NS_GREEN")
            g_rem = data.get("green_time_remaining_s", 0)
            cong = data.get("congestion_score_pct", 0)
            alert = "ALERT (HEAVY TRAFFIC)" if data.get("congestion_alert") else "FLOW NOMINAL"
            q_ns = data.get("queue_ns", 0)
            q_ew = data.get("queue_ew", 0)
            q_n = data.get("queue_north", q_ns // 2)
            q_s = data.get("queue_south", q_ns - q_n)
            q_e = data.get("queue_east", q_ew // 2)
            q_w = data.get("queue_west", q_ew - q_e)

            c_ns = data.get("cleared_ns_vehicles", 0)
            c_ew = data.get("cleared_ew_vehicles", 0)
            ovr = "ACTIVE" if data.get("override_active") else "AUTONOMOUS FSM"

            g_ns = data.get("calc_green_ns_s", 30)
            g_ew = data.get("calc_green_ew_s", 20)
            emg_str = f"ACTIVE ({data.get('emergency_direction', 'N')})" if data.get("emergency_active") else "NONE"
            ped_str = f"WALK ({data.get('pedestrian_time_remaining', 0)}s)" if data.get("pedestrian_walk_active") else "NONE"
            faults = data.get("fault_list", [])
            fault_str = ",".join(faults) if faults else "NONE"
            auth_str = "● AUTHORITATIVE" if telem.get("hardware") else "● EMULATED RTL"

            c1_w = 26
            c2_w = 46

            # Vehicle Queue Visualizer
            def _veh_bar(cnt):
                if cnt <= 10: return "🚗   🚗"
                elif cnt <= 30: return "🚗 🚗 🚗 🚗"
                elif cnt <= 65: return "🚗 🚗 🚗 🚗 🚗 🚗"
                else: return "🚗🚗🚗🚗🚗🚗🚗🚗"

            lines = [
                f"┌{'─' * (c1_w + 2)}┬{'─' * (c2_w + 2)}┐",
                f"│ {'SMART CITY TRAFFIC GRID':<{c1_w}} │ {f'SMART CITY — FPGA TRAFFIC ENGINE {hw_tag}':<{c2_w}} │",
                f"├{'─' * (c1_w + 2)}┼{'─' * (c2_w + 2)}┤",
                f"│ {'        N        ▲':<{c1_w}} │ {f'INTERSECTION   : ID {iid}':<{c2_w}} │",
                f"│ {'        │        │':<{c1_w}} │ {f'SIGNAL: {ph}':<{c2_w}} │",
                f"│ {'   W ───┼────────┼─── E':<{c1_w}} │ {f'TIMER : {g_rem:>4.1f} s':<{c2_w}} │",
                f"│ {'        │':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {'        ▼':<{c1_w}} │ {f'N QUEUE : {q_n:<3} ({_veh_bar(q_n)})':<{c2_w}} │",
                f"│ {'        S':<{c1_w}} │ {f'S QUEUE : {q_s:<3} ({_veh_bar(q_s)})':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {f'E QUEUE : {q_e:<3} ({_veh_bar(q_e)})':<{c2_w}} │",
                f"│ {f'QUEUES: NS={q_ns} | EW={q_ew}':<{c1_w}} │ {f'W QUEUE : {q_w:<3} ({_veh_bar(q_w)})':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {f'CONGESTION: {cong}%':<{c1_w}} │ {f'CONGESTION : {cong}% ({alert})':<{c2_w}} │",
                f"│ {f'CLEARED : {c_ns+c_ew} veh':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {f'NS GREEN : {g_ns} s':<{c2_w}} │",
                f"│ {f'ARBITRATION: {ovr}':<{c1_w}} │ {f'EW GREEN : {g_ew} s':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {f'EMG: {emg_str}':<{c1_w}} │ {f'EMERGENCY : {emg_str}':<{c2_w}} │",
                f"│ {f'PED: {ped_str}':<{c1_w}} │ {f'PEDESTRIAN: {ped_str}':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {f'PARALLEL VEHICLES: 16 ACTIVE':<{c2_w}} │",
                f"│ {f'FAULTS: {fault_str}':<{c1_w}} │ {f'FAULTS    : {fault_str}':<{c2_w}} │",
                f"│ {'':<{c1_w}} │ {'':<{c2_w}} │",
                f"│ {f'FPGA: {auth_str}':<{c1_w}} │ {f'FPGA: {auth_str}':<{c2_w}} │",
                f"└{'─' * (c1_w + 2)}┴{'─' * (c2_w + 2)}┘"
            ]
            return "\n".join(lines)

        return str(data)

    @staticmethod
    def render_debug_registers(debug_dict: Dict[str, Any]) -> str:
        lines = [
            "========================================================",
            f"HARDWARE DIAGNOSTICS: {debug_dict.get('scene', '').upper()}",
            f"BASE ADDRESS: {debug_dict.get('base_address', 'N/A')}",
            "--------------------------------------------------------"
        ]
        for k, v in debug_dict.items():
            if k not in ("scene", "base_address"):
                lines.append(f"  {k:<16} : {v}")
        lines.append("========================================================")
        return "\n".join(lines)
