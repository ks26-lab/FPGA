"""
fpga_interface.python.axi_interface
===================================
AXI4-Lite register communication abstraction layer.

Supports two distinct execution modes:
  1. RealAXIInterface: Direct physical hardware access via Linux memory-mapped
     I/O (/dev/mem, UIO, or PYNQ MMIO) or hardware transport bridge to Zynq PL.
  2. MockAXIInterface: Local register mirror executing cycle-accurate RTL logic
     matching underwater_probe_core.v for development and unit testing without
     physical hardware attached.
"""

from abc import ABC, abstractmethod
import os
import sys
import time
import struct
import threading
from typing import Dict, Optional

from fpga_interface.python.register_map import (
    AXI_BASE_ADDR,
    REG_CONTROL,
    REG_DEPTH_CFG,
    REG_CURRENT,
    REG_STATUS,
    REG_POSITION,
    REG_COUNTERS,
    REG_CYCLES,
    CTRL_START_BIT,
    CTRL_STOP_BIT,
    CTRL_RESET_BIT,
    CTRL_DISTURB_STROBE_BIT,
    CTRL_DISTURB_TYPE_SHIFT,
    CTRL_DISTURB_TYPE_MASK,
    CTRL_SET_DEPTH_WE_BIT,
)


class AXIInterface(ABC):
    """Abstract base class for 32-bit AXI memory-mapped peripheral access."""

    @abstractmethod
    def read32(self, offset: int) -> int:
        """Reads a 32-bit unsigned integer from register offset."""
        pass

    @abstractmethod
    def write32(self, offset: int, value: int) -> None:
        """Writes a 32-bit unsigned integer to register offset."""
        pass

    @abstractmethod
    def is_hardware(self) -> bool:
        """Returns True if communicating with real Zynq hardware, False if mock."""
        pass

    @abstractmethod
    def get_mode_name(self) -> str:
        """Returns human-readable execution mode name."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes memory map or transport handles."""
        pass


# =============================================================================
# REAL HARDWARE IMPLEMENTATION
# =============================================================================

class RealAXIInterface(AXIInterface):
    """
    Direct AXI4-Lite interface to Zynq-7000 PL peripheral.
    When running directly on the ARM Cortex-A9 under Linux (e.g. Petalinux/Ubuntu/PYNQ),
    maps physical memory via /dev/mem at base address 0x43C00000.
    """
    def __init__(self, base_addr: int = AXI_BASE_ADDR, size: int = 4096):
        self.base_addr = base_addr
        self.size = size
        self.fd: Optional[int] = None
        self.mmap_obj = None

        if not sys.platform.startswith("linux"):
            raise RuntimeError(
                "ERROR: FPGA hardware interface unavailable.\n"
                "Direct memory-mapped AXI is only supported natively on Zynq ARM Linux.\n"
                "Check board connection and AXI peripheral mapping."
            )

        try:
            import mmap
            self.fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
            # Align to system page size
            page_size = os.sysconf("SC_PAGE_SIZE")
            page_addr = self.base_addr & ~(page_size - 1)
            self.page_offset = self.base_addr - page_addr
            self.mmap_obj = mmap.mmap(
                self.fd,
                self.size,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
                offset=page_addr
            )
        except Exception as exc:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None
            raise RuntimeError(
                f"ERROR: FPGA hardware interface unavailable.\n"
                f"Failed to memory-map AXI address 0x{self.base_addr:08X} ({exc}).\n"
                f"Check board connection and AXI peripheral mapping."
            ) from exc

    def read32(self, offset: int) -> int:
        if self.mmap_obj is None:
            raise RuntimeError("AXI hardware interface is closed.")
        pos = self.page_offset + offset
        self.mmap_obj.seek(pos)
        data = self.mmap_obj.read(4)
        return struct.unpack("<I", data)[0]

    def write32(self, offset: int, value: int) -> None:
        if self.mmap_obj is None:
            raise RuntimeError("AXI hardware interface is closed.")
        pos = self.page_offset + offset
        self.mmap_obj.seek(pos)
        self.mmap_obj.write(struct.pack("<I", value & 0xFFFFFFFF))

    def is_hardware(self) -> bool:
        return True

    def get_mode_name(self) -> str:
        return "HARDWARE_AXI_MMAP"

    def close(self) -> None:
        if self.mmap_obj is not None:
            self.mmap_obj.close()
            self.mmap_obj = None
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


# =============================================================================
# MOCK AXI IMPLEMENTATION (Bit-accurate RTL emulation of Verilog modules)
# =============================================================================

