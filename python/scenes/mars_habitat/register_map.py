"""
python.scenes.mars_habitat.register_map
=======================================
AXI register definitions for Mars Space Habitat & Landing Accelerator peripheral.
Base Address: 0x43C20000 (M_AXI_GP0)
Expanded 256-byte register aperture (0x00 .. 0x7C).
"""

BASE_ADDRESS = 0x43C20000

# -----------------------------------------------------------------------------
# Register Offsets
# -----------------------------------------------------------------------------
REG_CONTROL                 = 0x00  # [W]   Bit 0: attack_strobe, 1: reset_strobe, 2: landing_start, 3: meteor_parallel_en
REG_ATTACK                  = 0x04  # [R/W] Bit 0: type (0=NORM, 1=BIG), Bits [2:1]: target (0=ALL, 1=A, 2=B), Bits [15:8]: count
REG_THRESHOLD               = 0x08  # [R/W] [15:0]: threshold_A x10, [31:16]: threshold_B x10
REG_STATUS                  = 0x0C  # [R]   [3:0]: state, 4: A_closed, 5: B_closed, 6: link_closed, 7: crossed, [9:8]: target
REG_IMPACT                  = 0x10  # [R]   [15:0]: last_impact x10, [23:16]: processed, [31:24]: total_requested
REG_COUNTERS                = 0x14  # [R]   [15:0]: impacts_A, [31:16]: impacts_B
REG_TOTAL                   = 0x18  # [R]   [15:0]: total_impacts, [31:16]: critical_impacts
REG_LANDING_ALTITUDE        = 0x1C  # [R]   [31:0]: altitude in 0.1m
REG_LANDING_VELOCITY        = 0x20  # [R]   [15:0]: velocity in 0.1m/s (signed), [31:16]: accel in 0.1m/s^2 (signed)
REG_THRUST_COMMAND          = 0x24  # [R]   [15:0]: thrust command 0..1000 (0.0% to 100.0%)
REG_PREDICTED_ALTITUDE      = 0x28  # [R]   [31:0]: predicted altitude at T+5 in 0.1m
REG_PREDICTED_TOUCHDOWN_VEL = 0x2C  # [R]   [15:0]: predicted touchdown velocity in 0.1m/s (signed)
REG_LANDING_STATUS          = 0x30  # [R]   [1:0]: 0=SAFE, 1=WARN, 2=CRIT; [3:2]: 0=PREP, 1=POWERED, 2=APPROACH, 3=TOUCHDOWN
REG_METEORITE_ACTIVE        = 0x34  # [R]   [7:0]: 8-channel active mask
REG_METEORITE_IMPACT_VECTOR = 0x38  # [R]   [7:0]: 8-channel impact vector
REG_TOTAL_IMPACT_ENERGY     = 0x3C  # [R]   [31:0]: accumulated kinetic impact energy
REG_SECTION_DAMAGE          = 0x40  # [R]   [15:0]: section A damage, [31:16]: section B damage
REG_RECOVERY_ACTION         = 0x44  # [R]   [3:0]: 0=NONE, 1=ISOLATE_A, 2=ISOLATE_B, 3=ISOLATE_BOTH, 4=EMERGENCY
REG_O2_PERCENT              = 0x48  # [R]   [15:0]: O2 percent x10 (e.g. 209 = 20.9%)
REG_CO2_PERCENT             = 0x4C  # [R]   [15:0]: CO2 percent x100 (e.g. 4 = 0.04%)
REG_PRESSURE_KPA            = 0x50  # [R]   [15:0]: pressure in kPa x10 (e.g. 1013 = 101.3 kPa)
REG_TEMPERATURE_C           = 0x54  # [R]   [15:0]: temperature in deg C x10 (signed)
REG_LIFE_SUPPORT_STATUS     = 0x58  # [R]   [1:0]: 0=STABLE, 1=DEGRADED, 2=WARNING, 3=CRITICAL
REG_HABITAT_HEALTH          = 0x5C  # [R]   [7:0]: composite health score (0..100)
REG_HAZARD_SCORE            = 0x60  # [R]   [7:0]: score 0..100, [9:8]: 0=NORMAL, 1=WARNING, 2=CRITICAL
REG_FAULT_FLAGS             = 0x64  # [R]   [15:0]: hardware fault safety bitmask
REG_SIMULATION_CYCLES       = 0x68  # [R]   [31:0]: master clock cycles
REG_METEORITES_PROCESSED    = 0x6C  # [R]   [15:0]: cumulative meteorites processed
REG_LATENCY_CYCLES          = 0x70  # [R]   [31:0]: hardware pipeline latency cycles (18 cycles)
REG_UPDATE_COUNTER          = 0x74  # [R]   [31:0]: authoritative simulation update counter
REG_HARDWARE_VERSION        = 0x78  # [R]   [31:0]: hardware ID tag (0x4D415253 = 'MARS')

# -----------------------------------------------------------------------------
# Enums and Lookup Tables
# -----------------------------------------------------------------------------
STATE_NAMES = {
    0: "IDLE",
    1: "ATTACK_RECEIVED",
    2: "METEORITE_ACTIVE",
    3: "TARGET_IDENT",
    4: "IMPACT_CALC",
    5: "THRESHOLD_CHECK",
    6: "PROTECTION_ACTION",
    7: "UPDATE_STATUS",
    8: "NEXT_METEORITE",
    9: "ATTACK_COMPLETE"
}

LANDING_FSM_NAMES = {
    0: "PREP",
    1: "POWERED_DESCENT",
    2: "APPROACH",
    3: "TOUCHDOWN"
}

LANDING_STATUS_NAMES = {
    0: "SAFE",
    1: "WARNING",
    2: "CRITICAL"
}

RECOVERY_ACTION_NAMES = {
    0: "NO_ACTION",
    1: "ISOLATE_A",
    2: "ISOLATE_B",
    3: "ISOLATE_BOTH",
    4: "EMERGENCY_RECOVERY"
}

LIFE_SUPPORT_STATUS_NAMES = {
    0: "STABLE",
    1: "DEGRADED",
    2: "WARNING",
    3: "CRITICAL"
}

HAZARD_STATUS_NAMES = {
    0: "NORMAL",
    1: "WARNING",
    2: "CRITICAL"
}

FAULT_FLAG_BITS = {
    0: "EXCESSIVE_VELOCITY",
    1: "LANDING_ALT_ERROR",
    2: "THRUST_SATURATION",
    3: "CRITICAL_METEORITE",
    4: "SECTION_A_BREACH",
    5: "SECTION_B_BREACH",
    6: "O2_DEPLETION",
    7: "CO2_TOXICITY",
    8: "PRESSURE_LOSS",
    9: "THERMAL_FAILURE"
}
