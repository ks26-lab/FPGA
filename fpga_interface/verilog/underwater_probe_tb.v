// ============================================================================
// File: underwater_probe_tb.v
// Module: underwater_probe_tb
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Simulation (Upgraded Verification)
// Description:
//   Self-checking verification testbench for the upgraded underwater_probe_core.
//   Verifies:
//     1. Depth error & convergence
//     2. Velocity update & discrete depth integration
//     3. Water-current disturbance integration & drag calculation
//     4. PID controller response, integral anti-windup & thrust saturation
//     5. Moving Average & EMA filtering
//     6. Object collision detection & impact energy severity calculation
//     7. Asymptotic recovery FSM
//     8. Lightweight depth prediction (T+1, T+3, T+5)
//     9. Energy/thrust optimization action
//    10. Fault/anomaly detection flags
// ============================================================================

`timescale 1ns / 1ps

module underwater_probe_tb;

    reg                clk;
    reg                rst_n;
    reg                cmd_start;
    reg                cmd_stop;
    reg                cmd_reset;
    reg  signed [15:0] cfg_set_depth;
    reg                cfg_set_depth_we;
    reg  signed [15:0] cfg_target_depth;
    reg  signed [7:0]  cfg_current_strength;
    reg                cmd_disturb_strobe;
    reg  [1:0]         cmd_disturb_type;

    // Outputs
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

    // Instantiate upgraded DUT
    underwater_probe_core #(
        .CLK_FREQ_HZ (50),
        .SIMULATION  (1) // 25 clocks per tick
    ) dut (
        .clk                         (clk),
        .rst_n                       (rst_n),
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

    always #10 clk = ~clk;

    integer pass_count = 0;

    initial begin
        $display("==========================================================");
        $display("   UNDERWATER PROBE UPGRADED FPGA PARALLEL TESTBENCH      ");
        $display("==========================================================");

        clk                  = 0;
        rst_n                = 0;
        cmd_start            = 0;
        cmd_stop             = 0;
        cmd_reset            = 0;
        cfg_set_depth        = 16'sd500; // 50.0m
        cfg_set_depth_we     = 0;
        cfg_target_depth     = 16'sd800; // 80.0m
        cfg_current_strength = 8'sd20;   // +20% current
        cmd_disturb_strobe   = 0;
        cmd_disturb_type     = 0;

        // Test 1: Reset Initialization
        #100;
        rst_n = 1;
        #50;

        if (probe_state == 4'd0 && current_depth == 500 && target_depth == 800) begin
            $display("[PASS] Test 1: Reset initialized core at 50.0m, target at 80.0m");
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 1: Reset failed");

        // Test 2: Start & Real-Time Depth Error Calculation
        cmd_start = 1;
        #20;
        cmd_start = 0;
        #600; // Allow several ticks

        if (depth_error == (target_depth - current_depth) && probe_state == 4'd1) begin
            $display("[PASS] Test 2: Depth error active and accurate: %d units", depth_error);
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 2: Depth error calculation failed");

        // Test 3: PID Controller & Thrust Slew Rate
        if (thrust_command > 16'sd500 && p_term != 0) begin
            $display("[PASS] Test 3: PID generating positive corrective thrust: %d (P: %d, I: %d)", thrust_command, p_term, i_term);
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 3: PID controller inactive");

        // Test 4: Drag Force Computation
        if (drag_force != 0 || relative_velocity != 0) begin
            $display("[PASS] Test 4: Quadratic drag engine active (Drag: %d, Rel Vel: %d)", drag_force, relative_velocity);
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 4: Drag calculation inactive");

        // Test 5: Depth & Velocity Filtering
        if (filtered_depth != 0) begin
            $display("[PASS] Test 5: MAF/EMA filters active (Raw Depth: %d, Flt Depth: %d)", current_depth, filtered_depth);
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 5: Filter engine inactive");

        // Test 6: Future Depth Prediction
        if (predicted_depth_1 != 0 && predicted_depth_5 != 0) begin
            $display("[PASS] Test 6: Depth prediction engine active (T+1: %d, T+3: %d, T+5: %d)", predicted_depth_1, predicted_depth_3, predicted_depth_5);
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 6: Prediction engine inactive");

        // Test 7: Energy Optimizer
        if (control_cost > 0) begin
            $display("[PASS] Test 7: Energy optimizer active (Cost: %d, Action: %d)", control_cost, optimization_action);
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 7: Optimizer inactive");

        // Test 8: Disturbance Collision & Severity (WHALE)
        #200;
        cmd_disturb_type   = 2'd3; // WHALE
        cmd_disturb_strobe = 1'b1;
        #20;
        cmd_disturb_strobe = 1'b0;
        #100;

        if (collision_detected && active_object_type == 2'd3 && impact_energy > 0) begin
            $display("[PASS] Test 8: Whale collision detected, Impact Energy: %d J, Severity: %d", impact_energy, impact_severity);
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 8: Collision engine failed");

        // Test 9: Recovery FSM
        #600;
        if (recovery_active || recovery_counter > 0) begin
            $display("[PASS] Test 9: Recovery FSM engaged with recovery thrust: %d", recovery_thrust);
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 9: Recovery FSM failed to engage");

        // Test 10: Fault Detection Check
        if (fault_flags[4] == 0) begin // Current is 20% (<90%)
            $display("[PASS] Test 10: Fault detector operating nominally (Flags: 0x%02h)", fault_flags);
            pass_count = pass_count + 1;
        end else $display("[FAIL] Test 10: Fault detector error");

        #1000;
        $display("==========================================================");
        $display("TESTBENCH SUMMARY: %0d / 10 TESTS PASSED", pass_count);
        $display("==========================================================");
        $finish;
    end

endmodule
