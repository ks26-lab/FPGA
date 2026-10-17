// ============================================================================
// File: underwater_filter_engine.v
// Module: underwater_filter_engine
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem
// Description:
//   Dedicated FPGA hardware filtering engine implementing:
//   1. 4-sample Moving Average Filter (MAF) for depth smoothing
//   2. Exponential Moving Average (EMA) Filter with alpha=0.25 for velocity smoothing
// ============================================================================

`timescale 1ns / 1ps

module underwater_filter_engine (
    input  wire               clk,
    input  wire               rst_n,
    input  wire               update_tick,

    input  wire signed [15:0] raw_depth,
    input  wire signed [7:0]  raw_velocity,

    output reg  signed [15:0] filtered_depth,
    output reg  signed [7:0]  filtered_velocity
);

    // ------------------------------------------------------------------------
    // 1. 4-Tap Moving Average Filter for Depth
    // ------------------------------------------------------------------------
    reg signed [15:0] depth_tap0;
    reg signed [15:0] depth_tap1;
    reg signed [15:0] depth_tap2;
    reg signed [15:0] depth_tap3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            depth_tap0     <= 16'sd500;
            depth_tap1     <= 16'sd500;
            depth_tap2     <= 16'sd500;
            depth_tap3     <= 16'sd500;
            filtered_depth <= 16'sd500;
        end else if (update_tick) begin
            depth_tap0 <= raw_depth;
            depth_tap1 <= depth_tap0;
            depth_tap2 <= depth_tap1;
            depth_tap3 <= depth_tap2;

            // Compute sum of 4 samples / 4 (arithmetic right shift by 2)
            reg signed [17:0] sum_depth;
            sum_depth = depth_tap0 + depth_tap1 + depth_tap2 + depth_tap3;
            filtered_depth <= sum_depth >>> 2;
        end
    end

    // ------------------------------------------------------------------------
    // 2. Exponential Moving Average (EMA) for Velocity:
    //    v_filtered = (1 - alpha) * v_filtered + alpha * v_raw
    //    With alpha = 1/4:
    //    v_filtered_next = (3 * v_filtered + v_raw) >>> 2
    // ------------------------------------------------------------------------
    reg signed [15:0] ema_vel_acc;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ema_vel_acc       <= 16'sd0;
            filtered_velocity <= 8'sd0;
        end else if (update_tick) begin
            reg signed [15:0] v_ext;
            reg signed [15:0] ema_next;
            v_ext = {{8{raw_velocity[7]}}, raw_velocity};
            // 3 * ema + 1 * v_ext = (ema << 1) + ema + v_ext
            ema_next = ((ema_vel_acc <<< 1) + ema_vel_acc + v_ext) >>> 2;
            ema_vel_acc       <= ema_next;
            filtered_velocity <= ema_next[7:0];
        end
    end

endmodule
