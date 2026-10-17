// ============================================================================
// File: underwater_drag_engine.v
// Module: underwater_drag_engine
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem
// Description:
//   Dedicated FPGA drag calculation engine executing quadratic hydrodynamic drag
//   with fixed-point multiplication:
//     v_relative = v_probe - v_current
//     F_drag = K_drag * v_relative * |v_relative|
// ============================================================================

`timescale 1ns / 1ps

module underwater_drag_engine (
    input  wire               clk,
    input  wire               rst_n,

    input  wire signed [7:0]  probe_velocity,   // 0.1 m/s units
    input  wire signed [7:0]  current_velocity, // 0.1 m/s units (cfg_current >>> 4)
    input  wire [7:0]         k_drag_coeff,     // Fixed-point factor (e.g. 8'd4 for 0.25)

    output reg  signed [15:0] relative_velocity,// 0.1 m/s units
    output reg  signed [15:0] drag_force        // 0.1 N units
);

    wire signed [15:0] v_rel_comb = {{8{probe_velocity[7]}}, probe_velocity} -
                                    {{8{current_velocity[7]}}, current_velocity};

    // Intermediate pipeline registers
    reg signed [15:0] v_rel_reg;
    reg [15:0]        abs_v_rel;
    reg signed [31:0] quad_product;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            relative_velocity <= 16'sd0;
            v_rel_reg         <= 16'sd0;
            abs_v_rel         <= 16'd0;
            quad_product      <= 32'sd0;
            drag_force        <= 16'sd0;
        end else begin
            // Stage 1: Compute relative velocity and absolute magnitude
            v_rel_reg         <= v_rel_comb;
            relative_velocity <= v_rel_comb;
            abs_v_rel         <= (v_rel_comb < 0) ? -v_rel_comb : v_rel_comb;

            // Stage 2: Multiply v_rel * |v_rel|
            quad_product      <= v_rel_reg * $signed({16'd0, abs_v_rel});

            // Stage 3: Scale by K_drag (divided by 16 fixed-point scaling)
            // F_drag = (quad_product * k_drag_coeff) >>> 4
            reg signed [31:0] scaled_force;
            scaled_force = (quad_product * $signed({24'd0, k_drag_coeff})) >>> 4;

            // Saturate to 16-bit signed
            if (scaled_force > 32'sd1000) begin
                drag_force <= 16'sd1000;
            end else if (scaled_force < -32'sd1000) begin
                drag_force <= -16'sd1000;
            end else begin
                drag_force <= scaled_force[15:0];
            end
        end
    end

endmodule
