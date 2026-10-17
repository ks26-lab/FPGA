"""
EDGE ZYNQ Z7010 Hardware State Model & Telemetry Health Presenter
==================================================================
Maintains the single authoritative hardware state model across all scenes
and renders compact, terminal-friendly hardware diagnostic panels.
"""

from typing import Dict, Any, List, Optional, Tuple
from hardware.fpga_protocol import FPGAConnectionStatus
from hardware.fpga_connection import FPGAConnectionManager


class HardwareSnapshot(dict):
    """Dictionary subclass supporting dot-attribute access for backwards compatibility."""
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            return None


def get_hardware_state() -> HardwareSnapshot:
    """Retrieves current authoritative hardware state snapshot."""
    mgr = FPGAConnectionManager()
    return HardwareSnapshot(mgr.get_snapshot())


def format_hardware_badge(state: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
    """
    Returns concise single-line hardware execution mode badge and curses color code.
    Format: (text, curses_color_index)
      1=White/Cyan, 2=Cyan, 3=Yellow, 4=Red, 5=Green
    """
    if state is None:
        state = get_hardware_state()

    status_str = state.get("status", "NOT_CONNECTED")

    if status_str == FPGAConnectionStatus.CONNECTED.value:
        resp = state.get("last_response_ms")
        resp_txt = f"{resp}ms" if resp is not None else "LIVE"
        return f"[● FPGA HARDWARE ACTIVE // {resp_txt}]", 5  # Green

    elif status_str == FPGAConnectionStatus.DETECTED_NOT_PROGRAMMED.value:
        return "[⚠ FPGA DETECTED — BITSTREAM NOT READY]", 3   # Yellow

    elif status_str == FPGAConnectionStatus.CONNECTION_LOST.value:
        return "[× FPGA CONNECTION LOST — SOFTWARE-ONLY]", 4  # Red

    else:
        return "[× FPGA NOT CONNECTED — SOFTWARE ONLY]", 4    # Red/Warning


def render_hardware_status_box(state: Optional[Dict[str, Any]] = None, width: int = 40) -> List[Tuple[str, int]]:
    """
    Renders the persistent compact Hardware Status UI panel exactly matching
    the specification in the prompt.
    Returns: list of (line_text, color_pair_id)
    """
    if state is None:
        state = get_hardware_state()

    status_str = state.get("status", "NOT_CONNECTED")
    dev_name = state.get("device", "EDGE ZYNQ Z7010")
    w = max(38, width)
    inner_w = w - 4

    lines = []
    top_bar = "┌" + "─" * (w - 2) + "┐"
    bot_bar = "└" + "─" * (w - 2) + "┘"

    if status_str == FPGAConnectionStatus.CONNECTED.value:
        lines.append((top_bar, 1))
        lines.append((f"│ HARDWARE STATUS{' ' * (inner_w - 15)} │", 2))
        lines.append((f"│{' ' * inner_w}  │", 1))
        lines.append((f"│ FPGA : {dev_name:<{inner_w - 7}} │", 1))
        lines.append((f"│ ● CONNECTED{' ' * (inner_w - 11)} │", 5))
        lines.append((f"│ LINK : ACTIVE{' ' * (inner_w - 13)} │", 5))
        lines.append((f"│ BITSTREAM : LOADED{' ' * (inner_w - 18)} │", 4 if state.get('bitstream') != 'LOADED' else 5))
        lines.append((f"│ TELEMETRY : LIVE{' ' * (inner_w - 16)} │", 5))
        resp_ms = state.get('last_response_ms')
        resp_str = f"{resp_ms:.0f} ms" if resp_ms is not None else "OK"
        lines.append((f"│ LAST RESPONSE : {resp_str:<{inner_w - 16}} │", 1))
        lines.append((bot_bar, 1))

    elif status_str == FPGAConnectionStatus.DETECTED_NOT_PROGRAMMED.value:
        lines.append((top_bar, 3))
        lines.append((f"│ HARDWARE STATUS{' ' * (inner_w - 15)} │", 3))
        lines.append((f"│ FPGA : {dev_name:<{inner_w - 7}} │", 1))
        lines.append((f"│ ⚠ DETECTED{' ' * (inner_w - 10)} │", 3))
        lines.append((f"│ BITSTREAM : NOT LOADED{' ' * (inner_w - 22)} │", 3))
        lines.append((f"│ STATUS : NOT READY{' ' * (inner_w - 18)} │", 3))
        port = state.get('port') or "COM?"
        lines.append((f"│ PORT : {port:<{inner_w - 7}} │", 1))
        lines.append((bot_bar, 3))

    else:  # NOT_CONNECTED or CONNECTION_LOST
        lines.append((top_bar, 4 if status_str == FPGAConnectionStatus.CONNECTION_LOST.value else 1))
        lines.append((f"│ HARDWARE STATUS{' ' * (inner_w - 15)} │", 2))
        lines.append((f"│{' ' * inner_w}  │", 1))
        lines.append((f"│ FPGA : {dev_name:<{inner_w - 7}} │", 1))
        lost_tag = "× CONNECTION LOST" if status_str == FPGAConnectionStatus.CONNECTION_LOST.value else "× NOT CONNECTED"
        lines.append((f"│ {lost_tag:<{inner_w}} │", 4))
        lines.append((f"│ LINK : OFFLINE{' ' * (inner_w - 14)} │", 4))
        lines.append((f"│{' ' * inner_w}  │", 1))
        lines.append((f"│ ⚠ FPGA HARDWARE NOT INCLUDED{' ' * (inner_w - 28)} │", 3))
        lines.append((f"│ SOFTWARE-ONLY MODE{' ' * (inner_w - 18)} │", 3))
        lines.append((bot_bar, 1))

    return lines
