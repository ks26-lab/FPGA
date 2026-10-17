# Scene Integration Guide & Multi-Scene Strategy

## 1. Supported FPGA Deployment Strategies

### Strategy A: One Scene Programmed at a Time (Separate Bitstreams)
In this strategy, each simulation scene has a dedicated bitstream:
- `underwater_probe_top.bit`
- `maze_top.bit`
- `mars_habitat_top.bit`
- `solar_gimbal_top.bit`
- `traffic_top.bit`

Each top module attaches to `M_AXI_GP0` at default base address `0x43C00000`.
To run the software in Strategy A mode:
```bash
./run_cli.sh --single-bitstream
```
When switching scenes via `scene <name>`, the runtime directs all register transactions through `0x43C00000` to whatever peripheral is currently programmed into the FPGA.

---

### Strategy B: Multi-Core Simultaneous Integration (Unified Subsystem)
In this strategy, all 5 scene peripherals are instantiated concurrently under `multi_scene_top.v` or via a Vivado SmartConnect / AXI Interconnect:
- Underwater: `0x43C00000`
- Maze Runner: `0x43C10000`
- Mars Space Habitat: `0x43C20000`
- Solar Gimbal: `0x43C30000`
- Traffic Grid: `0x43C40000`

To run in Strategy B mode:
```bash
./run_cli.sh
```
When the user issues `scene underwater` or `scene maze`, the runtime instantly updates its active AXI target address to the corresponding memory-mapped aperture without reprogramming the FPGA.

---

## 2. Adding a New Scene

To integrate a new 6th scene (e.g. `drone_flight`):

1. **Create Verilog Hardware Core & AXI Slave**:
   - `drone_flight_core.v`
   - `drone_flight_axi_slave.v`
   - `drone_flight_top.v`

2. **Assign Address in Vivado**:
   - Base address: `0x43C50000`, 64KB range.

3. **Create Scene Driver Package**:
   - `python/scenes/drone/register_map.py`
   - `python/scenes/drone/telemetry.py`
   - `python/scenes/drone/driver.py` (inherits from `BaseFPGADriver`)
   - `python/scenes/drone/command_handler.py`

4. **Register in `python/core/scene_manager.py`**:
   - Add `SceneType.DRONE` to `python/protocol/enums.py`.
   - Add mapping to `SceneManager.get_driver()`.

5. **Register in `python/cli/renderer.py`**:
   - Add rendering branch in `CLIRenderer.render_telemetry()`.
