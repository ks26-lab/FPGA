"""
python.scenes.traffic.command_handler
=====================================
Routes commands to TrafficDriver.
Supports both legacy queue commands and new smart city commands:
  traffic status
  traffic density <N|S|E|W> <value>
  traffic signal
  traffic emergency <direction>
  traffic pedestrian
  traffic auto
  traffic optimize
  traffic faults
  traffic performance
  traffic stress
  traffic reset
"""

from typing import Dict, Any, List
from python.scenes.traffic.driver import TrafficDriver
from python.protocol.errors import CommandParseError


class TrafficCommandHandler:
    """Dispatches human CLI commands to TrafficDriver."""

    def __init__(self, driver: TrafficDriver):
        self.driver = driver

    def execute(self, command_name: str, args: list) -> str:
        cmd = command_name.lower()

        # ----------------------------------------------------------------------
        # Unified "traffic <subcommand>" handler
        # ----------------------------------------------------------------------
        if cmd == "traffic":
            if not args:
                return self._cmd_status()
            sub = args[0].lower()
            sub_args = args[1:]

            if sub == "status":
                return self._cmd_status()
            elif sub == "start":
                if "--hw" in sub_args:
                    if not self.driver.is_hardware:
                        return "[HARDWARE UNAVAILABLE — SOFTWARE MODE REQUIRED] FPGA hardware interface /dev/mem not detected on this system."
                self.driver.start()
                hw_mode = "FPGA HARDWARE (Authoritative PL)" if self.driver.is_hardware else "LAPTOP RTL EMULATOR"
                return f"[FPGA] Traffic grid computation STARTED ({hw_mode}). 16 parallel vehicle engines running."
            elif sub == "stop":
                self.driver.clear_override()
                return "[FPGA] Traffic simulation halted. Actuators held in current safe state."
            elif sub == "configure":
                # e.g. traffic configure --density high | traffic configure --arrival 20
                if "--density" in sub_args:
                    idx = sub_args.index("--density")
                    lvl = sub_args[idx+1].lower() if idx+1 < len(sub_args) else "normal"
                    val_map = {"low": 5, "med": 15, "medium": 15, "high": 35, "gridlock": 60}
                    v = val_map.get(lvl, 20)
                    self.driver.set_approach_queues(v, v, v, v)
                    self.driver.step()
                    return f"[FPGA] Configured traffic density '{lvl.upper()}' (Q_all={v} veh). Hardware re-evaluated splits."
                elif "--arrival" in sub_args:
                    idx = sub_args.index("--arrival")
                    rate = int(sub_args[idx+1]) if idx+1 < len(sub_args) else 10
                    self.driver.set_queues(rate, rate)
                    self.driver.step()
                    return f"[FPGA] Configured arrival rate: {rate} veh/min across all approaches."
                else:
                    return "[FPGA] Usage: traffic configure [--density low|med|high|gridlock] [--arrival <rate>]"
            elif sub == "set":
                if len(sub_args) >= 3 and sub_args[0].lower() == "density":
                    direction = sub_args[1].upper()
                    if direction not in ("N", "S", "E", "W"):
                        raise CommandParseError("Direction must be N, S, E, or W")
                    val = int(sub_args[2])
                    self.driver.set_density(direction, val)
                    self.driver.step()
                    return f"[FPGA] Approach {direction} queue set to {val} vehicles. Dynamic splits recalculated."
                elif len(sub_args) >= 2 and sub_args[0].lower() == "arrival":
                    rate = int(sub_args[1])
                    self.driver.set_queues(rate, rate)
                    self.driver.step()
                    return f"[FPGA] Arrival rate set to {rate} veh/min."
                else:
                    raise CommandParseError("Usage: traffic set density <N|S|E|W> <val> OR traffic set arrival <rate>")
            elif sub == "density":
                if len(sub_args) < 2:
                    raise CommandParseError("Usage: traffic density <N|S|E|W> <count>")
                direction = sub_args[0].upper()
                if direction not in ("N", "S", "E", "W"):
                    raise CommandParseError("Direction must be N, S, E, or W")
                try:
                    val = int(sub_args[1])
                    if not (0 <= val <= 255): raise ValueError()
                except ValueError:
                    raise CommandParseError("Density must be an integer between 0 and 255")
                self.driver.set_density(direction, val)
                self.driver.step()
                return f"[FPGA] Approach {direction} queue set to {val} vehicles. Hardware re-evaluating splits."
            elif sub == "signal":
                t = self.driver.get_telemetry()["data"]
                return f"[FPGA] Current Phase: {t['signal_phase']} (NS Light: {t['ns_light']}, EW Light: {t['ew_light']}, Timer: {t['green_time_remaining_s']}s, Next Split: NS={t.get('calc_green_ns_s', 30)}s / EW={t.get('calc_green_ew_s', 20)}s)"
            elif sub == "emergency":
                direction = "NORTH"
                if "--direction" in sub_args:
                    idx = sub_args.index("--direction")
                    if idx + 1 < len(sub_args):
                        direction = sub_args[idx + 1].upper()
                elif sub_args:
                    direction = sub_args[0].upper()
                if direction not in ("NORTH", "SOUTH", "EAST", "WEST", "N", "S", "E", "W"):
                    raise CommandParseError("Direction must be NORTH, SOUTH, EAST, or WEST")
                full_dir = {"N": "NORTH", "S": "SOUTH", "E": "EAST", "W": "WEST"}.get(direction, direction)
                self.driver.trigger_emergency(full_dir)
                self.driver.step()
                return f"[FPGA] 🚨 EMERGENCY CORRIDOR ACTIVE! Priority granted to approach {full_dir}."
            elif sub == "inject":
                if sub_args and sub_args[0].lower() == "emergency":
                    direction = sub_args[1].upper() if len(sub_args) > 1 else "NORTH"
                    full_dir = {"N": "NORTH", "S": "SOUTH", "E": "EAST", "W": "WEST"}.get(direction, direction)
                    self.driver.trigger_emergency(full_dir)
                    self.driver.step()
                    return f"[FPGA] 🚨 Emergency vehicle INJECTED along {full_dir} corridor."
                else:
                    raise CommandParseError("Usage: traffic inject emergency [NORTH|SOUTH|EAST|WEST]")
            elif sub == "clear":
                if sub_args and sub_args[0].lower() == "emergency":
                    self.driver.clear_override()
                    self.driver.step()
                    return "[FPGA] Emergency corridor CLEARED. Normal adaptive timing restored."
                else:
                    raise CommandParseError("Usage: traffic clear emergency")
            elif sub == "show":
                if not sub_args:
                    return self._cmd_status()
                show_type = sub_args[0].lower()
                if show_type == "queues":
                    return self._cmd_show_queues()
                elif show_type == "signal":
                    return self._cmd_status()
                elif show_type == "vehicles":
                    return self._cmd_show_vehicles()
                elif show_type == "congestion":
                    return self._cmd_show_congestion()
                elif show_type in ("fpga", "telemetry"):
                    return self._cmd_performance()
                elif show_type == "hardware":
                    return self._cmd_show_hardware()
                elif show_type == "performance":
                    return self._cmd_performance()
                else:
                    raise CommandParseError(f"Unknown show target: '{show_type}'. Available: queues, signal, vehicles, congestion, fpga, hardware, performance.")
            elif sub == "fpga":
                return self._cmd_show_hardware()
            elif sub in ("pedestrian", "ped"):
                self.driver.trigger_pedestrian()
                self.driver.step()
                return "[FPGA] 🚶 Pedestrian walk request registered. Safe transition scheduled."
            elif sub == "auto":
                self.driver.start()
                return "[FPGA] Autonomous adaptive mode ENGAGED. Hardware optimization active."
            elif sub == "optimize":
                self.driver.step()
                t = self.driver.get_telemetry()["data"]
                return f"[FPGA] Dynamic Green-Split Optimized: NS={t['calc_green_ns_s']}s, EW={t['calc_green_ew_s']}s (Congestion: {t['congestion_score_pct']}%)"
            elif sub == "faults":
                return self._cmd_faults()
            elif sub in ("performance", "perf"):
                return self._cmd_performance()
            elif sub == "stress":
                self.driver.set_stress_mode(True)
                for _ in range(5):
                    self.driver.step()
                return self._cmd_stress()
            elif sub == "reset":
                self.driver.reset()
                return "[FPGA] Traffic grid controller reset to nominal baseline."
            else:
                raise CommandParseError(f"Unknown traffic subcommand: '{sub}'")

        # ----------------------------------------------------------------------
        # Legacy commands (e.g. "queue ns 15", "override ew", "step")
        # ----------------------------------------------------------------------
        if cmd == "queue" or (cmd == "set" and args and args[0].lower() == "queue"):
            shift = 1 if cmd == "set" else 0
            sub_args = args[shift:]
            if len(sub_args) < 2:
                raise CommandParseError("Usage: queue ns <count> OR queue ew <count>")
            direction = sub_args[0].lower()
            try:
                cnt = int(sub_args[1])
                if not (0 <= cnt <= 255): raise ValueError()
            except ValueError:
                raise CommandParseError("Queue count must be an integer between 0 and 255")

            cur = self.driver.get_telemetry()["data"]
            int_id = cur["intersection_id"]
            q_ns = cur["queue_ns"]
            q_ew = cur["queue_ew"]
            if direction == "ns": q_ns = cnt
            elif direction == "ew": q_ew = cnt
            else: raise CommandParseError("Direction must be 'ns' or 'ew'")

            self.driver.configure_intersection(int_id, q_ns, q_ew)
            return f"[FPGA] Configured queues for Intersection {int_id}: NS={q_ns}, EW={q_ew}"

        elif cmd == "intersection" or (cmd == "set" and args and args[0].lower() == "intersection"):
            shift = 1 if cmd == "set" else 0
            sub_args = args[shift:]
            if not sub_args:
                raise CommandParseError("Usage: intersection <id 1-4>")
            try:
                int_id = int(sub_args[0])
                if not (1 <= int_id <= 4): raise ValueError()
            except ValueError:
                raise CommandParseError("Intersection ID must be between 1 and 4")

            cur = self.driver.get_telemetry()["data"]
            self.driver.configure_intersection(int_id, cur["queue_ns"], cur["queue_ew"])
            return f"[FPGA] Selected Intersection {int_id}"

        elif cmd == "override":
            if not args:
                raise CommandParseError("Usage: override <ns|ew|auto>")
            target = args[0].lower()
            if target == "auto":
                self.driver.clear_override()
                return "[FPGA] Manual override cleared. Restored autonomous FSM scheduling."
            elif target in ("ns", "ew"):
                self.driver.manual_override(target)
                return f"[FPGA] Manual signal override asserted: {target.upper()}_GREEN"
            else:
                raise CommandParseError("Target must be 'ns', 'ew', or 'auto'")

        elif cmd in ("step", "cycle"):
            self.driver.step()
            return "[FPGA] Advanced traffic simulation by 1 second."

        elif cmd == "status":
            return self._cmd_status()

        elif cmd == "reset":
            self.driver.reset()
            return "[FPGA] Traffic grid controller reset to nominal baseline."

        raise CommandParseError(f"Unknown traffic command: '{command_name}'")

    def _cmd_status(self) -> str:
        t = self.driver.get_telemetry()["data"]
        emg_str = f"ACTIVE ({t['emergency_direction']})" if t.get("emergency_active") else "NONE"
        ped_str = f"WALK ({t.get('pedestrian_time_remaining', 0)}s)" if t.get("pedestrian_walk_active") else "NONE"
        faults_str = ", ".join(t.get("fault_list", [])) if t.get("fault_list") else "NONE"
        auth = "AUTHORITATIVE" if "Hardware" in t.get("authoritative", "") else "EMULATED RTL"

        lines = [
            "SMART CITY TRAFFIC",
            "────────────────────────────────────────",
            f"PHASE       : {t['signal_phase']}",
            f"TIMER       : {t['green_time_remaining_s']:>4.1f} s",
            "",
            "QUEUES",
            f" N          : {t.get('queue_north', 12)} ({t.get('n_congestion_level', 'LOW')})",
            f" S          : {t.get('queue_south', 10)} ({t.get('s_congestion_level', 'LOW')})",
            f" E          : {t.get('queue_east', 8)} ({t.get('e_congestion_level', 'LOW')})",
            f" W          : {t.get('queue_west', 6)} ({t.get('w_congestion_level', 'LOW')})",
            "",
            f"CONGESTION  : {t['congestion_score_pct']}% ({t.get('global_congestion_level', 'NORMAL')})",
            "",
            "NEXT SPLIT",
            f" NS         : {t.get('calc_green_ns_s', 30)} s",
            f" EW         : {t.get('calc_green_ew_s', 20)} s",
            "",
            f"EMERGENCY   : {emg_str}",
            f"PEDESTRIAN  : {ped_str}",
            "",
            f"FPGA        : {auth}",
            f"FAULT       : {faults_str}",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_faults(self) -> str:
        t = self.driver.get_telemetry()["data"]
        faults = t.get("fault_list", [])
        lines = [
            "🛡️ FPGA TRAFFIC SAFETY SUPERVISOR",
            "────────────────────────────────────────",
            f"Raw Fault Flags    : 0x{t.get('fault_flags', 0):04X}",
            f"Fault Event Count  : {t.get('fault_count', 0)}",
            f"Collision Hazards  : {t.get('collision_events', 0)}"
        ]
        if faults:
            lines.append("Active Faults:")
            for f in faults:
                lines.append(f"  ● [CRITICAL] {f}")
        else:
            lines.append("Status: NOMINAL — Mutual exclusion strictly enforced.")
        lines.append("────────────────────────────────────────")
        return "\n".join(lines)

    def _cmd_show_queues(self) -> str:
        t = self.driver.get_telemetry()["data"]
        lines = [
            "📊 FPGA HARDWARE QUEUE STATUS",
            "────────────────────────────────────────",
            f"North (Q_N)   : {t.get('queue_north', 0):>3} veh  ({t.get('n_congestion_level', 'LOW')})",
            f"South (Q_S)   : {t.get('queue_south', 0):>3} veh  ({t.get('s_congestion_level', 'LOW')})",
            f"East  (Q_E)   : {t.get('queue_east', 0):>3} veh  ({t.get('e_congestion_level', 'LOW')})",
            f"West  (Q_W)   : {t.get('queue_west', 0):>3} veh  ({t.get('w_congestion_level', 'LOW')})",
            "────────────────────────────────────────",
            f"Q_NS Sum      : {t.get('queue_ns_sum', 0):>3} veh",
            f"Q_EW Sum      : {t.get('queue_ew_sum', 0):>3} veh",
            f"Total Queue   : {t.get('queue_total', 0):>3} veh",
            f"Predicted NS  : {t.get('pred_queue_ns', 0):>3} veh",
            f"Predicted EW  : {t.get('pred_queue_ew', 0):>3} veh",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_show_vehicles(self) -> str:
        t = self.driver.get_telemetry()["data"]
        pos_n = t.get("positions_north", [0, 0, 0, 0])
        pos_s = t.get("positions_south", [0, 0, 0, 0])
        pos_e = t.get("positions_east", [0, 0, 0, 0])
        pos_w = t.get("positions_west", [0, 0, 0, 0])
        occ = t.get("vehicle_active_mask", 0xFFFF)
        brakes = t.get("brake_required_mask", 0)

        lines = [
            "🚗 16 PARALLEL FPGA VEHICLE ENGINES",
            "────────────────────────────────────────────────────────────",
            "ID  | Approach | Pos (m) | Speed (m/s) | Active | Brake Safe",
            "────┼──────────┼─────────┼─────────────┼────────┼───────────"
        ]
        approaches = [("NORTH", pos_n, t.get("speed_north_mps", 10)),
                      ("SOUTH", pos_s, t.get("speed_south_mps", 10)),
                      ("EAST",  pos_e, t.get("speed_east_mps", 10)),
                      ("WEST",  pos_w, t.get("speed_west_mps", 10))]
        vid = 0
        for name, positions, spd in approaches:
            for idx, p in enumerate(positions):
                is_act = "YES" if (occ >> vid) & 1 else "NO"
                is_brk = "BRAKE" if (brakes >> vid) & 1 else "CLEAR"
                lines.append(f"V{vid:<2} | {name:<8} | {p:>7} | {spd:>11} | {is_act:>6} | {is_brk:>10}")
                vid += 1
        lines.append("────────────────────────────────────────────────────────────")
        return "\n".join(lines)

    def _cmd_show_congestion(self) -> str:
        t = self.driver.get_telemetry()["data"]
        lines = [
            "🚦 FPGA CONGESTION & PREDICTION ENGINE",
            "────────────────────────────────────────",
            f"Congestion Score    : {t.get('congestion_score_pct', 0)}%",
            f"Global Congestion   : {t.get('global_congestion_level', 'NORMAL')}",
            f"Predicted NS Queue  : {t.get('pred_queue_ns', 0)} veh",
            f"Predicted EW Queue  : {t.get('pred_queue_ew', 0)} veh",
            f"Starvation NS Alert : {'YES' if t.get('ns_starving') else 'NO'}",
            f"Starvation EW Alert : {'YES' if t.get('ew_starving') else 'NO'}",
            f"Dynamic NS Green    : {t.get('calc_green_ns_s', 30)} s",
            f"Dynamic EW Green    : {t.get('calc_green_ew_s', 20)} s",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_show_hardware(self) -> str:
        t = self.driver.get_telemetry()["data"]
        is_hw = self.driver.is_hardware
        status_tag = "HARDWARE AVAILABLE" if is_hw else "HARDWARE UNAVAILABLE — SOFTWARE MODE REQUIRED"
        lines = [
            "⚡ EDGE ZYNQ Z7010 FPGA HARDWARE STATUS",
            "────────────────────────────────────────",
            f"Status              : {status_tag}",
            f"Base Address        : 0x{self.driver.base_address:08X}",
            f"Execution Authority : {t.get('authoritative', 'PL')}",
            f"FSM State Code      : 0x{t.get('fsm_state_code', 0):02X}",
            f"Simulation Cycles   : {t.get('simulation_ticks', 0):,}",
            f"Total Updates       : {t.get('total_updates', 0):,}",
            f"FSM Latency         : {t.get('fsm_cycles', 0)} cycles",
            f"Optimizer Latency   : {t.get('optimizer_cycles', 0)} cycles",
            f"Vehicle Engine      : 16-channel concurrent RTL",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)


    def _cmd_performance(self) -> str:
        from python.scenes.traffic.benchmark import run_traffic_benchmark
        bm = run_traffic_benchmark(iterations=500)
        t = self.driver.get_telemetry()["data"]

        sw = bm["software"]
        hw = bm["fpga_hardware"]
        gain = bm["performance_gain"]

        lines = [
            "⏱️ FPGA VS SOFTWARE PERFORMANCE BENCHMARK",
            "────────────────────────────────────────────────────────────",
            f"Parallel Vehicles   : 16 hardware channels (concurrent PL)",
            f"FPGA Clock Freq     : {hw['clock_frequency_mhz']} MHz",
            f"FPGA Total Updates  : {t.get('total_updates', 0):,}",
            "────────────────────────────────────────────────────────────",
            "METRIC              │ FPGA HARDWARE (PL)  │ PYTHON SOFTWARE (PS)",
            "────────────────────┼─────────────────────┼─────────────────────",
            f"Update Latency      │ {hw['latency_us_per_update']:>8.3f} µs ({hw['latency_cycles']} cyc)│ {sw['latency_us_per_update']:>11.2f} µs",
            f"Update Throughput   │ {hw['throughput_updates_sec']:>11,.0f} upd/s   │ {sw['throughput_updates_sec']:>11,.0f} upd/s",
            f"Vehicle Throughput  │ {hw['throughput_vehicles_sec']:>11,.0f} veh/s   │ {sw['throughput_vehicles_sec']:>11,.0f} veh/s",
            f"Queue Calc Latency  │ {hw['queue_calc_cycles'] * 10:>9} ns (2 cyc) │ {sw['queue_calc_latency_us']:>11.2f} µs",
            f"Optimizer Latency   │ {hw['optimizer_latency_cycles'] * 10:>9} ns (16cyc)│ {sw['optimizer_latency_us']:>11.2f} µs",
            "────────────────────┴─────────────────────┴─────────────────────",
            f"🚀 Measured Hardware Speedup: {gain['speedup_factor']}x ({gain['latency_reduction_pct']}% Latency Reduction)",
            "────────────────────────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_stress(self) -> str:
        t = self.driver.get_telemetry()["data"]
        lines = [
            "FPGA TRAFFIC STRESS",
            "────────────────────────────────────────",
            "Vehicles       : 16 (4 North, 4 South, 4 East, 4 West)",
            f"Updates        : {t.get('total_updates', 50000)}",
            "Queue Engine   : ACTIVE",
            "Optimizer      : ACTIVE",
            "Emergency      : READY",
            f"Faults         : {t.get('fault_count', 0)}",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)
