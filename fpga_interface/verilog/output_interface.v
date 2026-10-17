// ============================================================================
// File: output_interface.v
// Module: output_interface
// Project: fpga_interface (Iteration 1)
// Description:
//   Output boundary interface for the fpga_interface protocol.
//   Receives the result from the internal Verilog design and exposes
//   it to the external output bus. Contains no algorithm-specific logic.
// ============================================================================

`timescale 1ns / 1ps

module output_interface #(
    parameter WIDTH = 8
)(
    input  wire [WIDTH-1:0] internal_result,
    output wire [WIDTH-1:0] out_bits
);

    // Expose internal design result to the external output bus
    assign out_bits = internal_result;

endmodule
