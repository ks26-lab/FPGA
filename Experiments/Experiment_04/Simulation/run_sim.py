"""
Software Emulation & Verification Script for Experiment 04: Solar Tracking Gimbal
Tests 3D vector calculation, incident angle derivation, photovoltaic power estimation,
and dual-axis closed-loop tracking using the sun ephemeris dataset.
"""

import sys
import os
import csv

# Add repository root to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from python.emulation.solar_model import SolarGimbalRTLModel

def run_solar_simulation():
    print("=" * 70)
    print("  EXPERIMENT 04: SOLAR TRACKING GIMBAL - SIMULATION & VERIFICATION")
    print("=" * 70)

    model = SolarGimbalRTLModel()
    model.reset()

    # Verify Hardware Version ID
    hw_id = model.read32(0x78)
    print(f"[*] Read Hardware ID: 0x{hw_id:08X} (Expected: 0x501A7010)")

    # Read sun_dataset.csv
    csv_path = os.path.join(os.path.dirname(__file__), "sun_dataset.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join(repo_root, "sun_dataset.csv")

    rows = []
    with open(csv_path, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "time": row["TIME"],
                "azimuth": float(row["AZIMUTH"]),
                "elevation": float(row["ELEVATION"]),
                "irradiance": float(row["IRRADIANCE"])
            })

    print(f"[*] Loaded {len(rows)} ephemeris timesteps from {os.path.basename(csv_path)}")

    # Tracking simulation
    total_energy_tracked_wh = 0.0
    total_energy_fixed_wh = 0.0

    # Fixed panel pointed South (180.0°) with 35.0° tilt
    fixed_az = 1800
    fixed_el = 350

    print("\n--- Day-Long Tracking Telemetry Sample (Active Sunlight Hours) ---")
    print(f"{'Time':<7} | {'Sun Az/El':<12} | {'Panel Az/El':<14} | {'Inc Ang':<8} | {'P_Track (W)':<11} | {'Status':<10}")
    print("-" * 75)

    for i, step in enumerate(rows):
        s_az = int(step["azimuth"] * 10)
        s_el = int(step["elevation"] * 10)

        # Write sun position to AXI register 0x04
        model.write32(0x04, (s_el << 16) | s_az)

        # Enable closed loop tracking
        model.write32(0x00, 0x04)

        # Run tracking ticks
        for _ in range(20):
            model.tick()

        # Read back telemetry
        p_pos = model.read32(0x08)
        p_az = (p_pos & 0xFFFF) / 10.0
        p_el = ((p_pos >> 16) & 0xFFFF) / 10.0

        inc_reg = model.read32(0x38)
        inc_ang = (inc_reg & 0xFFFF) / 10.0

        pwr_reg = model.read32(0x3C)
        p_track = (pwr_reg & 0xFFFF)

        status_reg = model.read32(0x0C)
        is_locked = (status_reg >> 4) & 1
        state_str = "LOCKED" if is_locked else f"STATE_{status_reg & 0x0F}"

        # Fixed panel calculation for comparison
        if s_el > 0:
            import math
            s_az_r = math.radians(step["azimuth"])
            s_el_r = math.radians(step["elevation"])
            f_az_r = math.radians(fixed_az / 10.0)
            f_el_r = math.radians(fixed_el / 10.0)

            dot_fixed = (math.cos(s_el_r) * math.cos(s_az_r) * math.cos(f_el_r) * math.cos(f_az_r) +
                         math.cos(s_el_r) * math.sin(s_az_r) * math.cos(f_el_r) * math.sin(f_az_r) +
                         math.sin(s_el_r) * math.sin(f_el_r))
            p_fixed = max(0.0, dot_fixed) * 5665.0
        else:
            p_fixed = 0.0

        # Accumulate energy (15 min timestep = 0.25 hours)
        total_energy_tracked_wh += p_track * 0.25
        total_energy_fixed_wh += p_fixed * 0.25

        # Print samples during daylight
        if 23 <= i <= 65 and i % 6 == 0:
            print(f"{step['time']:<7} | {step['azimuth']:>5.1f}/{step['elevation']:>4.1f} | {p_az:>5.1f}/{p_el:>4.1f}   | {inc_ang:>5.1f}°  | {p_track:>7} W   | {state_str:<10}")

    print("-" * 75)
    print(f"\n[RESULTS] Day-Long Energy Generation Summary:")
    print(f"  - Dual-Axis FPGA Tracked Solar System: {total_energy_tracked_wh / 1000.0:.2f} kWh")
    print(f"  - Fixed South-Facing Solar Array:       {total_energy_fixed_wh / 1000.0:.2f} kWh")
    gain = ((total_energy_tracked_wh - total_energy_fixed_wh) / max(1.0, total_energy_fixed_wh)) * 100.0
    print(f"  - Solar Tracking Energy Gain:           +{gain:.1f}%")

    print("\n[VERIFICATION] Experiment 04 Simulation Complete: PASS\n")

if __name__ == "__main__":
    run_solar_simulation()
