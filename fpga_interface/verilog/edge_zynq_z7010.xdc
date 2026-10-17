# ==============================================================================
# File: edge_zynq_z7010.xdc
# Project: V_SPACE Multi-Scene FPGA Subsystem
# Target Device: XC7Z010-1CLG400C (EDGE ZYNQ Z7010)
# Top Module: multi_scene_top
# ==============================================================================

# ------------------------------------------------------------------------------
# AXI Clock Constraint (Period = 20.0 ns, 50 MHz)
# Note: For Out-Of-Context (OOC) synthesis of multi_scene_top or standalone mode.
# When integrated in system.bd with Zynq PS7, FCLK_CLK0 timing is auto-derived by PS7 IP.
# ------------------------------------------------------------------------------
create_clock -period 20.000 -name s_axi_aclk -waveform {0.000 10.000} [get_ports -quiet s_axi_aclk]

# ------------------------------------------------------------------------------
# Board Diagnostic LEDs (EDGE ZYNQ Z7010 on-board LEDs LD0..LD3)
# STATUS: UNVERIFIED BOARD PIN (Typical Z7010 pins M14, M15, K16, J16 assigned;
# pending vendor schematic / master XDC confirmation for EDGE Z7010 board)
# ------------------------------------------------------------------------------
set_property PACKAGE_PIN M14 [get_ports {board_leds[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {board_leds[0]}]

set_property PACKAGE_PIN M15 [get_ports {board_leds[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {board_leds[1]}]

set_property PACKAGE_PIN K16 [get_ports {board_leds[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {board_leds[2]}]

set_property PACKAGE_PIN J16 [get_ports {board_leds[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {board_leds[3]}]
