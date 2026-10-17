// ============================================================================
// File: maze_distance_engine.v
// Module: maze_distance_engine
// Project: Zynq Z7010 FPGA 3D Maze Runner
// Description:
//   Distance Map & Route Quality Analyzer.
//   Calculates dynamic Manhattan distance, extra moves over optimal,
//   and Q8.8 fixed-point route efficiency (256 = 1.00 = 100%).
// ============================================================================

`timescale 1ns / 1ps

module maze_distance_engine (
    input  wire [3:0]   player_x,
    input  wire [3:0]   player_y,
    input  wire [3:0]   goal_x,
    input  wire [3:0]   goal_y,
    input  wire [15:0]  total_moves,
    input  wire [7:0]   shortest_path_length,

    output wire [7:0]   current_distance,
    output reg  [15:0]  extra_moves,
    output reg  [15:0]  path_efficiency // Q8.8 format
);

    wire [3:0] dx = (player_x > goal_x) ? (player_x - goal_x) : (goal_x - player_x);
    wire [3:0] dy = (player_y > goal_y) ? (player_y - goal_y) : (goal_y - player_y);
    assign current_distance = dx + dy;

    always @(*) begin
        // Extra moves calculation
        if (total_moves > shortest_path_length) begin
            extra_moves = total_moves - shortest_path_length;
        end else begin
            extra_moves = 16'd0;
        end

        // Efficiency Q8.8: (shortest_path_length * 256) / max(1, total_moves)
        if (total_moves == 0) begin
            path_efficiency = 16'd256; // 1.00 default
        end else begin
            reg [23:0] eff_calc;
            eff_calc = (shortest_path_length * 24'd256) / total_moves;
            if (eff_calc > 24'd256) path_efficiency = 16'd256;
            else path_efficiency = eff_calc[15:0];
        end
    end

endmodule
