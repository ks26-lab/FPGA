// ============================================================================
// File: underwater_pid_controller.v
// Module: underwater_pid_controller
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem
// Description:
//   Dedicated FPGA PID depth controller with fixed-point arithmetic,
//   integral anti-windup clamping, derivative filtering, and disturbance compensation.
//
// Equations:
//   error      = target_depth - current_depth
//   P_term     = (Kp * error) >>> 4
//   I_term     = (Ki * integral) >>> 8
//   D_term     = (Kd * (error - prev_error)) >>> 2
//   control    = P_term + I_term + D_term
//   thrust     = clamp(BASE_THRUST + control + disturbance_comp, MIN_THRUST, MAX_THRUST)
// ============================================================================

`timescale 1ns / 1ps

module underwater_pid_controller #(
    parameter signed [15:0] BASE_THRUST = 16'sd500,  // 50.0 N neutral buoyancy
    parameter signed [15:0] MIN_THRUST  = 16'sd0,    // 0.0 N
    parameter signed [15:0] MAX_THRUST  = 16'sd1400  // 1400 N / 140.0 N project specification
)(
    input  wire               clk,
    input  wire               rst_n,
    input  wire               update_tick,
    input  wire               enable,

    // Inputs & Error
    input  wire signed [15:0] depth_error,          // 0.1 m units
    input  wire signed [7:0]  cfg_current_strength, // For disturbance feed-forward

    // Configurable Gain Parameters (Q8.8 or integer scaled)
    input  wire [7:0]         cfg_kp,               // e.g. 8'd20 (1.25x)
    input  wire [7:0]         cfg_ki,               // e.g. 8'd4  (0.25x)
    input  wire [7:0]         cfg_kd,               // e.g. 8'd12 (0.75x)

    // Telemetry Outputs
    output reg  signed [15:0] p_term,               // Proportional term
    output reg  signed [15:0] i_term,               // Integral term
    output reg  signed [15:0] d_term,               // Derivative term
    output reg  signed [15:0] control_output,       // Combined PID output
    output reg  signed [15:0] thrust_command,       // Bounded thrust (0.1 N units)
    output reg  signed [15:0] thrust_delta,         // Thrust slew rate
    output reg                integral_saturated    // Fault indicator
);

    // Anti-windup saturation limits for 24-bit accumulator
    localparam signed [23:0] INT_SAT_POS = 24'sd50000;
    localparam signed [23:0] INT_SAT_NEG = -24'sd50000;

    reg signed [15:0] prev_error;
    reg signed [23:0] integral_acc;
    reg signed [15:0] prev_thrust;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prev_error         <= 16'sd0;
            integral_acc       <= 24'sd0;
            p_term             <= 16'sd0;
            i_term             <= 16'sd0;
            d_term             <= 16'sd0;
            control_output     <= 16'sd0;
            thrust_command     <= BASE_THRUST;
            thrust_delta       <= 16'sd0;
            prev_thrust        <= BASE_THRUST;
            integral_saturated <= 1'b0;
        end else if (enable) begin
            if (update_tick) begin
                // 1. Proportional Term: Kp * error
                reg signed [31:0] p_calc;
                p_calc = depth_error * $signed({8'd0, cfg_kp});
                p_term <= p_calc[19:4]; // Shift by 4

                // 2. Integral Term with Anti-Windup Clamping
                reg signed [23:0] next_integral;
                next_integral = integral_acc + {{8{depth_error[15]}}, depth_error};

                if (next_integral > INT_SAT_POS) begin
                    integral_acc       <= INT_SAT_POS;
                    integral_saturated <= 1'b1;
                end else if (next_integral < INT_SAT_NEG) begin
                    integral_acc       <= INT_SAT_NEG;
                    integral_saturated <= 1'b1;
                end else begin
                    integral_acc       <= next_integral;
                    integral_saturated <= 1'b0;
                end

                reg signed [31:0] i_calc;
                i_calc = integral_acc * $signed({8'd0, cfg_ki});
                i_term <= i_calc[23:8]; // Shift by 8

                // 3. Derivative Term: Kd * (error - prev_error)
                reg signed [15:0] delta_err;
                reg signed [31:0] d_calc;
                delta_err  = depth_error - prev_error;
                prev_error <= depth_error;
                d_calc     = delta_err * $signed({8'd0, cfg_kd});
                d_term     <= d_calc[17:2]; // Shift by 2

                // 4. Combined Control Output + Disturbance Feedforward Compensation
                reg signed [15:0] comb_ctrl;
                reg signed [15:0] dist_comp;
                // Current feedforward counteracts drift
                dist_comp = -{{8{cfg_current_strength[7]}}, cfg_current_strength} * 16'sd2;
                comb_ctrl = p_term + i_term + d_term + dist_comp;
                control_output <= comb_ctrl;

                // 5. Bounded Thrust Calculation
                reg signed [15:0] raw_thrust;
                raw_thrust = BASE_THRUST + comb_ctrl;

                if (raw_thrust < MIN_THRUST) begin
                    thrust_command <= MIN_THRUST;
                end else if (raw_thrust > MAX_THRUST) begin
                    thrust_command <= MAX_THRUST;
                end else begin
                    thrust_command <= raw_thrust;
                end

                // 6. Thrust Delta (Slew Rate)
                thrust_delta <= thrust_command - prev_thrust;
                prev_thrust  <= thrust_command;
            end
        end else begin
            // Disabled / Holding neutral
            p_term             <= 16'sd0;
            i_term             <= 16'sd0;
            d_term             <= 16'sd0;
            control_output     <= 16'sd0;
            thrust_command     <= BASE_THRUST;
            thrust_delta       <= 16'sd0;
            integral_saturated <= 1'b0;
        end
    end

endmodule
