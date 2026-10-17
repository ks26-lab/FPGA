// ============================================================================
// File: traffic_green_split_optimizer.v
// Module: traffic_green_split_optimizer
// Project: Zynq Z7010 FPGA Smart City Traffic Grid
// Description:
//   Dynamic Green-Split & Starvation Optimizer.
//   Calculates green allocations clamped between G_min and G_max based on
//   queues, unserved waiting times, and starvation thresholds.
// ============================================================================

`timescale 1ns / 1ps

module traffic_green_split_optimizer (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        tick_enable,

    input  wire [8:0]  q_ns_sum,
    input  wire [8:0]  q_ew_sum,
    input  wire [15:0] min_green_s,
    input  wire [15:0] max_green_s,
    input  wire [15:0] starvation_limit_s,
    input  wire [3:0]  current_phase,

    output reg  [7:0]  calc_green_ns_s,
    output reg  [7:0]  calc_green_ew_s,
    output reg  [15:0] ns_wait_time_s,
    output reg  [15:0] ew_wait_time_s,
    output reg         ns_starving,
    output reg         ew_starving
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            calc_green_ns_s <= 8'd25;
            calc_green_ew_s <= 8'd20;
            ns_wait_time_s  <= 16'd0;
            ew_wait_time_s  <= 16'd0;
            ns_starving     <= 1'b0;
            ew_starving     <= 1'b0;
        end else if (tick_enable) begin
            // Wait time accumulation
            if (current_phase == 4'd0 || current_phase == 4'd1) begin // NS active
                ns_wait_time_s <= 16'd0;
                ew_wait_time_s <= ew_wait_time_s + 16'd1;
            end else if (current_phase == 4'd3 || current_phase == 4'd4) begin // EW active
                ew_wait_time_s <= 16'd0;
                ns_wait_time_s <= ns_wait_time_s + 16'd1;
            end else begin
                ns_wait_time_s <= ns_wait_time_s + 16'd1;
                ew_wait_time_s <= ew_wait_time_s + 16'd1;
            end

            // Starvation detection
            ns_starving <= (ns_wait_time_s >= starvation_limit_s) && (q_ns_sum > 0);
            ew_starving <= (ew_wait_time_s >= starvation_limit_s) && (q_ew_sum > 0);

            // Dynamic split calculation: Split = G_min + (Q_ratio * (G_max - G_min))
            reg [15:0] total_q;
            reg [15:0] g_range;
            reg [15:0] ns_alloc;
            reg [15:0] ew_alloc;

            total_q = q_ns_sum + q_ew_sum;
            g_range = (max_green_s > min_green_s) ? (max_green_s - min_green_s) : 16'd20;

            if (total_q > 0) begin
                ns_alloc = min_green_s + (q_ns_sum * g_range) / total_q;
                ew_alloc = min_green_s + (q_ew_sum * g_range) / total_q;
            end else begin
                ns_alloc = min_green_s + (g_range / 2);
                ew_alloc = min_green_s + (g_range / 2);
            end

            // Clamping
            if (ns_alloc < min_green_s)      calc_green_ns_s <= min_green_s[7:0];
            else if (ns_alloc > max_green_s) calc_green_ns_s <= max_green_s[7:0];
            else                             calc_green_ns_s <= ns_alloc[7:0];

            if (ew_alloc < min_green_s)      calc_green_ew_s <= min_green_s[7:0];
            else if (ew_alloc > max_green_s) calc_green_ew_s <= max_green_s[7:0];
            else                             calc_green_ew_s <= ew_alloc[7:0];
        end
    end

endmodule
