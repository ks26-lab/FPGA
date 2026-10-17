# ==============================================================================
# File: edge_zynq_z7010.xdc
# Project: V_SPACE Experiment 01 - Underwater Dynamic Probe Simulation
# Target Device: XC7Z010-1CLG400C (AMD EDGE ZYNQ Z7010)
# Top Module: underwater_probe_top
# ==============================================================================

# ------------------------------------------------------------------------------
# AXI Clock Constraint (Period = 20.0 ns, 50 MHz)
# ------------------------------------------------------------------------------
create_clock -period 20.000 -name s_axi_aclk -waveform {0.000 10.000} [get_ports -quiet s_axi_aclk]

# ------------------------------------------------------------------------------
# Physical Debug LEDs on Z7010 Board
# Status: Typical Z7010 package pins (M14, M15, K16, J16)
# ------------------------------------------------------------------------------
set_property PACKAGE_PIN M14 [get_ports {leds_probe_state[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds_probe_state[0]}]

set_property PACKAGE_PIN M15 [get_ports {leds_probe_state[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds_probe_state[1]}]

set_property PACKAGE_PIN K16 [get_ports {leds_probe_state[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds_probe_state[2]}]

set_property PACKAGE_PIN J16 [get_ports {leds_probe_state[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds_probe_state[3]}]

# Collision & Status Indicators
set_property PACKAGE_PIN L14 [get_ports led_collision]
set_property IOSTANDARD LVCMOS33 [get_ports led_collision]

set_property PACKAGE_PIN L15 [get_ports led_recovery]
set_property IOSTANDARD LVCMOS33 [get_ports led_recovery]

set_property PACKAGE_PIN G14 [get_ports led_target_reached]
set_property IOSTANDARD LVCMOS33 [get_ports led_target_reached]

# Ballast Pump PWM Output Port
set_property PACKAGE_PIN J15 [get_ports pump_pwm_out]
set_property IOSTANDARD LVCMOS33 [get_ports pump_pwm_out]
