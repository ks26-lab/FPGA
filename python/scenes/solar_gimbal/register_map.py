"""
python.scenes.solar_gimbal.register_map
=======================================
AXI register definitions for Solar Gimbal tracking peripheral.
Base Address: 0x43C30000 (M_AXI_GP0)
Aperture: 256 bytes (0x00 - 0x7C)
"""

BASE_ADDRESS = 0x43C30000

# ==============================================================================
# Legacy Registers (0x00 - 0x18) - Fully Preserved
# ==============================================================================
REG_CONTROL           = 0x00  # [W] Bit 0: calc_strobe, Bit 1: reset_strobe, Bit 2: track_en, Bit 3: multi_panel_en, Bit 4: opt_power_en
REG_SUN_POS           = 0x04  # [R/W] [15:0]: sun_azimuth x10, [31:16]: sun_elevation x10
REG_PANEL_POS         = 0x08  # [R/W] [15:0]: panel_azimuth x10, [31:16]: panel_elevation x10
REG_STATUS            = 0x0C  # [R] [3:0]: state, Bit 4: locked, Bit 5: az_dir, Bit 6: el_dir, Bit 7: az_hold, Bit 8: el_hold
REG_ERROR             = 0x10  # [R] [15:0]: az_error x10, [31:16]: el_error x10
REG_ACTUATORS         = 0x14  # [R] [15:0]: actuator_az x10, [31:16]: actuator_el x10
REG_CYCLES            = 0x18  # [R] [31:0]: cycle_counter

# ==============================================================================
# Upgraded Mathematical & Parallel Multi-Panel Engine Registers (0x1C - 0x70)
# ==============================================================================
REG_SUN_VECTOR_X      = 0x1C  # [R] Q16.16 signed Sun Direction Vector X
REG_SUN_VECTOR_Y      = 0x20  # [R] Q16.16 signed Sun Direction Vector Y
REG_SUN_VECTOR_Z      = 0x24  # [R] Q16.16 signed Sun Direction Vector Z
REG_PANEL_NORMAL_X    = 0x28  # [R] Q16.16 signed Panel Normal Vector X
REG_PANEL_NORMAL_Y    = 0x2C  # [R] Q16.16 signed Panel Normal Vector Y
REG_PANEL_NORMAL_Z    = 0x30  # [R] Q16.16 signed Panel Normal Z
REG_DOT_PRODUCT       = 0x34  # [R] Q16.16 signed N · S (cos incidence angle)
REG_INCIDENT_ANGLE    = 0x38  # [R] [15:0]: incident_angle x10, [31:16]: cos_incidence x1000
REG_ESTIMATED_POWER   = 0x3C  # [R] [15:0]: estimated_power in Watts, [31:16]: power_efficiency x10
REG_FILTERED_SUN      = 0x40  # [R] [15:0]: filtered_az x10, [31:16]: filtered_el x10
REG_PREDICTED_SUN     = 0x44  # [R] [15:0]: predicted_az x10, [31:16]: predicted_el x10
REG_ANGULAR_VELOCITY  = 0x48  # [R] [15:0]: signed omega_az x10, [31:16]: signed omega_el x10
REG_CONTROL_LIMITS    = 0x4C  # [R/W] [15:0]: az_deadband x10, [31:16]: el_deadband x10
REG_FAULT_FLAGS       = 0x50  # [R] 16-bit hardware safety fault flags bitmask
REG_VECTOR_CYCLES     = 0x54  # [R] 32-bit vector calculation cycles
REG_UPDATE_COUNTER    = 0x58  # [R] 32-bit update counter
REG_PANEL0_DATA       = 0x5C  # [R] [15:0]: panel 0 power (W), [31:16]: panel 0 incident angle x10
REG_PANEL1_DATA       = 0x60  # [R] [15:0]: panel 1 power (W), [31:16]: panel 1 incident angle x10
REG_PANEL2_DATA       = 0x64  # [R] [15:0]: panel 2 power (W), [31:16]: panel 2 incident angle x10
REG_PANEL3_DATA       = 0x68  # [R] [15:0]: panel 3 power (W), [31:16]: panel 3 incident angle x10
REG_TOTAL_ARRAY_POWER = 0x6C  # [R] 32-bit total 4-panel array power in Watts
REG_PANELS_ACTIVE_MASK= 0x70  # [R] [3:0]: active panels mask (0x0F)
REG_TRACKING_QUALITY  = 0x74  # [R] [15:0]: power_loss_watts, [31:16]: tracking_quality_pct
REG_HARDWARE_VERSION  = 0x78  # [R] 32-bit hardware core ID (0x501A7010)

# ==============================================================================
# FSM State & Fault Definitions
# ==============================================================================
STATE_NAMES = {
    0: "IDLE",
    1: "CALCULATING",
    2: "TRACKING_LOCKED",
    3: "SLEWING",
    4: "DEADBAND_HOLD",
    5: "FAULT_LOCKOUT"
}

FAULT_BITS = {
    0: "AZ_MIN_LIMIT_EXCEEDED",
    1: "AZ_MAX_LIMIT_EXCEEDED",
    2: "EL_MIN_LIMIT_EXCEEDED",
    3: "EL_MAX_LIMIT_EXCEEDED",
    4: "EXCESSIVE_TRACKING_ERROR",
    5: "SENSOR_DISAGREEMENT",
    6: "INVALID_NORMAL_VECTOR",
    7: "POWER_COLLAPSE",
    8: "MOTOR_STALL_DETECTED"
}

# Physical Simulation Constants
BENCHMARK_IRRADIANCE_W_M2 = 1361.0
PANEL_AREA_M2             = 18.5
PANEL_EFFICIENCY_PCT      = 22.5
PEAK_POWER_WATTS          = 5665.0
NUMBER_OF_PANELS          = 4
