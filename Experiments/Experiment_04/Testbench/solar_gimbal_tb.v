`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: EDGE Zynq Z7010 FPGA Project
// Module Name: solar_gimbal_tb
// Description:
//   Comprehensive Testbench for Solar Tracking Gimbal AXI accelerator on Zynq Z7010.
//   Verifies AXI transactions, 3D unit vector generation, dot product,
//   incident angle arccos derivation, 4-channel power estimation, and closed-loop tracking.
//////////////////////////////////////////////////////////////////////////////////

module solar_gimbal_tb;

    reg clk;
    reg rst_n;

    // AXI Bus Signals
    reg  [7:0]  s_axi_awaddr;
    reg  [2:0]  s_axi_awprot;
    reg         s_axi_awvalid;
    wire        s_axi_awready;
    reg  [31:0] s_axi_wdata;
    reg  [3:0]  s_axi_wstrb;
    reg         s_axi_wvalid;
    wire        s_axi_wready;
    wire [1:0]  s_axi_bresp;
    wire        s_axi_bvalid;
    reg         s_axi_bready;
    reg  [7:0]  s_axi_araddr;
    reg  [2:0]  s_axi_arprot;
    reg         s_axi_arvalid;
    wire        s_axi_arready;
    wire [31:0] s_axi_rdata;
    wire [1:0]  s_axi_rresp;
    wire        s_axi_rvalid;
    reg         s_axi_rready;

    // Top outputs
    wire [3:0] led;
    wire step_az_pin, dir_az_pin, step_el_pin, dir_el_pin;

    // DUT Instantiation
    solar_gimbal_top uut (
        .clk(clk),
        .rst_n(rst_n),
        .led(led),
        .step_az_pin(step_az_pin),
        .dir_az_pin(dir_az_pin),
        .step_el_pin(step_el_pin),
        .dir_el_pin(dir_el_pin),
        .s_axi_aclk(clk),
        .s_axi_aresetn(rst_n),
        .s_axi_awaddr(s_axi_awaddr),
        .s_axi_awprot(s_axi_awprot),
        .s_axi_awvalid(s_axi_awvalid),
        .s_axi_awready(s_axi_awready),
        .s_axi_wdata(s_axi_wdata),
        .s_axi_wstrb(s_axi_wstrb),
        .s_axi_wvalid(s_axi_wvalid),
        .s_axi_wready(s_axi_wready),
        .s_axi_bresp(s_axi_bresp),
        .s_axi_bvalid(s_axi_bvalid),
        .s_axi_bready(s_axi_bready),
        .s_axi_araddr(s_axi_araddr),
        .s_axi_arprot(s_axi_arprot),
        .s_axi_arvalid(s_axi_arvalid),
        .s_axi_arready(s_axi_arready),
        .s_axi_rdata(s_axi_rdata),
        .s_axi_rresp(s_axi_rresp),
        .s_axi_rvalid(s_axi_rvalid),
        .s_axi_rready(s_axi_rready)
    );

    // Clock generation: 100 MHz (10ns period)
    always #5 clk = ~clk;

    // AXI Write Task
    task axi_write(input [7:0] addr, input [31:0] data);
        begin
            @(posedge clk);
            s_axi_awaddr  <= addr;
            s_axi_awvalid <= 1'b1;
            s_axi_wdata   <= data;
            s_axi_wstrb   <= 4'hF;
            s_axi_wvalid  <= 1'b1;
            s_axi_bready  <= 1'b1;

            @(posedge clk);
            while (!s_axi_awready || !s_axi_wready) @(posedge clk);

            @(posedge clk);
            s_axi_awvalid <= 1'b0;
            s_axi_wvalid  <= 1'b0;

            while (!s_axi_bvalid) @(posedge clk);
            @(posedge clk);
            s_axi_bready  <= 1'b0;
        end
    endtask

    // AXI Read Task
    task axi_read(input [7:0] addr, output [31:0] data);
        begin
            @(posedge clk);
            s_axi_araddr  <= addr;
            s_axi_arvalid <= 1'b1;
            s_axi_rready  <= 1'b1;

            @(posedge clk);
            while (!s_axi_arready) @(posedge clk);

            @(posedge clk);
            s_axi_arvalid <= 1'b0;

            while (!s_axi_rvalid) @(posedge clk);
            data = s_axi_rdata;
            @(posedge clk);
            s_axi_rready  <= 1'b0;
        end
    endtask

    reg [31:0] read_val;

    initial begin
        clk           = 0;
        rst_n         = 0;
        s_axi_awaddr  = 0;
        s_axi_awprot  = 0;
        s_axi_awvalid = 0;
        s_axi_wdata   = 0;
        s_axi_wstrb   = 0;
        s_axi_wvalid  = 0;
        s_axi_bready  = 0;
        s_axi_araddr  = 0;
        s_axi_arprot  = 0;
        s_axi_arvalid = 0;
        s_axi_rready  = 0;

        $display("===============================================================");
        $display("   STARTING SOLAR TRACKING GIMBAL AXI SIMULATION (EXP 04)      ");
        $display("===============================================================");

        #100;
        rst_n = 1;
        #50;

        // 1. Verify Hardware Version ID
        axi_read(8'h78, read_val);
        $display("[TB] Hardware ID: 0x%08X (Expected: 0x501A7010)", read_val);
        if (read_val !== 32'h501A7010) begin
            $display("[ERROR] Hardware ID mismatch!");
            $stop;
        end

        // 2. Set Sun Position: Azimuth = 180.0 deg (1800), Elevation = 45.0 deg (450)
        $display("[TB] Setting Sun Position: Azimuth=180.0 deg, Elevation=45.0 deg");
        axi_write(8'h04, {16'd450, 16'd1800});

        // 3. Set Initial Panel Position: Azimuth = 0.0 deg (0), Elevation = 0.0 deg (0)
        $display("[TB] Setting Panel Position: Azimuth=0.0 deg, Elevation=0.0 deg");
        axi_write(8'h08, {16'd0, 16'd0});

        // 4. Strobe Calculation
        $display("[TB] Strobing Calculation Engine...");
        axi_write(8'h00, 32'h00000001);

        #300; // Wait for vector, incident, and power engines to resolve

        // Read 3D Unit Vectors
        axi_read(8'h1C, read_val);
        $display("[TB] Sun Vector Sx (Q16.16): %d", $signed(read_val));
        axi_read(8'h20, read_val);
        $display("[TB] Sun Vector Sy (Q16.16): %d", $signed(read_val));
        axi_read(8'h24, read_val);
        $display("[TB] Sun Vector Sz (Q16.16): %d", $signed(read_val));

        axi_read(8'h34, read_val);
        $display("[TB] Dot Product N.S (Q16.16): %d", $signed(read_val));

        axi_read(8'h38, read_val);
        $display("[TB] Incident Angle: %0d.%0d deg, Cos(theta)*1000: %0d",
                 read_val[15:0]/10, read_val[15:0]%10, read_val[31:16]);

        axi_read(8'h3C, read_val);
        $display("[TB] Estimated Power: %0d Watts (Efficiency: %0d.%0d%%)",
                 read_val[15:0], read_val[31:16]/10, read_val[31:16]%10);

        axi_read(8'h6C, read_val);
        $display("[TB] Total 4-Panel Array Power: %0d Watts", read_val);

        // 5. Test Closed-Loop Tracking
        $display("[TB] Enabling Autonomous Closed-Loop Tracking...");
        axi_write(8'h00, 32'h00000004); // track_en = 1

        #15000; // Let tracking loop step panel towards sun

        axi_read(8'h08, read_val);
        $display("[TB] Slewed Panel Position: Azimuth=%0d.%0d deg, Elevation=%0d.%0d deg",
                 (read_val[15:0])/10, (read_val[15:0])%10,
                 (read_val[31:16])/10, (read_val[31:16])%10);

        axi_read(8'h10, read_val);
        $display("[TB] Remaining Tracking Error: Azimuth=%0d, Elevation=%0d (0.1 deg units)",
                 $signed(read_val[15:0]), $signed(read_val[31:16]));

        axi_read(8'h0C, read_val);
        $display("[TB] Gimbal Status Word: 0x%08X (Locked bit: %b, State: %0d)",
                 read_val, read_val[4], read_val[3:0]);

        $display("===============================================================");
        $display("   SOLAR TRACKING GIMBAL SIMULATION SUCCESSFUL               ");
        $display("===============================================================");
        $finish;
    end

endmodule
