# Contributing to V_SPACE FPGA Projects

Thank you for your interest in contributing to the **V_SPACE FPGA Project** targeting the **AMD EDGE Zynq Z7010 SoC Development Board**.

## 1. Code of Conduct & Architectural Rules

To maintain timing closure, hardware reliability, and deterministic execution:

1. **Hardware-Authoritative Separation:**
   - Verilog RTL running on the Zynq PL is the authoritative engine for all physical dynamics, state transitions, collision detection, and mathematical transforms.
   - Python running on the ARM PS only handles register read/write transactions (`/dev/mem` memory-mapping) and telemetry presentation. Never implement simulation physics in software as a substitute for FPGA logic.

2. **Fixed-Point Arithmetic Standard:**
   - The XC7Z010 PL does not implement IEEE-754 floating-point hardware cores.
   - All arithmetic must adhere to the designated fixed-point formats (e.g., Q16.16, Q12.4, or scaled integer units).

3. **Strict AXI Address Decoupling:**
   - All register offsets and apertures must strictly adhere to `Documentation/AXI_Register_Map.md`.
   - Never write to unmapped address space.

4. **Zero-Collision Invariants:**
   - For safety-critical modules (such as Experiment 02 Traffic Grid), candidate movements must pass the PREDICT-to-PREVENT safety pipeline before committing state (`actual_collision == 0`).

---

## 2. Development & Pull Request Workflow

1. **Branching Strategy:**
   - Create a feature branch from `main`: `feature/exp0X-enhancement` or `fix/timing-closure`.
2. **Simulation & Parity Verification:**
   - Before submitting a pull request, run all unit and regression testbenches:
     ```bash
     python -m unittest discover tests/
     ```
   - Ensure bit-accurate parity is preserved between RTL testbenches and Python emulation models.
3. **Synthesis & Timing Closure:**
   - Run Vivado synthesis check to ensure **Worst Negative Slack (WNS) >= 0.000 ns** at the 50 MHz target clock.
4. **Documentation:**
   - Update the respective `Experiments/Experiment_0X/README.md` and architecture specifications for any register or datapath changes.

---

## 3. Submitting Issues

When reporting issues:
- Specify your Vivado toolchain version (recommended: Vivado 2020.2 or later).
- Include terminal logs from the PuTTY CLI or Python test output.
- State whether the issue occurred in hardware mode (`--hw`) or emulator mode (`--mock`).
