// ============================================================================
// File: maze_top.v
// Module: maze_top
// Project: Zynq Z7010 FPGA 3D Maze Runner
// Description:
//   Top-level module for Experiment 03 on EDGE ZYNQ Z7010 SoC.
//   Binds maze_axi_slave to maze_core and drives board diagnostic LEDs.
// ============================================================================

`timescale 1ns / 1ps

module maze_top #(
    parameter CLK_FREQ_HZ = 50_000_000,
    parameter SIMULATION  = 0
)(
    input  wire        s_axi_aclk,
    input  wire        s_axi_aresetn,

    // AXI4-Lite Slave Interface (8-bit address aperture for up to 256 bytes)
    input  wire [7:0]  s_axi_awaddr,
    input  wire        s_axi_awvalid,
    output wire        s_axi_awready,

    input  wire [31:0] s_axi_wdata,
    input  wire [3:0]  s_axi_wstrb,
    input  wire        s_axi_wvalid,
    output wire        s_axi_wready,

    output wire [1:0]  s_axi_bresp,
    output wire        s_axi_bvalid,
    input  wire        s_axi_bready,

    input  wire [7:0]  s_axi_araddr,
    input  wire        s_axi_arvalid,
    output wire        s_axi_arready,

    output wire [31:0] s_axi_rdata,
    output wire [1:0]  s_axi_rresp,
    output wire        s_axi_rvalid,
    input  wire        s_axi_rready,

    // Physical Diagnostic LEDs
    output wire [3:0]  board_leds,
    output wire        led_collision,
    output wire        led_goal_reached,
    output wire        led_maze_visible
);

    wire [3:0]  cmd_code;
    wire        cmd_strobe;
    wire [3:0]  cfg_start_x;
    wire [3:0]  cfg_start_y;
    wire [3:0]  cfg_goal_x;
    wire [3:0]  cfg_goal_y;
    wire        cfg_pos_we;
    wire [1:0]  cfg_path_algo;
    wire        cfg_path_start;
    wire [5:0]  maze_read_addr;

    wire [3:0]  game_state;
    wire        collision;
    wire        goal_reached;
    wire        maze_visible;
    wire [3:0]  player_x;
    wire [3:0]  player_y;
    wire [3:0]  start_x;
    wire [3:0]  start_y;
    wire [3:0]  goal_x;
    wire [3:0]  goal_y;
    wire [15:0] total_moves;
    wire [7:0]  valid_moves;
    wire [7:0]  collision_count;
    wire [3:0]  time_remaining_sec;
    wire [3:0]  maze_mem_data;

    wire        path_valid;
    wire        path_complete;
    wire [7:0]  path_length;
    wire [7:0]  nodes_explored;
    wire [15:0] path_cycles;
    wire [7:0]  current_distance;
    wire [15:0] extra_moves;
    wire [15:0] path_efficiency;
    wire [3:0]  valid_directions_mask;
    wire        is_dead_end;
    wire        is_branch;
    wire        is_intersection;
    wire [15:0] fault_flags;
    wire [15:0] total_cycles;

    // LED outputs
    assign board_leds[3:0]  = game_state;
    assign led_collision    = collision;
    assign led_goal_reached = goal_reached;
    assign led_maze_visible = maze_visible;

    // AXI Slave
    maze_axi_slave #(
        .C_S_AXI_DATA_WIDTH (32),
        .C_S_AXI_ADDR_WIDTH (8)
    ) u_axi_slave (
        .s_axi_aclk            (s_axi_aclk),
        .s_axi_aresetn          (s_axi_aresetn),

        .s_axi_awaddr           (s_axi_awaddr),
        .s_axi_awvalid          (s_axi_awvalid),
        .s_axi_awready          (s_axi_awready),

        .s_axi_wdata            (s_axi_wdata),
        .s_axi_wstrb            (s_axi_wstrb),
        .s_axi_wvalid           (s_axi_wvalid),
        .s_axi_wready           (s_axi_wready),

        .s_axi_bresp            (s_axi_bresp),
        .s_axi_bvalid           (s_axi_bvalid),
        .s_axi_bready           (s_axi_bready),

        .s_axi_araddr           (s_axi_araddr),
        .s_axi_arvalid          (s_axi_arvalid),
        .s_axi_arready          (s_axi_arready),

        .s_axi_rdata            (s_axi_rdata),
        .s_axi_rresp            (s_axi_rresp),
        .s_axi_rvalid           (s_axi_rvalid),
        .s_axi_rready           (s_axi_rready),

        .cmd_code               (cmd_code),
        .cmd_strobe             (cmd_strobe),
        .cfg_start_x            (cfg_start_x),
        .cfg_start_y            (cfg_start_y),
        .cfg_goal_x             (cfg_goal_x),
        .cfg_goal_y             (cfg_goal_y),
        .cfg_pos_we             (cfg_pos_we),
        .cfg_path_algo          (cfg_path_algo),
        .cfg_path_start         (cfg_path_start),
        .maze_read_addr         (maze_read_addr),

        .game_state             (game_state),
        .collision              (collision),
        .goal_reached           (goal_reached),
        .maze_visible           (maze_visible),
        .player_x               (player_x),
        .player_y               (player_y),
        .start_x                (start_x),
        .start_y                (start_y),
        .goal_x                 (goal_x),
        .goal_y                 (goal_y),
        .total_moves            (total_moves),
        .valid_moves            (valid_moves),
        .collision_count        (collision_count),
        .time_remaining_sec     (time_remaining_sec),
        .maze_mem_data          (maze_mem_data),

        .path_valid             (path_valid),
        .path_complete          (path_complete),
        .path_length            (path_length),
        .nodes_explored         (nodes_explored),
        .path_cycles            (path_cycles),
        .current_distance       (current_distance),
        .extra_moves            (extra_moves),
        .path_efficiency        (path_efficiency),
        .valid_directions_mask  (valid_directions_mask),
        .is_dead_end            (is_dead_end),
        .is_branch              (is_branch),
        .is_intersection        (is_intersection),
        .fault_flags            (fault_flags),
        .total_cycles           (total_cycles)
    );

    // Core
    maze_core #(
        .CLK_FREQ_HZ (CLK_FREQ_HZ),
        .SIMULATION  (SIMULATION)
    ) u_core (
        .clk                   (s_axi_aclk),
        .rst_n                 (s_axi_aresetn),

        .cmd_code              (cmd_code),
        .cmd_strobe            (cmd_strobe),
        .cfg_start_x           (cfg_start_x),
        .cfg_start_y           (cfg_start_y),
        .cfg_goal_x            (cfg_goal_x),
        .cfg_goal_y            (cfg_goal_y),
        .cfg_pos_we            (cfg_pos_we),
        .cfg_path_algo         (cfg_path_algo),
        .cfg_path_start        (cfg_path_start),
        .maze_read_addr        (maze_read_addr),

        .game_state            (game_state),
        .collision             (collision),
        .goal_reached          (goal_reached),
        .maze_visible          (maze_visible),
        .player_x              (player_x),
        .player_y              (player_y),
        .start_x               (start_x),
        .start_y               (start_y),
        .goal_x                (goal_x),
        .goal_y                (goal_y),
        .total_moves           (total_moves),
        .valid_moves           (valid_moves),
        .collision_count       (collision_count),
        .time_remaining_sec    (time_remaining_sec),
        .maze_mem_data         (maze_mem_data),

        .path_valid            (path_valid),
        .path_complete         (path_complete),
        .path_length           (path_length),
        .nodes_explored        (nodes_explored),
        .path_cycles           (path_cycles),
        .current_distance      (current_distance),
        .extra_moves           (extra_moves),
        .path_efficiency       (path_efficiency),
        .valid_directions_mask (valid_directions_mask),
        .is_dead_end           (is_dead_end),
        .is_branch             (is_branch),
        .is_intersection       (is_intersection),
        .fault_flags           (fault_flags),
        .total_cycles          (total_cycles)
    );

endmodule
