"""
python.core.backend_adapter
===========================
Bridges BaseExecutionBackend (FPGAHardwareBackend / LaptopFPGAEmulator)
into the AXIInterface contract required by BaseFPGADriver.

This guarantees that BaseFPGADriver and all scene drivers remain completely
unaware of whether they are talking to real /dev/mem hardware or the software
RTL emulator backend.
"""

from typing import Dict, Any, Optional
from python.core.axi_interface import AXIInterface
from python.backends.base_backend import BaseExecutionBackend


class BackendAXIAdapter(AXIInterface):
    """Adapts a BaseExecutionBackend to look like a standard AXIInterface."""

    def __init__(self, backend: BaseExecutionBackend, base_addr: int = 0x43C00000):
        self.backend = backend
        self.base_addr = base_addr

    def read32(self, offset: int) -> int:
        # Peripheral offset + base address = physical register address
        return self.backend.read32(self.base_addr + offset)

    def write32(self, offset: int, value: int) -> None:
        self.backend.write32(self.base_addr + offset, value)

    def is_hardware(self) -> bool:
        return self.backend.is_hardware

    def get_mode_name(self) -> str:
        return self.backend.mode_name

    def close(self) -> None:
        # Handled at runtime/backend level
        pass
