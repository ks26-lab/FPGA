# ==============================================================================
# File: create_zynq_system.tcl
# Project: V_SPACE Multi-Scene FPGA System
# Target Device: XC7Z010-1CLG400C (EDGE ZYNQ Z7010)
# Description:
#   Vivado TCL automation to construct the complete Zynq-7000 Processing System
#   Block Design (system.bd) and integrate multi_scene_top with M_AXI_GP0.
# ==============================================================================

set bd_name "system"

puts "==> Creating Block Design: $bd_name..."
create_bd_design $bd_name

# 1. Instantiate Processing System 7
puts "==> Instantiating processing_system7..."
set ps7 [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7_0]

# Configure PS7: 50 MHz FCLK_CLK0, M_AXI_GP0 enabled
set_property -dict [list \
    CONFIG.PCW_USE_M_AXI_GP0 {1} \
    CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {50} \
    CONFIG.PCW_EN_CLK0_PORT {1} \
    CONFIG.PCW_EN_RST0_PORT {1} \
    CONFIG.PCW_PRESET_BANK1_CHECKSUM {0} \
] $ps7

# 2. Instantiate Processor System Reset
puts "==> Instantiating proc_sys_reset..."
set rst_gen [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 rst_ps7_50M]

# 3. Instantiate multi_scene_top as RTL Module
puts "==> Referencing multi_scene_top RTL module..."
set scene_top [create_bd_cell -type module -reference multi_scene_top multi_scene_top_0]

# 4. Connect Clocks
puts "==> Connecting clocks..."
connect_bd_net [get_bd_pins ps7_0/FCLK_CLK0] \
               [get_bd_pins ps7_0/M_AXI_GP0_ACLK] \
               [get_bd_pins rst_ps7_50M/slowest_sync_clk] \
               [get_bd_pins multi_scene_top_0/s_axi_aclk]

# 5. Connect Resets
puts "==> Connecting resets..."
connect_bd_net [get_bd_pins ps7_0/FCLK_RESET0_N] \
               [get_bd_pins rst_ps7_50M/ext_reset_in]

connect_bd_net [get_bd_pins rst_ps7_50M/peripheral_aresetn] \
               [get_bd_pins multi_scene_top_0/s_axi_aresetn]

# 6. Connect AXI Interface: PS7 M_AXI_GP0 to multi_scene_top s_axi
puts "==> Connecting AXI interfaces..."
connect_bd_intf_net [get_bd_intf_pins ps7_0/M_AXI_GP0] \
                    [get_bd_intf_pins multi_scene_top_0/s_axi]

# 7. Make Board LEDs External
puts "==> Making board diagnostic LEDs external..."
make_bd_pins_external [get_bd_pins multi_scene_top_0/board_leds]
set_property name board_leds [get_bd_ports board_leds_0]

# 8. Assign Address Range in Address Editor
puts "==> Assigning AXI address segment (0x43C00000, 512K window covers all 5 scenes)..."
catch {
    assign_bd_address -offset 0x43C00000 -range 512K -target_address_space [get_bd_addr_spaces ps7_0/Data] [get_bd_addr_segs multi_scene_top_0/s_axi/reg0]
}
assign_bd_address

# 9. Validate and Save Block Design
validate_bd_design
save_bd_design

# 10. Generate Wrapper and set as top
puts "==> Generating HDL wrapper..."
set wrapper_file [make_wrapper -files [get_files [get_property FILE_NAME [current_bd_design]]] -top]
if {[file exists $wrapper_file]} {
    add_files -norecurse $wrapper_file
} else {
    add_files -norecurse [glob -nocomplain "./vivado_project/*.srcs/sources_1/bd/system/hdl/system_wrapper.v"]
}
set_property top system_wrapper [current_fileset]
update_compile_order -fileset sources_1
puts "==> Zynq PS Block Design setup completed successfully."
