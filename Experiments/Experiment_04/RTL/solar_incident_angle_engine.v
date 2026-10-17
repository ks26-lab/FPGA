`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_incident_angle_engine
// Description:
//   Computes 3D dot product N · S = cos(theta) in Q16.16,
//   scales cos_incidence (x1000), and derives incident angle theta via arccos table.
//////////////////////////////////////////////////////////////////////////////////

module solar_incident_angle_engine (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire signed [31:0] sx,
    input  wire signed [31:0] sy,
    input  wire signed [31:0] sz,
    input  wire signed [31:0] nx,
    input  wire signed [31:0] ny,
    input  wire signed [31:0] nz,
    output reg  signed [31:0] dot_product,   // Q16.16
    output reg  [15:0]        cos_incidence, // x1000 integer
    output reg  [15:0]        incident_angle,// 0.1 deg (0 to 1800)
    output reg                done
);

    // Products in Q16.16: (A * B) >>> 16
    wire signed [63:0] px = sx * nx;
    wire signed [63:0] py = sy * ny;
    wire signed [63:0] pz = sz * nz;

    reg [2:0] pipe_valid;
    reg signed [31:0] dot_raw;

    // Arccos piecewise linear lookup table (17 points for dot in [0.0, 1.0] -> [0.0, 90.0 deg])
    // dot indices: 0/16, 1/16, ..., 16/16
    // angle in 0.1 deg
    reg [15:0] acos_lut [0:16];
    initial begin
        acos_lut[0]  = 16'd900; // cos=0.000 -> 90.0 deg
        acos_lut[1]  = 16'd864; // cos=0.0625 -> 86.4 deg
        acos_lut[2]  = 16'd828; // cos=0.125 -> 82.8 deg
        acos_lut[3]  = 16'd792; // cos=0.1875 -> 79.2 deg
        acos_lut[4]  = 16'd755; // cos=0.250 -> 75.5 deg
        acos_lut[5]  = 16'd718; // cos=0.3125 -> 71.8 deg
        acos_lut[6]  = 16'd680; // cos=0.375 -> 68.0 deg
        acos_lut[7]  = 16'd641; // cos=0.4375 -> 64.1 deg
        acos_lut[8]  = 16'd600; // cos=0.500 -> 60.0 deg
        acos_lut[9]  = 16'd558; // cos=0.5625 -> 55.8 deg
        acos_lut[10] = 16'd513; // cos=0.625 -> 51.3 deg
        acos_lut[11] = 16'd466; // cos=0.6875 -> 46.6 deg
        acos_lut[12] = 16'd414; // cos=0.750 -> 41.4 deg
        acos_lut[13] = 16'd357; // cos=0.8125 -> 35.7 deg
        acos_lut[14] = 16'd290; // cos=0.875 -> 29.0 deg
        acos_lut[15] = 16'd204; // cos=0.9375 -> 20.4 deg
        acos_lut[16] = 16'd0;   // cos=1.000 -> 0.0 deg
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipe_valid     <= 3'b0;
            dot_product    <= 32'sd65536;
            cos_incidence  <= 16'd1000;
            incident_angle <= 16'd0;
            done           <= 1'b0;
            dot_raw        <= 32'sd65536;
        end else begin
            pipe_valid <= {pipe_valid[1:0], start};

            if (pipe_valid[0]) begin
                // Sum the products
                dot_raw <= px[47:16] + py[47:16] + pz[47:16];
            end

            if (pipe_valid[1]) begin
                // Clamp dot product to [-65536, +65536]
                reg signed [31:0] clamped_dot;
                if (dot_raw > 32'sd65536) clamped_dot = 32'sd65536;
                else if (dot_raw < -32'sd65536) clamped_dot = -32'sd65536;
                else clamped_dot = dot_raw;

                dot_product <= clamped_dot;

                // Positive cos for power
                if (clamped_dot <= 0) begin
                    cos_incidence <= 16'd0;
                end else begin
                    // (clamped_dot * 1000) >> 16
                    wire [47:0] scaled_cos = clamped_dot * 32'd1000;
                    cos_incidence <= scaled_cos[31:16];
                end

                // Compute incident angle via arccos table
                // For dot >= 0: angle in [0, 900]
                // For dot < 0: angle in [900, 1800], acos(-d) = 1800 - acos(d)
                reg [15:0] abs_dot;
                reg is_neg;
                if (clamped_dot < 0) begin
                    abs_dot = -clamped_dot;
                    is_neg  = 1'b1;
                end else begin
                    abs_dot = clamped_dot[15:0];
                    is_neg  = 1'b0;
                end

                // Map 0..65536 to 0..16
                wire [4:0] lut_idx = abs_dot[15:12]; // 0 to 15
                wire [11:0] lut_frac = abs_dot[11:0];

                wire [15:0] a0 = acos_lut[lut_idx];
                wire [15:0] a1 = (lut_idx < 5'd16) ? acos_lut[lut_idx + 1] : 16'd0;

                // Interpolate
                wire signed [19:0] a_diff = $signed({4'b0, a1}) - $signed({4'b0, a0});
                wire signed [31:0] a_interp = (a_diff * $signed({20'b0, lut_frac})) / 4096;
                wire [15:0] base_angle = a0 + a_interp[15:0];

                if (is_neg) begin
                    incident_angle <= (16'd1800 > base_angle) ? (16'd1800 - base_angle) : 16'd1800;
                end else begin
                    incident_angle <= base_angle;
                end
            end

            done <= pipe_valid[2];
        end
    end

endmodule
