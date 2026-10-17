"""
python.scenes.underwater.driver
===============================
Dedicated hardware driver for Underwater Dynamic Probe scene.
Bridges AXI registers to Python command handlers and telemetry decoders.
"""

from typing import Dict, Any, Optional

from python.core.fpga_driver import BaseFPGADriver
from python.core.axi_interface import AXIInterface, MockAXIInterface
from python.protocol.encoding import float_to_fixed16
from python.scenes.underwater.register_map import (
    BASE_ADDRESS,
    REG_CONTROL,
    REG_DEPTH_CFG,
    REG_CURRENT,
    REG_STATUS,
    REG_CURRENT_DEPTH,
    REG_TARGET_DEPTH,
    REG_VELOCITY,
    REG_DEPTH_ERROR,
    REG_FILTERED_DEPTH,
    REG_FILTERED_VELOCITY,
    REG_DRAG_FORCE,
    REG_RELATIVE_VELOCITY,
    REG_P_TERM,
    REG_I_TERM,
    REG_D_TERM,
    REG_CONTROL_OUTPUT,
    REG_THRUST_COMMAND,
    REG_THRUST_DELTA,
    REG_IMPACT_ENERGY,
    REG_IMPACT_SEVERITY,
    REG_RECOVERY_THRUST,
    REG_POST_COL_VELOCITY,
    REG_PREDICTED_DEPTH_1,
    REG_PREDICTED_DEPTH_3,
    REG_PREDICTED_DEPTH_5,
    REG_CONTROL_COST,
    REG_OPTIMIZATION_ACT,
    REG_FAULT_FLAGS,
    REG_SIMULATION_CYCLES,
    REG_PHYSICS_UPDATES,
    REG_COLLISION_COUNT,
    REG_RECOVERY_COUNT,
    CTRL_START_BIT,
    CTRL_STOP_BIT,
    CTRL_RESET_BIT,
    CTRL_DISTURB_STROBE_BIT,
    CTRL_DISTURB_TYPE_SHIFT,
    CTRL_SET_DEPTH_WE_BIT,
    DISTURBANCE_TYPES,
)
from python.scenes.underwater.telemetry import decode_underwater_telemetry


