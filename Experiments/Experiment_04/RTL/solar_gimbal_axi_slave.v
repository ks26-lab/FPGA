`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_gimbal_axi_slave
// Description:
//   AXI4-Lite 32-register memory mapped slave interface for Solar Tracking Gimbal.
//   Base Aperture: 0x43C30000 - 0x43C300FF
//////////////////////////////////////////////////////////////////////////////////

module solar_gimbal_axi_slave #
(
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 8
)
(
    // AXI4-Lite Clock and Reset
    input  wire                                  s_axi_aclk,
    input  wire                                  s_axi_aresetn,

    // Write Address Channel
    input  wire [C_S_AXI_ADDR_WIDTH-1 : 0]       s_axi_awaddr,
    input  wire [2 : 0]                          s_axi_awprot,
    input  wire                                  s_axi_awvalid,
    output wire                                  s_axi_awready,

    // Write Data Channel
    input  wire [C_S_AXI_DATA_WIDTH-1 : 0]       s_axi_wdata,
    input  wire [(C_S_AXI_DATA_WIDTH/8)-1 : 0]   s_axi_wstrb,
    input  wire                                  s_axi_wvalid,
    output wire                                  s_axi_wready,

    // Write Response Channel
    output wire [1 : 0]                          s_axi_bresp,
    output wire                                  s_axi_bvalid,
    input  wire                                  s_axi_bready,

    // Read Address Channel
    input  wire [C_S_AXI_ADDR_WIDTH-1 : 0]       s_axi_araddr,
    input  wire [2 : 0]                          s_axi_arprot,
    input  wire                                  s_axi_arvalid,
    output wire                                  s_axi_arready,

    // Read Data Channel
    output wire [C_S_AXI_DATA_WIDTH-1 : 0]       s_axi_rdata,
    output wire [1 : 0]                          s_axi_rresp,
    output wire                                  s_axi_rvalid,
    input  wire                                  s_axi_rready,

    // Direct interface to core
    output reg  [31:0]                           control_reg,
    output reg  [31:0]                           sun_pos_reg,
    output reg                                   sun_pos_we,
    output reg  [31:0]                           panel_pos_reg,
    output reg                                   panel_pos_we,
    output reg  [31:0]                           limits_reg,
    output reg                                   limits_we,

    // Telemetry from core
    input  wire [31:0]                           sun_pos_in,
    input  wire [31:0]                           panel_pos_in,
    input  wire [31:0]                           status_in,
    input  wire [31:0]                           error_in,
    input  wire [31:0]                           actuators_in,
    input  wire [31:0]                           cycles_in,
    input  wire signed [31:0]                    sun_vec_x,
    input  wire signed [31:0]                    sun_vec_y,
    input  wire signed [31:0]                    sun_vec_z,
    input  wire signed [31:0]                    panel_norm_x,
    input  wire signed [31:0]                    panel_norm_y,
    input  wire signed [31:0]                    panel_norm_z,
    input  wire signed [31:0]                    dot_product,
    input  wire [31:0]                           incident_angle_in,
    input  wire [31:0]                           estimated_power_in,
    input  wire [31:0]                           filtered_sun_in,
    input  wire [31:0]                           predicted_sun_in,
    input  wire [31:0]                           angular_velocity_in,
    input  wire [31:0]                           limits_in,
    input  wire [15:0]                           fault_flags_in,
    input  wire [31:0]                           vector_cycles_in,
    input  wire [31:0]                           update_counter_in,
    input  wire [31:0]                           panel0_data_in,
    input  wire [31:0]                           panel1_data_in,
    input  wire [31:0]                           panel2_data_in,
    input  wire [31:0]                           panel3_data_in,
    input  wire [31:0]                           total_array_power_in,
    input  wire [31:0]                           panels_active_mask_in,
    input  wire [31:0]                           tracking_quality_in,
    input  wire [31:0]                           hardware_version_in
);

    // AXI handshake signals
    reg axi_awready;
    reg axi_wready;
    reg [1:0] axi_bresp;
    reg axi_bvalid;
    reg axi_arready;
    reg [31:0] axi_rdata;
    reg [1:0] axi_rresp;
    reg axi_rvalid;

    assign s_axi_awready = axi_awready;
    assign s_axi_wready  = axi_wready;
    assign s_axi_bresp   = axi_bresp;
    assign s_axi_bvalid  = axi_bvalid;
    assign s_axi_arready = axi_arready;
    assign s_axi_rdata   = axi_rdata;
    assign s_axi_rresp   = axi_rresp;
    assign s_axi_rvalid  = axi_rvalid;

    reg [C_S_AXI_ADDR_WIDTH-1 : 0] axi_awaddr;
    reg [C_S_AXI_ADDR_WIDTH-1 : 0] axi_araddr;

    // Write address & write handshake
    always @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            axi_awready <= 1'b0;
            axi_awaddr  <= 0;
            axi_wready  <= 1'b0;
            axi_bvalid  <= 1'b0;
            axi_bresp   <= 2'b0;
            control_reg <= 32'd0;
            sun_pos_reg <= {16'd450, 16'd1800};
            sun_pos_we  <= 1'b0;
            panel_pos_reg <= 32'd0;
            panel_pos_we  <= 1'b0;
            limits_reg  <= {16'd5, 16'd5};
            limits_we   <= 1'b0;
        end else begin
            sun_pos_we   <= 1'b0;
            panel_pos_we <= 1'b0;
            limits_we    <= 1'b0;

            if (~axi_awready && s_axi_awvalid && s_axi_wvalid) begin
                axi_awready <= 1'b1;
                axi_awaddr  <= s_axi_awaddr;
                axi_wready  <= 1'b1;
            end else begin
                axi_awready <= 1'b0;
                axi_wready  <= 1'b0;
            end

            // Write register decode
            if (axi_wready && s_axi_wvalid && axi_awready && s_axi_awvalid) begin
                case (s_axi_awaddr[7:2])
                    6'h00: control_reg   <= s_axi_wdata;
                    6'h01: begin
                        sun_pos_reg <= s_axi_wdata;
                        sun_pos_we  <= 1'b1;
                    end
                    6'h02: begin
                        panel_pos_reg <= s_axi_wdata;
                        panel_pos_we  <= 1'b1;
                    end
                    6'h13: begin
                        limits_reg  <= s_axi_wdata;
                        limits_we   <= 1'b1;
                    end
                    default: ;
                endcase
            end

            // Write response
            if (axi_awready && s_axi_awvalid && ~axi_bvalid && axi_wready && s_axi_wvalid) begin
                axi_bvalid <= 1'b1;
                axi_bresp  <= 2'b0;
            end else if (s_axi_bready && axi_bvalid) begin
                axi_bvalid <= 1'b0;
            end
        end
    end

    // Read channel handshake
    always @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            axi_arready <= 1'b0;
            axi_araddr  <= 0;
            axi_rvalid  <= 1'b0;
            axi_rresp   <= 2'b0;
            axi_rdata   <= 32'd0;
        end else begin
            if (~axi_arready && s_axi_arvalid) begin
                axi_arready <= 1'b1;
                axi_araddr  <= s_axi_araddr;
            end else begin
                axi_arready <= 1'b0;
            end

            if (axi_arready && s_axi_arvalid && ~axi_rvalid) begin
                axi_rvalid <= 1'b1;
                axi_rresp  <= 2'b0;

                case (s_axi_araddr[7:2])
                    6'h00: axi_rdata <= control_reg;
                    6'h01: axi_rdata <= sun_pos_in;
                    6'h02: axi_rdata <= panel_pos_in;
                    6'h03: axi_rdata <= status_in;
                    6'h04: axi_rdata <= error_in;
                    6'h05: axi_rdata <= actuators_in;
                    6'h06: axi_rdata <= cycles_in;
                    6'h07: axi_rdata <= sun_vec_x;
                    6'h08: axi_rdata <= sun_vec_y;
                    6'h09: axi_rdata <= sun_vec_z;
                    6'h0A: axi_rdata <= panel_norm_x;
                    6'h0B: axi_rdata <= panel_norm_y;
                    6'h0C: axi_rdata <= panel_norm_z;
                    6'h0D: axi_rdata <= dot_product;
                    6'h0E: axi_rdata <= incident_angle_in;
                    6'h0F: axi_rdata <= estimated_power_in;
                    6'h10: axi_rdata <= filtered_sun_in;
                    6'h11: axi_rdata <= predicted_sun_in;
                    6'h12: axi_rdata <= angular_velocity_in;
                    6'h13: axi_rdata <= limits_in;
                    6'h14: axi_rdata <= {16'd0, fault_flags_in};
                    6'h15: axi_rdata <= vector_cycles_in;
                    6'h16: axi_rdata <= update_counter_in;
                    6'h17: axi_rdata <= panel0_data_in;
                    6'h18: axi_rdata <= panel1_data_in;
                    6'h19: axi_rdata <= panel2_data_in;
                    6'h1A: axi_rdata <= panel3_data_in;
                    6'h1B: axi_rdata <= total_array_power_in;
                    6'h1C: axi_rdata <= panels_active_mask_in;
                    6'h1D: axi_rdata <= tracking_quality_in;
                    6'h1E: axi_rdata <= hardware_version_in;
                    default: axi_rdata <= 32'd0;
                endcase
            end else if (axi_rvalid && s_axi_rready) begin
                axi_rvalid <= 1'b0;
            end
        end
    end

endmodule
