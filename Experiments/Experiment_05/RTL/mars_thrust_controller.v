`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: mars_thrust_controller
// Description:
//   Closed-loop retro-thrust braking controller for Mars descent.
//   Adapts target deceleration velocity profile based on radar altitude
//   with terminal flare boost below 20 meters.
//////////////////////////////////////////////////////////////////////////////////

module mars_thrust_controller (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] landing_altitude,    // decimeters (0.1m)
    input  wire signed [15:0] landing_velocity, // decimeters/s (0.1m/s, signed)
    output reg  [15:0] thrust_cmd           // 0 to 1000 (0.0% to 100.0%)
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            thrust_cmd <= 16'd650; // Nominal 65.0%
        end else begin
            reg signed [15:0] target_v;
            if (landing_altitude < 32'd200) begin
                target_v = -16'sd20;  // -2.0 m/s terminal flare
            end else if (landing_altitude < 32'd1000) begin
                target_v = -16'sd100; // -10.0 m/s approach
            end else begin
                target_v = -16'sd200; // -20.0 m/s high descent
            end

            // Error: target_v - current_v
            wire signed [15:0] vel_err = target_v - landing_velocity;

            // Base gravity compensation (3710 N) + proportional gain (40 N per 0.1 m/s)
            wire signed [31:0] thrust_n = 32'sd3710 + ($signed(vel_err) * 32'sd40);

            // Clamp thrust to [0, 10,000 N]
            reg [31:0] clamped_n;
            if (thrust_n < 32'sd0)
                clamped_n = 32'd0;
            else if (thrust_n > 32'sd10000)
                clamped_n = 32'd10000;
            else
                clamped_n = thrust_n[31:0];

            // Convert to per-mille (0..1000)
            thrust_cmd <= clamped_n / 10;
        end
    end

endmodule
