"""
python.core.scene_manager
=========================
Manages scene drivers, coordinates active scene selection, and routes commands.
Seamlessly routes register transactions to either the FPGA Hardware backend or
the Laptop FPGA Emulator via BackendAXIAdapter.
"""

from typing import Dict, Any, Optional

from python.protocol.enums import SceneType
from python.protocol.errors import SceneNotSelectedError, CommandParseError
from python.backends.base_backend import BaseExecutionBackend
from python.core.backend_adapter import BackendAXIAdapter
from python.core.fpga_driver import BaseFPGADriver

from python.scenes.underwater import UnderwaterDriver, UnderwaterCommandHandler, BASE_ADDRESS as ADDR_UNDERWATER
from python.scenes.maze import MazeDriver, MazeCommandHandler, BASE_ADDRESS as ADDR_MAZE
from python.scenes.mars_habitat import MarsHabitatDriver, MarsHabitatCommandHandler, BASE_ADDRESS as ADDR_MARS
from python.scenes.solar_gimbal import SolarGimbalDriver, SolarGimbalCommandHandler, BASE_ADDRESS as ADDR_SOLAR
from python.scenes.traffic import TrafficDriver, TrafficCommandHandler, BASE_ADDRESS as ADDR_TRAFFIC


class SceneManager:
    """Manages scene selection and hardware driver lifetime."""

    def __init__(self, backend: BaseExecutionBackend, single_bitstream_mode: bool = False):
        self.backend = backend
        self.single_bitstream_mode = single_bitstream_mode

        # Base address lookup (if single bitstream mode, all point to 0x43C00000)
        self.address_map = {
            SceneType.UNDERWATER: 0x43C00000 if single_bitstream_mode else ADDR_UNDERWATER,
            SceneType.MAZE:       0x43C00000 if single_bitstream_mode else ADDR_MAZE,
            SceneType.MARS:       0x43C00000 if single_bitstream_mode else ADDR_MARS,
            SceneType.SOLAR:      0x43C00000 if single_bitstream_mode else ADDR_SOLAR,
            SceneType.TRAFFIC:    0x43C00000 if single_bitstream_mode else ADDR_TRAFFIC,
        }

        self.drivers: Dict[SceneType, BaseFPGADriver] = {}
        self.handlers: Dict[SceneType, Any] = {}
        self.active_scene: Optional[SceneType] = None

    def get_driver(self, scene_type: SceneType) -> BaseFPGADriver:
        """Lazily creates and caches the driver for a scene."""
        if scene_type not in self.drivers:
            base_addr = self.address_map[scene_type]
            adapter = BackendAXIAdapter(self.backend, base_addr=base_addr)

            if scene_type == SceneType.UNDERWATER:
                driver = UnderwaterDriver(adapter, base_address=base_addr)
                handler = UnderwaterCommandHandler(driver)
            elif scene_type == SceneType.MAZE:
                driver = MazeDriver(adapter, base_address=base_addr)
                handler = MazeCommandHandler(driver)
            elif scene_type == SceneType.MARS:
                driver = MarsHabitatDriver(adapter, base_address=base_addr)
                handler = MarsHabitatCommandHandler(driver)
            elif scene_type == SceneType.SOLAR:
                driver = SolarGimbalDriver(adapter, base_address=base_addr)
                handler = SolarGimbalCommandHandler(driver)
            elif scene_type == SceneType.TRAFFIC:
                driver = TrafficDriver(adapter, base_address=base_addr)
                handler = TrafficCommandHandler(driver)
            else:
                raise ValueError(f"Unknown scene type: {scene_type}")

            self.drivers[scene_type] = driver
            self.handlers[scene_type] = handler

        return self.drivers[scene_type]

    def set_active_scene(self, scene_type: SceneType) -> None:
        """Selects active scene."""
        self.active_scene = scene_type
        # Ensure driver is initialized and reset
        driver = self.get_driver(scene_type)
        driver.reset()

    def get_active_handler(self) -> Any:
        """Returns the command handler for the active scene."""
        if self.active_scene is None:
            raise SceneNotSelectedError("No scene selected. Use 'scene <name>' first.")
        return self.handlers[self.active_scene]

    def get_active_driver(self) -> BaseFPGADriver:
        """Returns the driver for the active scene."""
        if self.active_scene is None:
            raise SceneNotSelectedError("No scene selected. Use 'scene <name>' first.")
        return self.drivers[self.active_scene]
