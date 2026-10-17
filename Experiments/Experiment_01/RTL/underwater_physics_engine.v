// ============================================================================
// File: underwater_physics_engine.v
// Module: underwater_physics_engine
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem
// Description:
//   Dedicated FPGA hardware physics engine executing real-time discrete
//   depth updating, vertical velocity integration, and current disturbance
//   modeling with fixed-point arithmetic.
//
// Equations:
//   1. depth_error = target_depth - current_depth
//   2. v_current = cfg_current_strength >>> 4
//   3. acceleration = (thrust_force - drag_force - disturbance_force) / mass
//   4. velocity_next = clamp(velocity + acceleration_step, MIN_VEL, MAX_VEL)
//   5. depth_next = clamp(depth + velocity_next, 0, 10000) (0.0 m to 1000.0 m)
// ============================================================================

`timescale 1ns / 1ps

module underwater_physics_engine (
    input  wire               clk,
    input  wire               rst_n,
    input  wire               update_tick,
    input  wire               enable,

    // Configuration / Inputs
    input  wire signed [15:0] current_depth_in,
    input  wire signed [15:0] target_depth_in,
    input  wire signed [7:0]  cfg_current_strength,
    input  wire signed [15:0] thrust_force,        // 0.1 N units
    input  wire signed [15:0] drag_force,          // 0.1 N units
    input  wire signed [15:0] recovery_thrust,     // 0.1 N units
    input  wire               recovery_active,

    // Outputs
    output reg  signed [15:0] depth_error,         // 0.1 m units
    output reg  signed [7:0]  current_effect,      // 0.1 m/s drift velocity
    output reg  signed [7:0]  raw_velocity,        // 0.1 m/s units
    output reg  signed [15:0] raw_depth,           // 0.1 m units
    output reg  signed [15:0] depth_next           // 0.1 m units
);

    // Scaling constants:
    // Simulation timestep dt = 0.1s. Probe effective mass = 50.0 kg.
    // Net force = thrust - drag + current influence
    wire signed [15:0] current_drift_ext = {{12{cfg_current_strength[7]}}, cfg_current_strength[7:4]};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            depth_error    <= 16'sd0;
            current_effect <= 8'sd0;
            raw_velocity   <= 8'sd0;
            raw_depth      <= 16'sd500; // 50.0 m default
            depth_next     <= 16'sd500;
        end else if (enable) begin
            // 1. Continuous error computation
            depth_error    <= target_depth_in - current_depth_in;
            current_effect <= cfg_current_strength >>> 4;

            if (update_tick) begin
                // 2. Compute net acceleration force in fixed-point 0.1 N units
                reg signed [15:0] net_f;
                reg signed [15:0] v_step;
                reg signed [15:0] new_v;
                reg signed [15:0] new_d;

                // Restorative force derived from depth error and thrust
                if (recovery_active) begin
                    net_f = recovery_thrust - drag_force;
                end else begin
                    // Base force proportional to thrust difference from neutral buoyancy
                    net_f = (thrust_force - 16'sd500) - drag_force;
                end

                // Velocity update: v_next = v + (net_f / 32) + current_drift
                // Clamped to [-15, +15] (representing -1.5 m/s to +1.5 m/s)
                v_step = (net_f >>> 5); // divide by 32 fixed-point mass scale
                new_v  = {{8{raw_velocity[7]}}, raw_velocity} + v_step + current_drift_ext;

                if (new_v > 16'sd15)       new_v = 16'sd15;
                else if (new_v < -16'sd15) new_v = -16'sd15;

                raw_velocity <= new_v[7:0];

                // 3. Discrete Depth Integration: depth_next = depth + v
                // Clamped between 0.0 m (surface) and 1000.0 m (10000 units)
                new_d = current_depth_in + new_v;
                if (new_d < 16'sd0)          new_d = 16'sd0;
                else if (new_d > 16'sd10000) new_d = 16'sd10000;

                raw_depth  <= new_d;
                depth_next <= new_d;
            end
        end else begin
            raw_velocity   <= 8'sd0;
            depth_error    <= target_depth_in - current_depth_in;
            current_effect <= 8'sd0;
        end
    end

endmodule
