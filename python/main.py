#!/usr/bin/env python3
"""
python.main
===========
Primary entrypoint for the Universal Zynq Z7010 FPGA Multi-Scene Control System.
Supports Dual-Execution Architecture:
- Real Zynq FPGA Hardware (/dev/mem via AXI4-Lite)
- Laptop FPGA Emulator (Bit-accurate software RTL models with deterministic tick clock)
"""

import sys
import os
import argparse

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from python.core.runtime import SystemRuntime
from python.cli.cli import UniversalCLI
from python.protocol.errors import HardwareUnavailableError


def main():
    parser = argparse.ArgumentParser(
        description="Zynq Z7010 Universal Multi-Scene FPGA Dual-Execution Control System"
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "fpga", "emulator"],
        default="auto",
        help="Execution mode: 'auto' (detects FPGA, falls back to emulator), 'fpga' (force real hardware), 'emulator' (force laptop RTL emulator)"
    )
    parser.add_argument(
        "--hw",
        action="store_true",
        help="Alias for --mode fpga"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Alias for --mode emulator"
    )
    parser.add_argument(
        "--single-bitstream",
        action="store_true",
        help="Strategy A: Map all scenes to base address 0x43C00000 (one scene programmed at a time)"
    )
    parser.add_argument(
        "--scene",
        type=str,
        default=None,
        help="Optionally activate an initial scene on launch (e.g. underwater, maze, mars, solar, traffic)"
    )

    args = parser.parse_args()

    # Resolve execution mode
    if args.hw:
        mode = "fpga"
    elif args.mock:
        mode = "emulator"
    else:
        mode = args.mode

    try:
        runtime = SystemRuntime(mode=mode, single_bitstream=args.single_bitstream)
    except Exception as exc:
        print(f"\n[FATAL ERROR] Initialization Failed:\n{str(exc)}\n", file=sys.stderr)
        sys.exit(1)

    # Optional initial scene activation
    if args.scene:
        from python.protocol.enums import SceneType
        try:
            st = SceneType(args.scene.lower())
            runtime.scene_mgr.set_active_scene(st)
        except ValueError:
            print(f"[WARNING] Unknown initial scene '{args.scene}'. Launching to global menu.")

    cli = UniversalCLI(runtime)
    try:
        cli.run()
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    main()
