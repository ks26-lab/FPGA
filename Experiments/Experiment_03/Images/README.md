# Experiment 03 Evidence Assets & Waveforms

This directory stores visual evidence, Vivado simulation waveforms, and terminal screenshots for **Experiment 03: 3D Maze Runner**.

## Expected Artifacts
- `waveform_maze_fsm.png`: Vivado XSim simulation waveform showing transition from `IDLE` to `MAZE_DISPLAY` (with 5-second countdown) and automatic entry into `GAMEPLAY`.
- `waveform_bfs_search.png`: Waveform illustrating hardware BFS cycle exploration from start $(0,0)$ to goal $(7,7)$ yielding `path_length = 14`.
- `terminal_maze_ui.png`: Screenshot of the interactive 3D/ASCII terminal rendering the 8x8 maze grid, player cursor, and telemetry cards.

*(Note: Live waveform files and screen recordings are generated during Vivado hardware emulation and board testing sessions).*
