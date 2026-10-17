"""
EDGE ZYNQ Z7010 FPGA Hardware Abstraction Layer
===============================================
Exposes authoritative connection management, health metrics, and high-level
scene interaction services.
"""

from hardware.fpga_protocol import (
    FPGAConnectionStatus,
    FPGALinkStatus,
    FPGABitstreamStatus,
    FPGATelemetryStatus,
)
from hardware.fpga_connection import FPGAConnectionManager
from hardware.fpga_health import (
    get_hardware_state,
    format_hardware_badge,
    render_hardware_status_box,
)
from hardware.fpga_interface import FPGAHardwareInterface, get_fpga_interface

__all__ = [
    "FPGAConnectionStatus",
    "FPGALinkStatus",
    "FPGABitstreamStatus",
    "FPGATelemetryStatus",
    "FPGAConnectionManager",
    "get_hardware_state",
    "format_hardware_badge",
    "render_hardware_status_box",
    "FPGAHardwareInterface",
    "get_fpga_interface",
]
