"""
python.scenes.mars_habitat.driver
=================================
Dedicated hardware driver for Mars Space Habitat & Landing Accelerator.
Communicates directly with FPGA AXI peripheral at base address 0x43C20000.
Authoritative calculations (landing physics, 8-channel meteorites, damage,
atmosphere, life-support) run exclusively in FPGA PL.
"""

from typing import Dict, Any, Optional

from python.core.fpga_driver import BaseFPGADriver
from python.core.axi_interface import AXIInterface, MockAXIInterface
from python.protocol.encoding import float_to_fixed16
from python.scenes.mars_habitat.register_map import (
    BASE_ADDRESS,
    REG_CONTROL,
    REG_ATTACK,
    REG_THRESHOLD,
    REG_STATUS,
    REG_IMPACT,
    REG_COUNTERS,
    REG_TOTAL,
    REG_LANDING_ALTITUDE,
    REG_LANDING_VELOCITY,
    REG_THRUST_COMMAND,
    REG_PREDICTED_ALTITUDE,
    REG_PREDICTED_TOUCHDOWN_VEL,
    REG_LANDING_STATUS,
    REG_METEORITE_ACTIVE,
    REG_METEORITE_IMPACT_VECTOR,
    REG_TOTAL_IMPACT_ENERGY,
    REG_SECTION_DAMAGE,
    REG_RECOVERY_ACTION,
    REG_O2_PERCENT,
    REG_CO2_PERCENT,
    REG_PRESSURE_KPA,
    REG_TEMPERATURE_C,
    REG_LIFE_SUPPORT_STATUS,
    REG_HABITAT_HEALTH,
    REG_HAZARD_SCORE,
    REG_FAULT_FLAGS,
    REG_SIMULATION_CYCLES,
    REG_METEORITES_PROCESSED,
    REG_LATENCY_CYCLES,
    REG_UPDATE_COUNTER,
    REG_HARDWARE_VERSION
)
from python.scenes.mars_habitat.telemetry import decode_mars_telemetry


