# Experiment 04: Visual Demonstration Assets

This directory stores hardware execution waveforms, optical sun-sensor alignment photos, and Vivado synthesis schematics for the **Dual-Axis Solar Tracking Gimbal** on the AMD EDGE Zynq Z7010 SoC.

## Asset Directory Map

| Asset Filename | Format | Description | Target Subsystem |
|---|---|---|---|
| `gimbal_hardware_setup.png` | Image (PNG) | Dual-axis pan-tilt stepper motor gimbal mounted on test bench with photo-diode quad array. | Hardware Testbed |
| `vivado_schematic.png` | Image (PNG) | Elaborated RTL schematic showing vector multiplier pipelines and arccos lookup logic. | Vivado RTL Synthesis |
| `ila_waveform_lock.png` | Image (PNG) | Vivado Integrated Logic Analyzer (ILA) capture of azimuth and elevation error convergence. | Hardware Telemetry |
| `day_energy_curve.png` | Image (PNG) | Power output comparison plot (tracked array vs. stationary array) over a 24-hour cycle. | Photovoltaic Analysis |

*Note: In simulation-only environments, images are captured via Python matplotlib outputs or Vivado export netlists.*
