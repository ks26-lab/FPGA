// ============================================================================
// File: underwater_energy_optimizer.v
// Module: underwater_energy_optimizer
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem
// Description:
//   Dedicated FPGA hardware energy optimizer calculating real-time control cost
//   and determining optimal thrust action:
//     cost = W_error * |depth_error| + W_vel * |velocity| + W_thrust * |thrust - base|
//   Optimization Action:
//     0 = HOLD_THRUST, 1 = INCREASE_THRUST, 2 = DECREASE_THRUST
// ============================================================================

`timescale 1ns / 1ps

module underwater_energy_optimizer (
    input  wire               clk,
    input  wire               rst_n,

    input  wire signed [15:0] depth_error,      // 0.1 m units
    input  wire signed [7:0]  velocity,         // 0.1 m/s units
    input  wire signed [15:0] thrust_command,   // 0.1 N units

    output reg  [15:0]        control_cost,
    output reg  [1:0]         optimization_action, // 0=HOLD, 1=INCREASE, 2=DECREASE
    output reg  [15:0]        estimated_energy     // Accumulated Joules
);

    localparam ACT_HOLD     = 2'd0;
    localparam ACT_INCREASE = 2'd1;
    localparam ACT_DECREASE = 2'd2;

    wire [15:0] abs_err = (depth_error < 0) ? -depth_error : depth_error;
    wire [15:0] abs_vel = (velocity < 0) ? -{{8{velocity[7]}}, velocity} : {{8{velocity[7]}}, velocity};
    wire signed [15:0] delta_th = thrust_command - 16'sd500;
    wire [15:0] abs_th  = (delta_th < 0) ? -delta_th : delta_th;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            control_cost        <= 16'd0;
            optimization_action <= ACT_HOLD;
            estimated_energy    <= 16'd0;
        end else begin
            // Weighted cost computation:
            // cost = (2 * abs_err) + (4 * abs_vel) + (abs_th / 4)
            reg [31:0] c_calc;
            c_calc = (abs_err <<< 1) + (abs_vel <<< 2) + (abs_th >>> 2);
            control_cost <= (c_calc > 32'd65535) ? 16'd65535 : c_calc[15:0];

            // Action Determination:
            // If error is large and velocity is opposite -> Increase thrust
            // If probe is overshooting (error small, velocity high) -> Decrease thrust
            // Else -> Hold
            if ((depth_error > 16'sd20 && velocity < -8'sd2) ||
                (depth_error < -16'sd20 && velocity > 8'sd2)) begin
                optimization_action <= ACT_INCREASE;
            end else if ((abs_err < 16'd5) && (abs_vel > 16'd8)) begin
                optimization_action <= ACT_DECREASE;
            end else begin
                optimization_action <= ACT_HOLD;
            end

            // Energy accumulator: Power = thrust * dt
            estimated_energy <= estimated_energy + (abs_th[11:4]);
        end
    end

endmodule
