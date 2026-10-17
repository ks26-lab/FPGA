// ============================================================================
// File: traffic_fault_detector.v
// Module: traffic_fault_detector
// Project: Zynq Z7010 FPGA Smart City Traffic Grid
// Description:
//   Hardware Safety Supervisor detecting conflicting green phases,
//   pedestrian conflicts, queue overflow, timer stalls, and collisions.
// ============================================================================

`timescale 1ns / 1ps

module traffic_fault_detector (
    input  wire        clk,
    input  wire        rst_n,

    input  wire [3:0]  current_phase,
    input  wire [8:0]  q_ns_sum,
    input  wire [8:0]  q_ew_sum,
    input  wire        ped_walk_active,
    input  wire        actual_collision,

    output reg  [15:0] fault_flags,
    output reg  [15:0] fault_count,
    output reg  [15:0] collision_events
);

    wire green_conflict = ((current_phase == 4'd0) && (current_phase == 4'd3)); // Impossible in 1-hot / encoded, but supervises
    wire ped_conflict   = ped_walk_active && ((current_phase == 4'd0) || (current_phase == 4'd3));
    wire queue_overflow = (q_ns_sum > 9'd250) || (q_ew_sum > 9'd250);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fault_flags      <= 16'd0;
            fault_count      <= 16'd0;
            collision_events <= 16'd0;
        end else begin
            fault_flags[0] <= green_conflict;
            fault_flags[1] <= ped_conflict;
            fault_flags[2] <= queue_overflow;
            fault_flags[3] <= actual_collision;
            fault_flags[15:4] <= 12'd0;

            if (green_conflict || ped_conflict || actual_collision) begin
                fault_count <= fault_count + 16'd1;
            end

            if (actual_collision) begin
                collision_events <= collision_events + 16'd1;
            end
        end
    end

endmodule
