`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_fault_detector
// Description:
//   Hardware supervisor detecting mechanical limit violations, excessive error,
//   and photovoltaic generation collapse during high daylight.
//////////////////////////////////////////////////////////////////////////////////

module solar_fault_detector (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [15:0] sun_elevation,
    input  wire [15:0] panel_azimuth,
    input  wire [15:0] panel_elevation,
    input  wire signed [15:0] az_error,
    input  wire signed [15:0] el_error,
    input  wire [15:0] estimated_power,
    output reg  [15:0] fault_flags,
    output wire        fault_active
);

    wire [15:0] abs_az = (az_error < 0) ? -az_error : az_error;
    wire [15:0] abs_el = (el_error < 0) ? -el_error : el_error;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fault_flags <= 16'd0;
        end else begin
            fault_flags[0] <= 1'b0; // Underflow checked by unsigned limits
            fault_flags[1] <= (panel_azimuth > 16'd3600);
            fault_flags[2] <= 1'b0;
            fault_flags[3] <= (panel_elevation > 16'd900);
            fault_flags[4] <= (abs_az > 16'd900) || (abs_el > 16'd450);
            fault_flags[5] <= 1'b0;
            fault_flags[6] <= 1'b0;
            fault_flags[7] <= (sun_elevation > 16'd150) && (estimated_power == 16'd0);
            fault_flags[15:8] <= 8'd0;
        end
    end

    assign fault_active = |fault_flags;

endmodule
