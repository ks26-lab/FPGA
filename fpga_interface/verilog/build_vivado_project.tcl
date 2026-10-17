# ==============================================================================
# File: build_vivado_project.tcl
# Project: V_SPACE Multi-Scene FPGA System
# Description:
#   Vivado TCL script to create and configure the multi-scene FPGA project
#   targeting Xilinx Zynq-7000 XC7Z010-1CLG400C (EDGE ZYNQ Z7010 board).
# ==============================================================================

set project_name "v_space_fpga"
set project_dir  "./vivado_project"
set part_number  "xc7z010clg400-1"

puts "==> Creating Vivado Project: $project_name for part: $part_number"
create_project -force $project_name $project_dir -part $part_number

# Set project properties
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_property default_lib work [current_project]

# Add Verilog and Header sources
puts "==> Adding RTL sources from fpga_interface/verilog..."
add_files -norecurse [glob -nocomplain "./*.v"]
add_files -norecurse [glob -nocomplain "./*.vh"]

# Add Constraints
puts "==> Adding constraints..."
add_files -fileset constrs_1 -norecurse "./edge_zynq_z7010.xdc"

# Set multi_scene_top as the top module (or source create_zynq_system.tcl for PS Block Design)
puts "==> Updating compile order..."
update_compile_order -fileset sources_1

# Build Zynq PS Block Design if requested or synthesize multi_scene_top
if {[file exists "./create_zynq_system.tcl"]} {
    puts "==> Building Zynq Processing System Block Design..."
    source "./create_zynq_system.tcl"
} else {
    set_property top multi_scene_top [current_fileset]
    update_compile_order -fileset sources_1
}

# Automatic synthesis and implementation execution
set auto_run [expr {[info exists env(AUTO_RUN)] ? $env(AUTO_RUN) : 1}]

if {$auto_run == 1} {
    puts "================================================================="
    puts "==> Step 1: Launching Synthesis (synth_1)..."
    puts "================================================================="
    launch_runs synth_1 -jobs 4
    wait_on_run synth_1

    if {[get_property PROGRESS [get_runs synth_1]] != "100%"} {
        puts "ERROR: Synthesis failed. Check ./vivado_project/v_space_fpga.runs/synth_1/runme.log"
        exit 1
    }
    puts "==> Synthesis completed successfully."

    puts "================================================================="
    puts "==> Step 2: Launching Implementation & Bitstream (impl_1)..."
    puts "================================================================="
    launch_runs impl_1 -to_step write_bitstream -jobs 4
    wait_on_run impl_1

    if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {
        puts "ERROR: Implementation failed. Check ./vivado_project/v_space_fpga.runs/impl_1/runme.log"
        exit 1
    }
    puts "==> Implementation & Bitstream generated successfully!"

    # Open implemented run and report results
    open_run impl_1
    puts "================================================================="
    puts "==> RESOURCE UTILIZATION SUMMARY:"
    puts "================================================================="
    report_utilization -hierarchical -hierarchical_depth 2
    puts "================================================================="
    puts "==> TIMING SUMMARY:"
    puts "================================================================="
    report_timing_summary -max_paths 5
} else {
    puts "==> Setup completed successfully."
    puts "To synthesize and implement, run:"
    puts "  launch_runs synth_1 -jobs 4"
    puts "  wait_on_run synth_1"
    puts "  launch_runs impl_1 -to_step write_bitstream -jobs 4"
    puts "  wait_on_run impl_1"
}
