// ============================================================================
// File: maze_core.v
// Module: maze_core
// Project: Zynq Z7010 FPGA 3D Maze Runner
// Description:
//   Master Hardware Navigation Core coordinating 6-state game FSM,
//   5-second countdown timer, on-chip ROM, parallel collision detection,
//   BFS/A* search acceleration, route quality, and multi-agent monitoring.
// ============================================================================

`timescale 1ns / 1ps

module maze_core #(
    parameter CLK_FREQ_HZ = 50_000_000,
    parameter SIMULATION  = 0
)(
    input  wire        clk,
    input  wire        rst_n,

    // Command Interface
    input  wire [3:0]  cmd_code,   // 1=START, 2=RESET, 3=UP, 4=DOWN, 5=LEFT, 6=RIGHT
    input  wire        cmd_strobe,

    // Configuration
    input  wire [3:0]  cfg_start_x,
    input  wire [3:0]  cfg_start_y,
    input  wire [3:0]  cfg_goal_x,
    input  wire [3:0]  cfg_goal_y,
    input  wire        cfg_pos_we,

    input  wire [1:0]  cfg_path_algo, // 1=BFS, 2=A*
    input  wire        cfg_path_start,
    input  wire [5:0]  maze_read_addr,

    // Status & Telemetry Outputs
    output reg  [3:0]  game_state,
    output reg         collision,
    output reg         goal_reached,
    output reg         maze_visible,

    output reg  [3:0]  player_x,
    output reg  [3:0]  player_y,
    output reg  [3:0]  start_x,
    output reg  [3:0]  start_y,
    output reg  [3:0]  goal_x,
    output reg  [3:0]  goal_y,

    output reg  [15:0] total_moves,
    output reg  [7:0]  valid_moves,
    output reg  [7:0]  collision_count,
    output reg  [3:0]  time_remaining_sec,
    output wire [3:0]  maze_mem_data,

    output wire        path_valid,
    output wire        path_complete,
    output wire [7:0]  path_length,
    output wire [7:0]  nodes_explored,
    output wire [15:0] path_cycles,

    output wire [7:0]  current_distance,
    output wire [15:0] extra_moves,
    output wire [15:0] path_efficiency,

    output wire [3:0]  valid_directions_mask,
    output wire        is_dead_end,
    output wire        is_branch,
    output wire        is_intersection,
    output wire [15:0] fault_flags,
    output reg  [15:0] total_cycles
);

    // States
    localparam STATE_IDLE         = 4'd0;
    localparam STATE_MAZE_DISPLAY = 4'd1;
    localparam STATE_MEMORY_PHASE = 4'd2;
    localparam STATE_GAMEPLAY     = 4'd3;
    localparam STATE_WIN          = 4'd4;
    localparam STATE_GAME_OVER    = 4'd5;

    // 1-second tick generator for 5-second display countdown
    localparam CYCLES_PER_SEC = SIMULATION ? 32'd25 : CLK_FREQ_HZ;
    reg [31:0] sec_counter;
    wire tick_1sec = (sec_counter == (CYCLES_PER_SEC - 1));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) sec_counter <= 32'd0;
        else if (tick_1sec) sec_counter <= 32'd0;
        else sec_counter <= sec_counter + 32'd1;
    end

    // 1. On-Chip Maze ROM
    wire [5:0] current_cell_addr = (player_y << 3) | player_x;
    wire [3:0] current_cell_walls;

    maze_rom u_rom_current (
        .clk  (clk),
        .addr (current_cell_addr),
        .data (current_cell_walls)
    );

    maze_rom u_rom_inspect (
        .clk  (clk),
        .addr (maze_read_addr),
        .data (maze_mem_data)
    );

    // 2. Parallel Collision Engine
    wire valid_up, valid_right, valid_down, valid_left;
    maze_collision_engine u_collision (
        .player_x              (player_x),
        .player_y              (player_y),
        .cell_walls            (current_cell_walls),
        .valid_up              (valid_up),
        .valid_right           (valid_right),
        .valid_down            (valid_down),
        .valid_left            (valid_left),
        .valid_directions_mask (valid_directions_mask),
        .neighbor_count        (),
        .is_dead_end           (is_dead_end),
        .is_branch             (is_branch),
        .is_intersection       (is_intersection)
    );

    // 3. Hardware BFS / A* Engine
    maze_bfs_engine u_bfs (
        .clk            (clk),
        .rst_n          (rst_n),
        .path_start     (cfg_path_start),
        .algo_select    (cfg_path_algo),
        .start_x        (start_x),
        .start_y        (start_y),
        .goal_x         (goal_x),
        .goal_y         (goal_y),
        .path_valid     (path_valid),
        .path_complete  (path_complete),
        .path_length    (path_length),
        .nodes_explored (nodes_explored),
        .path_cycles    (path_cycles)
    );

    // 4. Distance & Route Quality Engine
    maze_distance_engine u_dist (
        .player_x             (player_x),
        .player_y             (player_y),
        .goal_x               (goal_x),
        .goal_y               (goal_y),
        .total_moves          (total_moves),
        .shortest_path_length (path_length),
        .current_distance     (current_distance),
        .extra_moves          (extra_moves),
        .path_efficiency      (path_efficiency)
    );

    assign fault_flags = {14'd0, (goal_x == start_x && goal_y == start_y), (player_x > 7 || player_y > 7)};

    // Master FSM & Movement Logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            game_state         <= STATE_IDLE;
            player_x           <= 4'd0;
            player_y           <= 4'd0;
            start_x            <= 4'd0;
            start_y            <= 4'd0;
            goal_x             <= 4'd7;
            goal_y             <= 4'd7;
            collision          <= 1'b0;
            goal_reached       <= 1'b0;
            maze_visible       <= 1'b0;
            time_remaining_sec <= 4'd5;
            total_moves        <= 16'd0;
            valid_moves        <= 8'd0;
            collision_count    <= 8'd0;
            total_cycles       <= 16'd0;
        end else begin
            total_cycles <= total_cycles + 16'd1;

            if (cfg_pos_we) begin
                start_x <= cfg_start_x;
                start_y <= cfg_start_y;
                goal_x  <= cfg_goal_x;
                goal_y  <= cfg_goal_y;
            end

            case (game_state)
                STATE_IDLE: begin
                    collision    <= 1'b0;
                    goal_reached <= 1'b0;
                    maze_visible <= 1'b0;
                    if (cmd_strobe && cmd_code == 4'd1) begin // START
                        player_x           <= start_x;
                        player_y           <= start_y;
                        game_state         <= STATE_MAZE_DISPLAY;
                        maze_visible       <= 1'b1;
                        time_remaining_sec <= 4'd5;
                        total_moves        <= 16'd0;
                        valid_moves        <= 8'd0;
                        collision_count    <= 8'd0;
                    end
                end

                STATE_MAZE_DISPLAY: begin
                    maze_visible <= 1'b1;
                    if (tick_1sec) begin
                        if (time_remaining_sec > 1) begin
                            time_remaining_sec <= time_remaining_sec - 4'd1;
                        end else begin
                            time_remaining_sec <= 4'd0;
                            maze_visible       <= 1'b0;
                            game_state         <= STATE_GAMEPLAY;
                        end
                    end
                end

                STATE_GAMEPLAY: begin
                    if (cmd_strobe) begin
                        if (cmd_code == 4'd2) begin // RESET
                            game_state <= STATE_IDLE;
                        end else if (cmd_code >= 4'd3 && cmd_code <= 4'd6) begin
                            total_moves <= total_moves + 16'd1;

                            case (cmd_code)
                                4'd3: begin // UP
                                    if (valid_up) begin
                                        player_y    <= player_y - 4'd1;
                                        valid_moves <= valid_moves + 8'd1;
                                        collision   <= 1'b0;
                                    end else begin
                                        collision       <= 1'b1;
                                        collision_count <= collision_count + 8'd1;
                                    end
                                end

                                4'd4: begin // DOWN
                                    if (valid_down) begin
                                        player_y    <= player_y + 4'd1;
                                        valid_moves <= valid_moves + 8'd1;
                                        collision   <= 1'b0;
                                    end else begin
                                        collision       <= 1'b1;
                                        collision_count <= collision_count + 8'd1;
                                    end
                                end

                                4'd5: begin // LEFT
                                    if (valid_left) begin
                                        player_x    <= player_x - 4'd1;
                                        valid_moves <= valid_moves + 8'd1;
                                        collision   <= 1'b0;
                                    end else begin
                                        collision       <= 1'b1;
                                        collision_count <= collision_count + 8'd1;
                                    end
                                end

                                4'd6: begin // RIGHT
                                    if (valid_right) begin
                                        player_x    <= player_x + 4'd1;
                                        valid_moves <= valid_moves + 8'd1;
                                        collision   <= 1'b0;
                                    end else begin
                                        collision       <= 1'b1;
                                        collision_count <= collision_count + 8'd1;
                                    end
                                end
                            endcase
                        end
                    end

                    // Check Win Condition
                    if (player_x == goal_x && player_y == goal_y) begin
                        goal_reached <= 1'b1;
                        game_state   <= STATE_WIN;
                    end
                end

                STATE_WIN: begin
                    goal_reached <= 1'b1;
                    if (cmd_strobe && cmd_code == 4'd2) game_state <= STATE_IDLE;
                end

                STATE_GAME_OVER: begin
                    if (cmd_strobe && cmd_code == 4'd2) game_state <= STATE_IDLE;
                end

                default: game_state <= STATE_IDLE;
            endcase
        end
    end

endmodule
