// ============================================================================
// File: traffic_top.v
// Module: traffic_top
// Project: Zynq Z7010 FPGA Smart City Traffic Grid
// Description:
//   Top-level module for Experiment 02 on EDGE ZYNQ Z7010 SoC.
//   Binds traffic_axi_slave to traffic_core and drives board diagnostic LEDs.
// ============================================================================

`timescale 1ns / 1ps

module traffic_top #(
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

    // Physical Diagnostic LEDs
    output wire [3:0]  board_leds,
    output wire        ns_green,
    output wire        ns_yellow,
    output wire        ns_red,
    output wire        ew_green,
    output wire        ew_yellow,
    output wire        ew_red
);

    wire        cmd_step;
    wire        cmd_reset;
    wire        cmd_override_en;
    wire        cmd_override_phase;
    wire        cmd_auto;
    wire        cmd_emg;
    wire [1:0]  cmd_emg_dir;
    wire        cmd_ped;

    wire [7:0]  cfg_intersection_id;
    wire [7:0]  cfg_queue_ns;
    wire [7:0]  cfg_queue_ew;
    wire        cfg_queue_we;
    wire [15:0] cfg_min_green_s;
    wire [15:0] cfg_max_green_s;
    wire [15:0] cfg_starvation_limit_s;

    wire [3:0]  phase;
    wire        alert_bit;
    wire        override_bit;
    wire [7:0]  green_rem_s;
    wire [7:0]  congestion_score;
    wire [7:0]  cleared_ns;
    wire [7:0]  cleared_ew;
    wire [31:0] cycle_count;

    wire [7:0]  queue_north;
    wire [7:0]  queue_south;
    wire [7:0]  queue_east;
    wire [7:0]  queue_west;
    wire [8:0]  queue_ns_sum;
    wire [8:0]  queue_ew_sum;
    wire [9:0]  queue_total;
    wire [7:0]  calc_green_ns_s;
    wire [7:0]  calc_green_ew_s;
    wire [15:0] ns_wait_time_s;
    wire [15:0] ew_wait_time_s;
    wire [8:0]  pred_queue_ns;
    wire [8:0]  pred_queue_ew;
    wire [2:0]  global_congestion_level;

    wire        emergency_active;
    wire [1:0]  emergency_dir;
    wire        corridor_active;
    wire [2:0]  curr_node;
    wire [2:0]  next_node;
    wire [4:0]  emg_events;
    wire        ped_walk_active;
    wire [6:0]  ped_time_rem;
    wire [7:0]  ped_serviced_count;

    wire [15:0] fault_flags;
    wire [15:0] fault_count;
    wire [15:0] collision_events;
    wire [15:0] vehicle_occupancy_mask;
    wire [15:0] brake_required_mask;
    wire [31:0] veh_pos_north;
    wire [31:0] veh_pos_south;
    wire [31:0] veh_pos_east;
    wire [31:0] veh_pos_west;
    wire [31:0] veh_speeds;
    wire        ns_starving;
    wire        ew_starving;

    // Board LED mapping
    assign board_leds[3:0] = phase;

    // Traffic signal states
    assign ns_green  = (phase == 4'd0);
    assign ns_yellow = (phase == 4'd1);
    assign ns_red    = (phase != 4'd0 && phase != 4'd1);

    assign ew_green  = (phase == 4'd3);
    assign ew_yellow = (phase == 4'd4);
    assign ew_red    = (phase != 4'd3 && phase != 4'd4);

    // AXI4-Lite Slave Instance
    traffic_axi_slave #(
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

        .cmd_step                 (cmd_step),
        .cmd_reset                (cmd_reset),
        .cmd_override_en          (cmd_override_en),
        .cmd_override_phase       (cmd_override_phase),
        .cmd_auto                 (cmd_auto),
        .cmd_emg                  (cmd_emg),
        .cmd_emg_dir              (cmd_emg_dir),
        .cmd_ped                  (cmd_ped),

        .cfg_intersection_id      (cfg_intersection_id),
        .cfg_queue_ns             (cfg_queue_ns),
        .cfg_queue_ew             (cfg_queue_ew),
        .cfg_queue_we             (cfg_queue_we),
        .cfg_min_green_s          (cfg_min_green_s),
        .cfg_max_green_s          (cfg_max_green_s),
        .cfg_starvation_limit_s   (cfg_starvation_limit_s),

        .phase                    (phase),
        .alert_bit                (alert_bit),
        .override_bit             (override_bit),
        .green_rem_s              (green_rem_s),
        .congestion_score         (congestion_score),
        .cleared_ns               (cleared_ns),
        .cleared_ew               (cleared_ew),
        .cycle_count              (cycle_count),

        .queue_north              (queue_north),
        .queue_south              (queue_south),
        .queue_east               (queue_east),
        .queue_west               (queue_west),
        .queue_ns_sum             (queue_ns_sum),
        .queue_ew_sum             (queue_ew_sum),
        .queue_total              (queue_total),
        .calc_green_ns_s          (calc_green_ns_s),
        .calc_green_ew_s          (calc_green_ew_s),
        .ns_wait_time_s           (ns_wait_time_s),
        .ew_wait_time_s           (ew_wait_time_s),
        .pred_queue_ns            (pred_queue_ns),
        .pred_queue_ew            (pred_queue_ew),
        .global_congestion_level  (global_congestion_level),

        .emergency_active         (emergency_active),
        .emergency_dir            (emergency_dir),
        .corridor_active          (corridor_active),
        .curr_node                (curr_node),
        .next_node                (next_node),
        .emg_events               (emg_events),
        .ped_walk_active          (ped_walk_active),
        .ped_time_rem             (ped_time_rem),
        .ped_serviced_count       (ped_serviced_count),

        .fault_flags              (fault_flags),
        .fault_count              (fault_count),
        .collision_events         (collision_events),
        .vehicle_occupancy_mask   (vehicle_occupancy_mask),
        .brake_required_mask      (brake_required_mask),
        .veh_pos_north            (veh_pos_north),
        .veh_pos_south            (veh_pos_south),
        .veh_pos_east             (veh_pos_east),
        .veh_pos_west             (veh_pos_west),
        .veh_speeds               (veh_speeds),
        .ns_starving              (ns_starving),
        .ew_starving              (ew_starving)
    );

    // Master Traffic Core Instance
    traffic_core #(
        .CLK_FREQ_HZ (CLK_FREQ_HZ),
        .SIMULATION  (SIMULATION)
    ) u_core (
        .clk                     (s_axi_aclk),
        .rst_n                   (s_axi_aresetn),

        .cmd_step                (cmd_step),
        .cmd_reset               (cmd_reset),
        .cmd_override_en         (cmd_override_en),
        .cmd_override_phase      (cmd_override_phase),
        .cmd_auto                (cmd_auto),
        .cmd_emg                 (cmd_emg),
        .cmd_emg_dir             (cmd_emg_dir),
        .cmd_ped                 (cmd_ped),

        .cfg_intersection_id     (cfg_intersection_id),
        .cfg_queue_ns            (cfg_queue_ns),
        .cfg_queue_ew            (cfg_queue_ew),
        .cfg_queue_we            (cfg_queue_we),
        .cfg_min_green_s         (cfg_min_green_s),
        .cfg_max_green_s         (cfg_max_green_s),
        .cfg_starvation_limit_s  (cfg_starvation_limit_s),

        .phase                   (phase),
        .alert_bit               (alert_bit),
        .override_bit            (override_bit),
        .green_rem_s             (green_rem_s),
        .congestion_score        (congestion_score),
        .cleared_ns              (cleared_ns),
        .cleared_ew              (cleared_ew),
        .cycle_count             (cycle_count),

        .queue_north             (queue_north),
        .queue_south             (queue_south),
        .queue_east              (queue_east),
        .queue_west              (queue_west),
        .queue_ns_sum            (queue_ns_sum),
        .queue_ew_sum            (queue_ew_sum),
        .queue_total             (queue_total),
        .calc_green_ns_s         (calc_green_ns_s),
        .calc_green_ew_s         (calc_green_ew_s),
        .ns_wait_time_s          (ns_wait_time_s),
        .ew_wait_time_s          (ew_wait_time_s),
        .pred_queue_ns           (pred_queue_ns),
        .pred_queue_ew           (pred_queue_ew),
        .global_congestion_level (global_congestion_level),

        .emergency_active        (emergency_active),
        .emergency_dir           (emergency_dir),
        .corridor_active         (corridor_active),
        .curr_node               (curr_node),
        .next_node               (next_node),
        .emg_events              (emg_events),
        .ped_walk_active         (ped_walk_active),
        .ped_time_rem            (ped_time_rem),
        .ped_serviced_count      (ped_serviced_count),

        .fault_flags             (fault_flags),
        .fault_count             (fault_count),
        .collision_events        (collision_events),
        .vehicle_occupancy_mask  (vehicle_occupancy_mask),
        .brake_required_mask     (brake_required_mask),
        .veh_pos_north           (veh_pos_north),
        .veh_pos_south           (veh_pos_south),
        .veh_pos_east            (veh_pos_east),
        .veh_pos_west            (veh_pos_west),
        .veh_speeds              (veh_speeds),
        .ns_starving             (ns_starving),
        .ew_starving             (ew_starving)
    );

endmodule
