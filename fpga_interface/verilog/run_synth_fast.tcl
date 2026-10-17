# ==============================================================================
# File: run_synth_fast.tcl
# Project: V_SPACE Multi-Scene FPGA System
# Target Device: XC7Z010-1CLG400C (EDGE ZYNQ Z7010)
# Description:
#   Fast non-project mode synthesis test of multi_scene_top.
#   Validates all 70+ RTL modules in 1-2 minutes without GUI project overhead.
# ==============================================================================

set part_number "xc7z010clg400-1"
set top_module  "multi_scene_top"

puts "================================================================="
puts "==> Fast In-Memory Synthesis Check for $top_module ($part_number)"
puts "================================================================="

# Read all Verilog and include files
puts "==> Reading Verilog sources..."
read_verilog [glob -nocomplain "./*.v"]

# Read XDC constraints
puts "==> Reading constraints..."
read_xdc "./edge_zynq_z7010.xdc"

# Run Out-Of-Context Synthesis on multi_scene_top
puts "==> Running synth_design in OOC mode..."
synth_design -top $top_module -part $part_number -mode out_of_context

# Report Utilization
puts "================================================================="
puts "==> FAST SYNTHESIS UTILIZATION REPORT:"
puts "================================================================="
report_utilization -hierarchical -hierarchical_depth 2

# Report Timing
puts "================================================================="
puts "==> FAST SYNTHESIS TIMING CHECK:"
puts "================================================================="
report_timing_summary -max_paths 5

puts "================================================================="
puts "==> Fast Synthesis check completed successfully!"
puts "================================================================="
