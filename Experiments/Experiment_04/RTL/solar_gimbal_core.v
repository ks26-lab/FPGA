`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_gimbal_core
// Description:
//   Master mathematical core coordinating 3D vector conversions, incident angle,
//   photovoltaic power generation, circular tracking, and safety fault detection.
//////////////////////////////////////////////////////////////////////////////////

module solar_gimbal_core (
    input  wire        clk,
    input  wire        rst_n,

    // Control and configuration inputs
    input  wire [31:0] control_reg,
    input  wire [31:0] sun_pos_in,
    input  wire        sun_pos_we,
    input  wire [31:0] panel_pos_in,
    input  wire        panel_pos_we,
    input  wire [31:0] limits_in,
    input  wire        limits_we,

    // Telemetry outputs to AXI Slave
    output wire [31:0] sun_pos_out,
    output wire [31:0] panel_pos_out,
    output wire [31:0] status_out,
    output wire [31:0] error_out,
    output wire [31:0] actuators_out,
    output reg  [31:0] cycles_out,
    output wire signed [31:0] sun_vec_x,
    output wire signed [31:0] sun_vec_y,
    output wire signed [31:0] sun_vec_z,
    output wire signed [31:0] panel_norm_x,
    output wire signed [31:0] panel_norm_y,
    output wire signed [31:0] panel_norm_z,
    output wire signed [31:0] dot_product,
    output wire [31:0] incident_angle_out,
    output wire [31:0] estimated_power_out,
    output wire [31:0] filtered_sun_out,
    output wire [31:0] predicted_sun_out,
    output wire [31:0] angular_velocity_out,
    output wire [31:0] limits_out,
    output wire [15:0] fault_flags_out,
    output wire [31:0] vector_cycles_out,
    output reg  [31:0] update_counter_out,
    output wire [31:0] panel0_data_out,
    output wire [31:0] panel1_data_out,
    output wire [31:0] panel2_data_out,
    output wire [31:0] panel3_data_out,
    output wire [31:0] total_array_power_out,
    output wire [31:0] panels_active_mask_out,
    output wire [31:0] tracking_quality_out,
    output wire [31:0] hardware_version_out
);

    // Hardware Version Tag: 'SOLAR-7010'
    assign hardware_version_out = 32'h501A7010;
    assign panels_active_mask_out = 32'h0000000F;
    assign vector_cycles_out = 32'd18;
    assign angular_velocity_out = 32'd0;

    // Internal state registers
    reg [15:0] sun_azimuth;
    reg [15:0] sun_elevation;
    reg [15:0] az_deadband;
    reg [15:0] el_deadband;

    wire [15:0] panel_azimuth;
    wire [15:0] panel_elevation;
    wire signed [15:0] az_error;
    wire signed [15:0] el_error;
    wire signed [15:0] actuator_az;
    wire signed [15:0] actuator_el;
    wire [31:0] status_word;

    // Deadbands and inputs
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sun_azimuth   <= 16'd1800; // 180.0 deg
            sun_elevation <= 16'd450;  // 45.0 deg
            az_deadband   <= 16'd5;    // 0.5 deg
            el_deadband   <= 16'd5;    // 0.5 deg
        end else begin
            if (sun_pos_we) begin
                sun_azimuth   <= sun_pos_in[15:0];
                sun_elevation <= sun_pos_in[31:16];
            end
            if (limits_we) begin
                az_deadband   <= limits_in[15:0];
                el_deadband   <= limits_in[31:16];
            end
        end
    end

    assign sun_pos_out   = {sun_elevation, sun_azimuth};
    assign panel_pos_out = {panel_elevation, panel_azimuth};
    assign limits_out    = {el_deadband, az_deadband};
    assign error_out     = {el_error, az_error};
    assign actuators_out = {actuator_el, actuator_az};
    assign status_out    = status_word;

    assign filtered_sun_out  = sun_pos_out;
    assign predicted_sun_out = sun_pos_out;

    // Sub-engine instantiations
    wire fault_active;
    wire [15:0] fault_flags;
    wire [15:0] est_pwr;
    wire [15:0] cos_inc;
    wire [15:0] inc_ang;

    assign fault_flags_out = fault_flags;
    assign incident_angle_out = {cos_inc, inc_ang};
    assign estimated_power_out = {16'd225, est_pwr}; // 22.5% efficiency

    // Control decoding
    wire calc_strobe = control_reg[0];
    wire track_en    = control_reg[2] | control_reg[0];

    // Stepping timer for closed loop tracking (e.g. step every 1024 cycles)
    reg [9:0] step_div;
    wire step_tick = (step_div == 10'd1023);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            step_div   <= 10'd0;
            cycles_out <= 32'd0;
        end else begin
            cycles_out <= cycles_out + 1'b1;
            step_div   <= step_div + 1'b1;
        end
    end

    // 1. Vector Engine
    wire vec_done;
    reg  vec_start;
    solar_vector_engine u_vec (
        .clk(clk),
        .rst_n(rst_n),
        .start(vec_start),
        .sun_azimuth(sun_azimuth),
        .sun_elevation(sun_elevation),
        .panel_azimuth(panel_azimuth),
        .panel_elevation(panel_elevation),
        .sun_vec_x(sun_vec_x),
        .sun_vec_y(sun_vec_y),
        .sun_vec_z(sun_vec_z),
        .panel_norm_x(panel_norm_x),
        .panel_norm_y(panel_norm_y),
        .panel_norm_z(panel_norm_z),
        .done(vec_done)
    );

    // 2. Incident Angle Engine
    wire inc_done;
    solar_incident_angle_engine u_inc (
        .clk(clk),
        .rst_n(rst_n),
        .start(vec_done),
        .sx(sun_vec_x),
        .sy(sun_vec_y),
        .sz(sun_vec_z),
        .nx(panel_norm_x),
        .ny(panel_norm_y),
        .nz(panel_norm_z),
        .dot_product(dot_product),
        .cos_incidence(cos_inc),
        .incident_angle(inc_ang),
        .done(inc_done)
    );

    // 3. Power Engine
    wire pwr_done;
    solar_power_engine u_pwr (
        .clk(clk),
        .rst_n(rst_n),
        .start(inc_done),
        .dot_product(dot_product),
        .incident_angle(inc_ang),
        .estimated_power(est_pwr),
        .panel0_data(panel0_data_out),
        .panel1_data(panel1_data_out),
        .panel2_data(panel2_data_out),
        .panel3_data(panel3_data_out),
        .total_array_power(total_array_power_out),
        .tracking_quality(tracking_quality_out),
        .done(pwr_done)
    );

    // 4. Tracking Controller
    solar_tracking_controller u_track (
        .clk(clk),
        .rst_n(rst_n),
        .track_en(track_en),
        .fault_active(fault_active),
        .sun_azimuth(sun_azimuth),
        .sun_elevation(sun_elevation),
        .az_deadband(az_deadband),
        .el_deadband(el_deadband),
        .step_tick(step_tick),
        .panel_azimuth(panel_azimuth),
        .panel_elevation(panel_elevation),
        .az_error(az_error),
        .el_error(el_error),
        .actuator_az(actuator_az),
        .actuator_el(actuator_el),
        .status_word(status_word)
    );

    // 5. Fault Detector
    solar_fault_detector u_fault (
        .clk(clk),
        .rst_n(rst_n),
        .sun_elevation(sun_elevation),
        .panel_azimuth(panel_azimuth),
        .panel_elevation(panel_elevation),
        .az_error(az_error),
        .el_error(el_error),
        .estimated_power(est_pwr),
        .fault_flags(fault_flags),
        .fault_active(fault_active)
    );

    // Periodic or on-demand computation trigger
    reg [4:0] trig_div;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            vec_start          <= 1'b0;
            trig_div           <= 5'd0;
            update_counter_out <= 32'd0;
        end else begin
            trig_div <= trig_div + 1'b1;
            if (calc_strobe || (track_en && trig_div == 5'd31)) begin
                vec_start <= 1'b1;
            end else begin
                vec_start <= 1'b0;
            end

            if (pwr_done) begin
                update_counter_out <= update_counter_out + 1'b1;
            end
        end
    end

endmodule
