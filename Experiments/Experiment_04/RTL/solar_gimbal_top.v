`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_gimbal_top
// Description:
//   Top-level integration wrapper for Solar Tracking Gimbal on EDGE Zynq Z7010.
//   Binds AXI4-Lite memory mapped interface to mathematical acceleration core,
//   with board diagnostic LEDs and motor control PMOD interfaces.
//////////////////////////////////////////////////////////////////////////////////

module solar_gimbal_top #
(
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 8
)
(
    // Physical Board Clocks & Resets
    input  wire                                  clk,
    input  wire                                  rst_n,

    // Board Diagnostic LEDs
    output wire [3:0]                            led,

    // Stepper Motor Actuator Signals (PMOD)
    output wire                                  step_az_pin,
    output wire                                  dir_az_pin,
    output wire                                  step_el_pin,
    output wire                                  dir_el_pin,

    // AXI4-Lite Slave Interface
    input  wire                                  s_axi_aclk,
    input  wire                                  s_axi_aresetn,
    input  wire [C_S_AXI_ADDR_WIDTH-1 : 0]       s_axi_awaddr,
    input  wire [2 : 0]                          s_axi_awprot,
    input  wire                                  s_axi_awvalid,
    output wire                                  s_axi_awready,
    input  wire [C_S_AXI_DATA_WIDTH-1 : 0]       s_axi_wdata,
    input  wire [(C_S_AXI_DATA_WIDTH/8)-1 : 0]   s_axi_wstrb,
    input  wire                                  s_axi_wvalid,
    output wire                                  s_axi_wready,
    output wire [1 : 0]                          s_axi_bresp,
    output wire                                  s_axi_bvalid,
    input  wire                                  s_axi_bready,
    input  wire [C_S_AXI_ADDR_WIDTH-1 : 0]       s_axi_araddr,
    input  wire [2 : 0]                          s_axi_arprot,
    input  wire                                  s_axi_arvalid,
    output wire                                  s_axi_arready,
    output wire [C_S_AXI_DATA_WIDTH-1 : 0]       s_axi_rdata,
    output wire [1 : 0]                          s_axi_rresp,
    output wire                                  s_axi_rvalid,
    input  wire                                  s_axi_rready
);

    // Core interconnect wires
    wire [31:0] control_reg;
    wire [31:0] sun_pos_reg;
    wire        sun_pos_we;
    wire [31:0] panel_pos_reg;
    wire        panel_pos_we;
    wire [31:0] limits_reg;
    wire        limits_we;

    wire [31:0] sun_pos_out;
    wire [31:0] panel_pos_out;
    wire [31:0] status_out;
    wire [31:0] error_out;
    wire [31:0] actuators_out;
    wire [31:0] cycles_out;
    wire signed [31:0] sun_vec_x;
    wire signed [31:0] sun_vec_y;
    wire signed [31:0] sun_vec_z;
    wire signed [31:0] panel_norm_x;
    wire signed [31:0] panel_norm_y;
    wire signed [31:0] panel_norm_z;
    wire signed [31:0] dot_product;
    wire [31:0] incident_angle_out;
    wire [31:0] estimated_power_out;
    wire [31:0] filtered_sun_out;
    wire [31:0] predicted_sun_out;
    wire [31:0] angular_velocity_out;
    wire [31:0] limits_out;
    wire [15:0] fault_flags_out;
    wire [31:0] vector_cycles_out;
    wire [31:0] update_counter_out;
    wire [31:0] panel0_data_out;
    wire [31:0] panel1_data_out;
    wire [31:0] panel2_data_out;
    wire [31:0] panel3_data_out;
    wire [31:0] total_array_power_out;
    wire [31:0] panels_active_mask_out;
    wire [31:0] tracking_quality_out;
    wire [31:0] hardware_version_out;

    // Master Core
    solar_gimbal_core u_core (
        .clk(s_axi_aclk),
        .rst_n(s_axi_aresetn),
        .control_reg(control_reg),
        .sun_pos_in(sun_pos_reg),
        .sun_pos_we(sun_pos_we),
        .panel_pos_in(panel_pos_reg),
        .panel_pos_we(panel_pos_we),
        .limits_in(limits_reg),
        .limits_we(limits_we),
        .sun_pos_out(sun_pos_out),
        .panel_pos_out(panel_pos_out),
        .status_out(status_out),
        .error_out(error_out),
        .actuators_out(actuators_out),
        .cycles_out(cycles_out),
        .sun_vec_x(sun_vec_x),
        .sun_vec_y(sun_vec_y),
        .sun_vec_z(sun_vec_z),
        .panel_norm_x(panel_norm_x),
        .panel_norm_y(panel_norm_y),
        .panel_norm_z(panel_norm_z),
        .dot_product(dot_product),
        .incident_angle_out(incident_angle_out),
        .estimated_power_out(estimated_power_out),
        .filtered_sun_out(filtered_sun_out),
        .predicted_sun_out(predicted_sun_out),
        .angular_velocity_out(angular_velocity_out),
        .limits_out(limits_out),
        .fault_flags_out(fault_flags_out),
        .vector_cycles_out(vector_cycles_out),
        .update_counter_out(update_counter_out),
        .panel0_data_out(panel0_data_out),
        .panel1_data_out(panel1_data_out),
        .panel2_data_out(panel2_data_out),
        .panel3_data_out(panel3_data_out),
        .total_array_power_out(total_array_power_out),
        .panels_active_mask_out(panels_active_mask_out),
        .tracking_quality_out(tracking_quality_out),
        .hardware_version_out(hardware_version_out)
    );

    // AXI Slave
    solar_gimbal_axi_slave #(
        .C_S_AXI_DATA_WIDTH(C_S_AXI_DATA_WIDTH),
        .C_S_AXI_ADDR_WIDTH(C_S_AXI_ADDR_WIDTH)
    ) u_axi_slave (
        .s_axi_aclk(s_axi_aclk),
        .s_axi_aresetn(s_axi_aresetn),
        .s_axi_awaddr(s_axi_awaddr),
        .s_axi_awprot(s_axi_awprot),
        .s_axi_awvalid(s_axi_awvalid),
        .s_axi_awready(s_axi_awready),
        .s_axi_wdata(s_axi_wdata),
        .s_axi_wstrb(s_axi_wstrb),
        .s_axi_wvalid(s_axi_wvalid),
        .s_axi_wready(s_axi_wready),
        .s_axi_bresp(s_axi_bresp),
        .s_axi_bvalid(s_axi_bvalid),
        .s_axi_bready(s_axi_bready),
        .s_axi_araddr(s_axi_araddr),
        .s_axi_arprot(s_axi_arprot),
        .s_axi_arvalid(s_axi_arvalid),
        .s_axi_arready(s_axi_arready),
        .s_axi_rdata(s_axi_rdata),
        .s_axi_rresp(s_axi_rresp),
        .s_axi_rvalid(s_axi_rvalid),
        .s_axi_rready(s_axi_rready),
        .control_reg(control_reg),
        .sun_pos_reg(sun_pos_reg),
        .sun_pos_we(sun_pos_we),
        .panel_pos_reg(panel_pos_reg),
        .panel_pos_we(panel_pos_we),
        .limits_reg(limits_reg),
        .limits_we(limits_we),
        .sun_pos_in(sun_pos_out),
        .panel_pos_in(panel_pos_out),
        .status_in(status_out),
        .error_in(error_out),
        .actuators_in(actuators_in),
        .cycles_in(cycles_out),
        .sun_vec_x(sun_vec_x),
        .sun_vec_y(sun_vec_y),
        .sun_vec_z(sun_vec_z),
        .panel_norm_x(panel_norm_x),
        .panel_norm_y(panel_norm_y),
        .panel_norm_z(panel_norm_z),
        .dot_product(dot_product),
        .incident_angle_in(incident_angle_out),
        .estimated_power_in(estimated_power_out),
        .filtered_sun_in(filtered_sun_out),
        .predicted_sun_in(predicted_sun_out),
        .angular_velocity_in(angular_velocity_out),
        .limits_in(limits_out),
        .fault_flags_in(fault_flags_out),
        .vector_cycles_in(vector_cycles_out),
        .update_counter_in(update_counter_out),
        .panel0_data_in(panel0_data_out),
        .panel1_data_in(panel1_data_out),
        .panel2_data_in(panel2_data_out),
        .panel3_data_in(panel3_data_out),
        .total_array_power_in(total_array_power_out),
        .panels_active_mask_in(panels_active_mask_out),
        .tracking_quality_in(tracking_quality_out),
        .hardware_version_in(hardware_version_out)
    );

    // Board Diagnostics
    assign led[0] = status_out[4]; // Locked
    assign led[1] = (status_out[3:0] == 4'd3); // Slewing
    assign led[2] = |fault_flags_out; // Fault
    assign led[3] = cycles_out[24]; // Heartbeat

    // Motor outputs
    assign step_az_pin = actuators_out[0];
    assign dir_az_pin  = status_out[5];
    assign step_el_pin = actuators_out[16];
    assign dir_el_pin  = status_out[6];

endmodule
