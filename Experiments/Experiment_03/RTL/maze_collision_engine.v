// ============================================================================
// File: maze_collision_engine.v
// Module: maze_collision_engine
// Project: Zynq Z7010 FPGA 3D Maze Runner
// Description:
//   Evaluates all 4 cardinal directions concurrently in combinational logic.
//   Tests outer grid boundaries, checks cell wall bitmasks, outputs 4-bit
//   validity mask, and classifies topological nature (dead-end, branch, intersection).
// ============================================================================

`timescale 1ns / 1ps

module maze_collision_engine (
    input  wire [3:0]  player_x,
    input  wire [3:0]  player_y,
    input  wire [3:0]  cell_walls, // [0]=UP, [1]=RIGHT, [2]=DOWN, [3]=LEFT

    // 4-Direction Parallel Validity
    output wire        valid_up,
    output wire        valid_right,
    output wire        valid_down,
    output wire        valid_left,
    output wire [3:0]  valid_directions_mask,

    // Topology Classification
    output wire [2:0]  neighbor_count,
    output wire        is_dead_end,
    output wire        is_branch,
    output wire        is_intersection
);

    // Boundary constraints: 8x8 grid (0..7)
    wire can_up    = (player_y > 4'd0);
    wire can_right = (player_x < 4'd7);
    wire can_down  = (player_y < 4'd7);
    wire can_left  = (player_x > 4'd0);

    // Wall checks (1 = wall present, 0 = open passage)
    assign valid_up    = can_up    && (~cell_walls[0]);
    assign valid_right = can_right && (~cell_walls[1]);
    assign valid_down  = can_down  && (~cell_walls[2]);
    assign valid_left  = can_left  && (~cell_walls[3]);

    assign valid_directions_mask = {valid_left, valid_down, valid_right, valid_up};

    assign neighbor_count = valid_up + valid_right + valid_down + valid_left;

    assign is_dead_end     = (neighbor_count == 3'd1);
    assign is_branch       = (neighbor_count == 3'd3);
    assign is_intersection = (neighbor_count == 3'd4);

endmodule
