// ============================================================================
// File: underwater_fault_detector.v
// Module: underwater_fault_detector
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem
// Description:
//   Dedicated FPGA hardware anomaly and fault detector monitoring:
//   Bit 0: SENSOR_FAULT      (Depth < 0 or > 1000m)
//   Bit 1: DEPTH_ERROR_FAULT (|depth_error| > 200m)
//   Bit 2: VELOCITY_FAULT    (|velocity| > 1.2 m/s)
//   Bit 3: THRUST_FAULT      (Thrust saturated at max)
//   Bit 4: CURRENT_FAULT     (|current_strength| > 90%)
//   Bit 5: COLLISION_FAULT   (Collision detected with unstable velocity)
//   Bit 6: PID_SATURATION    (Integral anti-windup clamp active)
// ============================================================================

`timescale 1ns / 1ps

module underwater_fault_detector (
    input  wire               clk,
    input  wire               rst_n,

    input  wire signed [15:0] current_depth,
    input  wire signed [15:0] depth_error,
    input  wire signed [7:0]  velocity,
    input  wire signed [15:0] thrust_command,
    input  wire signed [7:0]  current_strength,
    input  wire               collision_detected,
    input  wire               integral_saturated,

    output reg  [7:0]         fault_flags
);

    wire [15:0] abs_err = (depth_error < 0) ? -depth_error : depth_error;
    wire [7:0]  abs_vel = (velocity < 0) ? -velocity : velocity;
    wire [7:0]  abs_cur = (current_strength < 0) ? -current_strength : current_strength;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fault_flags <= 8'd0;
        end else begin
            fault_flags[0] <= (current_depth < 16'sd0) || (current_depth > 16'sd10000);
            fault_flags[1] <= (abs_err > 16'd2000); // > 200.0 m
            fault_flags[2] <= (abs_vel > 8'd12);   // > 1.2 m/s
            fault_flags[3] <= (thrust_command >= 16'sd1500) || (thrust_command <= 16'sd0);
            fault_flags[4] <= (abs_cur > 8'd90);   // > 90%
            fault_flags[5] <= collision_detected && (abs_vel > 8'd10);
            fault_flags[6] <= integral_saturated;
            fault_flags[7] <= 1'b0; // Reserved
        end
    end

endmodule
