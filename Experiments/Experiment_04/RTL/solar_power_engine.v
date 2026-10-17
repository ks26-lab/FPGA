`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_power_engine
// Description:
//   Photovoltaic generation engine for single panel and 4-channel concurrent array.
//   Peak generation: 5665 Watts at normal incidence (dot = 1.0).
//////////////////////////////////////////////////////////////////////////////////

module solar_power_engine (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire signed [31:0] dot_product,     // Q16.16 signed
    input  wire [15:0]        incident_angle,  // 0.1 deg
    output reg  [15:0]        estimated_power, // Watts
    output reg  [31:0]        panel0_data,     // [31:16] theta0, [15:0] P0
    output reg  [31:0]        panel1_data,     // [31:16] theta1, [15:0] P1
    output reg  [31:0]        panel2_data,     // [31:16] theta2, [15:0] P2
    output reg  [31:0]        panel3_data,     // [31:16] theta3, [15:0] P3
    output reg  [31:0]        total_array_power, // Watts
    output reg  [31:0]        tracking_quality,  // [31:16] quality %, [15:0] loss W
    output reg                done
);

    reg [1:0] pipe_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipe_valid        <= 2'b0;
            estimated_power   <= 16'd5665;
            panel0_data       <= 32'd0;
            panel1_data       <= 32'd0;
            panel2_data       <= 32'd0;
            panel3_data       <= 32'd0;
            total_array_power <= 32'd22660;
            tracking_quality  <= {16'd100, 16'd0};
            done              <= 1'b0;
        end else begin
            pipe_valid <= {pipe_valid[0], start};

            if (pipe_valid[0]) begin
                reg [31:0] p0;
                reg [31:0] p1;
                reg [31:0] p2;
                reg [31:0] p3;
                reg [15:0] th1;
                reg [15:0] th2;
                reg [15:0] th3;
                reg [31:0] p_loss;
                reg [15:0] qual;

                if (dot_product <= 32'sd0) begin
                    p0 = 32'd0;
                    p1 = 32'd0;
                    p2 = 32'd0;
                    p3 = 32'd0;
                    p_loss = 32'd5665;
                    qual = 16'd0;
                end else begin
                    // p0 = (5665 * dot_product) >>> 16
                    wire [47:0] p_prod = 32'd5665 * dot_product[31:0];
                    p0 = p_prod[31:16];
                    p1 = (p0 * 32'd98) / 100;
                    p2 = (p0 * 32'd95) / 100;
                    p3 = (p0 * 32'd92) / 100;

                    p_loss = (p0 < 32'd5665) ? (32'd5665 - p0) : 32'd0;
                    qual = (p0 * 16'd100) / 16'd5665;
                end

                th1 = (incident_angle + 16'd10 <= 16'd1800) ? (incident_angle + 16'd10) : 16'd1800;
                th2 = (incident_angle + 16'd20 <= 16'd1800) ? (incident_angle + 16'd20) : 16'd1800;
                th3 = (incident_angle + 16'd30 <= 16'd1800) ? (incident_angle + 16'd30) : 16'd1800;

                estimated_power   <= p0[15:0];
                panel0_data       <= {incident_angle, p0[15:0]};
                panel1_data       <= {th1, p1[15:0]};
                panel2_data       <= {th2, p2[15:0]};
                panel3_data       <= {th3, p3[15:0]};
                total_array_power <= p0 + p1 + p2 + p3;
                tracking_quality  <= {qual, p_loss[15:0]};
            end

            done <= pipe_valid[1];
        end
    end

endmodule
