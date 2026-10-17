// ============================================================================
// File: underwater_collision_engine.v
// Module: underwater_collision_engine
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem
// Description:
//   Dedicated FPGA collision and impact severity calculator.
//   Computes kinetic impact energy:
//     E_impact = 0.5 * m * v_relative^2 (in fixed-point Joules)
//   Classifies severity:
//     0 = NO_IMPACT, 1 = LOW, 2 = MEDIUM, 3 = HIGH, 4 = CRITICAL
// ============================================================================

`timescale 1ns / 1ps

module underwater_collision_engine (
    input  wire               clk,
    input  wire               rst_n,

    input  wire               cmd_disturb_strobe,
    input  wire [1:0]         cmd_disturb_type, // 0=NONE, 1=FISH, 2=GARBAGE, 3=WHALE
    input  wire signed [15:0] relative_velocity,// 0.1 m/s units

    output reg                collision_detected,
    output reg  [15:0]        impact_energy,    // Integer Joules
    output reg  [2:0]         impact_severity,  // 0..4
    output reg  [1:0]         active_object_type
);

    localparam SEV_NONE     = 3'd0;
    localparam SEV_LOW      = 3'd1;
    localparam SEV_MEDIUM   = 3'd2;
    localparam SEV_HIGH     = 3'd3;
    localparam SEV_CRITICAL = 3'd4;

    reg signed [15:0] object_mass_kg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            collision_detected <= 1'b0;
            impact_energy      <= 16'd0;
            impact_severity    <= SEV_NONE;
            active_object_type <= 2'd0;
            object_mass_kg     <= 16'd0;
        end else if (cmd_disturb_strobe && (cmd_disturb_type != 2'd0)) begin
            active_object_type <= cmd_disturb_type;
            collision_detected <= 1'b1;

            // Assign object mass
            case (cmd_disturb_type)
                2'd1: object_mass_kg <= 16'sd5;   // FISH (5 kg)
                2'd2: object_mass_kg <= 16'sd25;  // GARBAGE (25 kg)
                2'd3: object_mass_kg <= 16'sd200; // WHALE (200 kg)
                default: object_mass_kg <= 16'sd10;
            endcase

            // E = 0.5 * m * v_rel^2
            // v_rel is in 0.1 m/s -> (v_rel / 10)^2 = v_rel^2 / 100
            // E = (m * v_rel^2) / 200
            reg signed [31:0] v_sq;
            reg [31:0] e_calc;
            v_sq   = relative_velocity * relative_velocity;
            e_calc = (object_mass_kg * v_sq) / 32'd200;

            impact_energy <= (e_calc > 32'd65535) ? 16'd65535 : e_calc[15:0];

            // Severity Classification
            if (e_calc < 32'd50) begin
                impact_severity <= SEV_LOW;
            end else if (e_calc < 32'd250) begin
                impact_severity <= SEV_MEDIUM;
            end else if (e_calc < 32'd800) begin
                impact_severity <= SEV_HIGH;
            end else begin
                impact_severity <= SEV_CRITICAL;
            end
        end else begin
            // Pulse auto-cleared in upper FSM
        end
    end

endmodule
