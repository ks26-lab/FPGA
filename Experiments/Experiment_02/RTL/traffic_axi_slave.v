// ============================================================================
// File: traffic_axi_slave.v
// Module: traffic_axi_slave
// Project: Zynq Z7010 FPGA Smart City Traffic Grid
// Description:
//   AXI4-Lite Slave Interface bridging ARM Processing System (PS) to
//   the parallel traffic_core in PL. Implements 256-byte aperture (0x00 to 0x7C).
// ============================================================================

`timescale 1ns / 1ps

module traffic_axi_slave #(
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
    output reg                               cmd_step,
    output reg                               cmd_reset,
    output reg                               cmd_override_en,
    output reg                               cmd_override_phase,
    output reg                               cmd_auto,
    output reg                               cmd_emg,
    output reg  [1:0]                        cmd_emg_dir,
    output reg                               cmd_ped,

    output reg  [7:0]                        cfg_intersection_id,
    output reg  [7:0]                        cfg_queue_ns,
    output reg  [7:0]                        cfg_queue_ew,
    output reg                               cfg_queue_we,
    output reg  [15:0]                       cfg_min_green_s,
    output reg  [15:0]                       cfg_max_green_s,
    output reg  [15:0]                       cfg_starvation_limit_s,

    // Telemetry from Core
    input  wire [3:0]                        phase,
    input  wire                              alert_bit,
    input  wire                              override_bit,
    input  wire [7:0]                        green_rem_s,
    input  wire [7:0]                        congestion_score,
    input  wire [7:0]                        cleared_ns,
    input  wire [7:0]                        cleared_ew,
    input  wire [31:0]                       cycle_count,

    input  wire [7:0]                        queue_north,
    input  wire [7:0]                        queue_south,
    input  wire [7:0]                        queue_east,
    input  wire [7:0]                        queue_west,
    input  wire [8:0]                        queue_ns_sum,
    input  wire [8:0]                        queue_ew_sum,
    input  wire [9:0]                        queue_total,
    input  wire [7:0]                        calc_green_ns_s,
    input  wire [7:0]                        calc_green_ew_s,
    input  wire [15:0]                       ns_wait_time_s,
    input  wire [15:0]                       ew_wait_time_s,
    input  wire [8:0]                        pred_queue_ns,
    input  wire [8:0]                        pred_queue_ew,
    input  wire [2:0]                        global_congestion_level,

    input  wire                              emergency_active,
    input  wire [1:0]                        emergency_dir,
    input  wire                              corridor_active,
    input  wire [2:0]                        curr_node,
    input  wire [2:0]                        next_node,
    input  wire [4:0]                        emg_events,
    input  wire                              ped_walk_active,
    input  wire [6:0]                        ped_time_rem,
    input  wire [7:0]                        ped_serviced_count,

    input  wire [15:0]                       fault_flags,
    input  wire [15:0]                       fault_count,
    input  wire [15:0]                       collision_events,
    input  wire [15:0]                       vehicle_occupancy_mask,
    input  wire [15:0]                       brake_required_mask,
    input  wire [31:0]                       veh_pos_north,
    input  wire [31:0]                       veh_pos_south,
    input  wire [31:0]                       veh_pos_east,
    input  wire [31:0]                       veh_pos_west,
    input  wire [31:0]                       veh_speeds,
    input  wire                              ns_starving,
    input  wire                              ew_starving
);

    always @(posedge s_axi_aclk or negedge s_axi_aresetn) begin
        if (!s_axi_aresetn) begin
            s_axi_awready          <= 1'b0;
            s_axi_wready           <= 1'b0;
            s_axi_bvalid           <= 1'b0;
            s_axi_bresp            <= 2'b00;
            cmd_step               <= 1'b0;
            cmd_reset              <= 1'b0;
            cmd_override_en        <= 1'b0;
            cmd_override_phase     <= 1'b0;
            cmd_auto               <= 1'b1;
            cmd_emg                <= 1'b0;
            cmd_emg_dir            <= 2'd0;
            cmd_ped                <= 1'b0;
            cfg_intersection_id    <= 8'd1;
            cfg_queue_ns           <= 8'd22;
            cfg_queue_ew           <= 8'd14;
            cfg_queue_we           <= 1'b0;
            cfg_min_green_s        <= 16'd10;
            cfg_max_green_s        <= 16'd45;
            cfg_starvation_limit_s <= 16'd45;
        end else begin
            cmd_step     <= 1'b0;
            cmd_reset    <= 1'b0;
            cmd_emg      <= 1'b0;
            cmd_ped      <= 1'b0;
            cfg_queue_we <= 1'b0;

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
                        cmd_step           <= s_axi_wdata[0];
                        cmd_reset          <= s_axi_wdata[1];
                        cmd_override_en    <= s_axi_wdata[2];
                        cmd_override_phase <= s_axi_wdata[3];
                        cmd_auto           <= s_axi_wdata[4];
                        cmd_emg            <= s_axi_wdata[5];
                        cmd_emg_dir        <= s_axi_wdata[7:6];
                        cmd_ped            <= s_axi_wdata[8];
                    end
                    6'h01: begin // 0x04 CONFIG
                        cfg_intersection_id <= s_axi_wdata[7:0];
                        cfg_queue_ns        <= s_axi_wdata[15:8];
                        cfg_queue_ew        <= s_axi_wdata[23:16];
                        cfg_queue_we        <= 1'b1;
                    end
                    6'h02: begin // 0x08 TIMING_CFG
                        cfg_min_green_s <= s_axi_wdata[15:0];
                        cfg_max_green_s <= s_axi_wdata[31:16];
                    end
                    6'h17: begin // 0x5C STARVATION_FLAGS
                        cfg_starvation_limit_s <= s_axi_wdata[31:16];
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
                    6'h00: s_axi_rdata <= {22'd0, cmd_ped, cmd_emg_dir, cmd_emg, cmd_auto, cmd_override_phase, cmd_override_en, 2'd0}; // CONTROL
                    6'h01: s_axi_rdata <= {8'd0, cfg_queue_ew, cfg_queue_ns, cfg_intersection_id}; // CONFIG
                    6'h02: s_axi_rdata <= {cfg_max_green_s, cfg_min_green_s}; // TIMING_CFG
                    6'h03: s_axi_rdata <= {16'h00, 2'd0, override_bit, alert_bit, phase}; // STATUS
                    6'h04: s_axi_rdata <= {cleared_ew, cleared_ns, congestion_score, green_rem_s}; // TELEMETRY
                    6'h05: s_axi_rdata <= cycle_count; // CYCLES
                    6'h06: s_axi_rdata <= {8'd0, queue_south, 8'd0, queue_north}; // 0x18
                    6'h07: s_axi_rdata <= {8'd0, queue_west, 8'd0, queue_east};   // 0x1C
                    6'h08: s_axi_rdata <= {queue_ew_sum[7:0], queue_ns_sum[7:0], 6'd0, queue_total}; // 0x20
                    6'h09: s_axi_rdata <= {8'd0, calc_green_ew_s, 8'd0, calc_green_ns_s}; // 0x24
                    6'h0A: s_axi_rdata <= {ew_wait_time_s, ns_wait_time_s}; // 0x28
                    6'h0B: s_axi_rdata <= {7'd0, pred_queue_ew, 7'd0, pred_queue_ns}; // 0x2C
                    6'h0C: s_axi_rdata <= {5'd0, global_congestion_level, congestion_score, 16'h0111}; // 0x30
                    6'h0D: s_axi_rdata <= {16'd0, 5'd0, next_node, curr_node, corridor_active, 1'b0, emergency_dir, emergency_active}; // 0x34
                    6'h0E: s_axi_rdata <= {16'd0, ped_serviced_count, 1'b0, ped_time_rem, ped_walk_active}; // 0x38
                    6'h0F: s_axi_rdata <= {16'd0, fault_flags}; // 0x3C
                    6'h10: s_axi_rdata <= {collision_events, fault_count}; // 0x40
                    6'h11: s_axi_rdata <= {brake_required_mask, vehicle_occupancy_mask}; // 0x44
                    6'h12: s_axi_rdata <= veh_pos_north; // 0x48
                    6'h13: s_axi_rdata <= veh_pos_south; // 0x4C
                    6'h14: s_axi_rdata <= veh_pos_east;  // 0x50
                    6'h15: s_axi_rdata <= veh_pos_west;  // 0x54
                    6'h16: s_axi_rdata <= veh_speeds;    // 0x58
                    6'h17: s_axi_rdata <= {cfg_starvation_limit_s, 14'd0, ew_starving, ns_starving}; // 0x5C
                    6'h18: s_axi_rdata <= cycle_count * 10;  // 0x60
                    6'h19: s_axi_rdata <= cycle_count * 10;  // 0x64
                    6'h1A: s_axi_rdata <= cycle_count * 160; // 0x68
                    6'h1B: s_axi_rdata <= cycle_count * 10;  // 0x6C
                    6'h1C: s_axi_rdata <= cycle_count;       // 0x70
                    6'h1D: s_axi_rdata <= cycle_count * 16;  // 0x74
                    6'h1E: s_axi_rdata <= 32'h04040404;      // 0x78 ADAPTIVE_WEIGHTS
                    default: s_axi_rdata <= 32'h0;
                endcase
            end else if (s_axi_rvalid && s_axi_rready) begin
                s_axi_rvalid <= 1'b0;
            end
        end
    end

endmodule
