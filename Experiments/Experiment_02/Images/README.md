# Experiment 02 Evidence Assets & Waveforms

This directory stores visual evidence, Vivado simulation waveforms, and terminal screenshots for **Experiment 02: Smart City Traffic Grid**.

## Expected Artifacts
- `waveform_traffic_fsm.png`: Vivado XSim simulation waveform showing strict mutual exclusion of `ns_green` and `ew_green` with intermediate `ALL_RED` safety buffers.
- `waveform_emergency_preemption.png`: Waveform showing assertion of `cmd_emg` preemption, amber clearance, and immediate granting of arterial corridor green.
- `waveform_parallel_vehicles.png`: 16-channel concurrent position counter update waveform showing safe car-following distances.
- `terminal_traffic_ui.png`: Screenshot of the interactive traffic grid visualizer with queue counters and live signal phase indicators.

*(Note: Live waveform files and screen recordings are generated during Vivado hardware emulation and board testing sessions).*
