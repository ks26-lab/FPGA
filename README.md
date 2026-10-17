# V_SPACE: Universal Multi-Scene FPGA Cyber-Physical System

**Hardware-Authoritative Real-Time Computation & Control Platform for AMD EDGE Zynq Z7010 SoC (Xilinx XC7Z010-1CLG400C)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FPGA Target](https://img.shields.io/badge/Target%20SoC-AMD%20EDGE%20Zynq%20Z7010-blue.svg)](Documentation/Board_Setup.md)
[![Fabric](https://img.shields.io/badge/PL%20Device-XC7Z010--1CLG400C-darkblue.svg)](Documentation/Project_Overview.md)
[![System Clock](https://img.shields.io/badge/Clock-50.000%20MHz%20AXI4--Lite-green.svg)](docs/AXI_REGISTER_MAP.md)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](run_cli.py)
[![Verification](https://img.shields.io/badge/Test%20Suite-25%20Unit%20Tests%20Passing-brightgreen.svg)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Dual--Execution%20(HW%20%2B%20RTL%20Emulator)-orange.svg)](docs/DUAL_EXECUTION_ARCHITECTURE.md)
[![MATLAB](https://img.shields.io/badge/Golden%20Model-MATLAB%20Float64-red.svg)](MATLAB/)

---

## 📑 Table of Contents

- [1. Executive Summary & Core Philosophy](#1-executive-summary--core-philosophy)
- [2. 🖥️ How to Run ONLY the UI Setup (Web & Terminal)](#2-️-how-to-run-only-the-ui-setup-web--terminal)
  - [Option A: Interactive Web Control Station (HTML5 / CSS / Vanilla JS)](#option-a-interactive-web-control-station-html5--css--vanilla-js)
  - [Option B: Terminal-Native Curses Dashboard (`terminal_ui.py`)](#option-b-terminal-native-curses-dashboard-terminal_uipy)
  - [Option C: Universal Interactive CLI in Laptop Emulator Mode (`--mock`)](#option-c-universal-interactive-cli-in-laptop-emulator-mode---mock)
  - [Option D: Standalone Scene CLIs](#option-d-standalone-scene-clis)
- [3. The Five FPGA Computational Engines & Difficulty Hierarchy](#3-the-five-fpga-computational-engines--difficulty-hierarchy)
  - [Level 1 (Basic): Scene 01 — Underwater Dynamic Probe](#level-1-basic-scene-01--underwater-dynamic-probe)
  - [Level 1 (Basic): Scene 02 — Smart City Traffic Grid](#level-1-basic-scene-02--smart-city-traffic-grid)
  - [Level 2 (Intermediate): Scene 03 — 3D Maze Runner Engine](#level-2-intermediate-scene-03--3d-maze-runner-engine)
  - [Level 2 (Intermediate): Scene 04 — Dual-Axis Solar Tracking Gimbal](#level-2-intermediate-scene-04--dual-axis-solar-tracking-gimbal)
  - [Level 3 (Advanced): Scene 05 — Mars Space Habitat & Landing Defense](#level-3-advanced-scene-05--mars-space-habitat--landing-defense)
- [4. System Architecture & Hardware/Software Partitioning](#4-system-architecture--hardwaresoftware-partitioning)
- [5. Universal AXI4-Lite Register Memory Map](#5-universal-axi4-lite-register-memory-map)
- [6. EDGE Zynq Z7010 Hardware Deployment Guide](#6-edge-zynq-z7010-hardware-deployment-guide)
- [7. Verification, Testing & MATLAB Golden Models](#7-verification-testing--matlab-golden-models)
- [8. Repository Directory Structure](#8-repository-directory-structure)
- [9. Contributing & Architectural Rules](#9-contributing--architectural-rules)
- [10. License](#10-license)

---

## 1. Executive Summary & Core Philosophy

**V_SPACE** is an advanced cyber-physical FPGA computing platform targeting the **AMD EDGE Zynq Z7010 SoC Development Board (XC7Z010-1CLG400C)**. The platform implements five real-time computation engines in Verilog RTL, coordinated by a dual-core ARM Cortex-A9 Processing System (PS) running embedded Linux.

### Key Architectural Invariants:
1. **Hardware-Authoritative Computation:** All physical dynamics (discrete gravity, quadratic fluid drag, retro-thrust), 16-channel vehicle kinematics, 8-channel parallel meteorite detection, graph search accelerators (BFS / A*), trigonometric solar geometry, and safety supervisors are calculated exclusively within 50 MHz Verilog RTL pipelines in the Programmable Logic (PL).
2. **Zero Simulation in Software:** The Processing System (ARM Cortex-A9 Linux) and developer workstations never calculate physics or collision rules in place of the hardware. Software serves strictly as a command gateway, telemetry decoder, and register bridge via `/dev/mem` memory mapping.
3. **Dual-Execution Architecture:** Complete hardware/software parity allows full-system verification either natively on Zynq hardware (`--hw`) or via cycle-accurate, bit-accurate Python RTL emulation models (`--mock`) without requiring physical hardware.
4. **Structured Difficulty Gradient:** Five computational scenes spanning Level 1 (Basic Single-Domain), Level 2 (Intermediate Spatial Reasoning / Vector Math), and Level 3 (Advanced Coupled Multi-Domain Dynamics).

---

## 2. 🖥️ How to Run ONLY the UI Setup (Web & Terminal)

You do **not** need an FPGA board or Vivado installed to explore and interact with the user interfaces. The project includes standalone modes for both a rich **Web Control Station** and **Terminal-Native Interfaces**.

> [!TIP]
> ### ⚡ Quick Command Reference: Standalone UI Terminal Only
> If you are on a laptop or desktop (Windows, macOS, or Linux) without the physical Zynq FPGA board attached, use either of these commands to launch the terminal UI immediately:
>
> 1. **Visual Curses Dashboard (Animated ASCII UI):**
>    ```bash
>    python terminal_ui.py
>    ```
>    *(Windows users: run `pip install windows-curses` first)*
>
> 2. **Interactive FPGA Command-Line Terminal (Software RTL Emulation):**
>    ```bash
>    python run_cli.py --mock
>    ```
>    *(**Important:** Always supply `--mock` when running outside the physical Zynq board to avoid `/dev/mem` hardware errors!)*
>
> 3. **Direct Scene Interactive Terminal:**
>    ```bash
>    python mars_habitat_cli.py
>    ```

---

### Option A: Interactive Web Control Station (HTML5 / CSS / Vanilla JS)

The Web Control Station (`index.html`, `style.css`, `app.js`) is a zero-dependency, high-tech interface featuring:
- **Cinematic Boot Sequence:** Simulated 50 MHz PLL clock lock, bitstream configuration SRAM loading, and timing analysis verification (press `ESC` to skip).
- **Interactive Project Dock:** Switch between hardware targets (*Smart City Traffic Grid*, *Mars Rover Motor PWM*, *Android Joint Servo*, *Mars Space Habitat Defense*, *Solar Tracking Gimbal*).
- **Physical Pin Controls:** Live toggle switches, binary pins, bus range sliders, and multi-channel dropdown selectors.
- **Client-Side FPGA Logic:** Standalone evaluation loop that simulates exact register logic directly in the browser.
- **Visual Hardware Overlay & Live Telemetry:** Real-time feedback showing FSM states, queue depths, PWM duty cycles, vector coordinates, and safety supervisor status.
- **Human-to-FPGA Terminal:** Interactive command prompt (`set <pin> <value>`, `run`, `status`, `help`).

#### Launch Methods for the Web UI:

#### Method 1: Python Built-in HTTP Server (Recommended)
Open a terminal in the root of the repository and run:
```bash
# Python 3
python -m http.server 8000
# or on Linux/macOS:
python3 -m http.server 8000
```
Then open your web browser to:
```text
http://localhost:8000
```

#### Method 2: Node.js / npx
If you have Node.js installed:
```bash
npx serve .
# or
npx http-server -p 8000
```
Open the URL shown in your terminal.

#### Method 3: Direct Browser Launch (No Server Needed)
You can directly open `index.html` in your web browser:
- **Windows:** Double-click `index.html`, or run in PowerShell / Command Prompt:
  ```powershell
  start index.html
  ```
- **macOS:**
  ```bash
  open index.html
  ```
- **Linux:**
  ```bash
  xdg-open index.html
  ```

#### Method 4: VS Code Live Server
1. Open this repository in Visual Studio Code.
2. Install the **Live Server** extension (`ritwickdey.liveserver`).
3. Right-click `index.html` and click **"Open with Live Server"**.

> **Note on Standalone Web Mode:** When running without physical hardware connected, the UI automatically detects the offline status (`/api/hardware/status` unreachable) and switches seamlessly to **`SOFTWARE-ONLY (STANDALONE WEB)`** mode. All FPGA input/output evaluation executes locally inside `app.js`.

---

### Option B: Terminal-Native Curses Dashboard (`terminal_ui.py`)

For terminal environments (SSH, PuTTY, or local shell), `terminal_ui.py` provides a keyboard-driven ASCII/ANSI dashboard that runs in **software visualization mode** without requiring `/dev/mem` or physical FPGA access.

#### Requirements:
- Python 3.8+
- On **Linux / macOS**: Uses Python's built-in `curses` library (no installation required).
- On **Windows**: Install the Windows curses bridge:
  ```bash
  pip install windows-curses
  ```

#### Launching the Terminal UI:
```bash
python terminal_ui.py
```

#### Features:
- Keyboard navigation menu (Arrow keys to navigate, `ENTER` to select, `ESC` to return to menu).
- Real-time ASCII animated visualizers for all 5 environments:
  1. **UNDERSEA WORLD:** Fluid depth seeking, vertical velocity, current drift, and obstacle recovery.
  2. **SMART CITY:** 4-way intersection ASCII signal lights, queue depth gauges, and vehicle movement.
  3. **3D MAZE:** 8x8 maze rendering with player position, wall collisions, and BFS pathfinding.
  4. **SOLAR PANEL:** Dual-axis gimbal azimuth/elevation angles, sun tracking vectors, and generated power.
  5. **SPACE HABITAT:** Lander descent altitude/thrust radar, 8-channel meteorite field, and hull bulkhead integrity.

---

### Option C: Universal Interactive CLI in Laptop Emulator Mode (`--mock`)

If you want to interact with the full command-line dispatch system using cycle-accurate Python RTL models (matching the exact register map of the Verilog cores):

```bash
# Launch the universal multi-scene CLI in emulator mode
python run_cli.py --mock

# Or launch directly into a specific scene:
python run_cli.py --mock --scene underwater
python run_cli.py --mock --scene traffic
python run_cli.py --mock --scene maze
python run_cli.py --mock --scene solar
python run_cli.py --mock --scene mars
```

Inside the CLI prompt (`FPGA>`), run:
```text
FPGA> scene underwater
FPGA[underwater]> set depth 40
FPGA[underwater]> target 80
FPGA[underwater]> current +20
FPGA[underwater]> start
FPGA[underwater]> status
```

> [!NOTE]
> **Why `--mock` is used on laptops & PCs:**
> Native hardware mode maps physical registers via Linux `/dev/mem` on the Zynq ARM PS. If you execute without physical hardware or on Windows/macOS, adding the `--mock` flag (`python run_cli.py --mock`) instructs the runtime to load bit-accurate Python RTL emulator models (`python/emulation/`), giving you the full interactive hardware CLI experience without requiring physical hardware or `/dev/mem`.

---

### Option D: Standalone Scene CLIs

Each experiment also includes an independent, dedicated CLI driver that can be run directly:

```bash
# Mars Space Habitat & Lander
python mars_habitat_cli.py

# Solar Tracking Gimbal
python solar_gimbal_cli.py

# 3D Maze Runner Engine
python maze_runner_cli.py

# Underwater Dynamic Probe
python underwater_probe_cli.py
```

---

## 3. The Five FPGA Computational Engines & Difficulty Hierarchy

The system architecture implements a strict hierarchy of computational complexity across five scenes:

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      COMPLEXITY HIERARCHY                              │
 │                                                                        │
 │  LEVEL 3: ADVANCED      [ EXP 05: MARS SPACE HABITAT & DEFENSE ]       │
 │                         Coupled Descent Dynamics + 8-Ch Meteorites     │
 │                                                                        │
 │  LEVEL 2: INTERMEDIATE  [ EXP 03: 3D MAZE ]    [ EXP 04: SOLAR GIMBAL ]│
 │                         ROM Wall BFS/A* Accel  3D Vectors + Trig LUT   │
 │                                                                        │
 │  LEVEL 1: BASIC         [ EXP 01: UNDERSEA ]   [ EXP 02: TRAFFIC GRID ]│
 │                         PID Drag Control       16-Ch Kinematics FSM    │
 └────────────────────────────────────────────────────────────────────────┘
```

| Exp | Title | Difficulty | Base Address | Primary Computation | Key RTL Modules |
|:---:|---|:---:|:---:|---|---|
| **01** | [Underwater Dynamic Probe](Experiments/Experiment_01/) | **Basic** | `0x43C00000` | Closed-loop vertical depth seeking + quadratic hydrostatic drag $F_d = -c \cdot v \|v\|$ + 7-state recovery FSM | `underwater_probe_core.v`, `underwater_physics_engine.v`, `underwater_pid_controller.v`, `underwater_drag_engine.v` |
| **02** | [Smart City Traffic Grid](Experiments/Experiment_02/) | **Basic** | `0x43C40000` | Demand-driven green split optimization + 16-channel vehicle kinematics + zero-collision pipeline (`actual_collision == 0`) | `traffic_core.v`, `traffic_parallel_vehicle_engine.v`, `traffic_green_split_optimizer.v`, `traffic_emergency_corridor.v` |
| **03** | [3D Maze Runner Game Engine](Experiments/Experiment_03/) | **Intermediate** | `0x43C10000` | Spatial reasoning + 8x8 ROM wall collision + BFS / A* hardware graph search accelerators | `maze_core.v`, `maze_bfs_engine.v`, `maze_astar_engine.v`, `maze_collision_engine.v` |
| **04** | [Dual-Axis Solar Tracking Gimbal](Experiments/Experiment_04/) | **Intermediate** | `0x43C30000` | 3D solar geometry vectors + trigonometric fixed-point LUT + circular modulo error + 4-panel array estimation | `solar_gimbal_core.v`, `solar_vector_engine.v`, `solar_incident_angle_engine.v`, `solar_tracking_controller.v` |
| **05** | [Mars Space Habitat & Defense](Experiments/Experiment_05/) | **Advanced** | `0x43C20000` | Coupled descent dynamics $a = (T - mg)/m$ + 8-channel parallel meteorite detection + kinetic energy $E=\frac{1}{2}mv^2$ + bulkhead isolation | `mars_habitat_core.v`, `mars_landing_physics.v`, `meteorite_parallel_engine.v`, `impact_calculator.v`, `habitat_damage_engine.v` |

---

### Level 1 (Basic): Scene 01 — Underwater Dynamic Probe
- **Target Address:** `0x43C00000` (64 KB aperture)
- **Physics Engine:** Continuous closed-loop depth control with anti-windup PID error integration, upward/downward thrust saturation, and quadratic hydrostatic fluid drag.
- **Finite State Machine:** 7 operational states (`IDLE`, `DESCENDING`, `ASCENDING`, `TARGET_HOLD`, `COLLISION_AVOIDANCE`, `EMERGENCY_SURFACE`, `SYSTEM_FAULT`).
- **Safety Invariant:** Energy limits strictly prevent motor overshoot; depth seeking automatically damps out oscillation within $\pm 0.5\text{ m}$.

---

### Level 1 (Basic): Scene 02 — Smart City Traffic Grid
- **Target Address:** `0x43C40000` (64 KB aperture)
- **16-Channel Kinematics Engine:** Simultaneously updates positions and velocities for 16 vehicles (4 North, 4 South, 4 East, 4 West) at 50 MHz.
- **Green Split Optimizer:** Dynamically shifts green phase duration (10s to 45s) based on real-time arrival queues.
- **Absolute Safety Invariant:** Guaranteed `actual_collision == 0` via the mandatory **Predict-before-Move** pipeline:
  $$\text{Candidate State} \longrightarrow \text{Collision Prediction} \longrightarrow \text{Safety Validation} \longrightarrow \begin{cases} \text{Safe} \to \text{Commit Move} \\ \text{Hazard} \to \text{Clamp to 0 (Hold)} \end{cases}$$
- **Emergency Corridor:** Preempts all signals to grant an all-green priority corridor for emergency vehicles while asserting an all-red mutex on conflicting approaches.

---

### Level 2 (Intermediate): Scene 03 — 3D Maze Runner Engine
- **Target Address:** `0x43C10000` (64 KB aperture)
- **ROM-Based Spatial Storage:** 64-cell (8x8) hardware maze layout stored in on-chip Block RAM/ROM.
- **Hardware Graph Accelerators:**
  - Dedicated **Breadth-First Search (BFS)** engine for shortest-path verification.
  - Dedicated **A* Engine** with Manhattan distance heuristic evaluation for autonomous navigation.
- **Collision Core:** Single-cycle wall boundary check preventing illegal moves.

---

### Level 2 (Intermediate): Scene 04 — Dual-Axis Solar Tracking Gimbal
- **Target Address:** `0x43C30000` (64 KB aperture)
- **3D Vector Mathematics:** Computes unit Sun vector $\vec{S} = [S_x, S_y, S_z]$ and Panel Normal vector $\vec{N} = [N_x, N_y, N_z]$ in Q16.16 fixed-point representation.
- **Incident Angle & Power:** Calculates dot product $\vec{N} \cdot \vec{S} = \cos\theta$ and incident angle in an 18-cycle pipeline.
- **4-Panel Parallel Array:** Computes real-time electrical output for 4 independent photovoltaic panels, factoring in temperature coefficients and cosine loss.
- **Circular Modulo Error Minimization:** Resolves shortest rotational path across the $0^\circ \leftrightarrow 360^\circ$ discontinuity to prevent cable wrap.

---

### Level 3 (Advanced): Scene 05 — Mars Space Habitat & Landing Defense
- **Target Address:** `0x43C20000` (64 KB aperture)
- **Coupled Multi-Domain Computation:** Combines spacecraft descent dynamics with an active 8-channel parallel orbital defense grid.
- **Descent Dynamics Engine:** Real-time numerical integration of Martian descent:
  $$a(t) = \frac{T(t) - m(t) \cdot g_{\text{Mars}}}{m(t)} - \frac{1}{2m(t)} \rho C_d A v(t) |v(t)|$$
  with Martian gravity ($g_{\text{Mars}} = 3.721\text{ m/s}^2$), radar altimeter feedback, and closed-loop throttle control.
- **8-Channel Meteorite Pipeline:** 8 independent hardware tracking units concurrently projecting 3D ballistic ingress trajectories ($x, y, z, v_x, v_y, v_z$).
- **Impact & Damage Engine:** Determines kinetic energy $E = \frac{1}{2}mv^2$ upon hull impact, assesses Section A vs. Section B structural health, and commands autonomous airtight bulkhead isolation.

---

## 4. System Architecture & Hardware/Software Partitioning

```text
                          USER / OPERATOR
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
         PuTTY Serial Terminal        Web Control Panel
         (115200 baud, 8-N-1)         (HTML5 / CSS / JS)
                   │                           │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                        ZYNQ PROCESSING SYSTEM
                         (ARM Cortex-A9 Linux)
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
             CLI Dispatcher              Python Driver
            (Scene Manager)             (Command Parser)
                   │                           │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                        Linux /dev/mem Driver
                       (Physical mmap Aperture)
                                 │
 ════════════════════════════════╪══════════════════════════════════════
                          M_AXI_GP0 BUS (50 MHz)
 ════════════════════════════════╪══════════════════════════════════════
                                 │
                                 ▼
                      ZYNQ PROGRAMMABLE LOGIC
                     (Xilinx XC7Z010-1CLG400C)
                                 │
         ┌───────────────┬───────┴───────┬───────────────┐
         ▼               ▼               ▼               ▼
    EXP 01: UNDERSEA  EXP 02: TRAFFIC  EXP 03: MAZE   EXP 04: SOLAR
   (Depth PID, Drag) (Kinematics, FSM)(ROM, BFS, A*) (Vector Math, LUT)
         │               │               │               │
         └───────────────┼───────────────┼───────────────┘
                         ▼
                 EXP 05: MARS HABITAT
             (Coupled Landing & Meteorites)
```

### Partitioning Responsibilities:

| Subsystem | Execution Domain | Responsibilities |
|---|---|---|
| **Programmable Logic (PL)** | Verilog RTL @ 50 MHz | Authoritative state machines, discrete physics integration, 16-channel vehicle kinematics, 8-channel meteorite tracking, collision checks, trigonometric LUT, BFS/A* accelerators. |
| **Processing System (PS)** | ARM Cortex-A9 (Linux) | Interactive CLI shell, command string parsing, user menu rendering, memory-mapped `/dev/mem` 32-bit register reads/writes, telemetry decoding. |
| **Developer Laptop (Option)** | Python 3 RTL Emulator | Cycle-accurate, bit-accurate software models replicating Verilog registers, counters, and arithmetic clamping for hardware-free development and CI. |

---

## 5. Universal AXI4-Lite Register Memory Map

All five FPGA scenes connect to the Processing System master port `M_AXI_GP0` across dedicated 64 KB apertures:

| Peripheral Base | Scene | Key Registers & Offsets |
|---|---|---|
| `0x43C00000` | **Underwater Probe** | `+0x00` CONTROL, `+0x04` DEPTH_CFG, `+0x08` CURRENT, `+0x0C` STATUS, `+0x10` POSITION, `+0x14` COUNTERS, `+0x18` CYCLES |
| `0x43C10000` | **3D Maze Runner** | `+0x00` CONTROL, `+0x04` STATUS, `+0x08` POSITION, `+0x0C` COUNTERS, `+0x10` TIMER, `+0x14` MAZE_MEM (ROM access) |
| `0x43C20000` | **Mars Space Habitat** | `+0x00` CONTROL, `+0x04` ATTACK, `+0x08` THRESHOLD, `+0x0C` STATUS, `+0x10` IMPACT, `+0x14` COUNTERS, `+0x18` TOTAL |
| `0x43C30000` | **Solar Tracking Gimbal** | `+0x00` CONTROL, `+0x04` SUN_POS, `+0x08` PANEL_POS, `+0x0C` STATUS, `+0x10` ERROR, `+0x14` ACTUATORS, `+0x1C` SUN_VEC, `+0x34` DOT_PROD, `+0x3C` POWER, `+0x50` FAULT |
| `0x43C40000` | **Smart City Traffic** | `+0x00` CONTROL, `+0x04` CONFIG, `+0x08` TIMING, `+0x0C` STATUS, `+0x10` TELEMETRY, `+0x18` QUEUES_NS, `+0x1C` QUEUES_EW, `+0x24` DYN_SPLITS, `+0x3C` FAULT, `+0x48-54` VEH_POS |

*Full bitfield definitions, read/write masks, and reset values are documented in [Documentation/AXI_Register_Map.md](Documentation/AXI_Register_Map.md).*

---

## 6. EDGE Zynq Z7010 Hardware Deployment Guide

Follow these steps to run the complete system natively on physical hardware:

### Prerequisites:
- **Board:** AMD EDGE ZYNQ Z7010 SoC (XC7Z010-1CLG400C)
- **Cables:** Micro-USB cable for JTAG programming + Micro-USB cable for USB-UART serial
- **Software:** Xilinx Vivado 2020.2+ (Host PC) + PuTTY / minicom
- **Zynq OS:** Embedded Linux (PetaLinux, Ubuntu ARM, or PYNQ rootfs) booting from Micro-SD

```text
  ┌─────────────────────────────────────────────────────────────┐
  │                 EDGE ZYNQ Z7010 BOARD                       │
  │                                                             │
  │  [ Micro-USB JTAG ] ──────── USB Cable ────> Host PC (Vivado)
  │                                                             │
  │  [ Micro-USB UART ] ──────── USB Cable ────> Host PC (PuTTY) │
  │                                                             │
  │  [ Micro-SD Card  ] <─────── Boot Image (Linux + boot.bin)  │
  │                                                             │
  │  [ 5V DC Power    ] <─────── 5V Power Supply / USB          │
  └─────────────────────────────────────────────────────────────┘
```

### Step 1: Program the PL Bitstream
1. Connect the JTAG USB cable to the host PC.
2. Open **Vivado Hardware Manager** and connect to the target board.
3. Program the bitstream (`multi_scene_top.bit` for all scenes, or individual scene bitstreams).
4. **Close or minimize Vivado.** Vivado is not used during runtime execution.

### Step 2: Establish Serial Connection via PuTTY
1. Connect the USB-UART cable to the host PC.
2. Identify the COM port in Windows Device Manager (e.g. `COM4` or `COM5`).
3. Open **PuTTY** and set:
   - **Connection Type:** Serial
   - **Serial line:** `COM4` (or `/dev/ttyUSB0` on Linux)
   - **Speed (Baud):** `115200`
   - **Data bits:** `8` | **Stop bits:** `1` | **Parity:** `None` | **Flow control:** `None`
4. Click **Open** and log into Zynq Linux as `root`.

### Step 3: Transfer & Launch Software on Zynq
From your host PC, copy the repository to the board:
```bash
scp -r ./V_SPACE root@192.168.1.10:/home/root/v_space
```

On the Zynq terminal (inside PuTTY):
```bash
cd /home/root/v_space/deploy
sudo ./setup_zynq.sh
sudo ./run_cli.sh
```

You will enter the universal interactive hardware console:
```text
========================================================
       ZYNQ Z7010 MULTI-SCENE FPGA CONTROL SYSTEM       
========================================================
FPGA STATUS : HARDWARE ACTIVE
TRANSPORT   : AXI (/dev/mem)
PROCESSOR   : ZYNQ ARM CORTEX-A9
MODE        : FPGA AUTHORITATIVE
========================================================
FPGA> scene traffic
FPGA[traffic]> auto
FPGA[traffic]> status
```

---

## 7. Verification, Testing & MATLAB Golden Models

### 1. Automated Python Regression & Parity Tests
The repository includes 25 unit test suites covering register mapping, fixed-point conversion, FSM transitions, safety invariants, and hardware fail-fast policies:

```bash
# Run all automated tests from the repository root:
python -m unittest discover tests/
```

Key test suites:
- `test_traffic_safety.py`: Verifies zero-collision invariants (`actual_collision == 0`) across 10,000 randomized traffic scenarios.
- `test_rtl_emulator_parity.py`: Validates cycle-accurate, bit-accurate parity between Verilog RTL and Python emulation models.
- `test_hardware_failure.py`: Verifies truthful fail-fast reporting when physical `/dev/mem` registers are unreachable.
- `test_mars_performance_comparison.py`: Measures execution throughput of the 8-channel meteorite collision engine.

### 2. MATLAB Golden Reference Models
The [`MATLAB/`](MATLAB/) directory contains Float64 double-precision reference models:
- **Mathematical Parity Verification:** Verifies that fixed-point FPGA math (Q16.16) strictly aligns with IEEE-754 double precision within designated quantization limits.
- **Automated Validation:** Execute `matlab_engine_example.py` or run `prepareFPGAInput.m` and `processScene.m` inside MATLAB R2021b+ to validate scene datapaths.

---

## 8. Repository Directory Structure

```text
V_SPACE/
├── index.html                   # Interactive Web Control Station (UI Entrypoint)
├── style.css                    # Engineering-grade UI design system & CRT styles
├── app.js                       # Client-side FPGA evaluation & UI state machine
├── terminal_ui.py               # Terminal-native curses UI (Software visualization mode)
├── main.py                      # Curses dashboard launcher
├── run_cli.py                   # Root entrypoint for universal multi-scene CLI
│
├── Experiments/                 # Verilog RTL Hardware Cores (Vivado Projects)
│   ├── Experiment_01/           # Underwater Dynamic Probe (Depth PID, Drag, Recovery)
│   ├── Experiment_02/           # Smart City Traffic Grid (16-Vehicle Kinematics, Green Split)
│   ├── Experiment_03/           # 3D Maze Runner Engine (8x8 ROM, BFS / A* Accelerators)
│   ├── Experiment_04/           # Dual-Axis Solar Tracking Gimbal (3D Vectors, Trig LUT)
│   └── Experiment_05/           # Mars Space Habitat & Defense (Coupled Descent, 8-Ch Meteorites)
│
├── python/                      # Universal Runtime & Dual-Execution Framework
│   ├── backends/                # Physical AXI (/dev/mem) & Mock Hardware Interfaces
│   ├── cli/                     # Universal interactive CLI & syntax parser
│   ├── core/                    # System runtime & scene dispatch manager
│   ├── emulation/               # Bit-accurate Python RTL models of Verilog cores
│   ├── protocol/                # Register maps, enums, packet encoding, error definitions
│   └── scenes/                  # High-level Python scene drivers
│
├── deploy/                      # Zynq Hardware Deployment Scripts
│   ├── README.md                # Deployment walkthrough
│   ├── run_cli.sh               # Shell script to start the CLI with elevated privileges
│   └── setup_zynq.sh            # Script to verify kernel modules & /dev/mem permissions
│
├── Documentation/               # Hardware & Vivado Specifications
│   ├── AXI_Register_Map.md      # Complete 32-bit register map & bitfield layouts
│   ├── Board_Setup.md           # EDGE Zynq Z7010 board setup & cable pinouts
│   ├── Project_Overview.md      # Detailed system overview and partitioning rules
│   ├── Resource_Utilization.md  # LUT, FF, BRAM, DSP slice utilization reports
│   ├── Troubleshooting.md       # Hardware & software troubleshooting guide
│   └── Vivado_Setup.md          # Synthesis, implementation & bitstream generation guide
│
├── MATLAB/                      # Mathematical Golden Reference Models
│   ├── README.md                # MATLAB integration & validation guide
│   ├── comparison_engine.py     # Python-to-MATLAB verification engine
│   ├── prepareFPGAInput.m       # Pre-processing script formatting inputs for FPGA
│   └── processScene.m           # Reference simulation runner
│
├── tests/                       # Automated Unit & Parity Test Suite (25 Test Files)
├── environments/                # Terminal curses environment visualizers
├── cli/                         # Curses menu and frame rendering utilities
├── hardware/                    # Low-level hardware connection & health monitors
├── LICENSE                      # MIT License
└── CONTRIBUTING.md              # Contribution standards & architectural rules
```

---

## 9. Contributing & Architectural Rules

Contributions to the V_SPACE project must adhere to the rules outlined in [`CONTRIBUTING.md`](CONTRIBUTING.md):
1. **Preserve Hardware Authority:** Never implement simulation physics in software as a substitute for FPGA logic.
2. **Fixed-Point Arithmetic:** Arithmetic in the PL must strictly use designated fixed-point formats (Q16.16, Q12.4, or scaled integer units).
3. **Strict AXI Address Decoupling:** Register offsets must adhere strictly to the 64 KB memory apertures in [Documentation/AXI_Register_Map.md](Documentation/AXI_Register_Map.md).
4. **Timing Closure:** All Verilog modifications must meet timing (**WNS $\ge$ 0.000 ns** at the 50 MHz clock).
5. **Parity Tests:** All changes must pass the regression suite (`python -m unittest discover tests/`).

---

## 10. License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
