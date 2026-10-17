`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: mars_landing_physics
// Description:
//   Discrete-time Mars descent dynamics integrator.
//   Simulates altitude, velocity, acceleration under Mars gravity (3.71 m/s^2)
//   and retro-rocket thrust. Touchdown detection and predictive horizon.
//   Units: Altitude in decimeters (0.1m), Velocity in decimeters/s (0.1m/s).
//////////////////////////////////////////////////////////////////////////////////

module mars_landing_physics (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        landing_start,
    input  wire        tick_step,           // 100ms discrete physics step
    input  wire [15:0] thrust_cmd,          // 0 to 1000 (0.0% to 100.0%, 0 to 10,000 N)
    output reg  [31:0] landing_altitude,    // decimeters (0.1m)
    output reg  signed [15:0] landing_velocity, // decimeters/s (0.1m/s, signed)
    output reg  signed [15:0] landing_acceleration, // decimeters/s^2 (0.1m/s^2, signed)
    output reg  [31:0] predicted_altitude,  // projected T+5
    output reg  signed [15:0] predicted_touchdown_vel,
    output reg  [3:0]  landing_fsm,         // 0=PREP, 1=POWERED, 2=APPROACH, 3=TOUCHDOWN
    output reg  [1:0]  landing_safety_code, // 0=SAFE, 1=WARN, 2=CRITICAL
    output reg         landing_active
);

    localparam FSM_PREP      = 4'd0;
    localparam FSM_POWERED   = 4'd1;
    localparam FSM_APPROACH  = 4'd2;
    localparam FSM_TOUCHDOWN = 4'd3;

    // Mars gravity downward force for 1000 kg craft: 3710 N
    // In decimeters/s^2: 37.1 dm/s^2 -> 37
    localparam signed [31:0] MARS_GRAV_FORCE = 32'sd3710;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            landing_altitude        <= 32'd5000;  // 500.0 m
            landing_velocity        <= -16'sd200; // -20.0 m/s
            landing_acceleration    <= 16'sd0;
            predicted_altitude      <= 32'd4000;  // 400.0 m
            predicted_touchdown_vel <= -16'sd42;  // -4.2 m/s
            landing_fsm             <= FSM_PREP;
            landing_safety_code     <= 2'd0;      // SAFE
            landing_active          <= 1'b0;
        end else if (landing_start) begin
            landing_active          <= 1'b1;
            landing_altitude        <= 32'd5000;
            landing_velocity        <= -16'sd200;
            landing_fsm             <= FSM_POWERED;
        end else if (landing_active && tick_step) begin
            if (landing_altitude == 0) begin
                landing_active <= 1'b0;
                landing_fsm    <= FSM_TOUCHDOWN;
            end else begin
                // Convert thrust_cmd (0..1000) to Newtons (0..10,000 N)
                wire signed [31:0] thrust_n = $signed({16'd0, thrust_cmd}) * 32'sd10;

                // Net force: F_net = Thrust - F_grav
                wire signed [31:0] f_net = thrust_n - MARS_GRAV_FORCE;

                // Net acceleration: a = F_net / m (m = 1000 kg)
                // in m/s^2: f_net / 1000
                // in decimeters/s^2 (0.1 m/s^2): f_net / 100
                wire signed [15:0] a_net = f_net / 32'sd100;
                landing_acceleration <= a_net;

                // Discrete integration: dt = 0.1 s
                // v_{n+1} = v_n + a * 0.1 (in 0.1 m/s units: v + a * 1 / 10)
                reg signed [31:0] new_v;
                new_v = $signed(landing_velocity) + ($signed(a_net) / 32'sd10);

                // Velocity clamping [-100.0 m/s, +20.0 m/s]
                if (new_v > 32'sd200) new_v = 32'sd200;
                else if (new_v < -32'sd1000) new_v = -32'sd1000;

                // h_{n+1} = h_n + v * 0.1 (in 0.1 m units: h + v * 1 / 10)
                reg signed [31:0] new_h;
                new_h = $signed({1'b0, landing_altitude}) + (new_v / 32'sd10);

                if (new_h <= 32'sd0) begin
                    landing_altitude <= 32'd0;
                    landing_velocity <= new_v[15:0];
                    landing_fsm      <= FSM_TOUCHDOWN;
                    landing_active   <= 1'b0;

                    // Evaluate touchdown contact velocity
                    wire [15:0] abs_touchdown = (new_v < 0) ? -new_v[15:0] : new_v[15:0];
                    if (abs_touchdown <= 16'd50) begin
                        landing_safety_code <= 2'd0; // SAFE (<= 5.0 m/s)
                    end else if (abs_touchdown <= 16'd100) begin
                        landing_safety_code <= 2'd1; // WARN (5.0 to 10.0 m/s)
                    end else begin
                        landing_safety_code <= 2'd2; // CRITICAL (> 10.0 m/s)
                    end
                end else begin
                    landing_altitude <= new_h[31:0];
                    landing_velocity <= new_v[15:0];

                    if (new_h < 32'sd300) begin
                        landing_fsm <= FSM_APPROACH;
                    end else begin
                        landing_fsm <= FSM_POWERED;
                    end
                end

                // Predictive horizon: T+5 projection
                reg signed [31:0] pred_h;
                pred_h = new_h + (new_v * 32'sd5) / 32'sd10;
                predicted_altitude <= (pred_h > 0) ? pred_h[31:0] : 32'd0;
                predicted_touchdown_vel <= new_v[15:0];
            end
        end
    end

endmodule
