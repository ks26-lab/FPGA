# Experiment 01 Evidence Assets & Waveforms

This directory stores visual evidence, Vivado simulation waveforms, and terminal screenshots for **Experiment 01: Underwater Dynamic Probe Simulation**.

## Expected Artifacts
- `waveform_pid_response.png`: Vivado XSim simulation waveform showing `depth_error`, `p_term`, `i_term`, `d_term`, and resulting `thrust_command`.
- `waveform_collision_recovery.png`: Waveform showing kinetic impulse injection (`cmd_disturb_strobe`), transition to `STATE_COLLISION_DETECTED`, and restorative `recovery_thrust`.
- `terminal_telemetry_ui.png`: Screenshot of the 3-panel interactive CLI terminal displaying live depth, drift, velocity, and ASCII depth bar.

*(Note: Live waveform files and screen recordings are generated during Vivado hardware emulation and board testing sessions).*
