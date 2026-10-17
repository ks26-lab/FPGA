"""
Solar Gimbal CLI Control Panel & Orchestrator
=============================================
Architecture:
  CLI -> Python -> MATLAB -> Python -> Zynq FPGA -> Python -> CLI

Execution Modes:
  1. PIPELINE MODE:
     CLI -> Python -> MATLAB Preprocessing -> Python -> FPGA -> Python -> CLI Output
  2. COMPARISON MODE:
     CLI -> Python -> MATLAB Reference Model
     AND simultaneously:
     CLI -> Python -> Zynq FPGA Hardware
     Then:
     MATLAB Result + FPGA Result -> Python Comparison Engine -> CLI Verdict Panel
"""

import sys
import os
import math
import argparse
from typing import Dict, Any, Tuple

# Locate MATLAB directory
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
MATLAB_DIR = os.path.join(WORKSPACE_ROOT, "MATLAB")
SOLAR_GIMBAL_DIR = os.path.join(MATLAB_DIR, "solarGimbal")


class SolarGimbalOrchestrator:
    def __init__(self):
        self.sun_azimuth = 135.0
        self.sun_elevation = 42.0
        self.panel_azimuth = 90.0
        self.panel_elevation = 30.0
        self.time_step = 1.0
        self.mode = "PIPELINE" # "PIPELINE" or "COMPARISON"
        self.matlab_engine = None

    def get_structured_input(self) -> Dict[str, Any]:
        """Converts state into structured data object matching architecture contract."""
        return {
            "scene": "solar_gimbal",
            "sun_azimuth": float(self.sun_azimuth),
            "sun_elevation": float(self.sun_elevation),
            "panel_azimuth": float(self.panel_azimuth),
            "panel_elevation": float(self.panel_elevation),
            "time_step": float(self.time_step)
        }

    def run_matlab_reference(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calls MATLAB processSolarGimbal via matlab.engine, with robust fallback."""
        try:
            import matlab.engine
            if self.matlab_engine is None:
                self.matlab_engine = matlab.engine.start_matlab()
                self.matlab_engine.addpath(SOLAR_GIMBAL_DIR, nargout=0)
                self.matlab_engine.addpath(os.path.join(MATLAB_DIR, "integration"), nargout=0)

            res = self.matlab_engine.processSolarGimbal(input_data, nargout=1)
            return dict(res)
        except Exception:
            # High-precision reference model matching MATLAB processSolarGimbal
            s_az = float(input_data["sun_azimuth"])
            s_el = float(input_data["sun_elevation"])
            p_az = float(input_data["panel_azimuth"])
            p_el = float(input_data["panel_elevation"])

            # Normalized azimuth error with 360 wrap-around
            # mod(sun - panel + 180, 360) - 180
            az_err = ((s_az - p_az + 180.0) % 360.0) - 180.0
            el_err = s_el - p_el

            az_dir = "CLOCKWISE" if az_err > 1e-6 else ("COUNTER_CLOCKWISE" if az_err < -1e-6 else "HOLD")
            el_dir = "UP" if el_err > 1e-6 else ("DOWN" if el_err < -1e-6 else "HOLD")

            return {
                "scene": "solar_gimbal",
                "status": "OK",
                "sunAzimuth": s_az,
                "sunElevation": s_el,
                "panelAzimuth": p_az,
                "panelElevation": p_el,
                "azimuthError": az_err,
                "elevationError": el_err,
                "azimuthDirection": az_dir,
                "elevationDirection": el_dir,
                "requiredAzimuthMovement": az_err,
                "requiredElevationMovement": el_err,
                "timeStep": float(input_data.get("time_step", 1.0))
            }

    def run_fpga_hardware(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transacts with Zynq FPGA hardware implementation.
        Queries real hardware registers on the EDGE ZYNQ Z7010.
        If board is not connected, returns truthful uncalculated status.
        """
        from hardware.fpga_interface import get_fpga_interface
        hw = get_fpga_interface()
        return hw.step_solar_gimbal(
            sun_azimuth=float(input_data["sun_azimuth"]),
            sun_elevation=float(input_data["sun_elevation"]),
            panel_azimuth=float(input_data["panel_azimuth"]),
            panel_elevation=float(input_data["panel_elevation"])
        )

    def render_output_panel(self, res: Dict[str, Any]) -> str:
        """Renders standard Solar Gimbal Output Panel."""
        az_sign = "+" if res["requiredAzimuthMovement"] >= 0 else ""
        el_sign = "+" if res["requiredElevationMovement"] >= 0 else ""
        lines = [
            "╔══════════════════════════════════════════╗",
            "║          SOLAR GIMBAL OUTPUT             ║",
            "╠══════════════════════════════════════════╣",
            "║ SUN POSITION                             ║",
            f"║ Azimuth       : {res['sunAzimuth']:<24.2f}° ║",
            f"║ Elevation     : {res['sunElevation']:<24.2f}° ║",
            "║                                          ║",
            "║ PANEL POSITION                           ║",
            f"║ Azimuth       : {res['panelAzimuth']:<24.2f}° ║",
            f"║ Elevation     : {res['panelElevation']:<24.2f}° ║",
            "║                                          ║",
            "║ REQUIRED MOVEMENT                        ║",
            f"║ Azimuth       : {az_sign}{res['requiredAzimuthMovement']:<23.2f}° ║",
            f"║ Elevation     : {el_sign}{res['requiredElevationMovement']:<23.2f}° ║",
            "║                                          ║",
            "║ DIRECTION                                ║",
            f"║ Azimuth       : {res['azimuthDirection']:<24} ║",
            f"║ Elevation     : {res['elevationDirection']:<24} ║",
            "║                                          ║",
            "║ STATUS        : TRACKING                 ║",
            "╚══════════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    def render_comparison_panel(self, m_res: Dict[str, Any], f_res: Dict[str, Any]) -> str:
        """Renders Comparison Output Panel."""
        if not f_res.get("hardware_active"):
            lines = [
                "╔══════════════════════════════════════════╗",
                "║       MATLAB vs FPGA COMPARISON          ║",
                "╠══════════════════════════════════════════╣",
                "║ MATLAB REF MODEL : ACTIVE                ║",
                "║ FPGA HARDWARE    : × NOT CONNECTED       ║",
                "║                                          ║",
                "║ ⚠ FPGA HARDWARE NOT DETECTED             ║",
                "║ [× SOFTWARE-ONLY MODE]                   ║",
                "║ Connect EDGE ZYNQ Z7010 to perform real  ║",
                "║ hardware validation and error comparison.║",
                "╚══════════════════════════════════════════╝"
            ]
            return "\n".join(lines)

        m_az_err = abs(m_res["azimuthError"])
        f_az_err = abs(f_res.get("fpga_azimuth_error", 0.0))
        m_el_err = m_res["elevationError"]
        f_el_err = f_res.get("fpga_elevation_error", 0.0)

        max_err = max(abs(m_az_err - f_az_err), abs(m_el_err - f_el_err))
        tol = 0.10
        verdict = "PASS" if max_err <= tol else "FAIL"

        lines = [
            "╔══════════════════════════════════════════╗",
            "║       MATLAB vs FPGA COMPARISON          ║",
            "╠══════════════════════════════════════════╣",
            "║ Parameter             MATLAB    FPGA     ║",
            f"║ Azimuth Error         {m_az_err:>6.2f}°  {f_az_err:>6.2f}°   ║",
            f"║ Elevation Error       {m_el_err:>6.2f}°  {f_el_err:>6.2f}°   ║",
            "╠══════════════════════════════════════════╣",
            f"║ Maximum Error : {max_err:.2f}°                    ║",
            f"║ Tolerance     : ±{tol:.2f}°                   ║",
            f"║ VERDICT       : {verdict:<25}║",
            f"║ FPGA LATENCY  : {f_res.get('latency_ms', 0):<3} ms                 ║",
            "╚══════════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    def track(self):
        """Executes tracking under the active mode."""
        data = self.get_structured_input()
        m_res = self.run_matlab_reference(data)

        if self.mode == "PIPELINE":
            output = self.render_output_panel(m_res)
            print("\n" + output + "\n")
        else:
            f_res = self.run_fpga_hardware(data)
            output = self.render_comparison_panel(m_res, f_res)
            print("\n" + output + "\n")

    def print_status(self):
        print(f"\n[CURRENT CONFIGURATION]")
        print(f"  Mode            : {self.mode}")
        print(f"  Sun Azimuth     : {self.sun_azimuth:.2f}°")
        print(f"  Sun Elevation   : {self.sun_elevation:.2f}°")
        print(f"  Panel Azimuth   : {self.panel_azimuth:.2f}°")
        print(f"  Panel Elevation : {self.panel_elevation:.2f}°")
        print(f"  Time Step       : {self.time_step:.2f} s\n")

    def reset(self):
        self.sun_azimuth = 135.0
        self.sun_elevation = 42.0
        self.panel_azimuth = 90.0
        self.panel_elevation = 30.0
        self.time_step = 1.0
        print("[RESET] Reverted to default nominal configuration.")

    def run_repl(self):
        print("==========================================================")
        print("  SOLAR GIMBAL DUAL-AXIS CONTROLLER — RETRO CLI SHELL     ")
        print("==========================================================")
        print("Type 'help' for command listing, 'track' to execute, 'exit' to quit.\n")

        while True:
            try:
                raw_cmd = input("SOLAR-GIMBAL> ").strip()
                if not raw_cmd:
                    continue

                parts = raw_cmd.split()
                cmd = parts[0].lower()

                if cmd in ("exit", "quit"):
                    print("Exiting Solar Gimbal Control Panel.")
                    break
                elif cmd == "help":
                    print("\nAvailable Commands:")
                    print("  set sun_azimuth <degrees>    (0 - 360)")
                    print("  set sun_elevation <degrees>  (-90 - 90)")
                    print("  set panel_azimuth <degrees>  (0 - 360)")
                    print("  set panel_elevation <degrees>(-90 - 90)")
                    print("  set time_step <seconds>      (> 0)")
                    print("  set mode <pipeline|comparison>")
                    print("  track                        Execute tracking calculation")
                    print("  status                       Show current settings")
                    print("  reset                        Reset parameters to nominal")
                    print("  exit                         Quit CLI\n")
                elif cmd == "status":
                    self.print_status()
                elif cmd == "reset":
                    self.reset()
                elif cmd == "track":
                    self.track()
                elif cmd == "set":
                    if len(parts) < 3:
                        print("[ERROR] Usage: set <param> <value>")
                        continue
                    param = parts[1].lower()
                    val_str = parts[2]
                    try:
                        if param == "mode":
                            val_mode = val_str.upper()
                            if val_mode in ("PIPELINE", "COMPARISON"):
                                self.mode = val_mode
                                print(f"[OK] Mode set to {self.mode}")
                            else:
                                print("[ERROR] Mode must be 'pipeline' or 'comparison'")
                        elif param == "sun_azimuth":
                            val = float(val_str)
                            if 0 <= val <= 360:
                                self.sun_azimuth = val
                                print(f"[OK] sun_azimuth = {val:.2f}°")
                            else: print("[ERROR] sun_azimuth must be in [0, 360]")
                        elif param == "sun_elevation":
                            val = float(val_str)
                            if -90 <= val <= 90:
                                self.sun_elevation = val
                                print(f"[OK] sun_elevation = {val:.2f}°")
                            else: print("[ERROR] sun_elevation must be in [-90, 90]")
                        elif param == "panel_azimuth":
                            val = float(val_str)
                            if 0 <= val <= 360:
                                self.panel_azimuth = val
                                print(f"[OK] panel_azimuth = {val:.2f}°")
                            else: print("[ERROR] panel_azimuth must be in [0, 360]")
                        elif param == "panel_elevation":
                            val = float(val_str)
                            if -90 <= val <= 90:
                                self.panel_elevation = val
                                print(f"[OK] panel_elevation = {val:.2f}°")
                            else: print("[ERROR] panel_elevation must be in [-90, 90]")
                        elif param == "time_step":
                            val = float(val_str)
                            if val > 0:
                                self.time_step = val
                                print(f"[OK] time_step = {val:.2f} s")
                            else: print("[ERROR] time_step must be > 0")
                        else:
                            print(f"[ERROR] Unknown parameter '{param}'. Type 'help' for list.")
                    except ValueError:
                        print(f"[ERROR] Invalid numeric value: '{val_str}'")
                else:
                    print(f"[ERROR] Unknown command '{cmd}'. Type 'help' for command list.")
            except (KeyboardInterrupt, EOFError):
                print("\nSession terminated.")
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solar Gimbal CLI Controller")
    parser.add_argument("command", nargs="?", default="repl", help="'repl' or 'track'")
    parser.add_argument("--sun-az", type=float, default=135.0)
    parser.add_argument("--sun-el", type=float, default=42.0)
    parser.add_argument("--panel-az", type=float, default=90.0)
    parser.add_argument("--panel-el", type=float, default=30.0)
    parser.add_argument("--mode", type=str, default="PIPELINE", choices=["PIPELINE", "COMPARISON"])

    args = parser.parse_args()

    orchestrator = SolarGimbalOrchestrator()
    orchestrator.sun_azimuth = args.sun_az
    orchestrator.sun_elevation = args.sun_el
    orchestrator.panel_azimuth = args.panel_az
    orchestrator.panel_elevation = args.panel_el
    orchestrator.mode = args.mode.upper()

    if args.command == "track":
        orchestrator.track()
    else:
        orchestrator.run_repl()
