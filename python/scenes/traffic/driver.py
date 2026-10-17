"""
python.scenes.traffic.driver
============================
Dedicated hardware driver for Smart City Traffic Management scene.
Interacts with the FPGA via AXI4-Lite at base address 0x43C40000.
"""

from typing import Dict, Any, Optional

from python.core.fpga_driver import BaseFPGADriver
from python.core.axi_interface import AXIInterface, MockAXIInterface
from python.scenes.traffic.register_map import (
    BASE_ADDRESS,
    REG_CONTROL,
    REG_CONFIG,
    REG_TIMING_CFG,
    REG_STATUS,
    REG_TELEMETRY,
    REG_CYCLES,
    REG_APPROACH_QUEUES_NS,
    REG_APPROACH_QUEUES_EW,
    REG_TOTAL_QUEUES,
    REG_DYNAMIC_SPLITS,
    REG_WAIT_TIMES,
    REG_PREDICTED_QUEUES,
    REG_CONGESTION_LEVELS,
    REG_EMERGENCY_STATUS,
    REG_PEDESTRIAN_STATUS,
    REG_FAULT_FLAGS,
    REG_FAULT_COUNT,
    REG_VEHICLE_OCCUPANCY,
    REG_VEH_POS_NORTH,
    REG_VEH_POS_SOUTH,
    REG_VEH_POS_EAST,
    REG_VEH_POS_WEST,
    REG_VEH_SPEEDS,
    REG_STARVATION_FLAGS,
    REG_FSM_CYCLES,
    REG_QUEUE_CYCLES,
    REG_VEHICLE_CYCLES,
    REG_OPTIMIZER_CYCLES,
    REG_UPDATE_COUNTER,
    REG_THROUGHPUT,
    REG_ADAPTIVE_WEIGHTS
)
from python.scenes.traffic.telemetry import decode_traffic_telemetry