class MockAXIInterface(AXIInterface):
    """
    Cycle-accurate register mirror executing underwater_probe_core.v logic.
    Allows thorough end-to-end development, parsing validation, and testing
    on developer workstations without a physical Zynq board attached.
    """
    def __init__(self):
        self._lock = threading.Lock()
        
        # Internal state registers matching underwater_probe_core.v
        self.current_depth = 500       # 50.0 m (scaled x10)
        self.target_depth = 800        # 80.0 m (scaled x10)
        self.set_depth = 500           # 50.0 m preset
        self.current_strength = 20     # +20% default
        self.displacement_x = 0        # 0 = center line
        self.probe_velocity_z = 0      # 0 m/s
        self.probe_state = 0           # 0: IDLE
        self.collision_detected = 0    # bit 4
        self.recovery_active = 0       # bit 5
        self.target_reached = 0        # bit 6
        self.active_object_type = 0    # bits [8:7]
        self.collision_counter = 0     # 16-bit
        self.sim_cycle_counter = 0     # 32-bit
        self.recovery_step_counter = 0

        self._running = True
        self._ticker_thread = threading.Thread(target=self._hardware_clock_loop, daemon=True, name="MockFPGA-Clock")
        self._ticker_thread.start()

    def _hardware_clock_loop(self):
        """Simulates the 10 Hz update_tick in underwater_probe_core.v."""
        while self._running:
            time.sleep(0.1) # 100 ms update rate (10 Hz hardware tick)
            with self._lock:
                self.sim_cycle_counter = (self.sim_cycle_counter + 1) & 0xFFFFFFFF
                depth_error = self.target_depth - self.current_depth

                # -------------------------------------------------------------
                # FSM Transition Logic (matches underwater_probe_core.v)
                # -------------------------------------------------------------
                if self.probe_state == 0:  # STATE_IDLE
                    self.probe_velocity_z = 0
                    self.collision_detected = 0
                    self.recovery_active = 0
                    self.target_reached = 0
                    self.displacement_x = 0

                elif self.probe_state == 1:  # STATE_MOVING_TO_TARGET
                    self.collision_detected = 0
                    self.recovery_active = 0

                    # Current drift: cfg_current_strength >>> 4
                    current_drift = int(self.current_strength) // 16

                    if depth_error > 5:
                        self.current_depth += (5 + current_drift)
                        self.probe_velocity_z = 5 + current_drift
                        self.target_reached = 0
                    elif depth_error < -5:
                        self.current_depth -= (5 - current_drift)
                        self.probe_velocity_z = -5 + current_drift
                        self.target_reached = 0
                    else:
                        self.current_depth += current_drift
                        self.probe_velocity_z = current_drift
                        self.target_reached = 1
                        self.probe_state = 6  # STATE_TARGET_REACHED

                    # Clamp physical limits [0, 1000m -> 0, 10000 units]
                    self.current_depth = max(0, min(10000, self.current_depth))

                elif self.probe_state == 3:  # STATE_COLLISION_DETECTED
                    if self.active_object_type == 1:  # FISH
                        self.displacement_x = 15
                        self.current_depth -= 8
                    elif self.active_object_type == 2:  # GARBAGE
                        self.displacement_x = -28
                        self.current_depth += 14
                    elif self.active_object_type == 3:  # WHALE
                        self.displacement_x = 55
                        self.current_depth -= 32
                    else:
                        self.displacement_x = 10

                    self.recovery_step_counter = 8
                    self.probe_state = 4  # STATE_DISPLACEMENT

                elif self.probe_state == 4:  # STATE_DISPLACEMENT
                    self.collision_detected = 0
                    self.recovery_active = 1
                    self.probe_state = 5  # STATE_RECOVERY

                elif self.probe_state == 5:  # STATE_RECOVERY
                    self.recovery_active = 1
                    # Asymptotic recovery toward X = 0
                    if self.displacement_x > 4:
                        self.displacement_x -= 4
                    elif self.displacement_x < -4:
                        self.displacement_x += 4
                    else:
                        self.displacement_x = 0

                    # Resume target seeking concurrently
                    current_drift = int(self.current_strength) // 16
                    if depth_error > 5:
                        self.current_depth += (4 + current_drift)
                        self.probe_velocity_z = 4 + current_drift
                    elif depth_error < -5:
                        self.current_depth -= (4 - current_drift)
                        self.probe_velocity_z = -4 + current_drift

                    if self.recovery_step_counter > 0:
                        self.recovery_step_counter -= 1
                    else:
                        self.recovery_active = 0
                        self.active_object_type = 0
                        self.probe_state = 1  # Return to MOVING_TO_TARGET

                elif self.probe_state == 6:  # STATE_TARGET_REACHED
                    self.target_reached = 1
                    current_drift = int(self.current_strength) // 16
                    self.current_depth += current_drift
                    self.probe_velocity_z = current_drift
                    if abs(depth_error) > 10:
                        self.probe_state = 1
                        self.target_reached = 0

    def read32(self, offset: int) -> int:
        with self._lock:
            if offset == REG_CONTROL:
                return 0
            elif offset == REG_DEPTH_CFG:
                # {target_depth[15:0], set_depth[15:0]}
                return ((self.target_depth & 0xFFFF) << 16) | (self.set_depth & 0xFFFF)
            elif offset == REG_CURRENT:
                return self.current_strength & 0xFF
            elif offset == REG_STATUS:
                # {23'd0, active_object_type[1:0], target_reached, recovery_active, collision_detected, probe_state[3:0]}
                val = (self.probe_state & 0x0F)
                if self.collision_detected: val |= (1 << 4)
                if self.recovery_active: val |= (1 << 5)
                if self.target_reached: val |= (1 << 6)
                val |= ((self.active_object_type & 0x03) << 7)
                return val
            elif offset == REG_POSITION:
                # {velocity_z[7:0], displacement_x[7:0], current_depth[15:0]}
                v_u8 = self.probe_velocity_z & 0xFF
                d_u8 = self.displacement_x & 0xFF
                c_u16 = self.current_depth & 0xFFFF
                return (v_u8 << 24) | (d_u8 << 16) | c_u16
            elif offset == REG_COUNTERS:
                return self.collision_counter & 0xFFFF
            elif offset == REG_CYCLES:
                return self.sim_cycle_counter & 0xFFFFFFFF
            else:
                return 0xDEADBEEF

    def write32(self, offset: int, value: int) -> None:
        with self._lock:
            if offset == REG_CONTROL:
                # Auto-clear strobes matching RTL behavior
                if (value >> CTRL_START_BIT) & 1:
                    if self.probe_state in (0, 6):
                        self.probe_state = 1  # MOVING_TO_TARGET

                if (value >> CTRL_STOP_BIT) & 1:
                    self.probe_state = 0  # IDLE

                if (value >> CTRL_RESET_BIT) & 1:
                    self.probe_state = 0
                    self.current_depth = 500
                    self.target_depth = 800
                    self.displacement_x = 0
                    self.probe_velocity_z = 0
                    self.collision_detected = 0
                    self.recovery_active = 0
                    self.target_reached = 0
                    self.active_object_type = 0
                    self.collision_counter = 0

                if (value >> CTRL_DISTURB_STROBE_BIT) & 1:
                    if self.probe_state != 0:
                        d_type = (value >> CTRL_DISTURB_TYPE_SHIFT) & CTRL_DISTURB_TYPE_MASK
                        self.active_object_type = d_type
                        self.collision_detected = 1
                        self.collision_counter = (self.collision_counter + 1) & 0xFFFF
                        self.probe_state = 3  # STATE_COLLISION_DETECTED

                if (value >> CTRL_SET_DEPTH_WE_BIT) & 1:
                    self.current_depth = self.set_depth

            elif offset == REG_DEPTH_CFG:
                self.set_depth = value & 0xFFFF
                self.target_depth = (value >> 16) & 0xFFFF

            elif offset == REG_CURRENT:
                # Signed 8-bit
                raw = value & 0xFF
                self.current_strength = raw - 256 if raw >= 128 else raw

    def is_hardware(self) -> bool:
        return False

    def get_mode_name(self) -> str:
        return "MOCK_SIMULATION"

    def close(self) -> None:
        self._running = False


# =============================================================================
# FACTORY DISPATCHER
# =============================================================================

def get_axi_interface(force_mock: bool = False, base_addr: int = AXI_BASE_ADDR) -> AXIInterface:
    """
    Returns appropriate AXIInterface implementation.
    If force_mock is True, returns MockAXIInterface.
    Otherwise attempts RealAXIInterface. If hardware is unavailable, raises RuntimeError.
    """
    if force_mock:
        return MockAXIInterface()

    try:
        return RealAXIInterface(base_addr=base_addr)
    except Exception as exc:
        raise RuntimeError(
            "ERROR: FPGA hardware interface unavailable.\n"
            "Check board connection and AXI peripheral mapping."
        ) from exc