class UnderwaterDriver(BaseFPGADriver):
    """Driver for Underwater Dynamic Probe on AXI peripheral 0x43C00000."""

    def __init__(self, axi: AXIInterface, base_address: int = BASE_ADDRESS):
        super().__init__(axi, scene_name="underwater", base_address=base_address)
        if isinstance(self.axi, MockAXIInterface):
            self._setup_mock_hooks()

    def _setup_mock_hooks(self):
        """Initializes registers for standalone MockAXIInterface unit tests."""
        self.axi.write32(REG_DEPTH_CFG, (800 << 16) | 500)
        self.axi.write32(REG_CURRENT, 20)
        self.axi.write32(REG_STATUS, 0)
        self.axi.write32(REG_CURRENT_DEPTH, 500)
        self.axi.write32(REG_TARGET_DEPTH, 800)
        self.axi.write32(REG_COLLISION_COUNT, 0)
        self.axi.write32(REG_SIMULATION_CYCLES, 0)

        mock = self.axi
        def on_control_write(val: int):
            if (val >> CTRL_RESET_BIT) & 1:
                mock.registers[REG_STATUS] = 0
            if (val >> CTRL_DISTURB_STROBE_BIT) & 1:
                dtype = (val >> CTRL_DISTURB_TYPE_SHIFT) & 0x03
                st = mock.registers.get(REG_STATUS, 0)
                # set collision bit and object
                mock.registers[REG_STATUS] = st | (1 << 4) | (dtype << 7)
                mock.registers[REG_COLLISION_COUNT] = mock.registers.get(REG_COLLISION_COUNT, 0) + 1
            if (val >> CTRL_SET_DEPTH_WE_BIT) & 1:
                cfg = mock.registers.get(REG_DEPTH_CFG, 0)
                mock.registers[REG_CURRENT_DEPTH] = cfg & 0xFFFF

        def on_depth_cfg_write(val: int):
            mock.registers[REG_CURRENT_DEPTH] = val & 0xFFFF
            mock.registers[REG_TARGET_DEPTH] = (val >> 16) & 0xFFFF

        mock.write_hooks[REG_CONTROL] = on_control_write
        mock.write_hooks[REG_DEPTH_CFG] = on_depth_cfg_write

    def set_depth(self, depth_meters: float) -> None:
        """Sets starting/current depth register."""
        scaled = int(round(depth_meters * 10.0)) & 0xFFFF
        cur_cfg = self.read32(REG_DEPTH_CFG)
        target_part = cur_cfg & 0xFFFF0000
        self.write32(REG_DEPTH_CFG, target_part | scaled)
        self.write32(REG_CONTROL, 1 << CTRL_SET_DEPTH_WE_BIT)

    def set_target(self, target_meters: float) -> None:
        """Sets target depth register."""
        scaled = (int(round(target_meters * 10.0)) & 0xFFFF) << 16
        cur_cfg = self.read32(REG_DEPTH_CFG)
        cur_depth_part = cur_cfg & 0x0000FFFF
        self.write32(REG_DEPTH_CFG, scaled | cur_depth_part)

    def set_current(self, current_pct: int) -> None:
        """Sets ocean current strength percentage (-100 to +100)."""
        clamped = max(-100, min(100, int(current_pct)))
        unsigned_byte = clamped & 0xFF
        self.write32(REG_CURRENT, unsigned_byte)

    def disturb(self, obj_type: str) -> None:
        """Triggers collision disturbance strobe."""
        t_code = DISTURBANCE_TYPES.get(obj_type.upper(), 0)
        strobe_val = (1 << CTRL_DISTURB_STROBE_BIT) | (t_code << CTRL_DISTURB_TYPE_SHIFT)
        self.write32(REG_CONTROL, strobe_val)

    def start(self) -> None:
        """Sends start strobe."""
        self.write32(REG_CONTROL, 1 << CTRL_START_BIT)

    def stop(self) -> None:
        """Sends stop strobe."""
        self.write32(REG_CONTROL, 1 << CTRL_STOP_BIT)

    def reset(self) -> None:
        """Sends reset strobe."""
        self.write32(REG_CONTROL, 1 << CTRL_RESET_BIT)

    def get_telemetry(self) -> Dict[str, Any]:
        """Reads hardware registers and returns standard telemetry envelope."""
        status_reg          = self.read32(REG_STATUS)
        depth_cfg           = self.read32(REG_DEPTH_CFG)
        curr_reg            = self.read32(REG_CURRENT)
        cur_depth_reg       = self.read32(REG_CURRENT_DEPTH)
        tgt_depth_reg       = self.read32(REG_TARGET_DEPTH)
        vel_reg             = self.read32(REG_VELOCITY)
        depth_err_reg       = self.read32(REG_DEPTH_ERROR)
        flt_depth_reg       = self.read32(REG_FILTERED_DEPTH)
        flt_vel_reg         = self.read32(REG_FILTERED_VELOCITY)
        drag_reg            = self.read32(REG_DRAG_FORCE)
        rel_vel_reg         = self.read32(REG_RELATIVE_VELOCITY)
        p_term_reg          = self.read32(REG_P_TERM)
        i_term_reg          = self.read32(REG_I_TERM)
        d_term_reg          = self.read32(REG_D_TERM)
        ctrl_out_reg        = self.read32(REG_CONTROL_OUTPUT)
        thrust_cmd_reg      = self.read32(REG_THRUST_COMMAND)
        thrust_delta_reg    = self.read32(REG_THRUST_DELTA)
        impact_energy_reg   = self.read32(REG_IMPACT_ENERGY)
        impact_sev_reg      = self.read32(REG_IMPACT_SEVERITY)
        rec_thrust_reg      = self.read32(REG_RECOVERY_THRUST)
        post_col_vel_reg    = self.read32(REG_POST_COL_VELOCITY)
        pred_1_reg          = self.read32(REG_PREDICTED_DEPTH_1)
        pred_3_reg          = self.read32(REG_PREDICTED_DEPTH_3)
        pred_5_reg          = self.read32(REG_PREDICTED_DEPTH_5)
        ctrl_cost_reg       = self.read32(REG_CONTROL_COST)
        opt_act_reg         = self.read32(REG_OPTIMIZATION_ACT)
        fault_flags_reg     = self.read32(REG_FAULT_FLAGS)
        sim_cycles_reg      = self.read32(REG_SIMULATION_CYCLES)
        phys_updates_reg    = self.read32(REG_PHYSICS_UPDATES)
        col_count_reg       = self.read32(REG_COLLISION_COUNT)
        rec_count_reg       = self.read32(REG_RECOVERY_COUNT)

        return decode_underwater_telemetry(
            status_reg=status_reg,
            depth_cfg_reg=depth_cfg,
            current_reg=curr_reg,
            current_depth_reg=cur_depth_reg,
            target_depth_reg=tgt_depth_reg,
            velocity_reg=vel_reg,
            depth_error_reg=depth_err_reg,
            filtered_depth_reg=flt_depth_reg,
            filtered_velocity_reg=flt_vel_reg,
            drag_force_reg=drag_reg,
            relative_velocity_reg=rel_vel_reg,
            p_term_reg=p_term_reg,
            i_term_reg=i_term_reg,
            d_term_reg=d_term_reg,
            control_output_reg=ctrl_out_reg,
            thrust_command_reg=thrust_cmd_reg,
            thrust_delta_reg=thrust_delta_reg,
            impact_energy_reg=impact_energy_reg,
            impact_severity_reg=impact_sev_reg,
            recovery_thrust_reg=rec_thrust_reg,
            post_col_velocity_reg=post_col_vel_reg,
            predicted_depth_1_reg=pred_1_reg,
            predicted_depth_3_reg=pred_3_reg,
            predicted_depth_5_reg=pred_5_reg,
            control_cost_reg=ctrl_cost_reg,
            optimization_act_reg=opt_act_reg,
            fault_flags_reg=fault_flags_reg,
            sim_cycles_reg=sim_cycles_reg,
            physics_updates_reg=phys_updates_reg,
            collision_count_reg=col_count_reg,
            recovery_count_reg=rec_count_reg,
            is_hardware=self.is_hardware
        )

    def get_debug_registers(self) -> Dict[str, Any]:
        """Returns raw hexadecimal register snapshot."""
        return {
            "scene": "underwater",
            "base_address": f"0x{self.base_address:08X}",
            "CONTROL": f"0x{self.read32(REG_CONTROL):08X}",
            "DEPTH_CFG": f"0x{self.read32(REG_DEPTH_CFG):08X}",
            "CURRENT": f"0x{self.read32(REG_CURRENT):08X}",
            "STATUS": f"0x{self.read32(REG_STATUS):08X}",
            "CURRENT_DEPTH": f"0x{self.read32(REG_CURRENT_DEPTH):08X}",
            "DEPTH_ERROR": f"0x{self.read32(REG_DEPTH_ERROR):08X}",
            "DRAG_FORCE": f"0x{self.read32(REG_DRAG_FORCE):08X}",
            "THRUST_COMMAND": f"0x{self.read32(REG_THRUST_COMMAND):08X}",
            "FAULT_FLAGS": f"0x{self.read32(REG_FAULT_FLAGS):08X}",
            "CYCLES": f"0x{self.read32(REG_SIMULATION_CYCLES):08X}",
        }
