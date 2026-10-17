// ============================================================================
// File: traffic_prediction_engine.v
// Module: traffic_prediction_engine
// Project: Zynq Z7010 FPGA Smart City Traffic Grid
// Description:
//   Predictive Queue Engine calculating queue change velocity:
//     Delta Q = Q[n] - Q[n-1]
//     Q_pred = Q[n] + Delta Q * T_p
// ============================================================================

`timescale 1ns / 1ps

module traffic_prediction_engine (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        tick_enable,

    input  wire [8:0]  q_ns_sum,
    input  wire [8:0]  q_ew_sum,

    output reg  [8:0]  pred_queue_ns,
    output reg  [8:0]  pred_queue_ew
);

    reg [8:0] prev_q_ns;
    reg [8:0] prev_q_ew;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prev_q_ns     <= 9'd22;
            prev_q_ew     <= 9'd14;
            pred_queue_ns <= 9'd25;
            pred_queue_ew <= 9'd16;
        end else if (tick_enable) begin
            prev_q_ns <= q_ns_sum;
            prev_q_ew <= q_ew_sum;

            // Velocity prediction with forward lookahead
            reg signed [9:0] delta_ns;
            reg signed [9:0] delta_ew;
            reg signed [10:0] next_ns;
            reg signed [10:0] next_ew;

            delta_ns = $signed({1'b0, q_ns_sum}) - $signed({1'b0, prev_q_ns});
            delta_ew = $signed({1'b0, q_ew_sum}) - $signed({1'b0, prev_q_ew});

            next_ns = $signed({1'b0, q_ns_sum}) + (delta_ns <<< 1) + 11'sd2;
            next_ew = $signed({1'b0, q_ew_sum}) + (delta_ew <<< 1) + 11'sd1;

            if (next_ns < 0)       pred_queue_ns <= 9'd0;
            else if (next_ns > 255) pred_queue_ns <= 9'd255;
            else                   pred_queue_ns <= next_ns[8:0];

            if (next_ew < 0)       pred_queue_ew <= 9'd0;
            else if (next_ew > 255) pred_queue_ew <= 9'd255;
            else                   pred_queue_ew <= next_ew[8:0];
        end
    end

endmodule
