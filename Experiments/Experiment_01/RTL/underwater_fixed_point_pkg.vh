// ============================================================================
// File: underwater_fixed_point_pkg.vh
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Physics Subsystem
// Description:
//   Fixed-point definitions and constants for the upgraded underwater probe engine.
//
// Arithmetic Standard:
//   - Depth & Position: Q12.4 or integer 0.1m units (1 unit = 0.1 m).
//   - Velocity: 1 unit = 0.1 m/s.
//   - General Physics & Fractional forces: Q16.16 signed fixed-point format:
//       * Bit [31]     : Sign bit
//       * Bits [30:16] : 15-bit integer magnitude (range: -32768 to +32767)
//       * Bits [15:0]  : 16-bit fractional precision (1 LSB = 1/65536 ~= 0.00001526)
// ============================================================================

`ifndef UNDERWATER_FIXED_POINT_PKG_VH
`define UNDERWATER_FIXED_POINT_PKG_VH

// Q16.16 Conversion Macros
`define INT_TO_Q16_16(val)  ({val, 16'd0})
`define Q16_16_TO_INT(val)  (val[31:16])
`define FLOAT_0_5_Q16_16    (32'h00008000) // 0.5 in Q16.16
`define FLOAT_1_0_Q16_16    (32'h00010000) // 1.0 in Q16.16
`define FLOAT_0_1_Q16_16    (32'h0000199A) // 0.1 in Q16.16

// Physics & Drag Constants
// K_drag = 0.25 in Q16.16 -> 0x00004000
`define K_DRAG_Q16_16       (32'h00004000)

// PID Constants (Fixed-Point Q8.8 or integer scaled)
// Kp = 1.25 -> 32'h00014000 (Q16.16)
// Ki = 0.05 -> 32'h00000CCD (Q16.16)
// Kd = 0.75 -> 32'h0000C000 (Q16.16)
`define PID_KP_DEFAULT      (32'h00014000)
`define PID_KI_DEFAULT      (32'h00000CCD)
`define PID_KD_DEFAULT      (32'h0000C000)
`define PID_INTEGRAL_MAX    (32'sd500000)   // Anti-windup clamp in Q16.16
`define PID_INTEGRAL_MIN   (-32'sd500000)

// Thrust Limits (Newtons, scaled x10 for 0.1 N units)
// Base thrust = 50.0 N (500 units), Min = 0.0 N (0), Max = 150.0 N (1500 units)
`define BASE_THRUST_UNITS   (16'sd500)
`define MIN_THRUST_UNITS    (16'sd0)
`define MAX_THRUST_UNITS    (16'sd1500)

// Impact Masses (kg)
`define MASS_FISH_KG        (16'sd5)
`define MASS_GARBAGE_KG     (16'sd25)
`define MASS_WHALE_KG       (16'sd200)

// Fault Bit Flags
`define FAULT_BIT_SENSOR      (0)
`define FAULT_BIT_DEPTH_ERROR (1)
`define FAULT_BIT_VELOCITY    (2)
`define FAULT_BIT_THRUST      (3)
`define FAULT_BIT_CURRENT     (4)
`define FAULT_BIT_COLLISION   (5)
`define FAULT_BIT_PID_SAT     (6)

`endif // UNDERWATER_FIXED_POINT_PKG_VH
