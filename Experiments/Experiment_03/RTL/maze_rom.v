// ============================================================================
// File: maze_rom.v
// Module: maze_rom
// Project: Zynq Z7010 FPGA 3D Maze Runner
// Description:
//   64-cell x 4-bit On-Chip Distributed ROM storing the 8x8 maze structure.
//   Address = (y << 3) | x.
//   Data format: 4'b<LEFT><DOWN><RIGHT><UP> (1 = wall, 0 = open).
// ============================================================================

`timescale 1ns / 1ps

module maze_rom (
    input  wire        clk,
    input  wire [5:0]  addr,
    output reg  [3:0]  data
);

    (* rom_style = "distributed" *) reg [3:0] rom [0:63];

    initial begin
        // Row 0
        rom[0]  = 4'b1101; rom[1]  = 4'b0001; rom[2]  = 4'b0111; rom[3]  = 4'b1101;
        rom[4]  = 4'b0001; rom[5]  = 4'b0111; rom[6]  = 4'b1101; rom[7]  = 4'b0011;
        // Row 1
        rom[8]  = 4'b1011; rom[9]  = 4'b1000; rom[10] = 4'b0101; rom[11] = 4'b1001;
        rom[12] = 4'b0000; rom[13] = 4'b0111; rom[14] = 4'b1011; rom[15] = 4'b1010;
        // Row 2
        rom[16] = 4'b1000; rom[17] = 4'b0100; rom[18] = 4'b1000; rom[19] = 4'b0100;
        rom[20] = 4'b1000; rom[21] = 4'b0001; rom[22] = 4'b0100; rom[23] = 4'b1010;
        // Row 3
        rom[24] = 4'b1100; rom[25] = 4'b0010; rom[26] = 4'b1100; rom[27] = 4'b0010;
        rom[28] = 4'b1100; rom[29] = 4'b0100; rom[30] = 4'b1000; rom[31] = 4'b0010;
        // Row 4
        rom[32] = 4'b1001; rom[33] = 4'b0110; rom[34] = 4'b1001; rom[35] = 4'b0110;
        rom[36] = 4'b1001; rom[37] = 4'b0010; rom[38] = 4'b1100; rom[39] = 4'b0010;
        // Row 5
        rom[40] = 4'b1010; rom[41] = 4'b1001; rom[42] = 4'b0110; rom[43] = 4'b1001;
        rom[44] = 4'b0110; rom[45] = 4'b1000; rom[46] = 4'b0011; rom[47] = 4'b1010;
        // Row 6
        rom[48] = 4'b1000; rom[49] = 4'b0100; rom[50] = 4'b1001; rom[51] = 4'b0100;
        rom[52] = 4'b1001; rom[53] = 4'b0000; rom[54] = 4'b0100; rom[55] = 4'b1010;
        // Row 7
        rom[56] = 4'b1100; rom[57] = 4'b0001; rom[58] = 4'b0001; rom[59] = 4'b0001;
        rom[60] = 4'b0001; rom[61] = 4'b0001; rom[62] = 4'b0001; rom[63] = 4'b0111;
    end

    always @(posedge clk) begin
        data <= rom[addr];
    end

endmodule
