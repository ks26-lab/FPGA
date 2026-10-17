`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_vector_engine
// Description:
//   Computes 3D spherical-to-Cartesian unit vectors for Sun (S) and Panel Normal (N)
//   Sx = cos(Es) * cos(As), Sy = cos(Es) * sin(As), Sz = sin(Es)
//   Nx = cos(Ep) * cos(Ap), Ny = cos(Ep) * sin(Ap), Nz = sin(Ep)
//   Format: Signed Q16.16 fixed-point
//////////////////////////////////////////////////////////////////////////////////

module solar_vector_engine (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [15:0] sun_azimuth,     // 0.1 deg
    input  wire [15:0] sun_elevation,   // 0.1 deg
    input  wire [15:0] panel_azimuth,   // 0.1 deg
    input  wire [15:0] panel_elevation, // 0.1 deg
    output reg  signed [31:0] sun_vec_x,
    output reg  signed [31:0] sun_vec_y,
    output reg  signed [31:0] sun_vec_z,
    output reg  signed [31:0] panel_norm_x,
    output reg  signed [31:0] panel_norm_y,
    output reg  signed [31:0] panel_norm_z,
    output reg         done
);

    // Trig table outputs
    wire signed [31:0] sin_s_az, cos_s_az;
    wire signed [31:0] sin_s_el, cos_s_el;
    wire signed [31:0] sin_p_az, cos_p_az;
    wire signed [31:0] sin_p_el, cos_p_el;

    solar_trig_table u_trig_s_az (.clk(clk), .rst_n(rst_n), .angle_tenths(sun_azimuth),     .sin_q16(sin_s_az), .cos_q16(cos_s_az));
    solar_trig_table u_trig_s_el (.clk(clk), .rst_n(rst_n), .angle_tenths(sun_elevation),   .sin_q16(sin_s_el), .cos_q16(cos_s_el));
    solar_trig_table u_trig_p_az (.clk(clk), .rst_n(rst_n), .angle_tenths(panel_azimuth),   .sin_q16(sin_p_az), .cos_q16(cos_p_az));
    solar_trig_table u_trig_p_el (.clk(clk), .rst_n(rst_n), .angle_tenths(panel_elevation), .sin_q16(sin_p_el), .cos_q16(cos_p_el));

    // Pipeline registers
    reg [2:0] pipe_valid;

    // Multiplication in Q16.16: (A * B) >>> 16
    wire signed [63:0] prod_sx = cos_s_el * cos_s_az;
    wire signed [63:0] prod_sy = cos_s_el * sin_s_az;
    wire signed [63:0] prod_nx = cos_p_el * cos_p_az;
    wire signed [63:0] prod_ny = cos_p_el * sin_p_az;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipe_valid   <= 3'b0;
            sun_vec_x    <= 32'sd65536;
            sun_vec_y    <= 32'sd0;
            sun_vec_z    <= 32'sd0;
            panel_norm_x <= 32'sd65536;
            panel_norm_y <= 32'sd0;
            panel_norm_z <= 32'sd0;
            done         <= 1'b0;
        end else begin
            pipe_valid <= {pipe_valid[1:0], start};

            if (pipe_valid[1]) begin
                // Stage 2: Register calculated unit vectors
                sun_vec_x    <= prod_sx[47:16];
                sun_vec_y    <= prod_sy[47:16];
                sun_vec_z    <= sin_s_el;
                panel_norm_x <= prod_nx[47:16];
                panel_norm_y <= prod_ny[47:16];
                panel_norm_z <= sin_p_el;
            end

            done <= pipe_valid[2];
        end
    end

endmodule
