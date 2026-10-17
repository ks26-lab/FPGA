"""
EDGE ZYNQ Z7010 FPGA Physical Connection Manager & Monitor
===========================================================
Discovers physical USB-UART / JTAG / Serial interfaces, conducts genuine
hardware handshakes, and continuously monitors live link health in a background
daemon thread.

CRITICAL HARDWARE RULE:
- NEVER assumes or hardcodes FPGA_CONNECTED = True.
- Only sets CONNECTED if a real hardware ping frame succeeds.
- Immediately detects disconnection when physical USB cable is detached.
"""

import sys
import os
import time
import threading
from typing import Dict, Any, Optional, List, Tuple

from hardware.fpga_protocol import (
    FPGAConnectionStatus,
    FPGALinkStatus,
    FPGABitstreamStatus,
    FPGATelemetryStatus,
    SCENE_SYSTEM,
    OP_PING,
    FPGA_MAGIC_SIGNATURE,
    build_packet,
    parse_response,
    STATUS_OK,
)


def list_candidate_serial_ports() -> List[Dict[str, str]]:
    """
    Discovers available serial COM ports on the system.
    Tries pyserial list_ports first, falls back to Windows Registry queries.
    """
    candidates = []

    # Method 1: pyserial discovery (if installed)
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        for p in ports:
            candidates.append({
                "port": p.device,
                "description": p.description or "",
                "hwid": p.hwid or ""
            })
        if candidates:
            return candidates
    except ImportError:
        pass

    # Method 2: Native Windows Registry query (Standard Library winreg)
    if sys.platform.startswith("win"):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
            i = 0
            while True:
                try:
                    val_name, port_val, _ = winreg.EnumValue(key, i)
                    candidates.append({
                        "port": str(port_val),
                        "description": f"Windows Device: {val_name}",
                        "hwid": ""
                    })
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass

    return candidates


