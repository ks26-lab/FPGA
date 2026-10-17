# FPGA Resource Budget & Feasibility Report
## Target Device: Xilinx Zynq-7000 XC7Z010-1CLG400C (EDGE ZYNQ Z7010)

---

## 1. Zynq-7000 XC7Z010 Hardware Capacity Limits

| Resource Type | Available on Device | Utilization Threshold (Safe) |
|---|---|---|
| **Logic Cells** | 28,000 | 80% Max (22,400) |
| **LUTs (Look-Up Tables)** | 17,600 | 75% Max (13,200) |
| **Flip-Flops (FF)** | 35,200 | 75% Max (26,400) |
| **Block RAM (BRAM 36Kb / 18Kb)** | 60 (18Kb equivalent) / 2.1 Mb | 70% Max (42) |
| **DSP48 Slices** | 80 | 70% Max (56) |
| **I/O Pins** | 100 Available | 80% Max |

---

## 2. Resource Budget Per Scene Core

Estimated gate counts and memory blocks from synthesized RTL architectures:

| Module / Scene | Estimated LUTs | Estimated FFs | BRAM (18Kb) | DSP48 | Clock Domain | Feasibility Status |
|---|---|---|---|---|---|---|
| **AXI Interconnect Subsystem** | 850 | 920 | 0 | 0 | 50 MHz (FCLK0) | **FEASIBLE** |
| **Underwater Dynamic Probe** | 420 | 310 | 0 | 1 | 50 MHz | **FEASIBLE** |
| **Maze Runner (8x8 BRAM ROM)** | 310 | 240 | 1 | 0 | 50 MHz | **FEASIBLE** |
| **Mars Space Habitat Defense** | 480 | 360 | 0 | 2 | 50 MHz | **FEASIBLE** |
| **Solar Tracking Gimbal** | 390 | 280 | 0 | 0 | 50 MHz | **FEASIBLE** |
| **Smart City Traffic Grid** | 290 | 220 | 0 | 0 | 50 MHz | **FEASIBLE** |
| **Multi-Scene Combined Top** | **2,740** | **2,330** | **1** | **3** | 50 MHz | **FEASIBLE (15.5% LUTs)** |

---

## 3. Operations Excluded (Inappropriate for Z7010)

To prevent resource exhaustion and timing closure failures, the following algorithms were explicitly **excluded** from the FPGA design and from the software RTL emulator:

1. **Floating-Point Hydrodynamics**: Double/single-precision Navier-Stokes fluid simulations would exhaust all 80 DSP slices and exceed BRAM limits.
   - *FPGA Approach*: Fixed-point linear buoyancy with integer velocity increments and bitwise shift drift (`>> 4`).
2. **A* / Dijkstra Dynamic Pathfinding**: Storing large priority queues and dynamic node graphs in PL requires dynamic heap allocation impossible in fixed RTL.
   - *FPGA Approach*: Static 64-nibble BRAM ROM lookup for wall collision.
3. **SciPy Non-Linear Least Squares Solar Optimization**: Requires matrix inversion and trigonometric math libraries.
   - *FPGA Approach*: 3600-count circular modulo error with proportional step slewing.
4. **Microscopic Agent-Based Traffic Simulation**: Multi-agent cellular automata or neural network traffic optimization cannot fit in a Z7010 alongside other scenes.
   - *FPGA Approach*: 5-phase deterministic FSM with counter-based adaptive timing.

---

## 4. Conclusion
The entire multi-scene core subsystem fits within **~15.5% of LUTs**, **6.6% of Flip-Flops**, **1.6% of BRAM**, and **3.7% of DSPs**, leaving ample routing and timing margin on the Zynq Z7010.
