"""
python.backends.fpga_backend
============================
Physical FPGA hardware execution backend.
Maps physical AXI4-Lite registers via /dev/mem on Zynq-7000 ARM Linux.
"""

import sys
import os
import struct
from typing import Dict, Any, Optional

from python.backends.base_backend import BaseExecutionBackend
from python.protocol.errors import HardwareUnavailableError


class FPGAHardwareBackend(BaseExecutionBackend):
    """
    Direct memory-mapped AXI4-Lite backend for the EDGE ZYNQ Z7010 board.
    Operates natively on ARM Cortex-A9 running embedded Linux.
    """

    def __init__(self, base_addr: int = 0x43C00000, size: int = 0x50000):
        self.base_addr = base_addr
        self.size = size
        self.fd: Optional[int] = None
        self.mmap_obj = None

        if not sys.platform.startswith("linux"):
            raise HardwareUnavailableError(
                "ERROR: FPGA hardware interface unavailable.\n"
                f"Direct memory-mapped AXI requires Zynq ARM Linux with /dev/mem.\n"
                f"Attempted physical access from non-Linux platform: {sys.platform}."
            )

        if not os.path.exists("/dev/mem"):
            raise HardwareUnavailableError(
                "ERROR: /dev/mem not found on this system.\n"
                "Kernel must be compiled with CONFIG_DEVMEM=y and run with root privileges."
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
                f"ERROR: Failed to memory-map AXI aperture 0x{self.base_addr:08X}: {str(exc)}\n"
                "Ensure root/sudo permissions and valid PL bitstream programming."
            ) from exc

    def read32(self, address: int) -> int:
        if self.mmap_obj is None:
            raise HardwareUnavailableError("Hardware AXI bus interface is closed.")
        offset = address - self.base_addr
        pos = self.page_offset + offset
        self.mmap_obj.seek(pos)
        data = self.mmap_obj.read(4)
        return struct.unpack("<I", data)[0]

    def write32(self, address: int, value: int) -> None:
        if self.mmap_obj is None:
            raise HardwareUnavailableError("Hardware AXI bus interface is closed.")
        offset = address - self.base_addr
        pos = self.page_offset + offset
        self.mmap_obj.seek(pos)
        self.mmap_obj.write(struct.pack("<I", value & 0xFFFFFFFF))

    def is_hardware(self) -> bool:
        return True

    def get_backend_name(self) -> str:
        return "FPGA HARDWARE"

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "backend": "FPGA HARDWARE",
            "hardware_connected": True,
            "transport": "AXI4-Lite (/dev/mem)",
            "processor": "Zynq ARM Cortex-A9",
            "base_aperture": f"0x{self.base_addr:08X}",
            "computation_model": "RTL in Programmable Logic"
        }

    def tick(self) -> None:
        """Hardware ticks autonomously via 50 MHz FPGA clock oscillator."""
        pass

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
