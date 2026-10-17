// ============================================================================
// File: underwater_probe_axi_slave.v
// Module: underwater_probe_axi_slave
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem (Upgraded Map)
// Description:
//   AXI4-Lite Slave Interface bridging ARM Processing System (PS) to
//   the parallel underwater_probe_core in PL.
//
// Register Map (64KB Aperture at 0x43C00000):
//   0x00: CONTROL            [W]   Bit 0: start, Bit 1: stop, Bit 2: reset, Bit 3: disturb_strobe,
//                                  Bits [5:4]: disturb_type (1=FISH, 2=GARBAGE, 3=WHALE), Bit 6: set_depth_we
//   0x04: DEPTH_CFG          [R/W] Bits [15:0]: set_depth (x10), Bits [31:16]: target_depth (x10)
//   0x08: CURRENT            [R/W] Bits [7:0]: current_strength (signed % -100 to +100)
//   0x0C: STATUS             [R]   Bits [3:0]: probe_state, Bit 4: collision, Bit 5: recovery,
//                                  Bit 6: target_reached, Bits [8:7]: active_object
//   0x10: CURRENT_DEPTH      [R]   Bits [15:0]: current_depth (0.1m)
//   0x14: TARGET_DEPTH       [R]   Bits [15:0]: target_depth (0.1m)
//   0x18: VELOCITY           [R]   Bits [7:0]: probe_velocity_z (signed 0.1 m/s)
//   0x1C: DEPTH_ERROR        [R]   Bits [15:0]: signed depth error (0.1m)
//   0x20: FILTERED_DEPTH     [R]   Bits [15:0]: MAF filtered depth (0.1m)
//   0x24: FILTERED_VELOCITY  [R]   Bits [7:0]: EMA filtered velocity (signed 0.1 m/s)
//   0x28: DRAG_FORCE         [R]   Bits [15:0]: Hydrodynamic drag force (signed 0.1 N)
//   0x2C: RELATIVE_VELOCITY  [R]   Bits [15:0]: Relative water velocity (signed 0.1 m/s)
//   0x30: P_TERM             [R]   Bits [15:0]: Proportional term
//   0x34: I_TERM             [R]   Bits [15:0]: Integral term
//   0x38: D_TERM             [R]   Bits [15:0]: Derivative term
//   0x3C: CONTROL_OUTPUT     [R]   Bits [15:0]: Combined PID output
//   0x40: THRUST_COMMAND     [R]   Bits [15:0]: Bounded thrust (0.1 N)
//   0x44: THRUST_DELTA       [R]   Bits [15:0]: Thrust rate of change (0.1 N/tick)
//   0x48: IMPACT_ENERGY      [R]   Bits [15:0]: Collision kinetic energy (Joules)
//   0x4C: IMPACT_SEVERITY    [R]   Bits [2:0]: Severity (0=NONE, 1=LOW, 2=MED, 3=HIGH, 4=CRIT)
//   0x50: RECOVERY_THRUST    [R]   Bits [15:0]: Recovery force (0.1 N)
//   0x54: POST_COL_VELOCITY  [R]   Bits [7:0]: Pre/post impact velocity (signed 0.1 m/s)
//   0x58: PREDICTED_DEPTH_1  [R]   Bits [15:0]: Projected depth at T+1 (0.1m)
//   0x5C: PREDICTED_DEPTH_3  [R]   Bits [15:0]: Projected depth at T+3 (0.1m)
//   0x60: PREDICTED_DEPTH_5  [R]   Bits [15:0]: Projected depth at T+5 (0.1m)
//   0x64: CONTROL_COST       [R]   Bits [15:0]: Optimizer cost metric
//   0x68: OPTIMIZATION_ACT   [R]   Bits [1:0]: 0=HOLD, 1=INCREASE, 2=DECREASE
//   0x6C: FAULT_FLAGS        [R]   Bits [7:0]: Anomaly/fault register
//   0x70: SIMULATION_CYCLES  [R]   Bits [31:0]: Clock cycle counter
//   0x74: PHYSICS_UPDATES    [R]   Bits [31:0]: Physics update ticks
//   0x78: COLLISION_COUNT    [R]   Bits [15:0]: Cumulative impact count
//   0x7C: RECOVERY_COUNT     [R]   Bits [15:0]: Cumulative recovery count
// ============================================================================

