# ==============================================================================
# File: edge_zynq_z7010.xdc
# Project: V_SPACE Experiment 02 - Smart City Traffic Grid
# Target Device: XC7Z010-1CLG400C (AMD EDGE ZYNQ Z7010)
# Top Module: traffic_top
# ==============================================================================

# ------------------------------------------------------------------------------
# AXI Clock Constraint (Period = 20.0 ns, 50 MHz)
# ------------------------------------------------------------------------------
create_clock -period 20.000 -name s_axi_aclk -waveform {0.000 10.000} [get_ports -quiet s_axi_aclk]

# ------------------------------------------------------------------------------
# Board Diagnostic LEDs (EDGE ZYNQ Z7010 on-board LEDs LD0..LD3)
# Status: Typical Z7010 package pins (M14, M15, K16, J16)
# ------------------------------------------------------------------------------
set_property PACKAGE_PIN M14 [get_ports {board_leds[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {board_leds[0]}]

set_property PACKAGE_PIN M15 [get_ports {board_leds[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {board_leds[1]}]

set_property PACKAGE_PIN K16 [get_ports {board_leds[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {board_leds[2]}]

set_property PACKAGE_PIN J16 [get_ports {board_leds[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {board_leds[3]}]

# Traffic Signal Output Indicators (Expansion Header IO)
set_property PACKAGE_PIN L14 [get_ports ns_green]
set_property IOSTANDARD LVCMOS33 [get_ports ns_green]

set_property PACKAGE_PIN L15 [get_ports ns_yellow]
set_property IOSTANDARD LVCMOS33 [get_ports ns_yellow]

set_property PACKAGE_PIN G14 [get_ports ns_red]
set_property IOSTANDARD LVCMOS33 [get_ports ns_red]

set_property PACKAGE_PIN J15 [get_ports ew_green]
set_property IOSTANDARD LVCMOS33 [get_ports ew_green]

set_property PACKAGE_PIN H15 [get_ports ew_yellow]
set_property IOSTANDARD LVCMOS33 [get_ports ew_yellow]

set_property PACKAGE_PIN V13 [get_ports ew_red]
set_property IOSTANDARD LVCMOS33 [get_ports ew_red]
