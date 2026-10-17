"""
tests.test_hardware_failure
===========================
Verifies that hardware mode strictly fails when physical AXI is unavailable
and NEVER silently falls back to mock simulation.
"""

import unittest
import sys
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.core.transport import TransportManager
from python.core.axi_interface import RealAXIInterface
from python.protocol.errors import HardwareUnavailableError


class TestHardwareFailure(unittest.TestCase):

    def test_hardware_mode_fails_on_non_linux_or_missing_devmem(self):
        # Unless running on actual Zynq Linux with /dev/mem, RealAXIInterface MUST raise HardwareUnavailableError
        if not sys.platform.startswith("linux") or not os.path.exists("/dev/mem"):
            with self.assertRaises(HardwareUnavailableError):
                RealAXIInterface(base_addr=0x43C00000)

    def test_transport_manager_no_silent_fallback(self):
        # Force hardware mode (force_mock=False)
        transport_mgr = TransportManager(force_mock=False)
        if not sys.platform.startswith("linux") or not os.path.exists("/dev/mem"):
            with self.assertRaises(HardwareUnavailableError):
                transport_mgr.get_transport(0x43C00000)


if __name__ == "__main__":
    unittest.main()
