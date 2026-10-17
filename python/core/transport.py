"""
python.core.transport
=====================
Factory and management for AXI transport instances.
Strictly enforces:
- If hardware mode is requested, failure raises HardwareUnavailableError; never silently falls back.
- If mock mode is requested, explicitly instantiates MockAXIInterface.
"""

from typing import Dict
from python.core.axi_interface import AXIInterface, RealAXIInterface, MockAXIInterface
from python.protocol.errors import HardwareUnavailableError


class TransportManager:
    """Manages active AXI peripheral transports mapped by base address."""

    def __init__(self, force_mock: bool = False):
        self.force_mock = force_mock
        self._instances: Dict[int, AXIInterface] = {}

    def get_transport(self, base_addr: int) -> AXIInterface:
        """Returns or creates the transport interface for the requested AXI base address."""
        if base_addr in self._instances:
            return self._instances[base_addr]

        if self.force_mock:
            transport = MockAXIInterface(base_addr=base_addr)
        else:
            # Real hardware mode: If it fails, raise HardwareUnavailableError!
            transport = RealAXIInterface(base_addr=base_addr)

        self._instances[base_addr] = transport
        return transport

    def close_all(self):
        """Closes all open transports."""
        for t in self._instances.values():
            try:
                t.close()
            except Exception:
                pass
        self._instances.clear()
