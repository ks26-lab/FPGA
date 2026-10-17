// ============================================================================
// File: input_interface.v
// Module: input_interface
// Project: fpga_interface (Iteration 1)
// Description:
//   Input boundary interface for the fpga_interface protocol.
//   Receives a defined-width binary input bus and exposes the data
//   to the internal Verilog design. Contains no algorithm-specific logic.
// ============================================================================

`timescale 1ns / 1ps

module input_interface #(
    parameter WIDTH = 8
)(
    input  wire [WIDTH-1:0] in_bits,
    output wire [WIDTH-1:0] internal_data
);

    // Expose received binary bits directly to internal design
    assign internal_data = in_bits;

endmodule
