"""
EDGE ZYNQ Z7010 FPGA Communication Protocol Specification
==========================================================
Defines frame formats, opcodes, register offsets, and status codes for
the physical UART/AXI bridge between host PC and Zynq-7000 PL cores.

Frame Format (Binary Packet):
  [0]    SYNC_1    (0xAA)
  [1]    SYNC_2    (0x55)
  [2]    SCENE_ID  (1 byte: 0x01=UNDERSEA, 0x02=SOLAR, 0x03=CITY, 0x04=SPACE, 0x05=MAZE, 0xFF=SYSTEM)
  [3]    OPCODE    (1 byte: 0x01=PING, 0x02=READ_REG, 0x03=WRITE_REG, 0x04=STREAM_REQ)
  [4]    LENGTH    (1 byte: Payload length N, 0-64)
  [5..N+4] PAYLOAD (N bytes)
  [N+5]  CHECKSUM  (1 byte: XOR of bytes 2 through N+4)

Response Frame:
  [0]    RESP_1    (0x55)
  [1]    RESP_2    (0xAA)
  [2]    STATUS    (1 byte: 0x00=OK, 0x01=ERR_CRC, 0x02=ERR_OPCODE, 0x03=NOT_PROGRAMMED)
  [3]    LENGTH    (1 byte: Payload length M)
  [4..M+3] PAYLOAD (M bytes)
  [M+4]  CHECKSUM  (1 byte: XOR of bytes 2 through M+3)
"""

from enum import Enum
from typing import Dict, Any, Optional, Tuple, List


class FPGAConnectionStatus(Enum):
    CONNECTED = "CONNECTED"                              # Hardware responding to live ping
    DETECTED_NOT_PROGRAMMED = "DETECTED_NOT_PROGRAMMED"  # Port detected, no valid handshake reply
    NOT_CONNECTED = "NOT_CONNECTED"                      # No board/port detected
    CONNECTION_LOST = "CONNECTION_LOST"                  # Disconnected during active session
    COMM_ERROR = "COMM_ERROR"                            # Framing/parity/checksum errors


class FPGALinkStatus(Enum):
    ACTIVE = "ACTIVE"
    STANDBY = "STANDBY"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class FPGABitstreamStatus(Enum):
    LOADED = "LOADED"
    NOT_LOADED = "NOT_LOADED"
    UNKNOWN = "UNKNOWN"


class FPGATelemetryStatus(Enum):
    LIVE = "LIVE"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


# Scene Identifiers
SCENE_SYSTEM    = 0xFF
SCENE_UNDERSEA  = 0x01
SCENE_SOLAR     = 0x02
SCENE_CITY      = 0x03
SCENE_SPACE     = 0x04
SCENE_MAZE      = 0x05

# Command Opcodes
OP_PING         = 0x01
OP_READ_REG     = 0x02
OP_WRITE_REG    = 0x03
OP_STEP_SIM     = 0x04
OP_RESET        = 0x05
OP_GET_TELEMETRY= 0x06

# Response Status Codes
STATUS_OK             = 0x00
STATUS_ERR_CRC        = 0x01
STATUS_ERR_OPCODE     = 0x02
STATUS_NOT_READY      = 0x03
STATUS_BUS_ERROR      = 0x04

# Known AXI Base Addresses on Zynq-7000 Memory Map
AXI_BASE_UNDERSEA = 0x43C00000
AXI_BASE_MAZE     = 0x43C10000
AXI_BASE_MARS     = 0x43C20000
AXI_BASE_SOLAR    = 0x43C30000
AXI_BASE_CITY     = 0x43C40000

# Magic handshake signature expected from Zynq ARM PS / PL Bridge
FPGA_MAGIC_SIGNATURE = b"Z7010_FPGA_LIVE"


def calculate_checksum(data: bytes) -> int:
    """Calculates single-byte XOR checksum."""
    c = 0
    for b in data:
        c ^= b
    return c & 0xFF


def build_packet(scene_id: int, opcode: int, payload: bytes = b"") -> bytes:
    """Constructs a framed protocol packet."""
    length = len(payload) & 0xFF
    header = bytes([0xAA, 0x55, scene_id, opcode, length])
    body = header[2:] + payload
    crc = calculate_checksum(body)
    return header + payload + bytes([crc])


def parse_response(raw: bytes) -> Tuple[bool, int, bytes, str]:
    """
    Parses a response frame.
    Returns: (is_valid, status_code, payload, error_message)
    """
    if len(raw) < 5:
        return False, 0xFF, b"", "Packet too short"

    if raw[0] != 0x55 or raw[1] != 0xAA:
        return False, 0xFF, b"", "Invalid sync bytes"

    status_code = raw[2]
    length = raw[3]
    if len(raw) < 5 + length:
        return False, 0xFF, b"", "Truncated payload"

    payload = raw[4:4 + length]
    expected_crc = raw[4 + length]
    actual_crc = calculate_checksum(raw[2:4 + length])

    if expected_crc != actual_crc:
        return False, STATUS_ERR_CRC, b"", f"CRC mismatch (got {actual_crc:02X}, expected {expected_crc:02X})"

    return True, status_code, payload, "OK"
