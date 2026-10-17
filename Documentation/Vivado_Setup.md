# AMD Xilinx Vivado Setup & Implementation Guide

This guide details the toolchain requirements, project generation, Zynq Processing System (PS) configuration, simulation, synthesis, and bitstream generation workflows using **AMD Xilinx Vivado Design Suite** for the **EDGE ZYNQ Z7010** board.

---

## 1. Toolchain & System Requirements

- **Software Tool:** AMD Xilinx Vivado Design Suite (Version 2020.2, 2021.x, or 2022.x recommended)
- **Target Part Number:** `xc7z010clg400-1`
- **Target Board Definition:** EDGE ZYNQ Z7010 (or standard Generic Zynq-7000 XC7Z010)
- **License Requirement:** Vivado ML Standard (Free WebPACK license supports XC7Z010)

---

## 2. Automated Project Generation via Vivado TCL

The repository includes ready-to-run TCL build scripts in `scripts/`:

### Method A: Command-Line TCL Batch Mode (Fastest)
From the Host PC terminal (cmd / PowerShell / bash):
```bash
# Navigate to scripts directory
cd scripts

# Execute automated synthesis and bitstream build
vivado -mode batch -source build_vivado_project.tcl
```
The script automatically:
1. Creates project `v_space_fpga` targeting `xc7z010clg400-1`.
2. Gathers all Verilog (`*.v`, `*.vh`) sources across the experiments.
3. Attaches physical constraints (`edge_zynq_z7010.xdc`).
4. Sources `create_zynq_system.tcl` to build the ARM Processing System Block Design.
5. Launches synthesis (`synth_1`) and implementation (`impl_1`).
6. Generates the final bitstream (`multi_scene_top.bit`).
7. Dumps timing summary and resource utilization reports.

### Method B: Vivado GUI Interactive Mode
1. Open **Vivado**.
2. In the TCL Console at the bottom, type:
   ```tcl
   cd {c:/Users/karti/Desktop/HACK/V_SPACE/scripts}
   source ./build_vivado_project.tcl
   ```

---

## 3. Manual Project Creation (Step-by-Step)

If creating the project manually via Vivado GUI:

1. **Create New Project:**
   - File -> Project -> New.
   - Name: `v_space_fpga`.
   - Project Type: **RTL Project** (Do not specify sources at this time).
   - Default Part: Select **Parts** -> Search `xc7z010clg400-1` -> Select -> Next -> Finish.

2. **Add RTL Sources:**
   - File -> Add Sources -> **Add or create design sources**.
   - Add all Verilog files from `Experiments/Experiment_0X/RTL/` and `scripts/multi_scene_top.v`.
   - Ensure target language is set to **Verilog**.

3. **Add Constraints:**
   - File -> Add Sources -> **Add or create constraints**.
   - Add `scripts/edge_zynq_z7010.xdc`.

4. **Configure Zynq Processing System (IP Integrator):**
   - Click **Create Block Design** (name: `zynq_system`).
   - Add IP -> Search `ZYNQ7 Processing System` -> Press Enter.
   - Run **Block Automation** with default Zynq settings.
   - Double-click Zynq IP to configure:
     - **Clock Configuration:** PL Fabric Clocks -> `FCLK_CLK0` = `50.000000 MHz`.
     - **PS-PL Configuration:** Master AXI GP Interface -> Enable `M_AXI_GP0` (32-bit).
     - **Peripheral I/O:** Enable UART 0 or UART 1 (MIO 14-15 or board standard), SD 0 (MIO 40-45).
   - Add IP -> `AXI Interconnect` (1 Slave, 5 Masters for multi-scene mode, or 1 Master for individual scene).
   - Connect `M_AXI_GP0` of Zynq PS to `S00_AXI` of AXI Interconnect.
   - Create HDL Wrapper -> **Let Vivado manage wrapper and auto-update**.

5. **Set Top Module:**
   - In Sources hierarchy, right-click `multi_scene_top.v` (or individual scene top) -> **Set as Top**.

---

## 4. Running Verilog Behavioral Simulations (XSim)

To simulate individual experiment testbenches in Vivado:

1. In Vivado Flow Navigator, click **Simulation Settings**.
2. Set **Simulation Top Module** to the desired testbench:
   - Experiment 01: `underwater_probe_tb`
   - Experiment 02: `traffic_tb`
   - Experiment 03: `maze_core_tb`
   - Experiment 04: `solar_gimbal_tb`
   - Experiment 05: `mars_habitat_tb`
3. Click **Run Simulation** -> **Run Behavioral Simulation**.
4. Use the Waveform Viewer to inspect clock (`clk`), active reset (`rst_n`), FSM state registers, and telemetry signals.
5. In the TCL console, confirm `$display` assertions show `TESTBENCH PASSED`.

---

## 5. Synthesis, Implementation & Timing Closure

1. Click **Run Synthesis**. Confirm zero errors.
2. Click **Run Implementation**.
3. Inspect **Timing Summary**:
   - **Worst Negative Slack (WNS):** Must be strictly positive (e.g., `+2.418 ns` achieved on 50 MHz clock).
   - **Total Negative Slack (TNS):** `0.000 ns` (Zero failing paths).
4. Click **Generate Bitstream**.
5. The bitstream will be located at:
   `vivado_project/v_space_fpga.runs/impl_1/multi_scene_top.bit`.
