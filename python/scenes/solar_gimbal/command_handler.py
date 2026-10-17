"""
python.scenes.solar_gimbal.command_handler
==========================================
Routes commands to SolarGimbalDriver.
Supports both legacy angle commands and new solar commands:
  solar start [--hw | --software]
  solar configure [--deadband <az> <el>] [--multi-panel]
  solar sun --azimuth <val> --elevation <val>  (or: solar sun <az> <el>)
  solar gimbal --azimuth <val> --elevation <val>  (or: solar gimbal <az> <el>)
  solar track
  solar status
  solar vectors
  solar power
  solar actuator
  solar fpga
  solar performance
  solar stop
  solar reset
"""

from typing import Dict, Any, List
from python.scenes.solar_gimbal.driver import SolarGimbalDriver
from python.scenes.solar_gimbal.benchmark import run_solar_benchmark
from python.protocol.errors import CommandParseError


class SolarGimbalCommandHandler:
    """Dispatches human CLI commands to SolarGimbalDriver."""

    def __init__(self, driver: SolarGimbalDriver):
        self.driver = driver

    def execute(self, command_name: str, args: list) -> str:
        cmd = command_name.lower()

        # ----------------------------------------------------------------------
        # Unified "solar <subcommand>" handler
        # ----------------------------------------------------------------------
        if cmd == "solar":
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
                    self.driver.start()
                    return "[FPGA] Solar tracking computation STARTED (FPGA HARDWARE MODE - Authoritative PL). Active tracking engaged."
                else:
                    self.driver.start()
                    mode_str = "FPGA HARDWARE MODE" if self.driver.is_hardware else "SOFTWARE SIMULATION MODE (Laptop RTL Emulator)"
                    return f"[FPGA] Solar tracking computation STARTED ({mode_str}). Active tracking engaged."

            elif sub == "configure":
                return self._cmd_configure(sub_args)

            elif sub == "status":
                return self._cmd_status()

            elif sub == "track":
                self.driver.start_tracking()
                self.driver.calculate()
                return "[FPGA] Solar tracking ACTIVE. FPGA closed-loop controller running."

            elif sub == "stop":
                self.driver.stop()
                return "[FPGA] Solar tracking STOPPED. Actuators in HOLD."

            elif sub in ("sun", "target"):
                az, el = self._parse_az_el(sub_args, "solar sun")
                self.driver.set_sun_position(az, el)
                self.driver.calculate()
                return f"[FPGA] Target Sun position updated: Azimuth={az:.1f}°, Elevation={el:.1f}°"

            elif sub in ("gimbal", "panel"):
                az, el = self._parse_az_el(sub_args, "solar gimbal")
                self.driver.set_panel_position(az, el)
                self.driver.calculate()
                return f"[FPGA] Gimbal orientation updated: Azimuth={az:.1f}°, Elevation={el:.1f}°"

            elif sub == "vectors":
                return self._cmd_vectors()

            elif sub == "power":
                return self._cmd_power()

            elif sub == "actuator":
                return self._cmd_actuator()

            elif sub == "fpga":
                return self._cmd_fpga()

            elif sub in ("performance", "perf"):
                return self._cmd_performance()

            elif sub == "panels":
                return self._cmd_panels()

            elif sub == "faults":
                return self._cmd_faults()

            elif sub == "auto":
                self.driver.start_tracking()
                self.driver.enable_multi_panel(True)
                self.driver.calculate()
                return "[FPGA] Autonomous mode ENGAGED. 4-panel parallel tracking active in PL."

            elif sub == "reset":
                self.driver.reset()
                return "[FPGA] Solar Gimbal controller reset to baseline state."

            else:
                raise CommandParseError(f"Unknown solar subcommand: '{sub}'")

        # ----------------------------------------------------------------------
        # Legacy command support (e.g. "sun azimuth 120", "set sun az 120")
        # ----------------------------------------------------------------------
        if cmd == "sun" or (cmd == "set" and args and args[0].lower() == "sun"):
            shift = 1 if cmd == "set" else 0
            sub_args = args[shift:]
            if len(sub_args) >= 2 and sub_args[0].replace(".", "", 1).replace("-", "", 1).isdigit():
                az = float(sub_args[0])
                el = float(sub_args[1])
                self.driver.set_sun_position(az, el)
                self.driver.calculate()
                return f"[FPGA] Updated Sun position: Azimuth={az:.1f}°, Elevation={el:.1f}°"
            if len(sub_args) < 2:
                raise CommandParseError("Usage: sun azimuth <val> OR sun elevation <val>")
            prop = sub_args[0].lower()
            try:
                val = float(sub_args[1])
            except ValueError:
                raise CommandParseError(f"Value must be a numeric angle (got {sub_args[1]})")

            cur = self.driver.get_telemetry()["data"]
            s_az = cur["sun_azimuth"]
            s_el = cur["sun_elevation"]
            if "az" in prop:
                s_az = val
            elif "el" in prop:
                s_el = val
            else:
                raise CommandParseError("Specify 'azimuth' or 'elevation'")

            self.driver.set_sun_position(s_az, s_el)
            self.driver.calculate()
            return f"[FPGA] Updated Sun position: Azimuth={s_az:.1f}°, Elevation={s_el:.1f}°"

        elif cmd in ("panel", "gimbal") or (cmd == "set" and args and args[0].lower() in ("panel", "gimbal")):
            shift = 1 if cmd == "set" else 0
            sub_args = args[shift:]
            if len(sub_args) >= 2 and sub_args[0].replace(".", "", 1).replace("-", "", 1).isdigit():
                az = float(sub_args[0])
                el = float(sub_args[1])
                self.driver.set_panel_position(az, el)
                self.driver.calculate()
                return f"[FPGA] Updated Panel position: Azimuth={az:.1f}°, Elevation={el:.1f}°"
            if len(sub_args) < 2:
                raise CommandParseError("Usage: panel azimuth <val> OR panel elevation <val>")
            prop = sub_args[0].lower()
            try:
                val = float(sub_args[1])
            except ValueError:
                raise CommandParseError(f"Value must be a numeric angle (got {sub_args[1]})")

            cur = self.driver.get_telemetry()["data"]
            p_az = cur["panel_azimuth"]
            p_el = cur["panel_elevation"]
            if "az" in prop:
                p_az = val
            elif "el" in prop:
                p_el = val
            else:
                raise CommandParseError("Specify 'azimuth' or 'elevation'")

            self.driver.set_panel_position(p_az, p_el)
            self.driver.calculate()
            return f"[FPGA] Updated Panel position: Azimuth={p_az:.1f}°, Elevation={p_el:.1f}°"

        elif cmd in ("calculate", "calc", "track"):
            self.driver.calculate()
            return "[FPGA] Solar tracking calculation strobe triggered."

        elif cmd == "status":
            return self._cmd_status()

        elif cmd == "reset":
            self.driver.reset()
            return "[FPGA] Solar Gimbal controller reset to baseline."

        raise CommandParseError(f"Unknown solar command: '{command_name}'")

    def _parse_az_el(self, args: list, usage_prefix: str) -> tuple:
        """Parses azimuth and elevation supporting both flags and positional arguments."""
        az = None
        el = None
        idx = 0
        while idx < len(args):
            tok = args[idx].lower()
            if tok in ("--azimuth", "-az", "--az") and idx + 1 < len(args):
                az = float(args[idx + 1])
                idx += 2
            elif tok in ("--elevation", "-el", "--el") and idx + 1 < len(args):
                el = float(args[idx + 1])
                idx += 2
            else:
                if az is None:
                    try:
                        az = float(tok)
                    except ValueError:
                        pass
                elif el is None:
                    try:
                        el = float(tok)
                    except ValueError:
                        pass
                idx += 1

        if az is None or el is None:
            raise CommandParseError(f"Usage: {usage_prefix} --azimuth <val> --elevation <val> (or {usage_prefix} <az> <el>)")
        return az, el

    def _cmd_configure(self, args: list) -> str:
        """Configures deadband, multi-panel mode, or controller parameters."""
        if not args:
            return "[FPGA] Usage: solar configure [--deadband <az> <el>] [--multi-panel on|off] [--mppt on|off]"

        msg_parts = []
        if "--deadband" in args:
            idx = args.index("--deadband")
            if idx + 2 < len(args):
                try:
                    az_db = float(args[idx + 1])
                    el_db = float(args[idx + 2])
                    self.driver.set_deadband(az_db, el_db)
                    msg_parts.append(f"Deadband set to Az={az_db:.1f}°, El={el_db:.1f}°")
                except ValueError:
                    raise CommandParseError("Deadband values must be numeric degrees.")

        if "--multi-panel" in args:
            idx = args.index("--multi-panel")
            val = True
            if idx + 1 < len(args) and args[idx + 1].lower() in ("0", "false", "off"):
                val = False
            self.driver.enable_multi_panel(val)
            msg_parts.append(f"Multi-panel parallel engine {'ENABLED' if val else 'DISABLED'}")

        if "--mppt" in args or "--optimizer" in args:
            opt_tag = "--mppt" if "--mppt" in args else "--optimizer"
            idx = args.index(opt_tag)
            val = True
            if idx + 1 < len(args) and args[idx + 1].lower() in ("0", "false", "off"):
                val = False
            self.driver.enable_power_optimizer(val)
            msg_parts.append(f"Power optimizer {'ENABLED' if val else 'DISABLED'}")

        if not msg_parts:
            return "[FPGA] Configuration updated."
        return "[FPGA] Configured: " + "; ".join(msg_parts)

    def _cmd_status(self) -> str:
        t = self.driver.get_telemetry()["data"]
        az_act = "HOLD" if t.get("az_hold") else ("STEP →" if t.get("azimuth_direction") == "CLOCKWISE" else "← STEP")
        el_act = "HOLD" if t.get("el_hold") else ("STEP ↑" if t.get("elevation_direction") == "UP" else "↓ STEP")
        faults_str = ", ".join(t.get("fault_list", [])) if t.get("fault_list") else "NONE"
        auth = "FPGA HARDWARE MODE" if "Hardware" in t.get("authoritative", "") else "SOFTWARE SIMULATION MODE"

        lines = [
            "SOLAR GIMBAL — STATUS",
            "────────────────────────────────────────",
            f"OPERATIONAL MODE : {auth}",
            f"SUN POSITION     : AZ {t['sun_azimuth']:>5.1f}° / EL {t['sun_elevation']:>5.1f}°",
            f"GIMBAL POSITION  : AZ {t['panel_azimuth']:>5.1f}° / EL {t['panel_elevation']:>5.1f}°",
            "",
            f"AZIMUTH ERROR    : {t['azimuth_error']:>+5.1f}°",
            f"ELEVATION ERROR  : {t['elevation_error']:>+5.1f}°",
            f"TOTAL ERROR      : {t.get('total_tracking_error_deg', 0.0):>5.2f}°",
            f"TRACKING QUALITY : {t.get('tracking_quality_pct', 100)}%",
            "",
            f"INCIDENT ANGLE   : {t['incident_angle']:>5.2f}° (cos θ = {t['cos_incidence']:.3f})",
            f"SOLAR POWER      : {t['estimated_power']:>5.0f} W (Array: {t['total_array_power']:>5.0f} W)",
            f"POWER LOSS EST.  : {t.get('power_loss_w', 0.0):>5.1f} W",
            "",
            f"AZ ACTUATOR      : {az_act}",
            f"EL ACTUATOR      : {el_act}",
            "",
            f"PARALLEL PANELS  : {t.get('panels_active_count', 4)} ACTIVE",
            f"HARDWARE CYCLES  : {t.get('vector_cycles', 18)} cycles (180 ns)",
            f"SAFETY FAULTS    : {faults_str}",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_vectors(self) -> str:
        """Section 19.D: Vector data engineering view."""
        t = self.driver.get_telemetry()["data"]
        s = t.get("sun_vector", {"x": 0.0, "y": 0.0, "z": 0.0})
        n = t.get("panel_normal", {"x": 0.0, "y": 0.0, "z": 0.0})
        d = t.get("dot_product", 1.0)
        theta = t.get("incident_angle", 0.0)
        cos_t = t.get("cos_incidence", 1.0)

        lines = [
            "☀️ 3D VECTOR & INCIDENT ANGLE PIPELINE (Section 19.D)",
            "────────────────────────────────────────",
            "SUN VECTOR (Sx, Sy, Sz):",
            f"  Sx = {s['x']:>+8.4f} [cos(Es)*cos(As)]",
            f"  Sy = {s['y']:>+8.4f} [cos(Es)*sin(As)]",
            f"  Sz = {s['z']:>+8.4f} [sin(Es)]",
            "",
            "PANEL NORMAL (Nx, Ny, Nz):",
            f"  Nx = {n['x']:>+8.4f} [cos(Eg)*cos(Ag)]",
            f"  Ny = {n['y']:>+8.4f} [cos(Eg)*sin(Ag)]",
            f"  Nz = {n['z']:>+8.4f} [sin(Eg)]",
            "",
            "DOT PRODUCT & INCIDENT ANGLE:",
            f"  Dot Product (D = N · S) : {d:>+8.4f}",
            f"  Cosine Incident [cos(θ)]: {cos_t:>8.3f}",
            f"  Incident Angle (θ)      : {theta:>8.2f}° [arccos(D)]",
            f"  Pipeline Latency        : 7 clock cycles (Trig + Dot Product)",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_power(self) -> str:
        """Section 19.C: Solar power telemetry."""
        t = self.driver.get_telemetry()["data"]
        lines = [
            "☀️ PHOTOVOLTAIC POWER ENGINE (Section 19.C)",
            "────────────────────────────────────────",
            f"Solar Irradiance (I0) : 1361.0 W/m² (Earth AM0/AM1.5)",
            f"Panel Surface Area (A): 18.5 m²",
            f"Panel Efficiency (η)  : 22.5%",
            f"Theoretical Peak Power: 5665 W",
            "",
            f"Incident Angle (θ)    : {t['incident_angle']:.2f}°",
            f"Cosine Incident cos(θ): {t['cos_incidence']:.3f}",
            f"Effective Power (P)   : {t['estimated_power']:.0f} W",
            f"Power Loss Misalign   : {t.get('power_loss_w', 0.0):.1f} W",
            f"Tracking Efficiency   : {t.get('tracking_quality_pct', 100)}%",
            "",
            f"4-Panel Array Total   : {t['total_array_power']:.0f} W",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_actuator(self) -> str:
        """Section 19.E: Actuator status view."""
        t = self.driver.get_telemetry()["data"]
        az_dir = t.get("azimuth_direction", "HOLD")
        el_dir = t.get("elevation_direction", "HOLD")
        az_hold = "YES (Within Deadband)" if t.get("az_hold") else "NO"
        el_hold = "YES (Within Deadband)" if t.get("el_hold") else "NO"
        cmd_az = t.get("actuator_azimuth", 0.0)
        cmd_el = t.get("actuator_elevation", 0.0)
        faults_str = ", ".join(t.get("fault_list", [])) if t.get("fault_list") else "NOMINAL"

        lines = [
            "⚙️ ACTUATOR CONTROLLER STATUS (Section 19.E)",
            "────────────────────────────────────────",
            f"Azimuth Direction   : {az_dir}",
            f"Elevation Direction : {el_dir}",
            f"Azimuth Command     : {cmd_az:>+5.1f}°/step",
            f"Elevation Command   : {cmd_el:>+5.1f}°/step",
            f"Azimuth Deadband    : {az_hold}",
            f"Elevation Deadband  : {el_hold}",
            f"Tracking Alignment  : {'LOCKED' if t.get('tracking_locked') else 'TRACKING'}",
            f"Safety Fault State  : {faults_str}",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_fpga(self) -> str:
        """Section 19.F: FPGA status view."""
        t = self.driver.get_telemetry()["data"]
        auth_mode = "FPGA HARDWARE MODE" if self.driver.is_hardware else "SOFTWARE SIMULATION MODE (RTL Emulated)"
        hw_conn = "CONNECTED" if self.driver.is_hardware else "EMULATED (No /dev/mem)"
        ver = t.get("hardware_version", "0x501A7010")

        lines = [
            "⚡ FPGA SUBSYSTEM STATUS (Section 19.F)",
            "────────────────────────────────────────",
            f"Hardware Connection : {hw_conn}",
            f"Execution Mode      : {auth_mode}",
            f"Hardware Version    : {ver}",
            f"Target Board        : EDGE ZYNQ Z7010 (XC7Z010)",
            f"AXI Base Address    : 0x43C30000",
            f"Hardware State      : {t.get('state_str', 'TRACKING')}",
            f"Computation Counter : {t.get('update_counter', 0)} cycles",
            f"Pipeline Latency    : {t.get('vector_cycles', 18)} clock cycles (180 ns @ 100MHz)",
            f"Parallel Engines    : 4 Channels Active in PL",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_performance(self) -> str:
        """Section 23: Performance measurement benchmark."""
        results = run_solar_benchmark(iterations=1000)
        sw = results["software"]
        fpga = results["fpga"]

        lines = [
            "⏱️ SOLAR COMPUTATION ENGINE PERFORMANCE BENCHMARK (Section 23)",
            "────────────────────────────────────────",
            f"Iterations Evaluated : {results['iterations_tested']} updates (4 panels/update)",
            "",
            "SOFTWARE LATENCY (Python PS):",
            f"  Total Time         : {sw['total_time_s']:.4f} s",
            f"  Latency Per Update : {sw['latency_us_per_update']:.2f} µs",
            f"  Throughput         : {sw['throughput_updates_sec']:,.0f} updates/sec",
            "",
            "FPGA HARDWARE LATENCY (Zynq PL @ 100 MHz):",
            f"  Vector & Dot Latency : {fpga['vector_cycles']} cycles (70.0 ns)",
            f"  Arccos Solver Latency: {fpga['incident_cycles']} cycles (50.0 ns)",
            f"  Power Engine Latency : {fpga['power_cycles']} cycles (60.0 ns)",
            f"  Total Pipeline Latency: {fpga['total_pipeline_cycles']} cycles ({fpga['latency_ns']} ns / {fpga['latency_us_per_update']} µs)",
            f"  Parallel Throughput : {fpga['throughput_updates_sec']:,.0f} updates/sec ({fpga['panels_processed_per_sec']:,.0f} panels/sec)",
            "",
            f"🚀 HARDWARE ACCELERATION SPEEDUP: {results['speedup_factor']:.1f}x faster in PL",
            "────────────────────────────────────────"
        ]
        return "\n".join(lines)

    def _cmd_panels(self) -> str:
        t = self.driver.get_telemetry()["data"]
        panels = t.get("panels", [])
        lines = [
            "⚡ 4-CHANNEL CONCURRENT PARALLEL PANELS (Section 13)",
            "────────────────────────────────────────"
        ]
        for p in panels:
            status = "ONLINE" if p.get("active") else "OFFLINE"
            lines.append(
                f"Panel {p['panel_id']} : Power = {p['power_w']:>5.0f} W | "
                f"θ = {p['incident_angle_deg']:>4.1f}° | [{status}]"
            )
        lines.extend([
            "────────────────────────────────────────",
            f"Total Generated Power : {t['total_array_power']:.0f} W",
            f"Hardware Parallelism  : 4 pipelines simultaneous in PL"
        ])
        return "\n".join(lines)

    def _cmd_faults(self) -> str:
        t = self.driver.get_telemetry()["data"]
        faults = t.get("fault_list", [])
        raw = t.get("fault_flags", 0)
        lines = [
            "🛡️ FPGA HARDWARE FAULT DETECTION (Section 14)",
            "────────────────────────────────────────",
            f"Raw Fault Bitmask : 0x{raw:04X}"
        ]
        if faults:
            lines.append("Active Safety Faults:")
            for f in faults:
                lines.append(f"  ● [CRITICAL] {f}")
        else:
            lines.append("Status: NORMAL — All limits, sensors, and vectors nominal.")
        lines.append("────────────────────────────────────────")
        return "\n".join(lines)
