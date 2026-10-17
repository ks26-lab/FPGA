// ============================================================================
// File: underwater_prediction_engine.v
// Module: underwater_prediction_engine
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem
// Description:
//   Dedicated FPGA hardware predictive engine projecting future probe depth
//   at T+1, T+3, and T+5 discrete timesteps using current state, velocity,
//   and control acceleration.
//
// Equations:
//   predicted_depth[1] = current_depth + velocity*1 + (accel*1) / 2
//   predicted_depth[3] = current_depth + velocity*3 + (accel*9) / 2
//   predicted_depth[5] = current_depth + velocity*5 + (accel*25) / 2
// ============================================================================

`timescale 1ns / 1ps

module underwater_prediction_engine (
    input  wire               clk,
    input  wire               rst_n,

    input  wire signed [15:0] current_depth,    // 0.1 m units
    input  wire signed [7:0]  current_velocity, // 0.1 m/s units
    input  wire signed [15:0] thrust_force,     // 0.1 N units
    input  wire signed [15:0] drag_force,       // 0.1 N units

    output reg  signed [15:0] predicted_depth_1,// T+1
    output reg  signed [15:0] predicted_depth_3,// T+3
    output reg  signed [15:0] predicted_depth_5 // T+5
);

    wire signed [15:0] vel_ext = {{8{current_velocity[7]}}, current_velocity};
    // Acceleration estimate = (thrust - 500 - drag) / 32
    wire signed [15:0] accel   = (thrust_force - 16'sd500 - drag_force) >>> 5;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            predicted_depth_1 <= 16'sd500;
            predicted_depth_3 <= 16'sd500;
            predicted_depth_5 <= 16'sd500;
        end else begin
            reg signed [15:0] p1, p3, p5;

            // T+1: d + v + a/2
            p1 = current_depth + vel_ext + (accel >>> 1);
            if (p1 < 16'sd0)          p1 = 16'sd0;
            else if (p1 > 16'sd10000) p1 = 16'sd10000;
            predicted_depth_1 <= p1;

            // T+3: d + 3*v + (4*a)
            p3 = current_depth + (vel_ext * 16'sd3) + (accel <<< 2);
            if (p3 < 16'sd0)          p3 = 16'sd0;
            else if (p3 > 16'sd10000) p3 = 16'sd10000;
            predicted_depth_3 <= p3;

            // T+5: d + 5*v + (12*a)
            p5 = current_depth + (vel_ext * 16'sd5) + (accel * 16'sd12);
            if (p5 < 16'sd0)          p5 = 16'sd0;
            else if (p5 > 16'sd10000) p5 = 16'sd10000;
            predicted_depth_5 <= p5;
        end
    end

endmodule