class TrafficDriver(BaseFPGADriver):
    """Driver for Traffic Management on AXI peripheral 0x43C40000."""

    def __init__(self, axi: AXIInterface, base_address: int = BASE_ADDRESS):
        super().__init__(axi, scene_name="traffic", base_address=base_address)
        if isinstance(self.axi, MockAXIInterface):
            self._setup_mock_hooks()

    def _setup_mock_hooks(self):
        """Mock behavior replicating upgraded traffic_core.v logic."""
        mock = self.axi
        mock.registers[REG_CONTROL] = 0
        mock.registers[REG_CONFIG] = (0 << 24) | (8 << 16) | (12 << 8) | 1
        mock.registers[REG_TIMING_CFG] = (45 << 16) | 10
        mock.registers[REG_STATUS] = 0  # NS_GREEN
        mock.registers[REG_TELEMETRY] = (0 << 24) | (0 << 16) | (40 << 8) | 20
        mock.registers[REG_CYCLES] = 0
        mock.registers[REG_APPROACH_QUEUES_NS] = (10 << 16) | 12
        mock.registers[REG_APPROACH_QUEUES_EW] = (6 << 16) | 8
        mock.registers[REG_TOTAL_QUEUES] = (14 << 24) | (22 << 16) | 36
        mock.registers[REG_DYNAMIC_SPLITS] = (20 << 16) | 30
        mock.registers[REG_WAIT_TIMES] = (0 << 16) | 0
        mock.registers[REG_PREDICTED_QUEUES] = (14 << 16) | 22
        mock.registers[REG_CONGESTION_LEVELS] = (1 << 24) | (40 << 16) | 0x0111
        mock.registers[REG_EMERGENCY_STATUS] = 0
        mock.registers[REG_PEDESTRIAN_STATUS] = 0
        mock.registers[REG_FAULT_FLAGS] = 0
        mock.registers[REG_FAULT_COUNT] = 0
        mock.registers[REG_VEHICLE_OCCUPANCY] = 0xFFFF
        mock.registers[REG_VEH_POS_NORTH] = 0x1E5A8CB4
        mock.registers[REG_VEH_POS_SOUTH] = 0x145082AF
        mock.registers[REG_VEH_POS_EAST] = 0x235F91B9
        mock.registers[REG_VEH_POS_WEST] = 0x0F4678AA
        mock.registers[REG_VEH_SPEEDS] = 0x0A0A0A0A
        mock.registers[REG_STARVATION_FLAGS] = (45 << 16) | 0
        mock.registers[REG_FSM_CYCLES] = 100
        mock.registers[REG_QUEUE_CYCLES] = 100
        mock.registers[REG_VEHICLE_CYCLES] = 1600
        mock.registers[REG_OPTIMIZER_CYCLES] = 100
        mock.registers[REG_UPDATE_COUNTER] = 0
        mock.registers[REG_THROUGHPUT] = 1600
        mock.registers[REG_ADAPTIVE_WEIGHTS] = (10 << 24) | (1 << 16) | (3 << 8) | 2

        def on_control_write(val: int):
            step_strobe = val & 1
            reset_strobe = (val >> 1) & 1
            override_en = (val >> 2) & 1
            override_ph = (val >> 3) & 1
            emg_strobe = (val >> 5) & 1
            emg_dir = (val >> 6) & 3

            if reset_strobe:
                mock.registers[REG_STATUS] = 0
                mock.registers[REG_TELEMETRY] = 20
                mock.registers[REG_CYCLES] = 0
                mock.registers[REG_EMERGENCY_STATUS] = 0
                mock.registers[REG_FAULT_FLAGS] = 0
                return

            if emg_strobe:
                ph = 3 if emg_dir in (2, 3) else 0
                mock.registers[REG_STATUS] = ph | (1 << 5) | (0xEE << 8)
                mock.registers[REG_EMERGENCY_STATUS] = 1 | (emg_dir << 1) | (1 << 4) | (1 << 5) | (2 << 8)
                mock.registers[REG_TELEMETRY] = 30
                return

            if override_en:
                phase_code = 3 if override_ph else 0
                mock.registers[REG_STATUS] = phase_code | (1 << 5) | (0xAA << 8)
                mock.registers[REG_TELEMETRY] = 99
                return

            if step_strobe:
                cur_status = mock.registers.get(REG_STATUS, 0)
                cur_phase = cur_status & 0x0F
                cur_telem = mock.registers.get(REG_TELEMETRY, 20)
                green_rem = cur_telem & 0xFF
                cong = (cur_telem >> 8) & 0xFF
                clr_ns = (cur_telem >> 16) & 0xFF
                clr_ew = (cur_telem >> 24) & 0xFF

                if green_rem > 1:
                    green_rem -= 1
                    if cur_phase == 0: clr_ns = (clr_ns + 1) & 0xFF
                    elif cur_phase == 3: clr_ew = (clr_ew + 1) & 0xFF
                else:
                    next_phase = (cur_phase + 1) % 5
                    cur_phase = next_phase
                    green_rem = 25 if cur_phase in (0, 3) else 3

                mock.registers[REG_STATUS] = cur_phase | ((cong > 70) << 4)
                mock.registers[REG_TELEMETRY] = ((clr_ew & 0xFF) << 24) | ((clr_ns & 0xFF) << 16) | ((cong & 0xFF) << 8) | (green_rem & 0xFF)
                mock.registers[REG_CYCLES] = (mock.registers.get(REG_CYCLES, 0) + 1) & 0xFFFFFFFF
                mock.registers[REG_UPDATE_COUNTER] = (mock.registers.get(REG_UPDATE_COUNTER, 0) + 1) & 0xFFFFFFFF

        mock.write_hooks[REG_CONTROL] = on_control_write

    def configure_intersection(self, intersection_id: int, queue_ns: int, queue_ew: int, priority: int = 0) -> None:
        """Sets intersection queue depths and priority."""
        word = ((priority & 0xFF) << 24) | ((queue_ew & 0xFF) << 16) | ((queue_ns & 0xFF) << 8) | (intersection_id & 0xFF)
        self.write32(REG_CONFIG, word)

    def set_queues(self, queue_ns: int, queue_ew: int) -> None:
        """Convenience method to set directional queues."""
        self.configure_intersection(1, queue_ns, queue_ew)

    def set_approach_queues(self, q_n: int, q_s: int, q_e: int, q_w: int) -> None:
        """Sets individual approach queues."""
        self.set_queues(q_n + q_s, q_e + q_w)

    def set_density(self, direction: str, value: int) -> None:
        """Updates queue depth for a single approach (N, S, E, W)."""
        t = self.get_telemetry()["data"]
        q_n = t["queue_north"]
        q_s = t["queue_south"]
        q_e = t["queue_east"]
        q_w = t["queue_west"]

        d = direction.upper()
        if d == "N": q_n = value
        elif d == "S": q_s = value
        elif d == "E": q_e = value
        elif d == "W": q_w = value

        self.set_queues(q_n + q_s, q_e + q_w)

    def manual_override(self, phase_name: str) -> None:
        """Forces immediate signal phase override (NS or EW)."""
        ph_code = 1 if phase_name.upper() == "EW" else 0
        val = (1 << 2) | (ph_code << 3)
        self.write32(REG_CONTROL, val)

    def clear_override(self) -> None:
        """Returns to autonomous FPGA FSM scheduling."""
        self.write32(REG_CONTROL, 1 << 4)

    def trigger_emergency(self, direction_name: str = "NORTH") -> None:
        """Triggers emergency preemption corridor along specified approach."""
        d = direction_name.upper()
        dir_code = {"NORTH": 0, "SOUTH": 1, "EAST": 2, "WEST": 3}.get(d, 0)
        val = (1 << 5) | (dir_code << 6)
        self.write32(REG_CONTROL, val)

    def trigger_pedestrian(self) -> None:
        """Requests pedestrian crossing phase."""
        self.write32(REG_CONTROL, 1 << 8)

    def set_stress_mode(self, enable: bool = True) -> None:
        """Engages heavy traffic stress mode."""
        val = (1 << 9) if enable else 0
        self.write32(REG_CONTROL, val)

    def start(self) -> None:
        """Engages autonomous traffic controller."""
        self.write32(REG_CONTROL, 1 << 4)

    def step(self) -> None:
        """Strobes simulation cycle tick."""
        self.write32(REG_CONTROL, 1)

    def reset(self) -> None:
        """Sends reset strobe."""
        self.write32(REG_CONTROL, 2)

    def get_telemetry(self) -> Dict[str, Any]:
        """Reads all 32 AXI registers and decodes full FPGA telemetry."""
        return decode_traffic_telemetry(
            status_reg=self.read32(REG_STATUS),
            telemetry_reg=self.read32(REG_TELEMETRY),
            config_reg=self.read32(REG_CONFIG),
            timing_reg=self.read32(REG_TIMING_CFG),
            cycles_reg=self.read32(REG_CYCLES),
            is_hardware=self.is_hardware,
            queues_ns_reg=self.read32(REG_APPROACH_QUEUES_NS),
            queues_ew_reg=self.read32(REG_APPROACH_QUEUES_EW),
            total_queues_reg=self.read32(REG_TOTAL_QUEUES),
            dynamic_splits_reg=self.read32(REG_DYNAMIC_SPLITS),
            wait_times_reg=self.read32(REG_WAIT_TIMES),
            pred_queues_reg=self.read32(REG_PREDICTED_QUEUES),
            cong_levels_reg=self.read32(REG_CONGESTION_LEVELS),
            emergency_reg=self.read32(REG_EMERGENCY_STATUS),
            pedestrian_reg=self.read32(REG_PEDESTRIAN_STATUS),
            fault_flags_reg=self.read32(REG_FAULT_FLAGS),
            fault_count_reg=self.read32(REG_FAULT_COUNT),
            vehicle_occ_reg=self.read32(REG_VEHICLE_OCCUPANCY),
            veh_pos_n_reg=self.read32(REG_VEH_POS_NORTH),
            veh_pos_s_reg=self.read32(REG_VEH_POS_SOUTH),
            veh_pos_e_reg=self.read32(REG_VEH_POS_EAST),
            veh_pos_w_reg=self.read32(REG_VEH_POS_WEST),
            veh_speeds_reg=self.read32(REG_VEH_SPEEDS),
            starvation_reg=self.read32(REG_STARVATION_FLAGS),
            fsm_cycles_reg=self.read32(REG_FSM_CYCLES),
            queue_cycles_reg=self.read32(REG_QUEUE_CYCLES),
            vehicle_cycles_reg=self.read32(REG_VEHICLE_CYCLES),
            optimizer_cycles_reg=self.read32(REG_OPTIMIZER_CYCLES),
            update_counter_reg=self.read32(REG_UPDATE_COUNTER)
        )

    def get_traffic_state(self) -> Dict[str, Any]:
        """Returns structured JSON state matching the authoritative FPGA Traffic specification."""
        telem = self.get_telemetry()
        d = telem["data"]
        avg_speed = (d.get("speed_north_mps", 0) + d.get("speed_south_mps", 0) + 
                     d.get("speed_east_mps", 0) + d.get("speed_west_mps", 0)) / 4.0
        brake_mask = d.get("brake_required_mask", 0)
        stopped_cnt = bin(brake_mask).count("1")

        return {
            "mode": "fpga" if self.is_hardware else "emulator",
            "signal_phase": d.get("signal_phase", "NS_GREEN"),
            "green_time_s": d.get("green_time_remaining_s", 0),
            "phase_timer_s": d.get("green_time_remaining_s", 0),
            "queues": {
                "north": d.get("queue_north", 0),
                "south": d.get("queue_south", 0),
                "east": d.get("queue_east", 0),
                "west": d.get("queue_west", 0)
            },
            "total_queue": d.get("queue_total", 0),
            "average_speed": round(avg_speed, 2),
            "stopped_vehicles": stopped_cnt,
            "congestion_score": d.get("congestion_score_pct", 0),
            "predicted_congestion": (d.get("pred_queue_ns", 0) + d.get("pred_queue_ew", 0)) // 2,
            "emergency": {
                "active": d.get("emergency_active", False),
                "direction": d.get("emergency_direction", "NONE")
            },
            "hardware": {
                "connected": self.is_hardware,
                "latency_cycles": d.get("optimizer_cycles", 0),
                "update_counter": d.get("total_updates", 0)
            }
        }

    def configure_timing(self, min_green_s: int, max_green_s: int) -> None:
        """Configures min and max green intervals in hardware."""
        word = ((max_green_s & 0xFFFF) << 16) | (min_green_s & 0xFFFF)
        self.write32(REG_TIMING_CFG, word)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Returns measured hardware cycle counts, throughput, and latency."""
        t = self.get_telemetry()["data"]
        return {
            "fsm_cycles": t.get("fsm_cycles", 0),
            "queue_cycles": t.get("queue_cycles", 0),
            "vehicle_cycles": t.get("vehicle_cycles", 0),
            "optimizer_cycles": t.get("optimizer_cycles", 0),
            "total_updates": t.get("total_updates", 0),
            "authoritative": t.get("authoritative", "PL"),
            "parallel_channels": 16,
            "hardware_connected": self.is_hardware
        }

    def get_debug_registers(self) -> Dict[str, Any]:
        """Dumps all registers as hex strings."""
        return {
            "scene": "traffic",
            "base_address": f"0x{self.base_address:08X}",
            "REG_CONTROL": f"0x{self.read32(REG_CONTROL):08X}",
            "REG_CONFIG": f"0x{self.read32(REG_CONFIG):08X}",
            "REG_TIMING_CFG": f"0x{self.read32(REG_TIMING_CFG):08X}",
            "REG_STATUS": f"0x{self.read32(REG_STATUS):08X}",
            "REG_TELEMETRY": f"0x{self.read32(REG_TELEMETRY):08X}",
            "REG_CYCLES": f"0x{self.read32(REG_CYCLES):08X}",
            "REG_APPROACH_QUEUES_NS": f"0x{self.read32(REG_APPROACH_QUEUES_NS):08X}",
            "REG_APPROACH_QUEUES_EW": f"0x{self.read32(REG_APPROACH_QUEUES_EW):08X}",
            "REG_TOTAL_QUEUES": f"0x{self.read32(REG_TOTAL_QUEUES):08X}",
            "REG_DYNAMIC_SPLITS": f"0x{self.read32(REG_DYNAMIC_SPLITS):08X}",
            "REG_WAIT_TIMES": f"0x{self.read32(REG_WAIT_TIMES):08X}",
            "REG_PREDICTED_QUEUES": f"0x{self.read32(REG_PREDICTED_QUEUES):08X}",
            "REG_CONGESTION_LEVELS": f"0x{self.read32(REG_CONGESTION_LEVELS):08X}",
            "REG_EMERGENCY_STATUS": f"0x{self.read32(REG_EMERGENCY_STATUS):08X}",
            "REG_PEDESTRIAN_STATUS": f"0x{self.read32(REG_PEDESTRIAN_STATUS):08X}",
            "REG_FAULT_FLAGS": f"0x{self.read32(REG_FAULT_FLAGS):08X}",
            "REG_FAULT_COUNT": f"0x{self.read32(REG_FAULT_COUNT):08X}",
            "REG_VEHICLE_OCCUPANCY": f"0x{self.read32(REG_VEHICLE_OCCUPANCY):08X}",
            "REG_VEH_POS_NORTH": f"0x{self.read32(REG_VEH_POS_NORTH):08X}",
            "REG_VEH_POS_SOUTH": f"0x{self.read32(REG_VEH_POS_SOUTH):08X}",
            "REG_VEH_POS_EAST": f"0x{self.read32(REG_VEH_POS_EAST):08X}",
            "REG_VEH_POS_WEST": f"0x{self.read32(REG_VEH_POS_WEST):08X}",
            "REG_VEH_SPEEDS": f"0x{self.read32(REG_VEH_SPEEDS):08X}",
            "REG_STARVATION_FLAGS": f"0x{self.read32(REG_STARVATION_FLAGS):08X}",
            "REG_UPDATE_COUNTER": f"0x{self.read32(REG_UPDATE_COUNTER):08X}",
            "REG_THROUGHPUT": f"0x{self.read32(REG_THROUGHPUT):08X}"
        }
