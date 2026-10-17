"""
python.backends.base_backend
============================
Abstract base class for all execution backends.
Both physical FPGA hardware and the laptop FPGA emulator implement this contract.
Scene drivers interact ONLY with this interface and have zero knowledge of which backend is active.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseExecutionBackend(ABC):
    """Abstract execution backend exposing 32-bit memory-mapped register access."""

    @abstractmethod
    def read32(self, address: int) -> int:
        """Reads a 32-bit unsigned integer from the target address."""
        pass

    @abstractmethod
    def write32(self, address: int, value: int) -> None:
        """Writes a 32-bit unsigned integer to the target address."""
        pass

    @abstractmethod
    def is_hardware(self) -> bool:
        """Returns True if accessing physical FPGA registers, False if laptop emulation."""
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        """Returns human-readable name of the backend."""
        pass

    @abstractmethod
    def get_status_info(self) -> Dict[str, Any]:
        """Returns metadata regarding active backend state."""
        pass

    @abstractmethod
    def tick(self) -> None:
        """Advances logical FPGA simulation tick (noop on live hardware)."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Releases backend resources and handles."""
        pass
