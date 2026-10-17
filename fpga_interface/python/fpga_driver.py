"""
fpga_interface.python.fpga_driver
=================================
High-level FPGA Driver for the Zynq Z7010 Underwater Dynamic Probe.
Owns all AXI communication, register encoding, and telemetry retrieval.

The CLI communicates strictly with this driver; it never directly touches
AXI register addresses.
"""

from typing import Dict, Any, Optional

from fpga_interface.python.axi_interface import AXIInterface, get_axi_interface
from fpga_interface.python.protocol import (
    depth_to_fpga_units,
    validate_current,
    parse_disturb_type,
    DISTURB_CODE_TO_NAME,
)
from fpga_interface.python.register_map import (
    REG_CONTROL,
    REG_DEPTH_CFG,
    REG_CURRENT,
    REG_STATUS,
    REG_POSITION,
    REG_COUNTERS,
    REG_CYCLES,
    pack_control,
    pack_depth_cfg,
    unpack_depth_cfg,
    pack_current,
)
from fpga_interface.python.telemetry_decoder import Telemetry, decode_telemetry


class FPGADriver:
    """
    Authoritative hardware driver for the underwater_probe_axi_slave.v peripheral.
    """
    def __init__(self, axi: Optional[AXIInterface] = None, force_mock: bool = False):
        if axi is not None:
            self.axi = axi
        else:
            self.axi = get_axi_interface(force_mock=force_mock)

    @property
    def is_hardware(self) -> bool:
        """Returns True if connected to real hardware AXI, False if mock."""
        return self.axi.is_hardware()

    @property
    def mode_name(self) -> str:
        """Returns execution mode string."""
        return self.axi.get_mode_name()

    # -------------------------------------------------------------------------
    # Core Control APIs
    # -------------------------------------------------------------------------
    def set_depth(self, depth_m: float) -> float:
        """
        Sets the probe's current depth in meters.
        1. Encodes depth in 0.1 m FPGA units.
        2. Preserves the currently configured target depth in DEPTH_CFG.
        3. Writes to DEPTH_CFG.
        4. Strobes cfg_set_depth_we in CONTROL register.
        """
        depth_units = depth_to_fpga_units(depth_m)

        # Read existing target_depth to avoid clobbering it
        cur_depth_cfg = self.axi.read32(REG_DEPTH_CFG)
        _, cur_target_units = unpack_depth_cfg(cur_depth_cfg)

        # Write new set_depth
        new_depth_cfg = pack_depth_cfg(depth_units, cur_target_units)
        self.axi.write32(REG_DEPTH_CFG, new_depth_cfg)

        # Strobe cfg_set_depth_we (bit 6) in CONTROL register
        ctrl_val = pack_control(set_depth_we=True)
        self.axi.write32(REG_CONTROL, ctrl_val)

        return float(depth_m)

    def set_target(self, target_m: float) -> float:
        """
        Sets the probe's target depth in meters.
        Preserves set_depth and updates target_depth in DEPTH_CFG.
        """
        target_units = depth_to_fpga_units(target_m)

        # Read existing set_depth to preserve it
        cur_depth_cfg = self.axi.read32(REG_DEPTH_CFG)
        cur_set_units, _ = unpack_depth_cfg(cur_depth_cfg)

        # Write updated target_depth
        new_depth_cfg = pack_depth_cfg(cur_set_units, target_units)
        self.axi.write32(REG_DEPTH_CFG, new_depth_cfg)

        return float(target_m)

    def set_current(self, current_pct: int) -> int:
        """
        Sets the water current strength percentage (-100% to +100%).
        Writes signed 8-bit to REG_CURRENT.
        """
        valid_pct = validate_current(current_pct)
        packed_val = pack_current(valid_pct)
        self.axi.write32(REG_CURRENT, packed_val)
        return valid_pct

    def disturb(self, disturb_type_name: str) -> str:
        """
        Triggers a physical collision/disturbance on the probe.
        Types: 'FISH', 'GARBAGE', 'WHALE'.
        Strobes cmd_disturb_strobe and asserts cmd_disturb_type in CONTROL.
        """
        d_code = parse_disturb_type(disturb_type_name)
        ctrl_val = pack_control(disturb_strobe=True, disturb_type=d_code)
        self.axi.write32(REG_CONTROL, ctrl_val)
        return DISTURB_CODE_TO_NAME[d_code]

    def start(self) -> None:
        """Sends start command strobe to initiate probe motion."""
        ctrl_val = pack_control(start=True)
        self.axi.write32(REG_CONTROL, ctrl_val)

    def stop(self) -> None:
        """Sends stop command strobe to freeze probe in place."""
        ctrl_val = pack_control(stop=True)
        self.axi.write32(REG_CONTROL, ctrl_val)

    def reset(self) -> Telemetry:
        """
        Asserts synchronous reset strobe on FPGA (cmd_reset).
        Reads back telemetry to verify nominal hardware reset state:
          - state == IDLE
          - depth == 50.0 m (500 units)
          - target == 80.0 m (800 units)
          - displacement_x == 0
          - collision_count == 0
        """
        ctrl_val = pack_control(reset=True)
        self.axi.write32(REG_CONTROL, ctrl_val)

        # Confirm reset state by querying telemetry
        telemetry = self.get_telemetry()
        return telemetry

    # -------------------------------------------------------------------------
    # Telemetry APIs
    # -------------------------------------------------------------------------
    def get_telemetry(self) -> Telemetry:
        """
        Reads all active simulation registers from FPGA and decodes into Telemetry.
        """
        raw_status = self.axi.read32(REG_STATUS)
        raw_position = self.axi.read32(REG_POSITION)
        raw_counters = self.axi.read32(REG_COUNTERS)
        raw_cycles = self.axi.read32(REG_CYCLES)
        raw_depth_cfg = self.axi.read32(REG_DEPTH_CFG)
        raw_current = self.axi.read32(REG_CURRENT)

        return decode_telemetry(
            raw_status=raw_status,
            raw_position=raw_position,
            raw_counters=raw_counters,
            raw_cycles=raw_cycles,
            raw_depth_cfg=raw_depth_cfg,
            raw_current=raw_current
        )

    def get_position(self) -> Dict[str, float]:
        """Convenience method returning spatial coordinates from FPGA."""
        t = self.get_telemetry()
        return {
            "depth": t.depth,
            "target_depth": t.target_depth,
            "displacement_x": t.displacement_x,
            "velocity_z": t.velocity_z,
        }

    def get_status(self) -> Dict[str, Any]:
        """Convenience dictionary summary matching legacy CLI contract."""
        t = self.get_telemetry()
        direction_str = (
            "DESCENDING" if t.velocity_z > 0.05
            else ("ASCENDING" if t.velocity_z < -0.05 else "HOLDING")
        )
        return {
            "current_depth": t.depth,
            "target_depth": t.target_depth,
            "current_strength": t.current_strength,
            "displacement_x": t.displacement_x,
            "velocity_z": t.velocity_z,
            "state": t.state,
            "collision": t.collision,
            "recovery": t.recovery,
            "target_reached": t.target_reached,
            "active_object": t.active_object,
            "collision_count": t.collision_count,
            "simulation_cycles": t.simulation_cycles,
            "direction": direction_str,
            "is_hardware": self.is_hardware,
            "mode_name": self.mode_name,
        }

    def close(self) -> None:
        """Closes underlying AXI interface."""
        self.axi.close()
