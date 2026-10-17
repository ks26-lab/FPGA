`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_trig_table
// Description:
//   Sine and Cosine quarter-wave lookup table with linear sub-interpolation.
//   Input angle: tenths of a degree in [0, 3599] representing 0.0 to 359.9 deg.
//   Output: Signed Q1.15 fixed-point (-32768 to +32767 for -1.0 to +0.9999)
//           converted to Q16.16 format for 32-bit math.
//////////////////////////////////////////////////////////////////////////////////

module solar_trig_table (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [15:0] angle_tenths, // 0 to 3599 (0.0 to 359.9 deg)
    output reg  signed [31:0] sin_q16, // Q16.16 signed
    output reg  signed [31:0] cos_q16  // Q16.16 signed
);

    // Quarter-wave ROM table for sin(0) to sin(90) in steps of 1.0 degree (91 points).
    // Values scaled by 32767 (Q1.15 format)
    reg [15:0] sin_rom [0:90];

    initial begin
        sin_rom[0]  = 16'd0;     sin_rom[1]  = 16'd572;   sin_rom[2]  = 16'd1144;  sin_rom[3]  = 16'd1715;
        sin_rom[4]  = 16'd2286;  sin_rom[5]  = 16'd2856;  sin_rom[6]  = 16'd3425;  sin_rom[7]  = 16'd3993;
        sin_rom[8]  = 16'd4560;  sin_rom[9]  = 16'd5126;  sin_rom[10] = 16'd5690;  sin_rom[11] = 16'd6252;
        sin_rom[12] = 16'd6813;  sin_rom[13] = 16'd7371;  sin_rom[14] = 16'd7927;  sin_rom[15] = 16'd8481;
        sin_rom[16] = 16'd9032;  sin_rom[17] = 16'd9580;  sin_rom[18] = 16'd10126; sin_rom[19] = 16'd10668;
        sin_rom[20] = 16'd11207; sin_rom[21] = 16'd11743; sin_rom[22] = 16'd12275; sin_rom[23] = 16'd12803;
        sin_rom[24] = 16'd13328; sin_rom[25] = 16'd13848; sin_rom[26] = 16'd14364; sin_rom[27] = 16'd14876;
        sin_rom[28] = 16'd15383; sin_rom[29] = 16'd15886; sin_rom[30] = 16'd16384; sin_rom[31] = 16'd16876;
        sin_rom[32] = 16'd17364; sin_rom[33] = 16'd17846; sin_rom[34] = 16'd18323; sin_rom[35] = 16'd18794;
        sin_rom[36] = 16'd19260; sin_rom[37] = 16'd19720; sin_rom[38] = 16'd20173; sin_rom[39] = 16'd20621;
        sin_rom[40] = 16'd21062; sin_rom[41] = 16'd21497; sin_rom[42] = 16'd21925; sin_rom[43] = 16'd22347;
        sin_rom[44] = 16'd22762; sin_rom[45] = 16'd23170; sin_rom[46] = 16'd23571; sin_rom[47] = 16'd23964;
        sin_rom[48] = 16'd24351; sin_rom[49] = 16'd24730; sin_rom[50] = 16'd25101; sin_rom[51] = 16'd25465;
        sin_rom[52] = 16'd25821; sin_rom[53] = 16'd26169; sin_rom[54] = 16'd26509; sin_rom[55] = 16'd26841;
        sin_rom[56] = 16'd27165; sin_rom[57] = 16'd27481; sin_rom[58] = 16'd27788; sin_rom[59] = 16'd28087;
        sin_rom[60] = 16'd28377; sin_rom[61] = 16'd28659; sin_rom[62] = 16'd28932; sin_rom[63] = 16'd29196;
        sin_rom[64] = 16'd29451; sin_rom[65] = 16'd29697; sin_rom[66] = 16'd29934; sin_rom[67] = 16'd30162;
        sin_rom[68] = 16'd30381; sin_rom[69] = 16'd30591; sin_rom[70] = 16'd30791; sin_rom[71] = 16'd30982;
        sin_rom[72] = 16'd31163; sin_rom[73] = 16'd31335; sin_rom[74] = 16'd31498; sin_rom[75] = 16'd31650;
        sin_rom[76] = 16'd31794; sin_rom[77] = 16'd31927; sin_rom[78] = 16'd32051; sin_rom[79] = 16'd32165;
        sin_rom[80] = 16'd32269; sin_rom[81] = 16'd32364; sin_rom[82] = 16'd32448; sin_rom[83] = 16'd32523;
        sin_rom[84] = 16'd32587; sin_rom[85] = 16'd32642; sin_rom[86] = 16'd32687; sin_rom[87] = 16'd32722;
        sin_rom[88] = 16'd32747; sin_rom[89] = 16'd32762; sin_rom[90] = 16'd32767;
    end

    // Normalize angle to 0..3599
    wire [15:0] norm_angle = angle_tenths % 16'd3600;

    // Determine quadrant:
    // Q0: 0..899
    // Q1: 900..1799
    // Q2: 1800..2699
    // Q3: 2700..3599
    reg [1:0] quadrant;
    reg [15:0] q_angle; // Angle within quarter-circle (0..900 tenths)

    always @(*) begin
        if (norm_angle < 16'd900) begin
            quadrant = 2'd0;
            q_angle  = norm_angle;
        end else if (norm_angle < 16'd1800) begin
            quadrant = 2'd1;
            q_angle  = 16'd1800 - norm_angle;
        end else if (norm_angle < 16'd2700) begin
            quadrant = 2'd2;
            q_angle  = norm_angle - 16'd1800;
        end else begin
            quadrant = 2'd3;
            q_angle  = 16'd3600 - norm_angle;
        end
    end

    // Index and fraction
    wire [6:0] idx = q_angle / 10;
    wire [3:0] frac = q_angle % 10;

    // Table values with boundary clamp
    wire [15:0] v0 = sin_rom[idx];
    wire [15:0] v1 = (idx < 7'd90) ? sin_rom[idx + 1] : sin_rom[90];

    // Linear interpolation: v0 + (v1 - v0) * frac / 10
    wire signed [19:0] diff = $signed({4'b0, v1}) - $signed({4'b0, v0});
    wire signed [23:0] interp_offset = (diff * $signed({16'b0, frac})) / 10;
    wire [15:0] sin_mag = v0 + interp_offset[15:0];

    // Cosine magnitude by 90-degree fold
    reg [15:0] cos_q_angle;
    always @(*) begin
        if (q_angle >= 16'd900)
            cos_q_angle = 16'd0;
        else
            cos_q_angle = 16'd900 - q_angle;
    end

    wire [6:0] c_idx = cos_q_angle / 10;
    wire [3:0] c_frac = cos_q_angle % 10;
    wire [15:0] cv0 = sin_rom[c_idx];
    wire [15:0] cv1 = (c_idx < 7'd90) ? sin_rom[c_idx + 1] : sin_rom[90];
    wire signed [19:0] c_diff = $signed({4'b0, cv1}) - $signed({4'b0, cv0});
    wire signed [23:0] c_interp = (c_diff * $signed({16'b0, c_frac})) / 10;
    wire [15:0] cos_mag = cv0 + c_interp[15:0];

    // Apply quadrant signs:
    // Q0: sin+, cos+
    // Q1: sin+, cos-
    // Q2: sin-, cos-
    // Q3: sin-, cos+
    // Convert Q1.15 to Q16.16 (shift left 1)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sin_q16 <= 32'sd0;
            cos_q16 <= 32'sd65536; // 1.0
        end else begin
            case (quadrant)
                2'd0: begin
                    sin_q16 <= $signed({15'b0, sin_mag, 1'b0});
                    cos_q16 <= $signed({15'b0, cos_mag, 1'b0});
                end
                2'd1: begin
                    sin_q16 <= $signed({15'b0, sin_mag, 1'b0});
                    cos_q16 <= -$signed({15'b0, cos_mag, 1'b0});
                end
                2'd2: begin
                    sin_q16 <= -$signed({15'b0, sin_mag, 1'b0});
                    cos_q16 <= -$signed({15'b0, cos_mag, 1'b0});
                end
                2'd3: begin
                    sin_q16 <= -$signed({15'b0, sin_mag, 1'b0});
                    cos_q16 <= $signed({15'b0, cos_mag, 1'b0});
                end
            endcase
        end
    end

endmodule