class MarsHabitatDriver(BaseFPGADriver):
    """Driver for Mars Space Habitat on AXI peripheral 0x43C20000."""

    def __init__(self, axi: AXIInterface, base_address: int = BASE_ADDRESS):
        super().__init__(axi, scene_name="mars_habitat", base_address=base_address)
        if isinstance(self.axi, MockAXIInterface):
            self._setup_mock_hooks()

    def _setup_mock_hooks(self):
        """Mock behavior replicating mars_habitat_core.v registers."""
        mock = self.axi
        mock.registers[REG_CONTROL] = 0
        mock.registers[REG_ATTACK] = (20 << 8) | 0
        mock.registers[REG_THRESHOLD] = (650 << 16) | 700
        mock.registers[REG_STATUS] = 0
        mock.registers[REG_IMPACT] = 0
        mock.registers[REG_COUNTERS] = 0
        mock.registers[REG_TOTAL] = 0

        # Upgraded registers defaults
        mock.registers[REG_LANDING_ALTITUDE] = 5000       # 500.0 m
        mock.registers[REG_LANDING_VELOCITY] = (-200 & 0xFFFF) # -20.0 m/s
        mock.registers[REG_THRUST_COMMAND] = 650          # 65.0%
        mock.registers[REG_PREDICTED_ALTITUDE] = 4000     # 400.0 m
        mock.registers[REG_PREDICTED_TOUCHDOWN_VEL] = (-42 & 0xFFFF)
        mock.registers[REG_LANDING_STATUS] = 0            # SAFE, PREP
        mock.registers[REG_METEORITE_ACTIVE] = 0
        mock.registers[REG_METEORITE_IMPACT_VECTOR] = 0
        mock.registers[REG_TOTAL_IMPACT_ENERGY] = 0
        mock.registers[REG_SECTION_DAMAGE] = 0
        mock.registers[REG_RECOVERY_ACTION] = 0
        mock.registers[REG_O2_PERCENT] = 209              # 20.9%
        mock.registers[REG_CO2_PERCENT] = 4               # 0.04%
        mock.registers[REG_PRESSURE_KPA] = 1013           # 101.3 kPa
        mock.registers[REG_TEMPERATURE_C] = 210           # +21.0 C
        mock.registers[REG_LIFE_SUPPORT_STATUS] = 0       # STABLE
        mock.registers[REG_HABITAT_HEALTH] = 100          # 100%
        mock.registers[REG_HAZARD_SCORE] = 15             # 15/100 NORMAL
        mock.registers[REG_FAULT_FLAGS] = 0
        mock.registers[REG_SIMULATION_CYCLES] = 102400
        mock.registers[REG_METEORITES_PROCESSED] = 0
        mock.registers[REG_LATENCY_CYCLES] = 18
        mock.registers[REG_UPDATE_COUNTER] = 102400
        mock.registers[REG_HARDWARE_VERSION] = 0x4D415253  # 'MARS'

        def on_control_write(val: int):
            attack_strobe = val & 1
            reset_strobe = (val >> 1) & 1
            landing_start = (val >> 2) & 1
            meteor_parallel = (val >> 3) & 1

            if reset_strobe:
                mock.registers[REG_STATUS] = 0
                mock.registers[REG_IMPACT] = 0
                mock.registers[REG_COUNTERS] = 0
                mock.registers[REG_TOTAL] = 0
                mock.registers[REG_LANDING_ALTITUDE] = 5000
                mock.registers[REG_LANDING_VELOCITY] = (-200 & 0xFFFF)
                mock.registers[REG_METEORITE_ACTIVE] = 0
                mock.registers[REG_METEORITE_IMPACT_VECTOR] = 0
                mock.registers[REG_TOTAL_IMPACT_ENERGY] = 0
                mock.registers[REG_SECTION_DAMAGE] = 0
                mock.registers[REG_RECOVERY_ACTION] = 0
                mock.registers[REG_O2_PERCENT] = 209
                mock.registers[REG_CO2_PERCENT] = 4
                mock.registers[REG_PRESSURE_KPA] = 1013
                mock.registers[REG_TEMPERATURE_C] = 210
                mock.registers[REG_LIFE_SUPPORT_STATUS] = 0
                mock.registers[REG_HABITAT_HEALTH] = 100
                mock.registers[REG_HAZARD_SCORE] = 15
                mock.registers[REG_FAULT_FLAGS] = 0
                return

            if landing_start:
                mock.registers[REG_LANDING_STATUS] = (1 << 2) | 0  # POWERED, SAFE
                mock.registers[REG_LANDING_ALTITUDE] = 4125        # 412.5 m
                mock.registers[REG_LANDING_VELOCITY] = (-182 & 0xFFFF) # -18.2 m/s
                mock.registers[REG_THRUST_COMMAND] = 643          # 64.3%
                mock.registers[REG_PREDICTED_TOUCHDOWN_VEL] = (-42 & 0xFFFF) # -4.2 m/s

            if meteor_parallel:
                mock.registers[REG_METEORITE_ACTIVE] = 0xFF
                mock.registers[REG_METEORITE_IMPACT_VECTOR] = 0x22 # Channels 1 and 5
                mock.registers[REG_TOTAL_IMPACT_ENERGY] = 8424     # 842.4
                mock.registers[REG_COUNTERS] = (1 << 16) | 1
                mock.registers[REG_TOTAL] = (1 << 16) | 2          # 2 impacts, 1 crit
                mock.registers[REG_METEORITES_PROCESSED] = 8
                mock.registers[REG_SECTION_DAMAGE] = (250 << 16) | 720 # Sec A crossed
                mock.registers[REG_STATUS] = (mock.registers.get(REG_STATUS, 0) | (1 << 4) | (1 << 6)) # A closed, link closed
                mock.registers[REG_RECOVERY_ACTION] = 1            # ISOLATE_A
                mock.registers[REG_HABITAT_HEALTH] = 72
                mock.registers[REG_HAZARD_SCORE] = (1 << 8) | 48  # WARNING

            if attack_strobe:
                atk_cfg = mock.registers.get(REG_ATTACK, 0)
                is_big = atk_cfg & 1
                target_code = (atk_cfg >> 1) & 0x3
                count = (atk_cfg >> 8) & 0xFF
                if count == 0: count = 1

                thresh_cfg = mock.registers.get(REG_THRESHOLD, (650 << 16) | 700)
                thresh_a = thresh_cfg & 0xFFFF
                thresh_b = (thresh_cfg >> 16) & 0xFFFF

                cur_status = mock.registers.get(REG_STATUS, 0)
                a_closed = (cur_status >> 4) & 1
                b_closed = (cur_status >> 5) & 1
                link_closed = (cur_status >> 6) & 1

                cur_counters = mock.registers.get(REG_COUNTERS, 0)
                imp_a = cur_counters & 0xFFFF
                imp_b = (cur_counters >> 16) & 0xFFFF
                tot = mock.registers.get(REG_TOTAL, 0) & 0xFFFF

                last_imp_u16 = 0
                crossed = 0
                active_tgt = 1

                for i in range(count):
                    if target_code == 1: tgt = 1
                    elif target_code == 2: tgt = 2
                    else: tgt = 1 if (i % 2 == 0) else 2
                    active_tgt = tgt

                    if is_big:
                        imp_val = 874 if i == 0 else 820 + ((i * 17) % 120)
                    else:
                        imp_val = 280 + ((i * 13) % 140)

                    last_imp_u16 = imp_val
                    th = thresh_a if tgt == 1 else thresh_b
                    if imp_val >= th:
                        crossed = 1
                        if tgt == 1: a_closed = 1
                        else: b_closed = 1
                        link_closed = 1

                    if tgt == 1: imp_a += 1
                    else: imp_b += 1
                    tot += 1

                new_status = 9 | (a_closed << 4) | (b_closed << 5) | (link_closed << 6) | (crossed << 7) | (active_tgt << 8)
                mock.registers[REG_STATUS] = new_status
                mock.registers[REG_IMPACT] = ((count & 0xFF) << 24) | ((count & 0xFF) << 16) | (last_imp_u16 & 0xFFFF)
                mock.registers[REG_COUNTERS] = ((imp_b & 0xFFFF) << 16) | (imp_a & 0xFFFF)
                mock.registers[REG_TOTAL] = (mock.registers.get(REG_TOTAL, 0) & 0xFFFF0000) | (tot & 0xFFFF)
                mock.registers[REG_METEORITES_PROCESSED] = (mock.registers.get(REG_METEORITES_PROCESSED, 0) + count) & 0xFFFF

        mock.write_hooks[REG_CONTROL] = on_control_write

    def configure_attack(self, attack_type: str = "NORMAL", target: str = "ALL", count: int = 1) -> None:
        """Sets attack configuration register."""
        is_big = 1 if attack_type.upper() == "BIG" else 0
        tgt_map = {"ALL": 0, "A": 1, "B": 2}
        target_code = tgt_map.get(target.upper(), 0)
        clamped_count = max(1, min(255, int(count)))

        val = ((clamped_count & 0xFF) << 8) | ((target_code & 0x3) << 1) | (is_big & 1)
        self.write32(REG_ATTACK, val)

    def trigger_attack(self) -> None:
        """Sends attack strobe."""
        self.write32(REG_CONTROL, 1)

    def attack(self, attack_type: str = "NORMAL", target: str = "ALL", count: int = 1) -> None:
        """Configures and immediately strobes attack."""
        self.configure_attack(attack_type=attack_type, target=target, count=count)
        self.trigger_attack()

    def start_landing(self) -> None:
        """Commands FPGA to initiate/restart closed-loop powered landing."""
        self.write32(REG_CONTROL, 4)

    def start_parallel_meteorites(self) -> None:
        """Enables 8-channel concurrent parallel meteorite trajectory engine in FPGA."""
        self.write32(REG_CONTROL, 8)

    def stop_parallel_meteorites(self) -> None:
        """Disables parallel meteorite engine in FPGA."""
        self.write32(REG_CONTROL, 0)

    def set_thresholds(self, threshold_a: float, threshold_b: float) -> None:
        """Sets protection thresholds for sections A and B."""
        u_a = float_to_fixed16(threshold_a, scale=10.0)
        u_b = float_to_fixed16(threshold_b, scale=10.0)
        self.write32(REG_THRESHOLD, ((u_b & 0xFFFF) << 16) | (u_a & 0xFFFF))

    def reset(self) -> None:
        """Sends reset strobe."""
        self.write32(REG_CONTROL, 2)

    def start(self) -> None:
        """Starts autonomous landing or simulation."""
        self.start_landing()

    def get_telemetry(self) -> Dict[str, Any]:
        """Reads all authoritative FPGA registers and returns decoded telemetry."""
        status_reg = self.read32(REG_STATUS)
        impact_reg = self.read32(REG_IMPACT)
        counters_reg = self.read32(REG_COUNTERS)
        total_reg = self.read32(REG_TOTAL)
        thresh_reg = self.read32(REG_THRESHOLD)
        attack_reg = self.read32(REG_ATTACK)

        extended_regs = {
            "landing_altitude": self.read32(REG_LANDING_ALTITUDE),
            "landing_velocity": self.read32(REG_LANDING_VELOCITY),
            "thrust_command": self.read32(REG_THRUST_COMMAND),
            "predicted_altitude": self.read32(REG_PREDICTED_ALTITUDE),
            "predicted_touchdown_vel": self.read32(REG_PREDICTED_TOUCHDOWN_VEL),
            "landing_status": self.read32(REG_LANDING_STATUS),
            "meteorite_active": self.read32(REG_METEORITE_ACTIVE),
            "meteorite_impact_vector": self.read32(REG_METEORITE_IMPACT_VECTOR),
            "critical_impact_count": (total_reg >> 16) & 0xFFFF,
            "total_impact_energy": self.read32(REG_TOTAL_IMPACT_ENERGY),
            "section_damage": self.read32(REG_SECTION_DAMAGE),
            "recovery_action": self.read32(REG_RECOVERY_ACTION),
            "o2_percent": self.read32(REG_O2_PERCENT),
            "co2_percent": self.read32(REG_CO2_PERCENT),
            "pressure_kpa": self.read32(REG_PRESSURE_KPA),
            "temperature_c": self.read32(REG_TEMPERATURE_C),
            "life_support_status": self.read32(REG_LIFE_SUPPORT_STATUS),
            "habitat_health": self.read32(REG_HABITAT_HEALTH),
            "hazard_score": self.read32(REG_HAZARD_SCORE),
            "fault_flags": self.read32(REG_FAULT_FLAGS),
            "simulation_cycles": self.read32(REG_SIMULATION_CYCLES),
            "meteorites_processed": self.read32(REG_METEORITES_PROCESSED),
            "latency_cycles": self.read32(REG_LATENCY_CYCLES),
            "update_counter": self.read32(REG_UPDATE_COUNTER),
            "hardware_version": self.read32(REG_HARDWARE_VERSION),
        }

        telem = decode_mars_telemetry(
            status_reg=status_reg,
            impact_reg=impact_reg,
            counters_reg=counters_reg,
            total_reg=total_reg,
            thresh_reg=thresh_reg,
            attack_reg=attack_reg,
            is_hardware=self.is_hardware,
            extended_regs=extended_regs
        )
        telem["seg_a_health"] = 100 if telem["data"]["section_A"] == "OPERATIONAL" else 0
        telem["seg_b_health"] = 100 if telem["data"]["section_B"] == "OPERATIONAL" else 0
        telem["data"]["seg_a_health"] = telem["seg_a_health"]
        telem["data"]["seg_b_health"] = telem["seg_b_health"]
        return telem

    def launch(self) -> None:
        """Alias for start_landing to trigger powered descent sequence."""
        self.start_landing()

    def abort(self) -> None:
        """Sends abort / halt command to retro-thrust controller and stabilizes state."""
        self.write32(REG_CONTROL, 2)  # Reset strobe

    def get_mars_state(self) -> Dict[str, Any]:
        """Returns structured JSON state matching Section 20 backend API specification."""
        t = self.get_telemetry()["data"]
        # Convert thrust percentage back to Newtons: (thrust_pct / 100.0) * 8000 N
        thrust_n = round((t.get("thrust_command", 0.0) / 100.0) * 8000.0, 1)

        return {
            "mode": "fpga" if self.is_hardware else "emulator",
            "landing": {
                "stage": t.get("landing_fsm", "PREP"),
                "altitude_m": t.get("landing_altitude", 0.0),
                "velocity_mps": t.get("landing_velocity", 0.0),
                "acceleration_mps2": t.get("landing_acceleration", 0.0),
                "thrust_n": thrust_n,
                "thrust_pct": t.get("thrust_command", 0.0),
                "touchdown": t.get("touchdown", False),
                "status": t.get("landing_status", "SAFE")
            },
            "meteorites": {
                "active": t.get("meteorite_active_count", 0),
                "impacts": t.get("total_impacts", 0),
                "critical_impacts": t.get("critical_impact_count", 0),
                "total_energy": t.get("total_impact_energy", 0.0)
            },
            "habitat": {
                "section_A": t.get("section_A", "OPERATIONAL"),
                "section_B": t.get("section_B", "OPERATIONAL"),
                "integrity": t.get("habitat_health", 100),
                "link_status": t.get("link_status", "OPEN"),
                "damage_A": t.get("damage_A", 0.0),
                "damage_B": t.get("damage_B", 0.0),
                "recovery_action": t.get("recovery_action", "NO_ACTION")
            },
            "environment": {
                "thermal_risk": "NOMINAL" if t.get("temperature_c", 20.0) < 60.0 else "WARNING",
                "drag": round(0.5 * 0.020 * 1.5 * 2.5 * (t.get("landing_velocity", 0.0)**2), 2),
                "temperature_c": t.get("temperature_c", 21.0)
            },
            "life_support": {
                "oxygen": t.get("o2_percent", 20.9),
                "pressure": t.get("pressure_kpa", 101.3),
                "co2": t.get("co2_percent", 0.04),
                "power": t.get("habitat_health", 100),
                "status": t.get("life_support_status", "STABLE")
            },
            "hardware": {
                "connected": self.is_hardware,
                "latency_cycles": t.get("latency_cycles", 18),
                "update_counter": t.get("update_counter", 102400),
                "core_version": t.get("core_version", "0x4D415253")
            }
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Returns measured hardware cycle counts, latency, and throughput."""
        t = self.get_telemetry()["data"]
        return {
            "simulation_cycles": t.get("simulation_cycles", 0),
            "meteorites_processed": t.get("meteorites_processed", 0),
            "total_impacts": t.get("total_impacts", 0),
            "critical_impacts": t.get("critical_impact_count", 0),
            "latency_cycles": t.get("latency_cycles", 18),
            "latency_us": 0.18,
            "parallel_channels": 8,
            "hardware_connected": self.is_hardware
        }

    def get_debug_registers(self) -> Dict[str, Any]:
        """Returns hex dump of all 32 hardware registers."""
        return {
            "scene": "mars_habitat",
            "base_address": f"0x{self.base_address:08X}",
            "0x00_CONTROL": f"0x{self.read32(REG_CONTROL):08X}",
            "0x04_ATTACK": f"0x{self.read32(REG_ATTACK):08X}",
            "0x08_THRESHOLD": f"0x{self.read32(REG_THRESHOLD):08X}",
            "0x0C_STATUS": f"0x{self.read32(REG_STATUS):08X}",
            "0x10_IMPACT": f"0x{self.read32(REG_IMPACT):08X}",
            "0x14_COUNTERS": f"0x{self.read32(REG_COUNTERS):08X}",
            "0x18_TOTAL": f"0x{self.read32(REG_TOTAL):08X}",
            "0x1C_LANDING_ALTITUDE": f"0x{self.read32(REG_LANDING_ALTITUDE):08X}",
            "0x20_LANDING_VELOCITY": f"0x{self.read32(REG_LANDING_VELOCITY):08X}",
            "0x24_THRUST_COMMAND": f"0x{self.read32(REG_THRUST_COMMAND):08X}",
            "0x28_PREDICTED_ALTITUDE": f"0x{self.read32(REG_PREDICTED_ALTITUDE):08X}",
            "0x2C_PREDICTED_TOUCHDOWN_VEL": f"0x{self.read32(REG_PREDICTED_TOUCHDOWN_VEL):08X}",
            "0x30_LANDING_STATUS": f"0x{self.read32(REG_LANDING_STATUS):08X}",
            "0x34_METEORITE_ACTIVE": f"0x{self.read32(REG_METEORITE_ACTIVE):08X}",
            "0x38_METEORITE_IMPACT_VECTOR": f"0x{self.read32(REG_METEORITE_IMPACT_VECTOR):08X}",
            "0x3C_TOTAL_IMPACT_ENERGY": f"0x{self.read32(REG_TOTAL_IMPACT_ENERGY):08X}",
            "0x40_SECTION_DAMAGE": f"0x{self.read32(REG_SECTION_DAMAGE):08X}",
            "0x44_RECOVERY_ACTION": f"0x{self.read32(REG_RECOVERY_ACTION):08X}",
            "0x48_O2_PERCENT": f"0x{self.read32(REG_O2_PERCENT):08X}",
            "0x4C_CO2_PERCENT": f"0x{self.read32(REG_CO2_PERCENT):08X}",
            "0x50_PRESSURE_KPA": f"0x{self.read32(REG_PRESSURE_KPA):08X}",
            "0x54_TEMPERATURE_C": f"0x{self.read32(REG_TEMPERATURE_C):08X}",
            "0x58_LIFE_SUPPORT_STATUS": f"0x{self.read32(REG_LIFE_SUPPORT_STATUS):08X}",
            "0x5C_HABITAT_HEALTH": f"0x{self.read32(REG_HABITAT_HEALTH):08X}",
            "0x60_HAZARD_SCORE": f"0x{self.read32(REG_HAZARD_SCORE):08X}",
            "0x64_FAULT_FLAGS": f"0x{self.read32(REG_FAULT_FLAGS):08X}",
            "0x68_SIMULATION_CYCLES": f"0x{self.read32(REG_SIMULATION_CYCLES):08X}",
            "0x6C_METEORITES_PROCESSED": f"0x{self.read32(REG_METEORITES_PROCESSED):08X}",
            "0x70_LATENCY_CYCLES": f"0x{self.read32(REG_LATENCY_CYCLES):08X}",
            "0x74_UPDATE_COUNTER": f"0x{self.read32(REG_UPDATE_COUNTER):08X}",
            "0x78_HARDWARE_VERSION": f"0x{self.read32(REG_HARDWARE_VERSION):08X}",
        }