class FPGAConnectionManager:
    """
    Authoritative hardware connection controller for EDGE ZYNQ Z7010.
    Manages physical transport, handshakes, ping heartbeats, and fault handling.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, target_port: Optional[str] = None, baudrate: int = 115200):
        if getattr(self, "_initialized", False):
            return

        self.target_port = target_port
        self.baudrate = baudrate
        self.serial_handle = None

        # Live Authoritative Hardware State
        self.status = FPGAConnectionStatus.NOT_CONNECTED
        self.link = FPGALinkStatus.OFFLINE
        self.bitstream = FPGABitstreamStatus.NOT_LOADED
        self.telemetry = FPGATelemetryStatus.UNAVAILABLE
        self.active_port: Optional[str] = None
        self.last_response_ms: Optional[float] = None
        self.last_handshake_time: float = 0.0
        self.packets_sent: int = 0
        self.packets_received: int = 0
        self.packet_errors: int = 0
        self.active_function: str = "SYSTEM_IDLE"
        self.error_message: Optional[str] = None

        # Threading for background monitoring
        self._monitor_running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._io_lock = threading.Lock()
        self._initialized = True

        # Start continuous hardware monitoring daemon
        self.start_monitoring()

    def start_monitoring(self):
        """Launches background dynamic connection monitor thread."""
        if self._monitor_running:
            return
        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="FPGA-Monitor")
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stops background monitor thread."""
        self._monitor_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)

    def _monitor_loop(self):
        """Periodic background poll detecting plug/unplug events at ~3Hz."""
        while self._monitor_running:
            try:
                self.check_hardware_health()
            except Exception as ex:
                self.error_message = f"Monitor fault: {str(ex)}"
            time.sleep(0.35)

    def check_hardware_health(self):
        """
        Polls physical interface.
        If port is closed: scans candidate COM ports and attempts handshake.
        If port is open: sends PING heartbeat frame and measures round-trip latency.
        """
        with self._io_lock:
            # Case 1: Device was connected; verify it is still actively responding
            if self.serial_handle is not None:
                is_alive = self._send_ping_probe()
                if not is_alive:
                    # Physical disconnect or timeout occurred!
                    self._handle_disconnect("Ping timeout / Physical connection lost")
                return

            # Case 2: Not currently connected; scan for candidate Zynq ports
            candidates = list_candidate_serial_ports()
            if not candidates:
                self.status = FPGAConnectionStatus.NOT_CONNECTED
                self.link = FPGALinkStatus.OFFLINE
                self.bitstream = FPGABitstreamStatus.NOT_LOADED
                self.telemetry = FPGATelemetryStatus.UNAVAILABLE
                self.active_port = None
                self.last_response_ms = None
                return

            # Try candidate ports
            for cand in candidates:
                port_name = cand["port"]
                desc = cand.get("description", "").lower()
                # Prioritize Zynq / FTDI / CP210x / Silicon Labs bridges
                opened, programmed = self._attempt_port_handshake(port_name)
                if opened and programmed:
                    self.status = FPGAConnectionStatus.CONNECTED
                    self.link = FPGALinkStatus.ACTIVE
                    self.bitstream = FPGABitstreamStatus.LOADED
                    self.telemetry = FPGATelemetryStatus.LIVE
                    self.active_port = port_name
                    self.error_message = None
                    return
                elif opened and not programmed:
                    self.status = FPGAConnectionStatus.DETECTED_NOT_PROGRAMMED
                    self.link = FPGALinkStatus.STANDBY
                    self.bitstream = FPGABitstreamStatus.NOT_LOADED
                    self.telemetry = FPGATelemetryStatus.UNAVAILABLE
                    self.active_port = port_name
                    self.error_message = "Zynq port detected but PL bitstream not responding"
                    return

            # Ports found, but none is an active FPGA
            self.status = FPGAConnectionStatus.NOT_CONNECTED
            self.link = FPGALinkStatus.OFFLINE
            self.bitstream = FPGABitstreamStatus.NOT_LOADED
            self.telemetry = FPGATelemetryStatus.UNAVAILABLE
            self.active_port = None

    def _attempt_port_handshake(self, port_name: str) -> Tuple[bool, bool]:
        """
        Attempts to open port and send protocol PING.
        Returns: (port_opened: bool, handshake_success: bool)
        """
        try:
            import serial
        except ImportError:
            # Without pyserial, physical hardware communication cannot proceed
            self.error_message = "pyserial not installed: physical COM access unavailable"
            return False, False

        try:
            ser = serial.Serial(
                port=port_name,
                baudrate=self.baudrate,
                timeout=0.08,
                write_timeout=0.08
            )
        except Exception:
            return False, False

        # Port opened successfully. Now test for live FPGA bitstream response!
        ping_packet = build_packet(SCENE_SYSTEM, OP_PING, b"PING")
        t_start = time.perf_counter()
        try:
            ser.write(ping_packet)
            self.packets_sent += 1
            resp_bytes = ser.read(32)
            t_end = time.perf_counter()

            if resp_bytes:
                valid, status, payload, err = parse_response(resp_bytes)
                if valid and status == STATUS_OK:
                    self.serial_handle = ser
                    self.last_response_ms = round((t_end - t_start) * 1000.0, 1)
                    self.last_handshake_time = time.time()
                    self.packets_received += 1
                    return True, True
        except Exception:
            pass

        # Port open but did not reply with valid FPGA bitstream response
        try:
            ser.close()
        except Exception:
            pass
        return True, False

    def _send_ping_probe(self) -> bool:
        """Sends a single heartbeat PING to verify live link."""
        if not self.serial_handle:
            return False

        ping_packet = build_packet(SCENE_SYSTEM, OP_PING, b"PING")
        t_start = time.perf_counter()
        try:
            self.serial_handle.write(ping_packet)
            self.packets_sent += 1
            resp = self.serial_handle.read(32)
            t_end = time.perf_counter()

            if resp:
                valid, status, payload, err = parse_response(resp)
                if valid and status == STATUS_OK:
                    self.last_response_ms = round((t_end - t_start) * 1000.0, 1)
                    self.last_handshake_time = time.time()
                    self.packets_received += 1
                    return True
                else:
                    self.packet_errors += 1
        except Exception as ex:
            self.error_message = f"Link error: {str(ex)}"

        return False

    def _handle_disconnect(self, reason: str):
        """Immediately transitions state to DISCONNECTED / CONNECTION_LOST."""
        if self.serial_handle:
            try:
                self.serial_handle.close()
            except Exception:
                pass
            self.serial_handle = None

        if self.status == FPGAConnectionStatus.CONNECTED:
            self.status = FPGAConnectionStatus.CONNECTION_LOST
        else:
            self.status = FPGAConnectionStatus.NOT_CONNECTED

        self.link = FPGALinkStatus.OFFLINE
        self.bitstream = FPGABitstreamStatus.NOT_LOADED
        self.telemetry = FPGATelemetryStatus.UNAVAILABLE
        self.last_response_ms = None
        self.error_message = reason

    def transact(self, scene_id: int, opcode: int, payload: bytes = b"", timeout: float = 0.1) -> Tuple[bool, bytes, str]:
        """
        Thread-safe packet transaction with physical FPGA.
        Returns: (success: bool, response_payload: bytes, error_msg: str)
        """
        with self._io_lock:
            if not self.serial_handle or self.status != FPGAConnectionStatus.CONNECTED:
                return False, b"", "FPGA hardware not connected"

            pkt = build_packet(scene_id, opcode, payload)
            t_start = time.perf_counter()
            try:
                self.serial_handle.write(pkt)
                self.packets_sent += 1
                resp = self.serial_handle.read(64)
                t_end = time.perf_counter()

                if not resp:
                    self.packet_errors += 1
                    return False, b"", "Hardware response timed out"

                valid, status_code, resp_payload, err = parse_response(resp)
                if not valid:
                    self.packet_errors += 1
                    return False, b"", f"Protocol error: {err}"

                self.last_response_ms = round((t_end - t_start) * 1000.0, 1)
                self.packets_received += 1
                return True, resp_payload, "OK"
            except Exception as ex:
                self.packet_errors += 1
                self._handle_disconnect(f"IO Error: {str(ex)}")
                return False, b"", f"Hardware IO fault: {str(ex)}"

    def get_snapshot(self) -> Dict[str, Any]:
        """Returns instantaneous snapshot of authoritative hardware connection state."""
        return {
            "device": "EDGE ZYNQ Z7010",
            "status": self.status.value,
            "link": self.link.value,
            "bitstream": self.bitstream.value,
            "telemetry": self.telemetry.value,
            "port": self.active_port,
            "last_response_ms": self.last_response_ms,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "packet_errors": self.packet_errors,
            "active_function": self.active_function,
            "error_message": self.error_message,
            "is_connected": (self.status == FPGAConnectionStatus.CONNECTED)
        }
