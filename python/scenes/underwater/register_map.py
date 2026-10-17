"""
python.scenes.underwater.register_map
=====================================
AXI register definitions for the upgraded Underwater Dynamic Probe engine.
Base Address: 0x43C00000 (M_AXI_GP0, 64KB aperture)

All numerical representations and register layouts strictly match
fpga_interface/verilog/underwater_probe_axi_slave.v.
"""

BASE_ADDRESS = 0x43C00000

# Legacy Control & Status Registers
REG_CONTROL            = 0x00  # [W]   Bit 0: start, 1: stop, 2: reset, 3: disturb_strobe, [5:4]: disturb_type, 6: set_depth_we
REG_DEPTH_CFG          = 0x04  # [R/W] [15:0]: set_depth x10, [31:16]: target_depth x10
REG_CURRENT            = 0x08  # [R/W] [7:0]: signed current strength %
REG_STATUS             = 0x0C  # [R]   [3:0]: state, 4: col, 5: rec, 6: tgt_reached, [8:7]: active_obj

# Upgraded Parallel Telemetry Registers
REG_CURRENT_DEPTH      = 0x10  # [R]   [15:0]: current depth (0.1m)
REG_TARGET_DEPTH       = 0x14  # [R]   [15:0]: target depth (0.1m)
REG_VELOCITY           = 0x18  # [R]   [7:0]: probe velocity (signed 0.1 m/s)
REG_DEPTH_ERROR        = 0x1C  # [R]   [15:0]: depth error (signed 0.1m)
REG_FILTERED_DEPTH     = 0x20  # [R]   [15:0]: MAF filtered depth (0.1m)
REG_FILTERED_VELOCITY  = 0x24  # [R]   [7:0]: EMA filtered velocity (signed 0.1 m/s)
REG_DRAG_FORCE         = 0x28  # [R]   [15:0]: hydrodynamic drag force (signed 0.1 N)
REG_RELATIVE_VELOCITY  = 0x2C  # [R]   [15:0]: relative water velocity (signed 0.1 m/s)
REG_P_TERM             = 0x30  # [R]   [15:0]: PID P-term
REG_I_TERM             = 0x34  # [R]   [15:0]: PID I-term
REG_D_TERM             = 0x38  # [R]   [15:0]: PID D-term
REG_CONTROL_OUTPUT     = 0x3C  # [R]   [15:0]: combined PID control output
REG_THRUST_COMMAND     = 0x40  # [R]   [15:0]: bounded thrust (0.1 N)
REG_THRUST_DELTA       = 0x44  # [R]   [15:0]: thrust delta slew rate (0.1 N/tick)
REG_IMPACT_ENERGY      = 0x48  # [R]   [15:0]: kinetic impact energy (Joules)
REG_IMPACT_SEVERITY    = 0x4C  # [R]   [2:0]: severity level (0=NONE..4=CRIT)
REG_RECOVERY_THRUST    = 0x50  # [R]   [15:0]: recovery thrust (0.1 N)
REG_POST_COL_VELOCITY  = 0x54  # [R]   [7:0]: post-collision velocity (signed 0.1 m/s)
REG_PREDICTED_DEPTH_1  = 0x58  # [R]   [15:0]: projected depth at T+1 (0.1m)
REG_PREDICTED_DEPTH_3  = 0x5C  # [R]   [15:0]: projected depth at T+3 (0.1m)
REG_PREDICTED_DEPTH_5  = 0x60  # [R]   [15:0]: projected depth at T+5 (0.1m)
REG_CONTROL_COST       = 0x64  # [R]   [15:0]: energy optimizer cost
REG_OPTIMIZATION_ACT   = 0x68  # [R]   [1:0]: action (0=HOLD, 1=INCREASE, 2=DECREASE)
REG_FAULT_FLAGS        = 0x6C  # [R]   [7:0]: anomaly & fault flags
REG_SIMULATION_CYCLES  = 0x70  # [R]   [31:0]: simulation clock cycles
REG_PHYSICS_UPDATES    = 0x74  # [R]   [31:0]: physics tick counter
REG_COLLISION_COUNT    = 0x78  # [R]   [15:0]: cumulative collision count
REG_RECOVERY_COUNT     = 0x7C  # [R]   [15:0]: cumulative recovery count

# Aliases for backward compatibility
REG_POSITION = REG_CURRENT_DEPTH
REG_COUNTERS = REG_COLLISION_COUNT
REG_CYCLES   = REG_SIMULATION_CYCLES

# Control Register Bit Positions
CTRL_START_BIT          = 0
CTRL_STOP_BIT           = 1
CTRL_RESET_BIT          = 2
CTRL_DISTURB_STROBE_BIT = 3
CTRL_DISTURB_TYPE_SHIFT = 4
CTRL_DISTURB_TYPE_MASK  = 0x3
CTRL_SET_DEPTH_WE_BIT   = 6

DISTURBANCE_TYPES = {
    "NONE": 0,
    "FISH": 1,
    "GARBAGE": 2,
    "WHALE": 3
}

DISTURBANCE_NAMES = {v: k for k, v in DISTURBANCE_TYPES.items()}

STATE_NAMES = {
    0: "IDLE",
    1: "MOVING_TO_TARGET",
    2: "DISTURBED",
    3: "COLLISION_DETECTED",
    4: "DISPLACEMENT",
    5: "RECOVERY",
    6: "TARGET_REACHED"
}

SEVERITY_NAMES = {
    0: "NONE",
    1: "LOW",
    2: "MEDIUM",
    3: "HIGH",
    4: "CRITICAL"
}

ACTION_NAMES = {
    0: "HOLD_THRUST",
    1: "INCREASE_THRUST",
    2: "DECREASE_THRUST"
}

FAULT_BITS = {
    0: "SENSOR_FAULT",
    1: "DEPTH_ERROR_FAULT",
    2: "VELOCITY_FAULT",
    3: "THRUST_FAULT",
    4: "CURRENT_FAULT",
    5: "COLLISION_FAULT",
    6: "PID_SATURATION"
}
