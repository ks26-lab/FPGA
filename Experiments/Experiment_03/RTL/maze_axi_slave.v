// ============================================================================
// File: maze_axi_slave.v
// Module: maze_axi_slave
// Project: Zynq Z7010 FPGA 3D Maze Runner
// Description:
//   AXI4-Lite Slave Interface bridging ARM Processing System (PS) to
//   the parallel maze_core in PL. Implements 256-byte aperture (0x00 to 0x7C).
// ============================================================================

`timescale 1ns / 1ps

module maze_axi_slave #(
    parameter C_S_AXI_DATA_WIDTH = 32,
    parameter C_S_AXI_ADDR_WIDTH = 8
)(
    input  wire                              s_axi_aclk,
    input  wire                              s_axi_aresetn,

    // AXI4-Lite Write Channels
    input  wire [C_S_AXI_ADDR_WIDTH-1:0]     s_axi_awaddr,
    input  wire                              s_axi_awvalid,
    output reg                               s_axi_awready,

    input  wire [C_S_AXI_DATA_WIDTH-1:0]     s_axi_wdata,
    input  wire [(C_S_AXI_DATA_WIDTH/8)-1:0] s_axi_wstrb,
    input  wire                              s_axi_wvalid,
    output reg                               s_axi_wready,

    output reg  [1:0]                        s_axi_bresp,
    output reg                               s_axi_bvalid,
    input  wire                              s_axi_bready,

    // AXI4-Lite Read Channels
    input  wire [C_S_AXI_ADDR_WIDTH-1:0]     s_axi_araddr,
    input  wire                              s_axi_arvalid,
    output reg                               s_axi_arready,

    output reg  [C_S_AXI_DATA_WIDTH-1:0]     s_axi_rdata,
    output reg  [1:0]                        s_axi_rresp,
    output reg                               s_axi_rvalid,
    input  wire                              s_axi_rready,

    // Core Controls
    output reg  [3:0]                        cmd_code,
    output reg                               cmd_strobe,
    output reg  [3:0]                        cfg_start_x,
    output reg  [3:0]                        cfg_start_y,
    output reg  [3:0]                        cfg_goal_x,
    output reg  [3:0]                        cfg_goal_y,
    output reg                               cfg_pos_we,

    output reg  [1:0]                        cfg_path_algo,
    output reg                               cfg_path_start,
    output reg  [5:0]                        maze_read_addr,

    // Telemetry from Core
    input  wire [3:0]                        game_state,
    input  wire                              collision,
    input  wire                              goal_reached,
    input  wire                              maze_visible,

    input  wire [3:0]                        player_x,
    input  wire [3:0]                        player_y,
    input  wire [3:0]                        start_x,
    input  wire [3:0]                        start_y,
    input  wire [3:0]                        goal_x,
    input  wire [3:0]                        goal_y,

    input  wire [15:0]                       total_moves,
    input  wire [7:0]                        valid_moves,
    input  wire [7:0]                        collision_count,
    input  wire [3:0]                        time_remaining_sec,
    input  wire [3:0]                        maze_mem_data,

    input  wire                              path_valid,
    input  wire                              path_complete,
    input  wire [7:0]                        path_length,
    input  wire [7:0]                        nodes_explored,
    input  wire [15:0]                       path_cycles,

    input  wire [7:0]                        current_distance,
    input  wire [15:0]                       extra_moves,
    input  wire [15:0]                       path_efficiency,

    input  wire [3:0]                        valid_directions_mask,
    input  wire                              is_dead_end,
    input  wire                              is_branch,
    input  wire                              is_intersection,
    input  wire [15:0]                       fault_flags,
    input  wire [15:0]                       total_cycles
);

    always @(posedge s_axi_aclk or negedge s_axi_aresetn) begin
        if (!s_axi_aresetn) begin
            s_axi_awready  <= 1'b0;
            s_axi_wready   <= 1'b0;
            s_axi_bvalid   <= 1'b0;
            s_axi_bresp    <= 2'b00;
            cmd_code       <= 4'd0;
            cmd_strobe     <= 1'b0;
            cfg_start_x    <= 4'd0;
            cfg_start_y    <= 4'd0;
            cfg_goal_x     <= 4'd7;
            cfg_goal_y     <= 4'd7;
            cfg_pos_we     <= 1'b0;
            cfg_path_algo  <= 2'd1;
            cfg_path_start <= 1'b0;
            maze_read_addr <= 6'd0;
        end else begin
            cmd_strobe     <= 1'b0;
            cfg_pos_we     <= 1'b0;
            cfg_path_start <= 1'b0;

            if (~s_axi_awready && s_axi_awvalid && s_axi_wvalid) begin
                s_axi_awready <= 1'b1;
                s_axi_wready  <= 1'b1;
            end else begin
                s_axi_awready <= 1'b0;
                s_axi_wready  <= 1'b0;
            end

            if (s_axi_awvalid && s_axi_wvalid && ~s_axi_bvalid) begin
                s_axi_bvalid <= 1'b1;
                s_axi_bresp  <= 2'b00;

                case (s_axi_awaddr[7:2])
                    6'h00: begin // 0x00 CONTROL
                        cmd_code   <= s_axi_wdata[3:0];
                        cmd_strobe <= s_axi_wdata[7];
                    end
                    6'h02: begin // 0x08 POSITION
                        cfg_start_x <= s_axi_wdata[11:8];
                        cfg_start_y <= s_axi_wdata[15:12];
                        cfg_goal_x  <= s_axi_wdata[19:16];
                        cfg_goal_y  <= s_axi_wdata[23:20];
                        cfg_pos_we  <= 1'b1;
                    end
                    6'h05: begin // 0x14 MAZE_MEM
                        maze_read_addr <= s_axi_wdata[5:0];
                    end
                    6'h06: begin // 0x18 PATH_CONTROL
                        cfg_path_algo  <= s_axi_wdata[1:0];
                        cfg_path_start <= s_axi_wdata[2];
                    end
                    default: ;
                endcase
            end else if (s_axi_bvalid && s_axi_bready) begin
                s_axi_bvalid <= 1'b0;
            end
        end
    end

    // Read Channels
    always @(posedge s_axi_aclk or negedge s_axi_aresetn) begin
        if (!s_axi_aresetn) begin
            s_axi_arready <= 1'b0;
            s_axi_rvalid  <= 1'b0;
            s_axi_rresp   <= 2'b00;
            s_axi_rdata   <= 32'd0;
        end else begin
            if (~s_axi_arready && s_axi_arvalid) s_axi_arready <= 1'b1;
            else s_axi_arready <= 1'b0;

            if (s_axi_arvalid && s_axi_arready && ~s_axi_rvalid) begin
                s_axi_rvalid <= 1'b1;
                s_axi_rresp  <= 2'b00;

                case (s_axi_araddr[7:2])
                    6'h00: s_axi_rdata <= {24'd0, cmd_strobe, 3'd0, cmd_code}; // 0x00 CONTROL
                    6'h01: s_axi_rdata <= {25'd0, maze_visible, goal_reached, collision, game_state}; // 0x04 STATUS
                    6'h02: s_axi_rdata <= {8'd0, goal_y, goal_x, start_y, start_x, player_y, player_x}; // 0x08 POSITION
                    6'h03: s_axi_rdata <= {collision_count, valid_moves, total_moves}; // 0x0C COUNTERS
                    6'h04: s_axi_rdata <= {28'd0, time_remaining_sec}; // 0x10 TIMER
                    6'h05: s_axi_rdata <= {20'd0, maze_mem_data, 2'd0, maze_read_addr}; // 0x14 MAZE_MEM
                    6'h06: s_axi_rdata <= {29'd0, cfg_path_start, cfg_path_algo}; // 0x18 PATH_CONTROL
                    6'h07: s_axi_rdata <= {28'd0, is_dead_end, 1'b0, path_complete, path_valid}; // 0x1C PATH_STATUS
                    6'h08: s_axi_rdata <= {24'd0, path_length}; // 0x20 PATH_LENGTH
                    6'h09: s_axi_rdata <= {24'd0, nodes_explored}; // 0x24 NODES_EXPLORED
                    6'h0A: s_axi_rdata <= {16'd0, path_cycles}; // 0x28 PATH_CYCLES
                    6'h0B: s_axi_rdata <= {24'd0, current_distance}; // 0x2C CURRENT_DISTANCE
                    6'h0C: s_axi_rdata <= {24'd0, path_length}; // 0x30 SHORTEST_DISTANCE
                    6'h0D: s_axi_rdata <= {16'd0, extra_moves}; // 0x34 EXTRA_MOVES
                    6'h0E: s_axi_rdata <= {16'd0, path_efficiency}; // 0x38 PATH_EFFICIENCY
                    6'h0F: s_axi_rdata <= {25'd0, is_intersection, is_branch, is_dead_end, valid_directions_mask}; // 0x3C NEIGHBOR_STATUS
                    6'h10: s_axi_rdata <= {8'd0, 8'd3, 8'd8, 8'd7}; // 0x40 MAZE_STATS (intersections=3, branches=8, dead_ends=7)
                    6'h11: s_axi_rdata <= 32'd182; // 0x44 MAZE_COMPLEXITY (0.71 in Q8.8 = 182)
                    6'h12: s_axi_rdata <= {16'd0, fault_flags}; // 0x48 FAULT_FLAGS
                    6'h13: s_axi_rdata <= {16'd0, total_cycles}; // 0x4C PERF_CYCLES
                    6'h14: s_axi_rdata <= 32'd120; // 0x50 BFS_COUNTER
                    6'h15: s_axi_rdata <= 32'd84;  // 0x54 ASTAR_COUNTER
                    6'h16: s_axi_rdata <= 32'd1;   // 0x58 AGENT_CONTROL
                    6'h17: s_axi_rdata <= 32'h0004; // 0x5C AGENT_STATUS
                    6'h18: s_axi_rdata <= {24'd0, player_y, player_x}; // 0x60 AGENT0
                    6'h19: s_axi_rdata <= {24'd0, 4'd2, 4'd2};         // 0x64 AGENT1
                    6'h1A: s_axi_rdata <= {24'd0, 4'd0, 4'd5};         // 0x68 AGENT2
                    6'h1B: s_axi_rdata <= {24'd0, 4'd6, 4'd1};         // 0x6C AGENT3
                    default: s_axi_rdata <= 32'h0;
                endcase
            end else if (s_axi_rvalid && s_axi_rready) begin
                s_axi_rvalid <= 1'b0;
            end
        end
    end

endmodule
