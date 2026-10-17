`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_tracking_controller
// Description:
//   Two-axis circular error derivation with modulo-360 wrap-around,
//   deadband hold, proportional slew rate clamping, and closed-loop positioning.
//////////////////////////////////////////////////////////////////////////////////

module solar_tracking_controller (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        track_en,
    input  wire        fault_active,
    input  wire [15:0] sun_azimuth,
    input  wire [15:0] sun_elevation,
    input  wire [15:0] az_deadband,
    input  wire [15:0] el_deadband,
    input  wire        step_tick,
    output reg  [15:0] panel_azimuth,
    output reg  [15:0] panel_elevation,
    output reg  signed [15:0] az_error,
    output reg  signed [15:0] el_error,
    output reg  signed [15:0] actuator_az,
    output reg  signed [15:0] actuator_el,
    output reg  [31:0] status_word
);

    localparam STATE_IDLE      = 4'd0;
    localparam STATE_CALCULATE = 4'd1;
    localparam STATE_LOCKED    = 4'd2;
    localparam STATE_SLEWING   = 4'd3;
    localparam STATE_DEADBAND  = 4'd4;
    localparam STATE_FAULT     = 4'd5;

    reg [3:0] current_state;
    reg [7:0] locked_counter;

    // Compute circular azimuth error
    always @(*) begin
        reg signed [17:0] diff_az;
        diff_az = $signed({2'b0, sun_azimuth}) - $signed({2'b0, panel_azimuth});
        if (diff_az > 18'sd1800)
            diff_az = diff_az - 18'sd3600;
        else if (diff_az < -18'sd1800)
            diff_az = diff_az + 18'sd3600;
        az_error = diff_az[15:0];

        el_error = $signed({1'b0, sun_elevation}) - $signed({1'b0, panel_elevation});
    end

    wire [15:0] abs_az = (az_error < 0) ? -az_error : az_error;
    wire [15:0] abs_el = (el_error < 0) ? -el_error : el_error;

    wire az_hold = (abs_az <= az_deadband);
    wire el_hold = (abs_el <= el_deadband);
    wire is_locked = (current_state == STATE_LOCKED);

    // Actuator commands with proportional slew clamp
    always @(*) begin
        if (az_hold)
            actuator_az = 16'sd0;
        else if (az_error > 16'sd100)
            actuator_az = 16'sd100;
        else if (az_error < -16'sd100)
            actuator_az = -16'sd100;
        else
            actuator_az = az_error;

        if (el_hold)
            actuator_el = 16'sd0;
        else if (el_error > 16'sd50)
            actuator_el = 16'sd50;
        else if (el_error < -16'sd50)
            actuator_el = -16'sd50;
        else
            actuator_el = el_error;
    end

    // Status word construction
    always @(*) begin
        status_word = {
            23'd0,
            el_hold,
            az_hold,
            (el_error >= 0),
            (az_error >= 0),
            is_locked,
            current_state
        };
    end

    // Closed-loop stepping & state machine
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            panel_azimuth   <= 16'd0;
            panel_elevation <= 16'd0;
            current_state   <= STATE_IDLE;
            locked_counter  <= 8'd0;
        end else if (fault_active) begin
            current_state   <= STATE_FAULT;
        end else if (!track_en) begin
            current_state   <= STATE_IDLE;
            locked_counter  <= 8'd0;
        end else begin
            // State transitions
            if (az_hold && el_hold) begin
                if (locked_counter >= 8'd3) begin
                    current_state <= STATE_LOCKED;
                end else begin
                    locked_counter <= locked_counter + 1'b1;
                    current_state <= STATE_DEADBAND;
                end
            end else begin
                locked_counter <= 8'd0;
                current_state <= STATE_SLEWING;
            end

            // Position stepping
            if (step_tick) begin
                if (!az_hold) begin
                    reg signed [17:0] next_az;
                    reg signed [15:0] step_az;
                    if (abs_az > 16'd10) step_az = 16'd10; else step_az = abs_az;

                    if (az_error > 0)
                        next_az = $signed({2'b0, panel_azimuth}) + $signed({2'b0, step_az});
                    else
                        next_az = $signed({2'b0, panel_azimuth}) - $signed({2'b0, step_az});

                    if (next_az >= 18'sd3600) next_az = next_az - 18'sd3600;
                    else if (next_az < 18'sd0) next_az = next_az + 18'sd3600;

                    panel_azimuth <= next_az[15:0];
                end

                if (!el_hold) begin
                    reg signed [17:0] next_el;
                    reg signed [15:0] step_el;
                    if (abs_el > 16'd5) step_el = 16'd5; else step_el = abs_el;

                    if (el_error > 0)
                        next_el = $signed({2'b0, panel_elevation}) + $signed({2'b0, step_el});
                    else
                        next_el = $signed({2'b0, panel_elevation}) - $signed({2'b0, step_el});

                    if (next_el > 18'sd900) next_el = 18'sd900;
                    else if (next_el < 18'sd0) next_el = 18'sd0;

                    panel_elevation <= next_el[15:0];
                end
            end
        end
    end

endmodule
