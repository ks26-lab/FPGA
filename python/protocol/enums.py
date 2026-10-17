"""
python.protocol.enums
=====================
Enumerations for universal FPGA communication and scene states.
"""

from enum import Enum, auto


class SceneType(Enum):
    UNDERWATER = "underwater"
    MAZE = "maze"
    MARS = "mars"
    SOLAR = "solar"
    TRAFFIC = "traffic"

    @classmethod
    def from_string(cls, name: str) -> "SceneType":
        cleaned = name.strip().lower()
        mapping = {
            "underwater": cls.UNDERWATER,
            "undersea": cls.UNDERWATER,
            "probe": cls.UNDERWATER,
            "water": cls.UNDERWATER,
            "maze": cls.MAZE,
            "maze_runner": cls.MAZE,
            "mars": cls.MARS,
            "mars_habitat": cls.MARS,
            "habitat": cls.MARS,
            "space": cls.MARS,
            "solar": cls.SOLAR,
            "solar_gimbal": cls.SOLAR,
            "gimbal": cls.SOLAR,
            "traffic": cls.TRAFFIC,
            "city": cls.TRAFFIC,
            "smart_city": cls.TRAFFIC,
        }
        if cleaned in mapping:
            return mapping[cleaned]
        raise ValueError(f"Unknown scene: '{name}'. Available scenes: solar, maze, mars, underwater, traffic")


class ExecutionMode(Enum):
    HARDWARE = "HARDWARE"
    MOCK = "MOCK"


class HardwareStatus(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"
    NOT_PROGRAMMED = "NOT_PROGRAMMED"
