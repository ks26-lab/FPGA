"""
Laptop FPGA Emulator Backend.
Provides register-level AXI4-Lite emulation by dispatching read32/write32
to bit-accurate, cycle-deterministic software RTL models of each scene core.

Adheres strictly to the BaseExecutionBackend contract.
"""

from typing import Dict, Any, Optional
import time
from .base_backend import BaseExecutionBackend
from ..emulation.clock import FPGASimulationClock
from ..emulation.underwater_model import UnderwaterRTLModel
from ..emulation.maze_model import MazeRTLModel
from ..emulation.mars_model import MarsHabitatRTLModel
from ..emulation.solar_model import SolarGimbalRTLModel
from ..emulation.traffic_model import TrafficGridRTLModel

class LaptopFPGAEmulator(BaseExecutionBackend):
    def __init__(self, tick_rate_hz: float = 10.0, enable_autonomous_clock: bool = True):
        self.underwater = UnderwaterRTLModel()
        self.maze = MazeRTLModel()
        self.mars = MarsHabitatRTLModel()
        self.solar = SolarGimbalRTLModel()
        self.traffic = TrafficGridRTLModel()

        self._models = [
            self.underwater,
            self.maze,
            self.mars,
            self.solar,
            self.traffic
        ]

        self.clock = FPGASimulationClock(tick_rate_hz=tick_rate_hz)
        for model in self._models:
            self.clock.register_model(model)

        self._connected = False
        self._autonomous = enable_autonomous_clock

    @property
    def mode_name(self) -> str:
        return "LAPTOP FPGA EMULATION"

    def get_backend_name(self) -> str:
        return "LAPTOP FPGA EMULATION"

    @property
    def is_hardware(self) -> bool:
        return False

    def is_available(self) -> bool:
        # Software RTL emulator is always available on any host machine
        return True

    def open(self):
        self._connected = True
        if self._autonomous:
            self.clock.start_autonomous_ticks()

    def close(self):
        self.clock.stop_autonomous_ticks()
        self._connected = False

    def tick(self):
        """Execute single synchronous clock tick across all models."""
        self.clock.tick()

    def run_ticks(self, count: int):
        """Execute exact count of synchronous clock ticks."""
        self.clock.run_ticks(count)

    def _resolve_target(self, address: int):
        """Map 32-bit physical address to appropriate scene model and register offset."""
        base = address & 0xFFFF0000
        offset = address & 0x0000FFFF

        if base == UnderwaterRTLModel.BASE_ADDR:
            return self.underwater, offset
        elif base == MazeRTLModel.BASE_ADDR:
            return self.maze, offset
        elif base == MarsHabitatRTLModel.BASE_ADDR:
            return self.mars, offset
        elif base == SolarGimbalRTLModel.BASE_ADDR:
            return self.solar, offset
        elif base == TrafficGridRTLModel.BASE_ADDR:
            return self.traffic, offset
        return None, offset

    def read32(self, address: int) -> int:
        model, offset = self._resolve_target(address)
        if model:
            return model.read32(offset)
        return 0

    def write32(self, address: int, value: int):
        model, offset = self._resolve_target(address)
        if model:
            model.write32(offset, value)

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "mode": self.mode_name,
            "is_hardware": False,
            "connected": self._connected,
            "clock_tick_count": self.clock.tick_count,
            "clock_running": self.clock.is_running,
            "tick_rate_hz": self.clock.tick_rate_hz,
            "architecture": "EDGE ZYNQ Z7010 Emulated RTL",
            "models": {
                "underwater": "0x43C00000",
                "maze": "0x43C10000",
                "mars_habitat": "0x43C20000",
                "solar_gimbal": "0x43C30000",
                "traffic": "0x43C40000",
            }
        }
