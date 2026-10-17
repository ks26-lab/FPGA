// ============================================================================
// File: traffic_emergency_corridor.v
// Module: traffic_emergency_corridor
// Project: Zynq Z7010 FPGA Smart City Traffic Grid
// Description:
//   4-Node Emergency Preemption Corridor & Pedestrian Walk Logic:
//   Manages emergency vehicle preemption, progressive arterial wave (I1->I2->I3->I4),
//   and pedestrian walk cycle timer.
// ============================================================================

`timescale 1ns / 1ps

module traffic_emergency_corridor (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        tick_enable,

    // Controls
    input  wire        cmd_emg_strobe,
    input  wire [1:0]  cmd_emg_dir,    // 0=N, 1=S, 2=E, 3=W
    input  wire        cmd_ped_strobe,

    // Status outputs
    output reg         emergency_active,
    output reg  [1:0]  emergency_dir,
    output reg         corridor_active,
    output reg  [2:0]  curr_node,
    output reg  [2:0]  next_node,
    output reg  [4:0]  emg_events,

    output reg         ped_walk_active,
    output reg  [6:0]  ped_time_rem,
    output reg  [7:0]  ped_serviced_count
);

    reg [5:0] emg_timer;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            emergency_active   <= 1'b0;
            emergency_dir      <= 2'd0;
            corridor_active    <= 1'b0;
            curr_node          <= 3'd1;
            next_node          <= 3'd2;
            emg_events         <= 5'd0;
            emg_timer          <= 6'd0;
            ped_walk_active    <= 1'b0;
            ped_time_rem       <= 7'd0;
            ped_serviced_count <= 8'd0;
        end else begin
            if (cmd_emg_strobe) begin
                emergency_active <= 1'b1;
                emergency_dir    <= cmd_emg_dir;
                corridor_active  <= 1'b1;
                curr_node        <= 3'd1;
                next_node        <= 3'd2;
                emg_timer        <= 6'd20; // 20-second corridor duration
                emg_events       <= emg_events + 5'd1;
            end

            if (cmd_ped_strobe && !ped_walk_active && !emergency_active) begin
                ped_walk_active    <= 1'b1;
                ped_time_rem       <= 7'd15; // 15-second walk phase
                ped_serviced_count <= ped_serviced_count + 8'd1;
            end

            if (tick_enable) begin
                // Emergency progression
                if (emergency_active) begin
                    if (emg_timer > 0) begin
                        emg_timer <= emg_timer - 6'd1;
                        if (emg_timer == 15) begin curr_node <= 3'd2; next_node <= 3'd3; end
                        if (emg_timer == 10) begin curr_node <= 3'd3; next_node <= 3'd4; end
                        if (emg_timer == 5)  begin curr_node <= 3'd4; next_node <= 3'd1; end
                    end else begin
                        emergency_active <= 1'b0;
                        corridor_active  <= 1'b0;
                    end
                end

                // Pedestrian countdown
                if (ped_walk_active) begin
                    if (ped_time_rem > 0) begin
                        ped_time_rem <= ped_time_rem - 7'd1;
                    end else begin
                        ped_walk_active <= 1'b0;
                    end
                end
            end
        end
    end

endmodule
