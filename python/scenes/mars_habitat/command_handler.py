"""
python.scenes.mars_habitat.command_handler
==========================================
Routes human CLI commands to MarsHabitatDriver.
Supports both unified 'mars <subcommand>' commands and legacy standalone commands:
  mars start [--hw | --software]
  mars configure [--threshold-a <val>] [--threshold-b <val>]
  mars launch
  mars abort
  mars status
  mars landing
  mars meteorites [start | stop | <count>]
  mars attack [big | normal] [segment | section] [A | B | ALL] [count]
  mars habitat
  mars faults
  mars fpga
  mars performance
  mars reset
"""

from typing import Dict, Any, List
from python.scenes.mars_habitat.driver import MarsHabitatDriver
from python.scenes.mars_habitat.benchmark import run_mars_benchmark
from python.protocol.errors import CommandParseError


class MarsHabitatCommandHandler:
    """Dispatches human CLI commands to MarsHabitatDriver."""

    def __init__(self, driver: MarsHabitatDriver):
        self.driver = driver
        self.default_batch_count = 10

    def execute(self, command_name: str, args: List[str]) -> str:
        cmd = command_name.lower()

        # ---------------------------------------------------------------------
        # Unified "mars <subcommand>" Dispatcher (Section 22 & 23)
        # ---------------------------------------------------------------------
        if cmd == "mars":
            if not args:
                return self._cmd_status()
            sub = args[0].lower()
            sub_args = args[1:]

            if sub == "start":
                if "--hw" in sub_args:
                    if not self.driver.is_hardware:
                        return (
                            "[HARDWARE UNAVAILABLE — SOFTWARE SIMULATION MODE REQUIRED] "
                            "FPGA hardware interface /dev/mem not detected on this system."
                        )
                    self.driver.start_landing()
                    return "[FPGA] Mars Habitat & Landing Accelerator STARTED (FPGA HARDWARE MODE - Authoritative PL)."
                else:
                    self.driver.start_landing()
                    mode_str = "FPGA HARDWARE MODE" if self.driver.is_hardware else "SOFTWARE SIMULATION MODE (Laptop RTL Emulator)"
                    return f"[FPGA] Mars Habitat & Landing Accelerator STARTED ({mode_str})."

            elif sub == "configure":
                return self._cmd_configure(sub_args)

            elif sub == "launch":
                self.driver.launch()
                return "[FPGA] Powered descent sequence LAUNCHED. Closed-loop retro-thrust controller active in PL."

            elif sub == "abort":
                self.driver.abort()
                return "[FPGA] Mars descent sequence ABORTED. Thrusters commanded to safe state."

            elif sub == "status":
                return self._cmd_status()

            elif sub == "landing":
                return self._cmd_landing()

            elif sub == "meteorites":
                return self._cmd_meteorites(sub_args)

            elif sub == "attack":
                return self._cmd_attack(sub_args)

            elif sub == "habitat":
                return self._cmd_habitat()

            elif sub == "faults":
                return self._cmd_faults()

            elif sub == "fpga":
                return self._cmd_fpga()

            elif sub in ("performance", "perf"):
                return self._cmd_performance()

            elif sub == "reset":
                self.driver.reset()
                return "[FPGA] Mars Space Habitat reset to nominal operational state."

            else:
                raise CommandParseError(f"Unknown mars subcommand: '{sub}'")

        # ---------------------------------------------------------------------
        # Legacy Standalone Commands
        # ---------------------------------------------------------------------
        subcmd = args[0].lower() if args else ""

        if cmd == "landing":
            if subcmd == "start":
                self.driver.start_landing()
                return "[FPGA] Initiated closed-loop powered landing descent simulation."
            elif subcmd in ("status", ""):
                return self._cmd_landing()
            else:
                raise CommandParseError("Usage: landing [status|start]")

        elif cmd == "meteorites" or (cmd == "set" and len(args) >= 2 and args[0].lower() == "meteorites"):
            arg_idx = 0 if cmd == "meteorites" else 1
            return self._cmd_meteorites(args[arg_idx:])

        elif cmd == "habitat":
            return self._cmd_habitat()

        elif cmd in ("life", "lifesupport", "life_support"):
            return self._cmd_life_support()

        elif cmd in ("hazards", "hazard"):
            return self._cmd_hazards()

        elif cmd in ("performance", "perf"):
            return self._cmd_performance()

        elif cmd in ("faults", "fault"):
            return self._cmd_faults()

        elif cmd == "telemetry":
            return self._cmd_telemetry_dump()

        elif cmd == "attack":
            return self._cmd_attack(args)

        elif cmd == "threshold" or (cmd == "set" and len(args) >= 3 and args[0].lower() == "threshold"):
            shift = 1 if cmd == "set" else 0
            if len(args) < shift + 2:
                raise CommandParseError("Usage: threshold <A|B> <value>")
            sec = args[shift].upper()
            try:
                val = float(args[shift + 1])
            except ValueError:
                raise CommandParseError(f"Threshold value must be a float (got {args[shift + 1]})")

            cur = self.driver.get_telemetry()["data"]
            th_a = cur["threshold_A"]
            th_b = cur["threshold_B"]
            if sec == "A": th_a = val
            elif sec == "B": th_b = val
            else:
                raise CommandParseError("Section must be 'A' or 'B'")

            self.driver.set_thresholds(th_a, th_b)
            return f"[FPGA] Updated thresholds: Section A={th_a:.1f}, Section B={th_b:.1f}"

        elif cmd == "reset":
            self.driver.reset()
            return "[FPGA] Mars Space Habitat reset to nominal operational state."

        raise CommandParseError(f"Unknown mars command: '{command_name}'")

    # -------------------------------------------------------------------------
    # Helper Command Implementations
    # -------------------------------------------------------------------------
    def _cmd_configure(self, args: List[str]) -> str:
        """Configures damage thresholds or batch parameters."""
        if not args:
            return "[FPGA] Usage: mars configure [--threshold-a <val>] [--threshold-b <val>] [--batch <count>]"

        cur = self.driver.get_telemetry()["data"]
        th_a = cur.get("threshold_A", 70.0)
        th_b = cur.get("threshold_B", 65.0)
        msg_parts = []

        idx = 0
        while idx < len(args):
            tok = args[idx].lower()
            if tok in ("--threshold-a", "-ta") and idx + 1 < len(args):
                th_a = float(args[idx + 1])
                msg_parts.append(f"Threshold A={th_a:.1f}")
                idx += 2
            elif tok in ("--threshold-b", "-tb") and idx + 1 < len(args):
                th_b = float(args[idx + 1])
                msg_parts.append(f"Threshold B={th_b:.1f}")
                idx += 2
            elif tok in ("--batch", "-b") and idx + 1 < len(args):
                self.default_batch_count = int(args[idx + 1])
                msg_parts.append(f"Batch={self.default_batch_count}")
                idx += 2
            else:
                idx += 1

        self.driver.set_thresholds(th_a, th_b)
        if not msg_parts:
            return "[FPGA] Configuration updated."
        return "[FPGA] Configured: " + "; ".join(msg_parts)

    def _cmd_status(self) -> str:
        """Comprehensive operational status display."""
        t = self.driver.get_telemetry()["data"]
        auth = "FPGA HARDWARE MODE" if self.driver.is_hardware else "SOFTWARE SIMULATION MODE (RTL Emulated)"
        link_str = "ISOLATED (BREACH CONTAINED)" if t.get("link_closed") else "OPEN (NOMINAL)"

        lines = [
            "MARS SPACE HABITAT & LANDING ACCELERATOR — STATUS",
            "────────────────────────────────────────────────────────",
            f"OPERATIONAL MODE : {auth}",
            f"SYSTEM STATE     : {t.get('state_str', 'OPERATIONAL')} (Cycles: {t.get('simulation_cycles', 0):,})",
            "",
            "DESCENT & LANDING TRAJECTORY:",
            f"  Landing Stage  : {t.get('landing_fsm', 'PREP')} [{t.get('landing_status', 'SAFE')}]",
            f"  Altitude       : {t.get('landing_altitude', 0.0):>6.1f} m",
            f"  Velocity       : {t.get('landing_velocity', 0.0):>+6.1f} m/s",
            f"  Acceleration   : {t.get('landing_acceleration', 0.0):>+6.1f} m/s²",
            f"  Retro-Thrust   : {t.get('thrust_command', 0.0):>5.1f} % [{(t.get('thrust_command', 0.0)/100.0)*8000.0:>6.1f} N]",
            f"  Touchdown Pred : {t.get('predicted_touchdown_velocity', 0.0):>+6.1f} m/s",
            "",
            "PARALLEL METEORITE FIELD (8 CHANNELS):",
            f"  Active Stream  : {t.get('meteorite_active_count', 0)} Channels Active [Mask: 0x{t.get('meteorite_active_mask', 0):02X}]",
            f"  Total Impacts  : {t.get('total_impacts', 0)} hits ({t.get('critical_impact_count', 0)} critical)",
            f"  Accum. Energy  : {t.get('total_impact_energy', 0.0):.1f} kJ",
            "",
            "HABITAT STRUCTURAL INTEGRITY:",
            f"  Section A Hull : {t.get('section_A', 'OPERATIONAL')} (Damage: {t.get('damage_A', 0.0):.1f}%)",
            f"  Section B Hull : {t.get('section_B', 'OPERATIONAL')} (Damage: {t.get('damage_B', 0.0):.1f}%)",
            f"  Inter-Link     : {link_str}",
            f"  Recovery Action: {t.get('recovery_action', 'NO_ACTION')}",
            "",
            "ENVIRONMENT & LIFE SUPPORT:",
            f"  Oxygen (O2)    : {t.get('o2_percent', 20.9):.1f} %",
            f"  Cabin Pressure : {t.get('pressure_kpa', 101.3):.1f} kPa",
            f"  Temperature    : {t.get('temperature_c', 21.0):.1f} °C",
            f"  Overall Health : {t.get('habitat_health', 100)} % [{t.get('life_support_status', 'STABLE')}]",
            f"  Safety Faults  : {', '.join(t.get('faults', [])) if t.get('faults') else 'NOMINAL'}",
            "────────────────────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_landing(self) -> str:
        """Section 21.A/B: Landing telemetry view."""
        t = self.driver.get_telemetry()["data"]
        thrust_n = (t.get("thrust_command", 0.0) / 100.0) * 8000.0
        lines = [
            "🚀 MARS LANDING DESCENT & RETRO-THRUST CONTROLLER",
            "────────────────────────────────────────────────────────",
            f"Landing Stage      : {t.get('landing_fsm', 'PREP')}",
            f"Touchdown Status   : {'TOUCHDOWN CONFIRMED' if t.get('touchdown') else 'IN FLIGHT'}",
            f"Altitude           : {t.get('landing_altitude', 0.0):.1f} m",
            f"Vertical Velocity  : {t.get('landing_velocity', 0.0):+.1f} m/s",
            f"Acceleration       : {t.get('landing_acceleration', 0.0):+.1f} m/s²",
            f"Retro-Thrust Demand: {t.get('thrust_command', 0.0):.1f} % ({thrust_n:.1f} N / 8000 N Max)",
            f"Target Altitude    : 0.0 m (Ground Level)",
            f"Descent Risk Level : {t.get('landing_status', 'SAFE')}",
            f"Projected T+5 Alt  : {t.get('predicted_altitude', 0.0):.1f} m",
            f"Projected Touchdown: {t.get('predicted_touchdown_velocity', 0.0):+.1f} m/s",
            "────────────────────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_meteorites(self, args: List[str]) -> str:
        """Section 21.C: Meteorite engine view."""
        if args and args[0].lower() == "start":
            self.driver.start_parallel_meteorites()
            return "[FPGA] Enabled 8-channel parallel meteorite trajectory engine in PL."
        elif args and args[0].lower() == "stop":
            self.driver.stop_parallel_meteorites()
            return "[FPGA] Disabled parallel meteorite engine."
        elif args and args[0].isdigit():
            cnt = max(1, min(255, int(args[0])))
            self.default_batch_count = cnt
            return f"[FPGA] Configured default meteorite batch size: {cnt}"

        t = self.driver.get_telemetry()["data"]
        lines = [
            "☄️ 8-CHANNEL CONCURRENT PARALLEL METEORITE ENGINE",
            "────────────────────────────────────────────────────────",
            f"Active Channels    : {t.get('meteorite_active_count', 0)} / 8 Channels Active",
            f"Active Bitmask     : 0x{t.get('meteorite_active_mask', 0):02X}",
            f"Impact Vector      : 0x{t.get('meteorite_impact_vector', 0):02X}",
            f"Total Processed    : {t.get('meteorites_processed', 0):,} Meteorites",
            f"Total Impacts      : {t.get('total_impacts', 0):,} Hits",
            f"Critical Breaches  : {t.get('critical_impact_count', 0):,} High-Energy Impacts",
            f"Total Kinetic Energy: {t.get('total_impact_energy', 0.0):.1f} kJ (E = 0.5 * m * v²)",
            f"Execution Pipeline : 8 Simultaneous Trajectories Updated in PL",
            "────────────────────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_attack(self, args: List[str]) -> str:
        """Preserves legacy meteorite attack syntax."""
        atk_type = "NORMAL"
        target = "ALL"
        count = self.default_batch_count

        idx = 0
        while idx < len(args):
            a = args[idx].upper()
            if a in ("NORMAL", "BIG"):
                atk_type = a
            elif a in ("SEGMENT", "SECTION"):
                if idx + 1 < len(args):
                    idx += 1
                    target = args[idx].upper()
            elif a in ("A", "B", "ALL"):
                target = a
            elif a.isdigit():
                count = int(a)
            idx += 1

        self.driver.attack(attack_type=atk_type, target=target, count=count)
        return f"[FPGA] Executed {atk_type} attack ({count} meteorites) targeting Section {target}."

    def _cmd_habitat(self) -> str:
        """Section 21.E: Habitat status view."""
        t = self.driver.get_telemetry()["data"]
        lines = [
            "🛡️ MARS SPACE HABITAT INTEGRITY & SECTION ISOLATION",
            "────────────────────────────────────────────────────────",
            f"Section A Hull     : {t.get('section_A', 'OPERATIONAL')} (Damage: {t.get('damage_A', 0.0):.1f}%)",
            f"Section B Hull     : {t.get('section_B', 'OPERATIONAL')} (Damage: {t.get('damage_B', 0.0):.1f}%)",
            f"Interconnecting Link: {'ISOLATED' if t.get('link_closed') else 'OPEN (NOMINAL)'}",
            f"Threshold A Setting : {t.get('threshold_A', 70.0):.1f}%",
            f"Threshold B Setting : {t.get('threshold_B', 65.0):.1f}%",
            f"Threshold Crossed   : {'YES' if t.get('threshold_crossed') else 'NO'}",
            f"Composite Health    : {t.get('habitat_health', 100)} %",
            f"Automated Action    : {t.get('recovery_action', 'NO_ACTION')}",
            "────────────────────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_faults(self) -> str:
        """Section 16: Hardware fault monitor view."""
        t = self.driver.get_telemetry()["data"]
        faults_list = t.get("faults", [])
        lines = [
            "⚠️ FPGA HARDWARE SAFETY SUPERVISOR",
            "────────────────────────────────────────────────────────",
            f"Raw Fault Bitmask  : 0x{t.get('fault_flags', 0):04X}",
            f"Active Breaches    : {len(faults_list)} Condition(s) Detected"
        ]
        if faults_list:
            for f in faults_list:
                lines.append(f"  ● [CRITICAL] {f}")
        else:
            lines.append("  ● Status: NOMINAL (All sensors, vectors, and limits valid)")
        lines.append("────────────────────────────────────────────────────────")
        return "\n".join(lines)

    def _cmd_fpga(self) -> str:
        """Section 21.G: FPGA status view."""
        t = self.driver.get_telemetry()["data"]
        auth_mode = "FPGA HARDWARE MODE" if self.driver.is_hardware else "SOFTWARE SIMULATION MODE (RTL Emulated)"
        hw_conn = "CONNECTED" if self.driver.is_hardware else "EMULATED (No /dev/mem)"

        lines = [
            "⚡ FPGA SUBSYSTEM STATUS",
            "────────────────────────────────────────────────────────",
            f"Hardware Connection: {hw_conn}",
            f"Execution Mode     : {auth_mode}",
            f"Core Version Tag   : {t.get('core_version', '0x4D415253')} ('MARS')",
            f"Target Board       : EDGE ZYNQ Z7010 (XC7Z010-1CLG400C)",
            f"AXI Base Address   : 0x43C20000",
            f"Clock Frequency    : 100.0 MHz",
            f"Pipeline Latency   : {t.get('latency_cycles', 18)} clock cycles (180 ns)",
            f"Simulation Cycles  : {t.get('simulation_cycles', 0):,}",
            f"Meteorites Processed: {t.get('meteorites_processed', 0):,}",
            "────────────────────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_performance(self) -> str:
        """Section 26: Performance benchmark view."""
        results = run_mars_benchmark(iterations=1000)
        sw = results["software"]
        fpga = results["fpga"]

        lines = [
            "⏱️ MARS COMPUTATIONAL ENGINE PERFORMANCE BENCHMARK (Section 26)",
            "────────────────────────────────────────────────────────",
            f"Iterations Evaluated : {results['iterations_tested']} ticks (8 parallel meteorites/tick)",
            "",
            "SOFTWARE LATENCY (Python Host PS):",
            f"  Total Time         : {sw['total_time_s']:.4f} s",
            f"  Latency Per Update : {sw['latency_us_per_update']:.2f} µs",
            f"  Throughput         : {sw['throughput_updates_sec']:,.0f} updates/sec",
            f"  Meteorite Rate     : {sw['meteorites_processed_per_sec']:,.0f} meteorites/sec",
            "",
            "FPGA HARDWARE LATENCY (Zynq PL @ 100 MHz):",
            f"  Pipeline Latency   : {fpga['latency_cycles']} clock cycles ({fpga['latency_ns']} ns / {fpga['latency_us_per_update']} µs)",
            f"  Parallel Channels  : 8 Concurrent Trajectory Engines",
            f"  Throughput         : {fpga['throughput_updates_sec']:,.0f} updates/sec",
            f"  Meteorite Rate     : {fpga['meteorites_processed_per_sec']:,.0f} meteorites/sec",
            "",
            f"🚀 HARDWARE ACCELERATION SPEEDUP: {results['speedup_factor']:.1f}x faster in PL",
            "────────────────────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_life_support(self) -> str:
        t = self.driver.get_telemetry()["data"]
        return (
            "LIFE SUPPORT SUBSYSTEM\n"
            f"Status            : {t.get('life_support_status', 'STABLE')}\n"
            f"Health Score      : {t.get('habitat_health', 100)} %\n"
            f"O2 Concentration  : {t.get('o2_percent', 20.9):.1f} %\n"
            f"CO2 Concentration : {t.get('co2_percent', 0.04):.2f} %\n"
            f"Cabin Pressure    : {t.get('pressure_kpa', 101.3):.1f} kPa\n"
            f"Temperature       : {t.get('temperature_c', 21.0):.1f} °C"
        )

    def _cmd_hazards(self) -> str:
        t = self.driver.get_telemetry()["data"]
        faults_str = ", ".join(t.get("faults", [])) if t.get("faults") else "NONE"
        return (
            "PREDICTIVE HAZARD STATUS\n"
            f"Hazard Score      : {t.get('hazard_score', 0)}/100\n"
            f"Hazard Level      : {t.get('hazard_status', 'NORMAL')}\n"
            f"Landing Risk      : {t.get('landing_status', 'SAFE')}\n"
            f"Critical Impacts  : {t.get('critical_impact_count', 0)}\n"
            f"Active Breaches   : {faults_str}"
        )

    def _cmd_telemetry_dump(self) -> str:
        t = self.driver.get_telemetry()["data"]
        return (
            "MARS HABITAT TELEMETRY\n"
            f"Landing: alt={t.get('landing_altitude', 0.0):.1f}m vel={t.get('landing_velocity', 0.0):.1f}m/s thrust={t.get('thrust_command', 0.0):.1f}%\n"
            f"Meteorites: active={t.get('meteorite_active_count', 0)} hits={t.get('total_impacts', 0)} crit={t.get('critical_impact_count', 0)}\n"
            f"Habitat: A={t.get('section_A', 'OPERATIONAL')} B={t.get('section_B', 'OPERATIONAL')} link={t.get('link_status', 'OPEN')}\n"
            f"Life Support: O2={t.get('o2_percent', 20.9):.1f}% CO2={t.get('co2_percent', 0.04):.2f}% pres={t.get('pressure_kpa', 101.3):.1f}kPa temp={t.get('temperature_c', 21.0):.1f}C\n"
            f"Health: {t.get('habitat_health', 100)}% Hazard: {t.get('hazard_status', 'NORMAL')} Cycles: {t.get('simulation_cycles', 0):,}"
        )
