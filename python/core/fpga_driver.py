"""
python.core.fpga_driver
=======================
Common base FPGA driver providing low-level, scene-agnostic AXI register access.
Scene drivers inherit from this class to implement scene-specific commands and telemetry.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from python.core.axi_interface import AXIInterface


class BaseFPGADriver(ABC):
    """
    Common hardware communication base class for all FPGA scenes.
    Provides fundamental 32-bit register reads/writes and telemetry query contract.
    Does NOT contain scene-specific simulation mathematics.
    """

    def __init__(self, axi: AXIInterface, scene_name: str, base_address: int):
        self.axi = axi
        self.scene_name = scene_name
        self.base_address = base_address

    @property
    def is_hardware(self) -> bool:
        """Returns True if communicating with real FPGA PL registers."""
        return self.axi.is_hardware()

    @property
    def mode_name(self) -> str:
        """Returns hardware execution mode string."""
        return self.axi.get_mode_name()

    def write32(self, offset: int, value: int) -> None:
        """Writes a 32-bit unsigned integer to the peripheral register."""
        self.axi.write32(offset, value)

    def read32(self, offset: int) -> int:
        """Reads a 32-bit unsigned integer from the peripheral register."""
        return self.axi.read32(offset)

    @abstractmethod
    def reset(self) -> None:
        """Sends hardware reset pulse to the scene peripheral."""
        pass

    @abstractmethod
    def get_telemetry(self) -> Dict[str, Any]:
        """Reads live hardware registers and returns structured telemetry envelope."""
        pass

    @abstractmethod
    def get_debug_registers(self) -> Dict[str, Any]:
        """Returns raw hexadecimal register snapshot for hardware diagnostics."""
        pass
