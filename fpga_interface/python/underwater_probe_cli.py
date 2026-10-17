"""
fpga_interface.python.underwater_probe_cli
==========================================
Interactive CLI & 3-Panel Visualizer for Zynq Z7010 Underwater Dynamic Probe.

Architecture:
  USER -> CLI -> CommandParser -> FPGADriver -> AXIInterface -> Zynq PL -> Decoded Telemetry -> Renderer

Strict FPGA Rule:
  Python is the communication bridge. FPGA is the authoritative simulation engine.
  All physical motion, collisions, and state transitions originate from the FPGA.
"""

import sys
import os
import time
import argparse
from typing import Optional

# Ensure package root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fpga_interface.python.command_parser import CommandParser, CommandParseError
from fpga_interface.python.fpga_driver import FPGADriver
from fpga_interface.python.telemetry_decoder import Telemetry
from fpga_interface.python.axi_interface import get_axi_interface


def render_3panel_screen(telemetry: Telemetry, mode_name: str, is_hardware: bool) -> str:
    """
    Renders the three-panel underwater visualization driven entirely
    by live telemetry from the FPGA.
    """
    cur_d = telemetry.depth
    tgt_d = telemetry.target_depth
    disp_x = telemetry.displacement_x
    obj = telemetry.active_object

    # --- LEFT PANEL: Environment Visualization ---
    if disp_x > 15:
        probe_art = "             [ PROBE ] →"
    elif disp_x > 5:
        probe_art = "           [ PROBE ] →  "
    elif disp_x < -15:
        probe_art = "← [ PROBE ]             "
    elif disp_x < -5:
        probe_art = "  ← [ PROBE ]           "
    else:
        probe_art = "       [ PROBE ]        "

    obj_art = "                        "
    if obj == "FISH":
        obj_art = "         ><(((°>        "
    elif obj == "GARBAGE":
        obj_art = "        [■ GARBAGE ■]   "
    elif obj == "WHALE":
        obj_art = "     .---.  (WHALE)     "

    if cur_d < tgt_d - 0.5:
        arrow_dir = "          ↓             "
    elif cur_d > tgt_d + 0.5:
        arrow_dir = "          ↑             "
    else:
        arrow_dir = "          •             "

    env_lines = [
        "   UNDERWATER ENVIRONMENT   ",
        "  ~~~~~~~~~~~~~~~~~~~~~~~~  ",
        f"  {obj_art}  ",
        "                            ",
        f"  {arrow_dir}  ",
        f"  {probe_art}  ",
        f"  {arrow_dir}  ",
        "                            ",
        "  ~~~~~~~~~~~~~~~~~~~~~~~~  "
    ]

    # --- CENTER PANEL: Status Readout ---
    col_str = "DETECTED" if telemetry.collision else ("NONE" if obj == "NONE" else f"{obj}")
    rec_str = "ACTIVE" if telemetry.recovery else ("COMPLETE" if telemetry.state == "MOVING_TO_TARGET" and telemetry.collision_count > 0 else "NO")
    tgt_reached_str = "YES (HOLDING)" if telemetry.target_reached else "NO (SEEKING)"

    curr_sign = "+" if telemetry.current_strength >= 0 else ""
    hw_status_tag = "● HARDWARE (AXI MMAP)" if is_hardware else "⚠ SIMULATION (MOCK AXI)"

    direction_str = (
        "DESCENDING" if telemetry.velocity_z > 0.05
        else ("ASCENDING" if telemetry.velocity_z < -0.05 else "HOLDING")
    )

    d_err = getattr(telemetry, "depth_error", tgt_d - cur_d)
    vel_flt = getattr(telemetry, "filtered_velocity", telemetry.velocity_z)
    drag_f = getattr(telemetry, "drag_force", 0.0)
    pid_ctrl = getattr(telemetry, "control_output", 0.0)
    thrust_f = getattr(telemetry, "thrust", 50.0)
    pred_1 = getattr(telemetry, "predicted_depth_1", cur_d)
    pred_3 = getattr(telemetry, "predicted_depth_3", cur_d)
    pred_5 = getattr(telemetry, "predicted_depth_5", cur_d)
    opt_act = getattr(telemetry, "optimization_action", "HOLD")
    fault_str = getattr(telemetry, "fault_str", "NONE")

    center_lines = [
        "┌── STATUS READOUT ─────────────────────────┐",
        f"│ FPGA MODE     : {hw_status_tag:<26}│",
        f"│ CURRENT DEPTH : {cur_d:<5.1f} m                     │",
        f"│ TARGET DEPTH  : {tgt_d:<5.1f} m                     │",
        f"│ DEPTH ERROR   : {d_err:<+5.1f} m                     │",
        f"│ VELOCITY      : {telemetry.velocity_z:<+5.1f} m/s (Flt: {vel_flt:<+5.1f})   │",
        f"│ WATER CURRENT : {curr_sign}{telemetry.current_strength}%                       │",
        f"│ HYDRO DRAG    : {drag_f:<+5.1f} N                     │",
        f"│ PID OUTPUT    : {pid_ctrl:<+5.1f}                     │",
        f"│ THRUST        : {thrust_f:<5.1f} N                     │",
        "├───────────────────────────────────────────┤",
        "│ FPGA COMPUTATION PREDICTION               │",
        f"│   T+1: {pred_1:<5.1f} m | T+3: {pred_3:<5.1f} m | T+5: {pred_5:<5.1f} m │",
        "├───────────────────────────────────────────┤",
        f"│ PROBE STATE   : {telemetry.state:<26}│",
        f"│ IMPACT / OBJ  : {col_str:<26}│",
        f"│ RECOVERY FSM  : {rec_str:<26}│",
        f"│ OPTIMIZER     : {opt_act:<26}│",
        f"│ HARDWARE FAULT: {fault_str:<26}│",
        f"│ FPGA CYCLES   : {telemetry.simulation_cycles:<26}│",
        "└───────────────────────────────────────────┘"
    ]

    # --- RIGHT PANEL: Real-time Depth Scale (0m - 90m) ---
    scale_steps = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
    scale_lines = ["  DEPTH SCALE  ", "───────────────"]
    for s in scale_steps:
        marker = ""
        probe_match = abs(cur_d - s) <= 5.0
        target_match = abs(tgt_d - s) <= 5.0
        if probe_match and target_match and abs(cur_d - tgt_d) < 3.0:
            marker = " ← [PROBE & TARGET]"
        elif probe_match:
            marker = " ← [PROBE]"
        elif target_match:
            marker = " ← [TARGET]"

        scale_lines.append(f"{s:>2} m ──{marker}")

    # Combine 3 columns horizontally
    max_rows = max(len(env_lines), len(center_lines), len(scale_lines))
    output_rows = []
    output_rows.append("╔═══════════════════════════════════════════════════════════════════════════════════════╗")
    output_rows.append("║                   UNDERWATER DYNAMIC PROBE FPGA SIMULATION                            ║")
    output_rows.append("╠═══════════════════════════════════════════════════════════════════════════════════════╣")

    for r in range(max_rows):
        l_txt = env_lines[r] if r < len(env_lines) else " " * 28
        c_txt = center_lines[r] if r < len(center_lines) else " " * 45
        s_txt = scale_lines[r] if r < len(scale_lines) else ""
        output_rows.append(f"║ {l_txt} │ {c_txt} │ {s_txt:<20}║")

    output_rows.append("╚═══════════════════════════════════════════════════════════════════════════════════════╝")
    return "\n".join(output_rows)


