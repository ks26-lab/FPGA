"""
python.core.axi_interface
=========================
Unified memory-mapped AXI4-Lite abstraction layer.

Supports:
1. RealAXIInterface: Direct Linux /dev/mem mmap access on Zynq ARM Cortex-A9.
2. MockAXIInterface: Cycle-accurate register mirror executing FPGA RTL logic
   for offline developer testing.
"""

from abc import ABC, abstractmethod
import os
import sys
import struct
import threading
from typing import Dict, Optional

from python.protocol.errors import HardwareUnavailableError


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
        """Returns True if accessing physical FPGA registers via AXI MMAP."""
        pass

    @abstractmethod
    def get_mode_name(self) -> str:
        """Returns human-readable execution mode name."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Releases mmap and file descriptors."""
        pass


class RealAXIInterface(AXIInterface):
    """
    Direct AXI4-Lite interface for Zynq-7000 PL peripherals.
    Maps physical memory through /dev/mem on Zynq ARM Linux (Petalinux/Ubuntu/PYNQ).
    """

    def __init__(self, base_addr: int = 0x43C00000, size: int = 65536):
        self.base_addr = base_addr
        self.size = size
        self.fd: Optional[int] = None
        self.mmap_obj = None

        if not sys.platform.startswith("linux"):
            raise HardwareUnavailableError(
                "ERROR: FPGA hardware interface unavailable.\n"
                f"Direct memory-mapped AXI is only supported natively on Zynq ARM Linux.\n"
                f"Attempted to access physical address: 0x{self.base_addr:08X} from {sys.platform}.\n"
                "To run in simulation mode without hardware, pass --mock."
            )

        try:
            import mmap
            self.fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
            page_size = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096
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
                try:
                    os.close(self.fd)
                except Exception:
                    pass
                self.fd = None
            raise HardwareUnavailableError(
                f"ERROR: FPGA hardware interface unavailable.\n"
                f"Failed to memory-map AXI address 0x{self.base_addr:08X}: {str(exc)}\n"
                "Verify bitstream is programmed, /dev/mem is accessible (sudo/root), and AXI peripheral is mapped."
            ) from exc

    def read32(self, offset: int) -> int:
        if self.mmap_obj is None:
            raise HardwareUnavailableError("AXI hardware interface is closed.")
        pos = self.page_offset + offset
        self.mmap_obj.seek(pos)
        data = self.mmap_obj.read(4)
        return struct.unpack("<I", data)[0]

    def write32(self, offset: int, value: int) -> None:
        if self.mmap_obj is None:
            raise HardwareUnavailableError("AXI hardware interface is closed.")
        pos = self.page_offset + offset
        self.mmap_obj.seek(pos)
        self.mmap_obj.write(struct.pack("<I", value & 0xFFFFFFFF))

    def is_hardware(self) -> bool:
        return True

    def get_mode_name(self) -> str:
        return "HARDWARE_AXI_MMAP"

    def close(self) -> None:
        if self.mmap_obj is not None:
            try:
                self.mmap_obj.close()
            except Exception:
                pass
            self.mmap_obj = None
        if self.fd is not None:
            try:
                os.close(self.fd)
            except Exception:
                pass
            self.fd = None


class MockAXIInterface(AXIInterface):
    """
    Mock AXI Interface backing an in-memory 32-bit register dictionary.
    Each scene driver can register custom read/write hooks or cycle callbacks
    to emulate the exact hardware register responses.
    """

    def __init__(self, base_addr: int = 0x43C00000):
        self.base_addr = base_addr
        self._lock = threading.Lock()
        self.registers: Dict[int, int] = {}
        self.write_hooks = {}
        self.read_hooks = {}

    def read32(self, offset: int) -> int:
        with self._lock:
            if offset in self.read_hooks:
                return self.read_hooks[offset]()
            return self.registers.get(offset, 0)

    def write32(self, offset: int, value: int) -> None:
        with self._lock:
            val32 = value & 0xFFFFFFFF
            self.registers[offset] = val32
            if offset in self.write_hooks:
                self.write_hooks[offset](val32)

    def is_hardware(self) -> bool:
        return False

    def get_mode_name(self) -> str:
        return "MOCK_MODE"

    def close(self) -> None:
        with self._lock:
            self.registers.clear()
            self.write_hooks.clear()
            self.read_hooks.clear()
