"""
python.scenes.underwater.command_handler
========================================
Routes parsed commands to the UnderwaterDriver.
"""

from typing import Dict, Any
from python.scenes.underwater.driver import UnderwaterDriver
from python.protocol.errors import CommandParseError


class UnderwaterCommandHandler:
    """Dispatches human CLI commands to UnderwaterDriver."""

    def __init__(self, driver: UnderwaterDriver):
        self.driver = driver

    def execute(self, command_name: str, args: list) -> str:
        cmd = command_name.lower()
        if cmd == "set" and len(args) >= 2 and args[0].lower() == "depth":
            try:
                depth = float(args[1])
                if not (0.0 <= depth <= 1000.0):
                    raise ValueError()
            except ValueError:
                raise CommandParseError(f"Depth must be a float between 0.0 and 1000.0 (got {args[1]})")
            self.driver.set_depth(depth)
            return f"[FPGA] Depth configuration set to {depth:.1f} m"

        elif cmd == "target":
            if not args:
                raise CommandParseError("Usage: target <meters>")
            try:
                target = float(args[0])
                if not (0.0 <= target <= 1000.0):
                    raise ValueError()
            except ValueError:
                raise CommandParseError(f"Target depth must be a float between 0.0 and 1000.0 (got {args[0]})")
            self.driver.set_target(target)
            return f"[FPGA] Target depth set to {target:.1f} m"

        elif cmd == "current":
            if not args:
                raise CommandParseError("Usage: current <signed percentage -100 to +100>")
            try:
                raw_str = args[0].lstrip("+")
                curr = int(raw_str)
                if not (-100 <= curr <= 100):
                    raise ValueError()
            except ValueError:
                raise CommandParseError(f"Current must be an integer between -100 and +100 (got {args[0]})")
            self.driver.set_current(curr)
            sign = "+" if curr >= 0 else ""
            return f"[FPGA] Water current set to {sign}{curr}%"

        elif cmd == "disturb":
            if not args:
                raise CommandParseError("Usage: disturb <whale|fish|garbage>")
            d_type = args[0].upper()
            if d_type not in ["WHALE", "FISH", "GARBAGE"]:
                raise CommandParseError(f"Invalid disturbance '{args[0]}'. Allowed: whale, fish, garbage")
            self.driver.disturb(d_type)
            return f"[FPGA] Disturbance injected: {d_type}"

        elif cmd == "start":
            self.driver.start()
            return "[FPGA] Probe movement started"

        elif cmd == "stop":
            self.driver.stop()
            return "[FPGA] Probe movement stopped"

        elif cmd == "prediction":
            telem = self.driver.get_telemetry()
            d = telem["data"]
            return (
                f"[FPGA FUTURE DEPTH PROJECTION]\n"
                f"  Current Depth : {d['depth']:.1f} m (Target: {d['target_depth']:.1f} m)\n"
                f"  Predicted T+1 : {d['predicted_depth_1']:.1f} m\n"
                f"  Predicted T+3 : {d['predicted_depth_3']:.1f} m\n"
                f"  Predicted T+5 : {d['predicted_depth_5']:.1f} m"
            )

        elif cmd == "faults":
            telem = self.driver.get_telemetry()
            d = telem["data"]
            flags = d["fault_flags"]
            active = d["active_faults"]
            active_str = ", ".join(active) if active else "NONE (NOMINAL)"
            return f"[FPGA HARDWARE FAULT STATUS]\n  Flags: 0x{flags:02X}\n  Active Faults: {active_str}"

        elif cmd == "pid":
            telem = self.driver.get_telemetry()
            d = telem["data"]
            return (
                f"[FPGA PID DEPTH CONTROLLER]\n"
                f"  Error     : {d['depth_error']:+.1f} m\n"
                f"  P-term    : {d['p_term']:+.1f}\n"
                f"  I-term    : {d['i_term']:+.1f}\n"
                f"  D-term    : {d['d_term']:+.1f}\n"
                f"  Output    : {d['control_output']:+.1f}\n"
                f"  Thrust    : {d['thrust']:.1f} N (Delta: {d['thrust_delta']:+.1f} N)"
            )

        raise CommandParseError(f"Unknown underwater command: '{command_name}'")
