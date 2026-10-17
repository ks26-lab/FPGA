"""
python.core.runtime
===================
Universal Runtime orchestrator holding system state, active execution backend,
and scene managers.
"""

from typing import Dict, Any, Optional

from python.backends.base_backend import BaseExecutionBackend
from python.backends import detect_and_create_backend
from python.core.backend_adapter import BackendAXIAdapter
from python.core.scene_manager import SceneManager
from python.protocol.enums import ExecutionMode


class SystemRuntime:
    """Universal FPGA Runtime environment."""

    def __init__(self, mode: str = "auto", single_bitstream: bool = False):
        self.requested_mode = mode
        self.single_bitstream = single_bitstream

        # Instantiate authoritative execution backend (Hardware or Laptop Emulator)
        self.backend: BaseExecutionBackend = detect_and_create_backend(mode)
        self.backend.open()

        # Connect scene manager using backend adapter
        self.scene_mgr = SceneManager(
            backend=self.backend,
            single_bitstream_mode=single_bitstream
        )
        self.debug_mode = False

    @property
    def is_hardware(self) -> bool:
        return self.backend.is_hardware

    @property
    def mode_name(self) -> str:
        return self.backend.mode_name

    def set_debug(self, enable: bool):
        self.debug_mode = enable

    def shutdown(self):
        """Releases all hardware/emulation resources."""
        self.backend.close()