`timescale 1ns / 1ps

module underwater_probe_axi_slave #(
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

    // Interface to underwater_probe_core
    output reg                               cmd_start,
    output reg                               cmd_stop,
    output reg                               cmd_reset,
    output reg                               cmd_disturb_strobe,
    output reg  [1:0]                        cmd_disturb_type,
    output reg                               cfg_set_depth_we,
    output reg  signed [15:0]                cfg_set_depth,
    output reg  signed [15:0]                cfg_target_depth,
    output reg  signed [7:0]                 cfg_current_strength,

    // Core Telemetry Inputs
    input  wire [3:0]                        probe_state,
    input  wire signed [15:0]                current_depth,
    input  wire signed [15:0]                target_depth,
    input  wire signed [7:0]                 displacement_x,
    input  wire signed [7:0]                 probe_velocity_z,
    input  wire                              collision_detected,
    input  wire                              recovery_active,
    input  wire                              target_reached,
    input  wire [1:0]                        active_object_type,
    input  wire [15:0]                       collision_counter,
    input  wire [31:0]                       sim_cycle_counter,

    input  wire signed [15:0]                depth_error,
    input  wire signed [15:0]                filtered_depth,
    input  wire signed [7:0]                 filtered_velocity,
    input  wire signed [15:0]                drag_force,
    input  wire signed [15:0]                relative_velocity,
    input  wire signed [15:0]                p_term,
    input  wire signed [15:0]                i_term,
    input  wire signed [15:0]                d_term,
    input  wire signed [15:0]                control_output,
    input  wire signed [15:0]                thrust_command,
    input  wire signed [15:0]                thrust_delta,
    input  wire [15:0]                       impact_energy,
    input  wire [2:0]                        impact_severity,
    input  wire signed [15:0]                recovery_thrust,
    input  wire signed [7:0]                 post_collision_velocity,
    input  wire signed [15:0]                predicted_depth_1,
    input  wire signed [15:0]                predicted_depth_3,
    input  wire signed [15:0]                predicted_depth_5,
    input  wire [15:0]                       control_cost,
    input  wire [1:0]                        optimization_action,
    input  wire [7:0]                        fault_flags,
    input  wire [31:0]                       physics_update_count,
    input  wire [15:0]                       recovery_counter
);

    // ------------------------------------------------------------------------
    // Write Handling
    // ------------------------------------------------------------------------
    always @(posedge s_axi_aclk or negedge s_axi_aresetn) begin
        if (!s_axi_aresetn) begin
            s_axi_awready        <= 1'b0;
            s_axi_wready         <= 1'b0;
            s_axi_bvalid         <= 1'b0;
            s_axi_bresp          <= 2'b00;
            cmd_start            <= 1'b0;
            cmd_stop             <= 1'b0;
            cmd_reset            <= 1'b0;
            cmd_disturb_strobe   <= 1'b0;
            cmd_disturb_type     <= 2'd0;
            cfg_set_depth_we     <= 1'b0;
            cfg_set_depth        <= 16'sd500; // 50.0m
            cfg_target_depth     <= 16'sd800; // 80.0m
            cfg_current_strength <= 8'sd20;   // +20%
        end else begin
            cmd_start          <= 1'b0;
            cmd_stop           <= 1'b0;
            cmd_reset          <= 1'b0;
            cmd_disturb_strobe <= 1'b0;
            cfg_set_depth_we   <= 1'b0;

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
                        cmd_start          <= s_axi_wdata[0];
                        cmd_stop           <= s_axi_wdata[1];
                        cmd_reset          <= s_axi_wdata[2];
                        cmd_disturb_strobe <= s_axi_wdata[3];
                        cmd_disturb_type   <= s_axi_wdata[5:4];
                        cfg_set_depth_we   <= s_axi_wdata[6];
                    end
                    6'h01: begin // 0x04 DEPTH_CFG
                        cfg_set_depth    <= s_axi_wdata[15:0];
                        cfg_target_depth <= s_axi_wdata[31:16];
                    end
                    6'h02: begin // 0x08 CURRENT
                        cfg_current_strength <= s_axi_wdata[7:0];
                    end
                    default: ;
                endcase
            end else if (s_axi_bvalid && s_axi_bready) begin
                s_axi_bvalid <= 1'b0;
            end
        end
    end

    // ------------------------------------------------------------------------
    // Read Handling (Complete Telemetry Map)
    // ------------------------------------------------------------------------
    always @(posedge s_axi_aclk or negedge s_axi_aresetn) begin
        if (!s_axi_aresetn) begin
            s_axi_arready <= 1'b0;
            s_axi_rvalid  <= 1'b0;
            s_axi_rresp   <= 2'b00;
            s_axi_rdata   <= 32'd0;
        end else begin
            if (~s_axi_arready && s_axi_arvalid) begin
                s_axi_arready <= 1'b1;
            end else begin
                s_axi_arready <= 1'b0;
            end

            if (s_axi_arvalid && s_axi_arready && ~s_axi_rvalid) begin
                s_axi_rvalid <= 1'b1;
                s_axi_rresp  <= 2'b00;

                case (s_axi_araddr[7:2])
                    6'h00: s_axi_rdata <= 32'd0; // CONTROL
                    6'h01: s_axi_rdata <= {cfg_target_depth, cfg_set_depth}; // DEPTH_CFG
                    6'h02: s_axi_rdata <= {24'd0, cfg_current_strength};     // CURRENT
                    6'h03: s_axi_rdata <= {23'd0, active_object_type, target_reached, recovery_active, collision_detected, probe_state}; // STATUS
                    6'h04: s_axi_rdata <= {{16{current_depth[15]}}, current_depth};         // 0x10 CURRENT_DEPTH
                    6'h05: s_axi_rdata <= {{16{target_depth[15]}}, target_depth};           // 0x14 TARGET_DEPTH
                    6'h06: s_axi_rdata <= {{24{probe_velocity_z[7]}}, probe_velocity_z};     // 0x18 VELOCITY
                    6'h07: s_axi_rdata <= {{16{depth_error[15]}}, depth_error};             // 0x1C DEPTH_ERROR
                    6'h08: s_axi_rdata <= {{16{filtered_depth[15]}}, filtered_depth};       // 0x20 FILTERED_DEPTH
                    6'h09: s_axi_rdata <= {{24{filtered_velocity[7]}}, filtered_velocity};   // 0x24 FILTERED_VELOCITY
                    6'h0A: s_axi_rdata <= {{16{drag_force[15]}}, drag_force};               // 0x28 DRAG_FORCE
                    6'h0B: s_axi_rdata <= {{16{relative_velocity[15]}}, relative_velocity}; // 0x2C RELATIVE_VELOCITY
                    6'h0C: s_axi_rdata <= {{16{p_term[15]}}, p_term};                       // 0x30 P_TERM
                    6'h0D: s_axi_rdata <= {{16{i_term[15]}}, i_term};                       // 0x34 I_TERM
                    6'h0E: s_axi_rdata <= {{16{d_term[15]}}, d_term};                       // 0x38 D_TERM
                    6'h0F: s_axi_rdata <= {{16{control_output[15]}}, control_output};       // 0x3C CONTROL_OUTPUT
                    6'h10: s_axi_rdata <= {{16{thrust_command[15]}}, thrust_command};       // 0x40 THRUST_COMMAND
                    6'h11: s_axi_rdata <= {{16{thrust_delta[15]}}, thrust_delta};           // 0x44 THRUST_DELTA
                    6'h12: s_axi_rdata <= {16'd0, impact_energy};                           // 0x48 IMPACT_ENERGY
                    6'h13: s_axi_rdata <= {29'd0, impact_severity};                         // 0x4C IMPACT_SEVERITY
                    6'h14: s_axi_rdata <= {{16{recovery_thrust[15]}}, recovery_thrust};     // 0x50 RECOVERY_THRUST
                    6'h15: s_axi_rdata <= {{24{post_collision_velocity[7]}}, post_collision_velocity}; // 0x54 POST_COL_VELOCITY
                    6'h16: s_axi_rdata <= {{16{predicted_depth_1[15]}}, predicted_depth_1}; // 0x58 PREDICTED_DEPTH_1
                    6'h17: s_axi_rdata <= {{16{predicted_depth_3[15]}}, predicted_depth_3}; // 0x5C PREDICTED_DEPTH_3
                    6'h18: s_axi_rdata <= {{16{predicted_depth_5[15]}}, predicted_depth_5}; // 0x60 PREDICTED_DEPTH_5
                    6'h19: s_axi_rdata <= {16'd0, control_cost};                            // 0x64 CONTROL_COST
                    6'h1A: s_axi_rdata <= {30'd0, optimization_action};                     // 0x68 OPTIMIZATION_ACTION
                    6'h1B: s_axi_rdata <= {24'd0, fault_flags};                             // 0x6C FAULT_FLAGS
                    6'h1C: s_axi_rdata <= sim_cycle_counter;                                // 0x70 SIMULATION_CYCLES
                    6'h1D: s_axi_rdata <= physics_update_count;                             // 0x74 PHYSICS_UPDATES
                    6'h1E: s_axi_rdata <= {16'd0, collision_counter};                       // 0x78 COLLISION_COUNT
                    6'h1F: s_axi_rdata <= {16'd0, recovery_counter};                        // 0x7C RECOVERY_COUNT
                    default: s_axi_rdata <= 32'hDEADBEEF;
                endcase
            end else if (s_axi_rvalid && s_axi_rready) begin
                s_axi_rvalid <= 1'b0;
            end
        end
    end

endmodule
