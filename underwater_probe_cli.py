"""
underwater_probe_cli.py
=======================
Root entrypoint for the Zynq Z7010 FPGA Underwater Dynamic Probe CLI.
Delegates directly to the authoritative fpga_interface.python.underwater_probe_cli module.

Architecture:
  USER -> CLI -> CommandParser -> FPGADriver -> AXIInterface -> Zynq PL -> Decoded Telemetry -> Renderer
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from fpga_interface.python.underwater_probe_cli import run_cli
from fpga_interface.python.fpga_driver import FPGADriver
from fpga_interface.python.axi_interface import get_axi_interface, MockAXIInterface, RealAXIInterface
from fpga_interface.python.command_parser import CommandParser
from fpga_interface.python.telemetry_decoder import Telemetry, decode_telemetry


# Legacy alias for backward compatibility
class FPGAUnderwaterProbeInterface:
    def __init__(self, force_mock: bool = True):
        self.driver = FPGADriver(force_mock=force_mock)

    def set_depth(self, depth: float):
        return self.driver.set_depth(depth)

    def set_target(self, target: float):
        return self.driver.set_target(target)

    def set_current(self, current: int):
        return self.driver.set_current(current)

    def trigger_disturbance(self, d_type: str):
        return self.driver.disturb(d_type)

    def start_movement(self):
        return self.driver.start()

    def stop_movement(self):
        return self.driver.stop()

    def reset_state(self):
        return self.driver.reset()

    def get_status(self):
        return self.driver.get_status()

    def get_telemetry(self):
        return self.driver.get_telemetry()


if __name__ == "__main__":
    run_cli()
