// ============================================================================
// File: traffic_core.v
// Module: traffic_core
// Project: Zynq Z7010 FPGA Smart City Traffic Grid
// Description:
//   Master Computational Core coordinating the 7-State FSM, sub-engines,
//   phase transitions with strict mutual exclusion, and telemetry aggregation.
// ============================================================================

`timescale 1ns / 1ps

module traffic_core #(
    parameter CLK_FREQ_HZ = 50_000_000,
    parameter SIMULATION  = 0
)(
    input  wire        clk,
    input  wire        rst_n,

    // Controls
    input  wire        cmd_step,
    input  wire        cmd_reset,
    input  wire        cmd_override_en,
    input  wire        cmd_override_phase,
    input  wire        cmd_auto,
    input  wire        cmd_emg,
    input  wire [1:0]  cmd_emg_dir,
    input  wire        cmd_ped,

    // Config inputs
    input  wire [7:0]  cfg_intersection_id,
    input  wire [7:0]  cfg_queue_ns,
    input  wire [7:0]  cfg_queue_ew,
    input  wire        cfg_queue_we,
    input  wire [15:0] cfg_min_green_s,
    input  wire [15:0] cfg_max_green_s,
    input  wire [15:0] cfg_starvation_limit_s,

    // Status & Telemetry Outputs
    output reg  [3:0]  phase,
    output wire        alert_bit,
    output wire        override_bit,
    output reg  [7:0]  green_rem_s,
    output wire [7:0]  congestion_score,
    output reg  [7:0]  cleared_ns,
    output reg  [7:0]  cleared_ew,
    output reg  [31:0] cycle_count,

    // Sub-engine Telemetry
    output wire [7:0]  queue_north,
    output wire [7:0]  queue_south,
    output wire [7:0]  queue_east,
    output wire [7:0]  queue_west,
    output wire [8:0]  queue_ns_sum,
    output wire [8:0]  queue_ew_sum,
    output wire [9:0]  queue_total,
    output wire [7:0]  calc_green_ns_s,
    output wire [7:0]  calc_green_ew_s,
    output wire [15:0] ns_wait_time_s,
    output wire [15:0] ew_wait_time_s,
    output wire [8:0]  pred_queue_ns,
    output wire [8:0]  pred_queue_ew,
    output wire [2:0]  global_congestion_level,

    output wire        emergency_active,
    output wire [1:0]  emergency_dir,
    output wire        corridor_active,
    output wire [2:0]  curr_node,
    output wire [2:0]  next_node,
    output wire [4:0]  emg_events,
    output wire        ped_walk_active,
    output wire [6:0]  ped_time_rem,
    output wire [7:0]  ped_serviced_count,

    output wire [15:0] fault_flags,
    output wire [15:0] fault_count,
    output wire [15:0] collision_events,
    output wire [15:0] vehicle_occupancy_mask,
    output wire [15:0] brake_required_mask,
    output wire [31:0] veh_pos_north,
    output wire [31:0] veh_pos_south,
    output wire [31:0] veh_pos_east,
    output wire [31:0] veh_pos_west,
    output wire [31:0] veh_speeds,
    output wire        ns_starving,
    output wire        ew_starving
);

    // Phase definitions
    localparam PHASE_NS_GREEN   = 4'd0;
    localparam PHASE_NS_YELLOW  = 4'd1;
    localparam PHASE_ALL_RED    = 4'd2;
    localparam PHASE_EW_GREEN   = 4'd3;
    localparam PHASE_EW_YELLOW  = 4'd4;
    localparam PHASE_PEDESTRIAN = 4'd5;
    localparam PHASE_EMERGENCY  = 4'd6;

    // Simulation tick generation (1 Hz traffic tick)
    localparam CYCLES_PER_TICK = SIMULATION ? 32'd25 : (CLK_FREQ_HZ);
    reg [31:0] tick_counter;
    wire tick_1hz = (tick_counter == (CYCLES_PER_TICK - 1)) || cmd_step;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) tick_counter <= 32'd0;
        else if (tick_1hz) tick_counter <= 32'd0;
        else tick_counter <= tick_counter + 32'd1;
    end

    assign alert_bit    = (congestion_score > 70);
    assign override_bit = cmd_override_en || emergency_active;

    // 1. Queue Engine
    traffic_queue_engine u_queues (
        .clk                     (clk),
        .rst_n                   (rst_n),
        .tick_enable             (tick_1hz),
        .cfg_queue_ns_in         (cfg_queue_ns),
        .cfg_queue_ew_in         (cfg_queue_ew),
        .cfg_queue_we            (cfg_queue_we),
        .current_phase           (phase),
        .q_north                 (queue_north),
        .q_south                 (queue_south),
        .q_east                  (queue_east),
        .q_west                  (queue_west),
        .q_ns_sum                (queue_ns_sum),
        .q_ew_sum                (queue_ew_sum),
        .q_total                 (queue_total),
        .congestion_score        (congestion_score),
        .global_congestion_level (global_congestion_level)
    );

    // 2. Prediction Engine
    traffic_prediction_engine u_pred (
        .clk           (clk),
        .rst_n         (rst_n),
        .tick_enable   (tick_1hz),
        .q_ns_sum      (queue_ns_sum),
        .q_ew_sum      (queue_ew_sum),
        .pred_queue_ns (pred_queue_ns),
        .pred_queue_ew (pred_queue_ew)
    );

    // 3. Green Split Optimizer
    traffic_green_split_optimizer u_opt (
        .clk                 (clk),
        .rst_n               (rst_n),
        .tick_enable         (tick_1hz),
        .q_ns_sum            (queue_ns_sum),
        .q_ew_sum            (queue_ew_sum),
        .min_green_s         (cfg_min_green_s),
        .max_green_s         (cfg_max_green_s),
        .starvation_limit_s  (cfg_starvation_limit_s),
        .current_phase       (phase),
        .calc_green_ns_s     (calc_green_ns_s),
        .calc_green_ew_s     (calc_green_ew_s),
        .ns_wait_time_s      (ns_wait_time_s),
        .ew_wait_time_s      (ew_wait_time_s),
        .ns_starving         (ns_starving),
        .ew_starving         (ew_starving)
    );

    // 4. Emergency Corridor
    traffic_emergency_corridor u_emg (
        .clk                (clk),
        .rst_n              (rst_n),
        .tick_enable        (tick_1hz),
        .cmd_emg_strobe     (cmd_emg),
        .cmd_emg_dir        (cmd_emg_dir),
        .cmd_ped_strobe     (cmd_ped),
        .emergency_active   (emergency_active),
        .emergency_dir      (emergency_dir),
        .corridor_active    (corridor_active),
        .curr_node          (curr_node),
        .next_node          (next_node),
        .emg_events         (emg_events),
        .ped_walk_active    (ped_walk_active),
        .ped_time_rem       (ped_time_rem),
        .ped_serviced_count (ped_serviced_count)
    );

    // 5. Parallel Vehicle Engine
    wire actual_col;
    traffic_parallel_vehicle_engine u_vehicles (
        .clk                       (clk),
        .rst_n                     (rst_n),
        .tick_enable               (tick_1hz),
        .current_phase             (phase),
        .emergency_active          (emergency_active),
        .emergency_dir             (emergency_dir),
        .veh_pos_north             (veh_pos_north),
        .veh_pos_south             (veh_pos_south),
        .veh_pos_east              (veh_pos_east),
        .veh_pos_west              (veh_pos_west),
        .veh_speeds                (veh_speeds),
        .vehicle_occupancy_mask    (vehicle_occupancy_mask),
        .brake_required_mask       (brake_required_mask),
        .actual_collision_detected (actual_col)
    );

    // 6. Fault Detector
    traffic_fault_detector u_fault (
        .clk              (clk),
        .rst_n            (rst_n),
        .current_phase    (phase),
        .q_ns_sum         (queue_ns_sum),
        .q_ew_sum         (queue_ew_sum),
        .ped_walk_active  (ped_walk_active),
        .actual_collision (actual_col),
        .fault_flags      (fault_flags),
        .fault_count      (fault_count),
        .collision_events (collision_events)
    );

    // 7. Master Traffic FSM
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            phase       <= PHASE_NS_GREEN;
            green_rem_s <= 8'd20;
            cycle_count <= 32'd0;
            cleared_ns  <= 8'd0;
            cleared_ew  <= 8'd0;
        end else if (cmd_reset) begin
            phase       <= PHASE_NS_GREEN;
            green_rem_s <= 8'd20;
            cycle_count <= 32'd0;
        end else if (tick_1hz) begin
            cycle_count <= cycle_count + 32'd1;

            if (emergency_active) begin
                phase       <= PHASE_EMERGENCY;
                green_rem_s <= 8'd10;
            end else if (ped_walk_active && phase != PHASE_PEDESTRIAN) begin
                phase       <= PHASE_ALL_RED;
                green_rem_s <= 8'd2;
            end else if (cmd_override_en) begin
                phase       <= cmd_override_phase ? PHASE_EW_GREEN : PHASE_NS_GREEN;
                green_rem_s <= 8'd15;
            end else begin
                if (green_rem_s > 1) begin
                    green_rem_s <= green_rem_s - 8'd1;
                    if (phase == PHASE_NS_GREEN) cleared_ns <= cleared_ns + 8'd1;
                    if (phase == PHASE_EW_GREEN) cleared_ew <= cleared_ew + 8'd1;
                end else begin
                    case (phase)
                        PHASE_NS_GREEN: begin
                            phase       <= PHASE_NS_YELLOW;
                            green_rem_s <= 8'd3;
                        end
                        PHASE_NS_YELLOW: begin
                            phase       <= PHASE_ALL_RED;
                            green_rem_s <= 8'd2;
                        end
                        PHASE_ALL_RED: begin
                            if (ped_walk_active) begin
                                phase       <= PHASE_PEDESTRIAN;
                                green_rem_s <= {1'b0, ped_time_rem};
                            end else begin
                                phase       <= PHASE_EW_GREEN;
                                green_rem_s <= calc_green_ew_s;
                            end
                        end
                        PHASE_EW_GREEN: begin
                            phase       <= PHASE_EW_YELLOW;
                            green_rem_s <= 8'd3;
                        end
                        PHASE_EW_YELLOW: begin
                            phase       <= PHASE_ALL_RED;
                            green_rem_s <= 8'd2;
                        end
                        PHASE_PEDESTRIAN: begin
                            phase       <= PHASE_ALL_RED;
                            green_rem_s <= 8'd2;
                        end
                        PHASE_EMERGENCY: begin
                            phase       <= PHASE_ALL_RED;
                            green_rem_s <= 8'd2;
                        end
                        default: begin
                            phase       <= PHASE_NS_GREEN;
                            green_rem_s <= calc_green_ns_s;
                        end
                    endcase
                end
            end
        end
    end

endmodule
