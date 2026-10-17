// ============================================================================
// File: traffic_queue_engine.v
// Module: traffic_queue_engine
// Project: Zynq Z7010 FPGA Smart City Traffic Grid
// Description:
//   Tracks directional approach queues (Q_N, Q_S, Q_E, Q_W) with saturating
//   adders, computes directional sums (Q_NS, Q_EW, Q_total), and classifies
//   congestion into 5 levels (LOW, NORMAL, HIGH, HEAVY, GRIDLOCK).
// ============================================================================

`timescale 1ns / 1ps

module traffic_queue_engine (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        tick_enable,

    // Arrival / Departure pulses or queue updates
    input  wire [7:0]  cfg_queue_ns_in,
    input  wire [7:0]  cfg_queue_ew_in,
    input  wire        cfg_queue_we,

    // Signal state for departures
    input  wire [3:0]  current_phase, // 0=NS_G, 1=NS_Y, 2=ALL_RED, 3=EW_G, 4=EW_Y, 5=PED, 6=EMG

    // Queue outputs
    output reg  [7:0]  q_north,
    output reg  [7:0]  q_south,
    output reg  [7:0]  q_east,
    output reg  [7:0]  q_west,
    output wire [8:0]  q_ns_sum,
    output wire [8:0]  q_ew_sum,
    output wire [9:0]  q_total,
    output reg  [7:0]  congestion_score, // 0..100%
    output reg  [2:0]  global_congestion_level
);

    assign q_ns_sum = q_north + q_south;
    assign q_ew_sum = q_east + q_west;
    assign q_total  = q_ns_sum + q_ew_sum;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            q_north                 <= 8'd12;
            q_south                 <= 8'd10;
            q_east                  <= 8'd8;
            q_west                  <= 8'd6;
            congestion_score        <= 8'd45;
            global_congestion_level <= 3'd2; // NORMAL
        end else if (cfg_queue_we) begin
            q_north <= cfg_queue_ns_in / 2;
            q_south <= cfg_queue_ns_in - (cfg_queue_ns_in / 2);
            q_east  <= cfg_queue_ew_in / 2;
            q_west  <= cfg_queue_ew_in - (cfg_queue_ew_in / 2);
        end else if (tick_enable) begin
            // Departures during green
            if (current_phase == 4'd0) begin // NS_G
                if (q_north > 0) q_north <= q_north - 8'd1;
                if (q_south > 0) q_south <= q_south - 8'd1;
            end else if (current_phase == 4'd3) begin // EW_G
                if (q_east > 0) q_east <= q_east - 8'd1;
                if (q_west > 0) q_west <= q_west - 8'd1;
            end

            // Congestion score (0-100% scaled by capacity 80)
            reg [15:0] raw_cong;
            raw_cong = (q_total * 100) / 80;
            if (raw_cong > 100) raw_cong = 100;
            congestion_score <= raw_cong[7:0];

            // 5-level classification
            if (raw_cong < 25)      global_congestion_level <= 3'd1; // LOW
            else if (raw_cong < 50) global_congestion_level <= 3'd2; // NORMAL
            else if (raw_cong < 75) global_congestion_level <= 3'd3; // HIGH
            else if (raw_cong < 90) global_congestion_level <= 3'd4; // HEAVY
            else                    global_congestion_level <= 3'd5; // GRIDLOCK
        end
    end

endmodule