def print_help():
    print("""
COMMAND REFERENCE:
  set depth <m>      - Preset current probe depth (0..1000 meters)
  target <m>         - Configure target depth to seek (0..1000 meters)
  current <+/-pct>   - Set water current strength (-100% to +100%)
  disturb <type>     - Inject collision disturbance: fish, garbage, whale
  start              - Begin target-seeking motion on FPGA
  stop               - Pause motion on FPGA
  reset              - Reset FPGA simulation registers to nominal state
  status             - Fetch and display live 3-panel telemetry screen
  poll [seconds]     - Run continuous live display loop (press Ctrl+C to return)
  help               - Show this help reference
  exit / quit        - Terminate session
""")


def run_cli():
    parser = argparse.ArgumentParser(description="Zynq Z7010 Underwater Probe CLI")
    parser.add_argument("--mock", action="store_true", help="Force cycle-accurate mock AXI interface")
    parser.add_argument("--hw", action="store_true", help="Force physical hardware AXI interface")
    args = parser.parse_args()

    # Determine execution mode
    force_mock = True
    if args.hw:
        force_mock = False
    elif not args.mock:
        # Auto-detect: if on Linux with root/mem access, try hardware; otherwise default to mock on Windows
        if sys.platform.startswith("linux") and os.path.exists("/dev/mem"):
            force_mock = False
        else:
            force_mock = True

    try:
        axi = get_axi_interface(force_mock=force_mock)
        fpga = FPGADriver(axi=axi)
    except Exception as exc:
        print(f"\n{exc}\n")
        sys.exit(1)

    mode_label = "[● FPGA HARDWARE ACTIVE]" if fpga.is_hardware else "[⚠ MOCK SIMULATION MODE (Windows/Dev)]"

    print("==========================================================")
    print("   ZYNQ Z7010 FPGA UNDERWATER PROBE — CONTROL PANEL       ")
    print("==========================================================")
    print(f"Status      : {mode_label}")
    print(f"Base Address: 0x43C00000 (M_AXI_GP0)")
    print("Architecture: CLI -> Parser -> FPGADriver -> AXI -> Zynq PL")
    print("Type 'help' for commands, 'start' to begin, 'status' to view screen.\n")

    # Initial status display
    telemetry = fpga.get_telemetry()
    print(render_3panel_screen(telemetry, fpga.mode_name, fpga.is_hardware))

    while True:
        try:
            raw_input_line = input("\nUNDERWATER> ").strip()
            if not raw_input_line:
                continue

            try:
                cmd_obj = CommandParser.parse(raw_input_line)
            except CommandParseError as err:
                print(f"[ERROR] {err}")
                continue

            cmd = cmd_obj["command"]

            if cmd == "NOP":
                continue

            elif cmd == "EXIT":
                print("Terminating underwater probe session.")
                fpga.close()
                break

            elif cmd == "HELP":
                print_help()

            elif cmd == "SET_DEPTH":
                val = cmd_obj["value"]
                res = fpga.set_depth(val)
                print(f"[CLI] Command accepted.")
                print(f"[FPGA] Depth = {res:.1f} m")

            elif cmd == "SET_TARGET":
                val = cmd_obj["value"]
                res = fpga.set_target(val)
                print(f"[CLI] Command accepted.")
                print(f"[FPGA] Target = {res:.1f} m")

            elif cmd == "SET_CURRENT":
                val = cmd_obj["value"]
                res = fpga.set_current(val)
                sign = "+" if res >= 0 else ""
                print(f"[CLI] Command accepted.")
                print(f"[FPGA] Current = {sign}{res}%")

            elif cmd == "DISTURB":
                d_type = cmd_obj["type"]
                res = fpga.disturb(d_type)
                print(f"[CLI] Command accepted.")
                print(f"[FPGA] Disturbance injected: {res}. Collision strobe asserted.")

            elif cmd == "START":
                fpga.start()
                print(f"[CLI] Command accepted.")
                print("[FPGA] Simulation started.")

            elif cmd == "STOP":
                fpga.stop()
                print(f"[CLI] Command accepted.")
                print("[FPGA] Simulation stopped.")

            elif cmd == "RESET":
                reset_t = fpga.reset()
                print(f"[CLI] Command accepted.")
                print("[FPGA] Reset successful.")
                print(f"[FPGA] Depth: {reset_t.depth:.1f} m | Target: {reset_t.target_depth:.1f} m | State: {reset_t.state}")

            elif cmd == "STATUS":
                t = fpga.get_telemetry()
                print("\n" + render_3panel_screen(t, fpga.mode_name, fpga.is_hardware))

            elif cmd == "POLL":
                interval = cmd_obj.get("interval", 0.5)
                print(f"[CLI] Polling FPGA telemetry every {interval:.2f}s. Press Ctrl+C to return to prompt.\n")
                try:
                    while True:
                        t = fpga.get_telemetry()
                        # Clear screen or print screen
                        print("\033[H\033[J", end="") # ANSI clear screen
                        print(render_3panel_screen(t, fpga.mode_name, fpga.is_hardware))
                        print(f"\n[POLLING AT {1.0/interval:.1f} Hz] Press Ctrl+C to exit poll mode...")
                        time.sleep(interval)
                except KeyboardInterrupt:
                    print("\n[CLI] Polling paused. Returned to command prompt.")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting underwater probe session.")
            fpga.close()
            break


if __name__ == "__main__":
    run_cli()
