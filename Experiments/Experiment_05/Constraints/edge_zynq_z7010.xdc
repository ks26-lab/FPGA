## EDGE Zynq Z7010 SoC FPGA Physical Pin Constraints (Experiment 05: Mars Space Habitat & Defense)
## Device: XC7Z010-1CLG400C

## 50 MHz Master Clock
set_property PACKAGE_PIN L16 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]
create_clock -period 20.000 -name clk -waveform {0.000 10.000} [get_ports clk]

## Pushbutton Active-Low Reset (KEY0)
set_property PACKAGE_PIN R18 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

## Diagnostic Board LEDs (4x)
# LED0: Habitat Normal / Operational
set_property PACKAGE_PIN N18 [get_ports {led[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[0]}]

# LED1: Section Isolation Active
set_property PACKAGE_PIN P19 [get_ports {led[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[1]}]

# LED2: Hardware Safety Fault Alert
set_property PACKAGE_PIN U14 [get_ports {led[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[2]}]

# LED3: Master Heartbeat (Cycle counter toggle)
set_property PACKAGE_PIN U15 [get_ports {led[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[3]}]

## External PMOD Outputs (Actuators & Bulkhead Servos)
# Retro-Rocket Throttle PWM
set_property PACKAGE_PIN T14 [get_ports thrust_pwm_pin]
set_property IOSTANDARD LVCMOS33 [get_ports thrust_pwm_pin]

# Bulkhead A Isolation Servo Command
set_property PACKAGE_PIN T15 [get_ports bulkhead_a_pin]
set_property IOSTANDARD LVCMOS33 [get_ports bulkhead_a_pin]

# Bulkhead B Isolation Servo Command
set_property PACKAGE_PIN P14 [get_ports bulkhead_b_pin]
set_property IOSTANDARD LVCMOS33 [get_ports bulkhead_b_pin]

# Atmospheric Vent Emergency Dump Valve
set_property PACKAGE_PIN R14 [get_ports vent_dump_pin]
set_property IOSTANDARD LVCMOS33 [get_ports vent_dump_pin]
