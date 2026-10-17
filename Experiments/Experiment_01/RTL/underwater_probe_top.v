// ============================================================================
// File: underwater_probe_top.v
// Module: underwater_probe_top
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Simulation (Upgraded)
// Description:
//   Top-level Verilog wrapper integrating upgraded underwater_probe_axi_slave
//   and underwater_probe_core for Vivado block design on Zynq Z7010 board.
// ============================================================================

`timescale 1ns / 1ps

module underwater_probe_top #(
    parameter CLK_FREQ_HZ = 50_000_000,
    parameter SIMULATION  = 0
)(
    input  wire        s_axi_aclk,
    input  wire        s_axi_aresetn,

    // AXI4-Lite Slave Interface (8-bit address aperture for up to 256 bytes)
    input  wire [7:0]  s_axi_awaddr,
    input  wire        s_axi_awvalid,
    output wire        s_axi_awready,

    input  wire [31:0] s_axi_wdata,
    input  wire [3:0]  s_axi_wstrb,
    input  wire        s_axi_wvalid,
    output wire        s_axi_wready,

    output wire [1:0]  s_axi_bresp,
    output wire        s_axi_bvalid,
    input  wire        s_axi_bready,

    input  wire [7:0]  s_axi_araddr,
    input  wire        s_axi_arvalid,
    output wire        s_axi_arready,

    output wire [31:0] s_axi_rdata,
    output wire [1:0]  s_axi_rresp,
    output wire        s_axi_rvalid,
    input  wire        s_axi_rready,

    // Physical Debug LEDs on Z7010 Board
    output wire [3:0]  leds_probe_state,
    output wire        led_collision,
    output wire        led_recovery,
    output wire        led_target_reached,
    
    // PWM output for Ballast Pump
    output wire        pump_pwm_out
);

    // Command wires
    wire               cmd_start;
    wire               cmd_stop;
    wire               cmd_reset;
    wire               cmd_disturb_strobe;
    wire [1:0]         cmd_disturb_type;
    wire               cfg_set_depth_we;
    wire signed [15:0] cfg_set_depth;
    wire signed [15:0] cfg_target_depth;
    wire signed [7:0]  cfg_current_strength;

    // Legacy telemetry
    wire [3:0]         probe_state;
    wire signed [15:0] current_depth;
    wire signed [15:0] target_depth;
    wire signed [7:0]  displacement_x;
    wire signed [7:0]  probe_velocity_z;
    wire               collision_detected;
    wire               recovery_active;
    wire               target_reached;
    wire [1:0]         active_object_type;
    wire [15:0]        collision_counter;
    wire [31:0]        sim_cycle_counter;

    // Upgraded telemetry
    wire signed [15:0] depth_error;
    wire signed [15:0] filtered_depth;
    wire signed [7:0]  filtered_velocity;
    wire signed [15:0] drag_force;
    wire signed [15:0] relative_velocity;
    wire signed [15:0] p_term;
    wire signed [15:0] i_term;
    wire signed [15:0] d_term;
    wire signed [15:0] control_output;
    wire signed [15:0] thrust_command;
    wire signed [15:0] thrust_delta;
    wire [15:0]        impact_energy;
    wire [2:0]         impact_severity;
    wire signed [15:0] recovery_thrust;
    wire signed [7:0]  post_collision_velocity;
    wire signed [15:0] predicted_depth_1;
    wire signed [15:0] predicted_depth_3;
    wire signed [15:0] predicted_depth_5;
    wire [15:0]        control_cost;
    wire [1:0]         optimization_action;
    wire [7:0]         fault_flags;
    wire [31:0]        physics_update_count;
    wire [15:0]        recovery_counter;

    // Direct Status LEDs
    assign leds_probe_state   = probe_state;
    assign led_collision      = collision_detected;
    assign led_recovery       = recovery_active;
    assign led_target_reached = target_reached;

    // AXI4-Lite Slave Register Interface
    underwater_probe_axi_slave #(
        .C_S_AXI_DATA_WIDTH (32),
        .C_S_AXI_ADDR_WIDTH (8)
    ) u_axi_slave (
        .s_axi_aclk              (s_axi_aclk),
        .s_axi_aresetn            (s_axi_aresetn),

        .s_axi_awaddr             (s_axi_awaddr),
        .s_axi_awvalid            (s_axi_awvalid),
        .s_axi_awready            (s_axi_awready),

        .s_axi_wdata              (s_axi_wdata),
        .s_axi_wstrb              (s_axi_wstrb),
        .s_axi_wvalid             (s_axi_wvalid),
        .s_axi_wready             (s_axi_wready),

        .s_axi_bresp              (s_axi_bresp),
        .s_axi_bvalid             (s_axi_bvalid),
        .s_axi_bready             (s_axi_bready),

        .s_axi_araddr             (s_axi_araddr),
        .s_axi_arvalid            (s_axi_arvalid),
        .s_axi_arready            (s_axi_arready),

        .s_axi_rdata              (s_axi_rdata),
        .s_axi_rresp              (s_axi_rresp),
        .s_axi_rvalid             (s_axi_rvalid),
        .s_axi_rready             (s_axi_rready),

        .cmd_start                (cmd_start),
        .cmd_stop                 (cmd_stop),
        .cmd_reset                (cmd_reset),
        .cmd_disturb_strobe       (cmd_disturb_strobe),
        .cmd_disturb_type         (cmd_disturb_type),
        .cfg_set_depth_we         (cfg_set_depth_we),
        .cfg_set_depth            (cfg_set_depth),
        .cfg_target_depth         (cfg_target_depth),
        .cfg_current_strength     (cfg_current_strength),

        .probe_state              (probe_state),
        .current_depth            (current_depth),
        .target_depth             (target_depth),
        .displacement_x           (displacement_x),
        .probe_velocity_z         (probe_velocity_z),
        .collision_detected       (collision_detected),
        .recovery_active          (recovery_active),
        .target_reached           (target_reached),
        .active_object_type       (active_object_type),
        .collision_counter        (collision_counter),
        .sim_cycle_counter        (sim_cycle_counter),

        .depth_error              (depth_error),
        .filtered_depth           (filtered_depth),
        .filtered_velocity        (filtered_velocity),
        .drag_force               (drag_force),
        .relative_velocity        (relative_velocity),
        .p_term                   (p_term),
        .i_term                   (i_term),
        .d_term                   (d_term),
        .control_output           (control_output),
        .thrust_command           (thrust_command),
        .thrust_delta             (thrust_delta),
        .impact_energy            (impact_energy),
        .impact_severity          (impact_severity),
        .recovery_thrust          (recovery_thrust),
        .post_collision_velocity  (post_collision_velocity),
        .predicted_depth_1        (predicted_depth_1),
        .predicted_depth_3        (predicted_depth_3),
        .predicted_depth_5        (predicted_depth_5),
        .control_cost             (control_cost),
        .optimization_action      (optimization_action),
        .fault_flags              (fault_flags),
        .physics_update_count     (physics_update_count),
        .recovery_counter         (recovery_counter)
    );

    // Parallel Processing Core
    underwater_probe_core #(
        .CLK_FREQ_HZ (CLK_FREQ_HZ),
        .SIMULATION  (SIMULATION)
    ) u_core (
        .clk                         (s_axi_aclk),
        .rst_n                       (s_axi_aresetn),

        .cmd_start                   (cmd_start),
        .cmd_stop                    (cmd_stop),
        .cmd_reset                   (cmd_reset),
        .cfg_set_depth               (cfg_set_depth),
        .cfg_set_depth_we            (cfg_set_depth_we),
        .cfg_target_depth            (cfg_target_depth),
        .cfg_current_strength        (cfg_current_strength),
        .cmd_disturb_strobe          (cmd_disturb_strobe),
        .cmd_disturb_type            (cmd_disturb_type),

        .probe_state                 (probe_state),
        .current_depth               (current_depth),
        .target_depth                (target_depth),
        .displacement_x              (displacement_x),
        .probe_velocity_z            (probe_velocity_z),
        .collision_detected          (collision_detected),
        .recovery_active             (recovery_active),
        .target_reached              (target_reached),
        .active_object_type          (active_object_type),
        .collision_counter           (collision_counter),
        .sim_cycle_counter           (sim_cycle_counter),

        .depth_error_out             (depth_error),
        .filtered_depth_out          (filtered_depth),
        .filtered_velocity_out       (filtered_velocity),
        .drag_force_out              (drag_force),
        .relative_velocity_out       (relative_velocity),
        .p_term_out                  (p_term),
        .i_term_out                  (i_term),
        .d_term_out                  (d_term),
        .control_output_out          (control_output),
        .thrust_command_out          (thrust_command),
        .thrust_delta_out            (thrust_delta),
        .impact_energy_out           (impact_energy),
        .impact_severity_out         (impact_severity),
        .recovery_thrust_out         (recovery_thrust),
        .post_collision_velocity_out (post_collision_velocity),
        .predicted_depth_1_out       (predicted_depth_1),
        .predicted_depth_3_out       (predicted_depth_3),
        .predicted_depth_5_out       (predicted_depth_5),
        .control_cost_out            (control_cost),
        .optimization_action_out     (optimization_action),
        .fault_flags_out             (fault_flags),
        .physics_update_count        (physics_update_count),
        .recovery_counter            (recovery_counter)
    );

    // Ballast Pump PWM Generator
    reg [7:0] pwm_counter;
    always @(posedge s_axi_aclk or negedge s_axi_aresetn) begin
        if (!s_axi_aresetn) pwm_counter <= 8'd0;
        else pwm_counter <= pwm_counter + 8'd1;
    end
    
    wire [15:0] abs_thrust = (thrust_command[15]) ? (~thrust_command + 16'd1) : thrust_command;
    wire [7:0] thrust_8bit = (abs_thrust > 16'd255) ? 8'd255 : abs_thrust[7:0];
    assign pump_pwm_out = (pwm_counter < thrust_8bit) ? 1'b1 : 1'b0;

endmodule
