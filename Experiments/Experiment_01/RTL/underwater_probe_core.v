// ============================================================================
// File: underwater_probe_core.v
// Module: underwater_probe_core
// Project: Zynq Z7010 FPGA Underwater Dynamic Probe Subsystem (Upgraded Engine)
// Description:
//   Top-level motion and physics core coordinating parallel FPGA processing blocks:
//     1. underwater_physics_engine
//     2. underwater_drag_engine
//     3. underwater_pid_controller
//     4. underwater_filter_engine
//     5. underwater_collision_engine
//     6. underwater_prediction_engine
//     7. underwater_energy_optimizer
//     8. underwater_fault_detector
//     9. 7-State Recovery & Trajectory FSM
// ============================================================================

`timescale 1ns / 1ps

module underwater_probe_core #(
    parameter CLK_FREQ_HZ = 50_000_000,
    parameter SIMULATION  = 0
)(
    input  wire        clk,
    input  wire        rst_n,

    // Command Strobes
    input  wire        cmd_start,
    input  wire        cmd_stop,
    input  wire        cmd_reset,

    // Runtime Parameters from AXI Registers
    input  wire signed [15:0] cfg_set_depth,        // Preset current depth (0.1m)
    input  wire               cfg_set_depth_we,     // Write strobe for current depth
    input  wire signed [15:0] cfg_target_depth,     // Target depth (0.1m)
    input  wire signed [7:0]  cfg_current_strength, // Current (-100% to +100%)

    // Disturbance Trigger
    input  wire               cmd_disturb_strobe,
    input  wire [1:0]         cmd_disturb_type,     // 1=FISH, 2=GARBAGE, 3=WHALE

    // Telemetry & Authoritative State Outputs to AXI Registers (Legacy + Upgraded)
    output reg  [3:0]         probe_state,
    output reg  signed [15:0] current_depth,
    output reg  signed [15:0] target_depth,
    output reg  signed [7:0]  displacement_x,
    output reg  signed [7:0]  probe_velocity_z,
    output reg                collision_detected,
    output reg                recovery_active,
    output reg                target_reached,
    output reg  [1:0]         active_object_type,
    output reg  [15:0]        collision_counter,
    output reg  [31:0]        sim_cycle_counter,

    // Upgraded Physics & Advanced Telemetry Outputs
    output wire signed [15:0] depth_error_out,
    output wire signed [15:0] filtered_depth_out,
    output wire signed [7:0]  filtered_velocity_out,
    output wire signed [15:0] drag_force_out,
    output wire signed [15:0] relative_velocity_out,
    output wire signed [15:0] p_term_out,
    output wire signed [15:0] i_term_out,
    output wire signed [15:0] d_term_out,
    output wire signed [15:0] control_output_out,
    output wire signed [15:0] thrust_command_out,
    output wire signed [15:0] thrust_delta_out,
    output wire [15:0]        impact_energy_out,
    output wire [2:0]         impact_severity_out,
    output reg  signed [15:0] recovery_thrust_out,
    output reg  signed [7:0]  post_collision_velocity_out,
    output wire signed [15:0] predicted_depth_1_out,
    output wire signed [15:0] predicted_depth_3_out,
    output wire signed [15:0] predicted_depth_5_out,
    output wire [15:0]        control_cost_out,
    output wire [1:0]         optimization_action_out,
    output wire [7:0]         fault_flags_out,
    output reg  [31:0]        physics_update_count,
    output reg  [15:0]        recovery_counter
);

    // ------------------------------------------------------------------------
    // FSM State Encoding (Exact Backward-Compatible 7-State FSM)
    // ------------------------------------------------------------------------
    localparam STATE_IDLE               = 4'd0;
    localparam STATE_MOVING_TO_TARGET   = 4'd1;
    localparam STATE_DISTURBED          = 4'd2;
    localparam STATE_COLLISION_DETECTED = 4'd3;
    localparam STATE_DISPLACEMENT       = 4'd4;
    localparam STATE_RECOVERY           = 4'd5;
    localparam STATE_TARGET_REACHED     = 4'd6;

    localparam DISTURB_NONE    = 2'd0;
    localparam DISTURB_FISH    = 2'd1;
    localparam DISTURB_GARBAGE = 2'd2;
    localparam DISTURB_WHALE   = 2'd3;

    // ------------------------------------------------------------------------
    // Simulation Update Tick Generator (10 Hz update rate in hardware)
    // ------------------------------------------------------------------------
    localparam CYCLES_PER_TICK = SIMULATION ? 32'd25 : (CLK_FREQ_HZ / 10);
    reg [31:0] tick_div_counter;
    wire       update_tick = (tick_div_counter == (CYCLES_PER_TICK - 1));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tick_div_counter <= 32'd0;
        end else if (update_tick) begin
            tick_div_counter <= 32'd0;
        end else begin
            tick_div_counter <= tick_div_counter + 32'd1;
        end
    end

    // ------------------------------------------------------------------------
    // Interconnect Wires Between Processing Blocks
    // ------------------------------------------------------------------------
    wire signed [15:0] pe_depth_error;
    wire signed [7:0]  pe_current_effect;
    wire signed [7:0]  pe_raw_velocity;
    wire signed [15:0] pe_raw_depth;
    wire signed [15:0] pe_depth_next;

    wire signed [15:0] de_rel_vel;
    wire signed [15:0] de_drag_force;

    wire signed [15:0] pid_p;
    wire signed [15:0] pid_i;
    wire signed [15:0] pid_d;
    wire signed [15:0] pid_ctrl;
    wire signed [15:0] pid_thrust;
    wire signed [15:0] pid_thrust_delta;
    wire               pid_int_sat;

    wire signed [15:0] flt_depth;
    wire signed [7:0]  flt_vel;

    wire               col_flag;
    wire [15:0]        col_energy;
    wire [2:0]         col_sev;
    wire [1:0]         col_obj;

    wire signed [15:0] pred_d1;
    wire signed [15:0] pred_d3;
    wire signed [15:0] pred_d5;

    wire [15:0]        opt_cost;
    wire [1:0]         opt_action;
    wire [15:0]        opt_energy;

    wire [7:0]         fault_reg;

    // Export internal signals to outputs
    assign depth_error_out             = pe_depth_error;
    assign filtered_depth_out          = flt_depth;
    assign filtered_velocity_out       = flt_vel;
    assign drag_force_out              = de_drag_force;
    assign relative_velocity_out       = de_rel_vel;
    assign p_term_out                  = pid_p;
    assign i_term_out                  = pid_i;
    assign d_term_out                  = pid_d;
    assign control_output_out          = pid_ctrl;
    assign thrust_command_out          = pid_thrust;
    assign thrust_delta_out            = pid_thrust_delta;
    assign impact_energy_out           = col_energy;
    assign impact_severity_out         = col_sev;
    assign predicted_depth_1_out       = pred_d1;
    assign predicted_depth_3_out       = pred_d3;
    assign predicted_depth_5_out       = pred_d5;
    assign control_cost_out            = opt_cost;
    assign optimization_action_out     = opt_action;
    assign fault_flags_out             = fault_reg;

    // ------------------------------------------------------------------------
    // 1. Parallel Physics Engine Instance
    // ------------------------------------------------------------------------
    underwater_physics_engine u_physics (
        .clk                  (clk),
        .rst_n                (rst_n),
        .update_tick          (update_tick),
        .enable               (probe_state != STATE_IDLE),
        .current_depth_in     (current_depth),
        .target_depth_in      (target_depth),
        .cfg_current_strength (cfg_current_strength),
        .thrust_force         (pid_thrust),
        .drag_force           (de_drag_force),
        .recovery_thrust      (recovery_thrust_out),
        .recovery_active      (recovery_active),
        .depth_error          (pe_depth_error),
        .current_effect       (pe_current_effect),
        .raw_velocity         (pe_raw_velocity),
        .raw_depth            (pe_raw_depth),
        .depth_next           (pe_depth_next)
    );

    // ------------------------------------------------------------------------
    // 2. Parallel Drag Engine Instance
    // ------------------------------------------------------------------------
    underwater_drag_engine u_drag (
        .clk               (clk),
        .rst_n             (rst_n),
        .probe_velocity    (pe_raw_velocity),
        .current_velocity  (pe_current_effect),
        .k_drag_coeff      (8'd4), // 0.25 scaling
        .relative_velocity (de_rel_vel),
        .drag_force        (de_drag_force)
    );

    // ------------------------------------------------------------------------
    // 3. Parallel PID Controller Instance
    // ------------------------------------------------------------------------
    underwater_pid_controller u_pid (
        .clk                  (clk),
        .rst_n                (rst_n),
        .update_tick          (update_tick),
        .enable               (probe_state != STATE_IDLE),
        .depth_error          (pe_depth_error),
        .cfg_current_strength (cfg_current_strength),
        .cfg_kp               (8'd20), // 1.25
        .cfg_ki               (8'd4),  // 0.25
        .cfg_kd               (8'd12), // 0.75
        .p_term               (pid_p),
        .i_term               (pid_i),
        .d_term               (pid_d),
        .control_output       (pid_ctrl),
        .thrust_command       (pid_thrust),
        .thrust_delta         (pid_thrust_delta),
        .integral_saturated   (pid_int_sat)
    );

    // ------------------------------------------------------------------------
    // 4. Parallel Filter Engine Instance
    // ------------------------------------------------------------------------
    underwater_filter_engine u_filter (
        .clk               (clk),
        .rst_n             (rst_n),
        .update_tick       (update_tick),
        .raw_depth         (current_depth),
        .raw_velocity      (probe_velocity_z),
        .filtered_depth    (flt_depth),
        .filtered_velocity (flt_vel)
    );

    // ------------------------------------------------------------------------
    // 5. Parallel Collision Engine Instance
    // ------------------------------------------------------------------------
    underwater_collision_engine u_collision (
        .clk                (clk),
        .rst_n              (rst_n),
        .cmd_disturb_strobe (cmd_disturb_strobe),
        .cmd_disturb_type   (cmd_disturb_type),
        .relative_velocity  (de_rel_vel),
        .collision_detected (col_flag),
        .impact_energy      (col_energy),
        .impact_severity    (col_sev),
        .active_object_type (col_obj)
    );

    // ------------------------------------------------------------------------
    // 6. Parallel Prediction Engine Instance
    // ------------------------------------------------------------------------
    underwater_prediction_engine u_prediction (
        .clk               (clk),
        .rst_n             (rst_n),
        .current_depth     (current_depth),
        .current_velocity  (probe_velocity_z),
        .thrust_force      (pid_thrust),
        .drag_force        (de_drag_force),
        .predicted_depth_1 (pred_d1),
        .predicted_depth_3 (pred_d3),
        .predicted_depth_5 (pred_d5)
    );

    // ------------------------------------------------------------------------
    // 7. Parallel Energy Optimizer Instance
    // ------------------------------------------------------------------------
    underwater_energy_optimizer u_optimizer (
        .clk                 (clk),
        .rst_n               (rst_n),
        .depth_error         (pe_depth_error),
        .velocity            (probe_velocity_z),
        .thrust_command      (pid_thrust),
        .control_cost        (opt_cost),
        .optimization_action (opt_action),
        .estimated_energy    (opt_energy)
    );

    // ------------------------------------------------------------------------
    // 8. Parallel Fault Detector Instance
    // ------------------------------------------------------------------------
    underwater_fault_detector u_fault (
        .clk                (clk),
        .rst_n              (rst_n),
        .current_depth      (current_depth),
        .depth_error        (pe_depth_error),
        .velocity           (probe_velocity_z),
        .thrust_command     (pid_thrust),
        .current_strength   (cfg_current_strength),
        .collision_detected (collision_detected),
        .integral_saturated (pid_int_sat),
        .fault_flags        (fault_reg)
    );

    // ------------------------------------------------------------------------
    // 9. Master Sequential Trajectory & Recovery FSM
    // ------------------------------------------------------------------------
    reg [7:0] recovery_step_counter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            probe_state                 <= STATE_IDLE;
            current_depth               <= 16'sd500;
            target_depth                <= 16'sd800;
            displacement_x              <= 8'sd0;
            probe_velocity_z            <= 8'sd0;
            collision_detected          <= 1'b0;
            recovery_active             <= 1'b0;
            target_reached              <= 1'b0;
            active_object_type          <= DISTURB_NONE;
            collision_counter           <= 16'd0;
            sim_cycle_counter           <= 32'd0;
            physics_update_count        <= 32'd0;
            recovery_counter            <= 16'd0;
            recovery_step_counter       <= 8'd0;
            recovery_thrust_out         <= 16'sd500;
            post_collision_velocity_out <= 8'sd0;
        end else if (cmd_reset) begin
            probe_state                 <= STATE_IDLE;
            current_depth               <= 16'sd500;
            target_depth                <= 16'sd800;
            displacement_x              <= 8'sd0;
            probe_velocity_z            <= 8'sd0;
            collision_detected          <= 1'b0;
            recovery_active             <= 1'b0;
            target_reached              <= 1'b0;
            active_object_type          <= DISTURB_NONE;
            collision_counter           <= 16'd0;
            recovery_step_counter       <= 8'd0;
            recovery_thrust_out         <= 16'sd500;
            post_collision_velocity_out <= 8'sd0;
        end else begin
            // Dynamic parameter configuration override
            if (cfg_set_depth_we) begin
                current_depth <= cfg_set_depth;
            end
            target_depth <= cfg_target_depth;

            // Disturbance Trigger
            if (cmd_disturb_strobe && (probe_state != STATE_IDLE)) begin
                active_object_type          <= cmd_disturb_type;
                collision_detected          <= 1'b1;
                collision_counter           <= collision_counter + 16'd1;
                post_collision_velocity_out <= probe_velocity_z;
                probe_state                 <= STATE_COLLISION_DETECTED;
            end

            // Main Sequential Control Loop on Hardware Update Tick
            if (update_tick) begin
                sim_cycle_counter    <= sim_cycle_counter + 32'd1;
                physics_update_count <= physics_update_count + 32'd1;

                case (probe_state)
                    STATE_IDLE: begin
                        probe_velocity_z   <= 8'sd0;
                        collision_detected <= 1'b0;
                        recovery_active    <= 1'b0;
                        target_reached     <= 1'b0;
                        displacement_x     <= 8'sd0;
                        if (cmd_start) begin
                            probe_state <= STATE_MOVING_TO_TARGET;
                        end
                    end

                    STATE_MOVING_TO_TARGET: begin
                        if (cmd_stop) begin
                            probe_state <= STATE_IDLE;
                        end else begin
                            collision_detected <= 1'b0;
                            recovery_active    <= 1'b0;

                            // Update depth & velocity from physics engine
                            current_depth    <= pe_depth_next;
                            probe_velocity_z <= pe_raw_velocity;

                            // Drift integration
                            displacement_x <= displacement_x + (cfg_current_strength >>> 4);

                            // Target arrival condition (|error| <= 5 units / 0.5m)
                            if (abs_val(pe_depth_error) <= 16'sd5) begin
                                target_reached <= 1'b1;
                                probe_state    <= STATE_TARGET_REACHED;
                            end else begin
                                target_reached <= 1'b0;
                            end
                        end
                    end

                    STATE_COLLISION_DETECTED: begin
                        case (active_object_type)
                            DISTURB_FISH: begin
                                displacement_x      <= 8'sd15;
                                current_depth       <= current_depth - 16'sd8;
                                recovery_thrust_out <= 16'sd580;
                            end
                            DISTURB_GARBAGE: begin
                                displacement_x      <= -8'sd28;
                                current_depth       <= current_depth + 16'sd14;
                                recovery_thrust_out <= 16'sd420;
                            end
                            DISTURB_WHALE: begin
                                displacement_x      <= 8'sd55;
                                current_depth       <= current_depth - 16'sd32;
                                recovery_thrust_out <= 16'sd750;
                            end
                            default: begin
                                displacement_x      <= 8'sd10;
                                recovery_thrust_out <= 16'sd500;
                            end
                        endcase
                        recovery_step_counter <= 8'd8;
                        probe_state           <= STATE_DISPLACEMENT;
                    end

                    STATE_DISPLACEMENT: begin
                        collision_detected <= 1'b0;
                        recovery_active    <= 1'b1;
                        recovery_counter   <= recovery_counter + 16'd1;
                        probe_state        <= STATE_RECOVERY;
                    end

                    STATE_RECOVERY: begin
                        recovery_active <= 1'b1;

                        // Lateral centering
                        if (displacement_x > 8'sd4) begin
                            displacement_x <= displacement_x - 8'sd4;
                        end else if (displacement_x < -8'sd4) begin
                            displacement_x <= displacement_x + 8'sd4;
                        end else begin
                            displacement_x <= 8'sd0;
                        end

                        // Apply restorative recovery physics
                        current_depth    <= pe_depth_next;
                        probe_velocity_z <= pe_raw_velocity;

                        if (recovery_step_counter > 8'd1) begin
                            recovery_step_counter <= recovery_step_counter - 8'd1;
                        end else begin
                            recovery_step_counter <= 8'd0;
                            recovery_active       <= 1'b0;
                            active_object_type    <= DISTURB_NONE;
                            recovery_thrust_out   <= 16'sd500;
                            probe_state           <= STATE_MOVING_TO_TARGET;
                        end
                    end

                    STATE_TARGET_REACHED: begin
                        target_reached <= 1'b1;
                        if (abs_val(pe_depth_error) > 16'sd8) begin
                            target_reached <= 1'b0;
                            probe_state    <= STATE_MOVING_TO_TARGET;
                        end else begin
                            // Maintain depth with restorative buoyancy
                            current_depth    <= pe_depth_next;
                            probe_velocity_z <= pe_raw_velocity;
                        end
                    end

                    default: probe_state <= STATE_IDLE;
                endcase
            end
        end
    end

    function signed [15:0] abs_val(input signed [15:0] val);
        abs_val = (val < 0) ? -val : val;
    endfunction

endmodule
