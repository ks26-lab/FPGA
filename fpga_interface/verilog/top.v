// ============================================================================
// File: top.v
// Module: top
// Project: fpga_interface (Iteration 1)
// Description:
//   Top-level Verilog integration module for fpga_interface.
//   Provides a clean pass-through test path between input_interface
//   and output_interface to verify the complete communication pipeline.
//
// Data flow:
//   hw_input_bits -> input_interface -> internal_signal -> output_interface -> hw_output_bits
// ============================================================================

`timescale 1ns / 1ps

module top #(
    parameter INPUT_WIDTH  = 8,
    parameter OUTPUT_WIDTH = 8
)(
    input  wire [INPUT_WIDTH-1:0]  hw_input_bits,
    output wire [OUTPUT_WIDTH-1:0] hw_output_bits
);

    // Internal bus signal connecting input and output interfaces
    wire [INPUT_WIDTH-1:0] internal_signal;

    // 1. Input boundary interface instance
    input_interface #(
        .WIDTH(INPUT_WIDTH)
    ) u_input_interface (
        .in_bits(hw_input_bits),
        .internal_data(internal_signal)
    );

    // 2. Pass-through test path for Iteration 1:
    //    Connects internal_signal directly to output interface.
    //    (In future iterations, algorithmic FPGA processing is placed here).

    // 3. Output boundary interface instance
    output_interface #(
        .WIDTH(OUTPUT_WIDTH)
    ) u_output_interface (
        .internal_result(internal_signal),
        .out_bits(hw_output_bits)
    );

endmodule
