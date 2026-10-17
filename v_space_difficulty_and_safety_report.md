# V_SPACE Difficulty Hierarchy & Safety Constraint Enforcement Report

**Target FPGA:** EDGE ZYNQ Z7010  
**Device:** XC7Z010-1CLG400C  
**Project:** V_SPACE  

---

## 1. Executive Summary

This report documents the architectural audit, difficulty level classification enforcement, deterministic safety constraint implementation, and verification for the five computational scenes of the `V_SPACE` Zynq Z7010 FPGA system.

Difficulty levels are strictly defined by **computational complexity** and **system architecture**, not by visual presentation, Python code size, or UI element count.

---

## 2. Difficulty Level Hierarchy & Definitions

### LEVEL 1 — BASIC
**Definition:** A single-domain deterministic feedback/control system with ONE dominant computational task. Supporting state machines and monitoring logic are permitted, but multi-domain coupled simulations are strictly forbidden.
- **Scenes Classified:**
  1. *Underwater Dynamic Probe*
  2. *Smart City Traffic Grid*

### LEVEL 2 — INTERMEDIATE
**Definition:** A system requiring spatial reasoning, graph search/optimization, or 3D mathematical transformation pipelines across bounded dynamic states.
- **Scenes Classified:**
  3. *3D Maze Runner*
  4. *Solar Tracking Gimbal*

### LEVEL 3 — ADVANCED
**Definition:** A system containing **multiple concurrent and coupled subsystems** operating simultaneously and directly affecting each other's outcomes (cascading consequences, hazard propagation, autonomous recovery).
- **Scenes Classified:**
  5. *Mars Space Habitat*

---

## 3. Detailed Scene Audits & Status

### Scene 1: Underwater Dynamic Probe
- **DIFFICULTY LEVEL:** BASIC
- **PRIMARY COMPUTATION:** Closed-loop depth control + 1D/2D hydrostatic physical dynamics.
- **REQUIRED FEATURES:** Target-depth error, PID control with anti-windup, thrust response, quadratic drag $F_d = -c \cdot v |v|$, velocity/depth update, collision detection, 7-state recovery FSM, energy/thrust bounding.
- **FORBIDDEN / OUT-OF-SCOPE FEATURES:** Navier-Stokes, CFD, full fluid turbulence, particle solvers, multi-probe swarms, reinforcement learning.
- **FPGA-AUTHORITATIVE COMPUTATION:** `underwater_probe_core.v`, `underwater_physics_engine.v`, `underwater_pid_controller.v`, `underwater_drag_engine.v`, `underwater_collision_engine.v`.
- **SOFTWARE-ONLY FUNCTIONS:** Telemetry visualization, PuTTY/CLI interface, parameter configuration, software fallback.
- **TEST STATUS:** PASS
- **FINAL STATUS:** COMPLETE

### Scene 2: Smart City Traffic Grid
- **DIFFICULTY LEVEL:** BASIC
- **PRIMARY COMPUTATION:** Traffic signal arbitration FSM + queue accumulation + demand-driven green split optimization + deterministic vehicle kinematics + zero-collision safety pipeline.
- **REQUIRED FEATURES:** 7-state FSM, queue tracking, dynamic green split, emergency preemption corridor, 16-channel vehicle kinematics, lane-aware movement, vehicle safety validation.
- **ABSOLUTE SAFETY INVARIANT:** `actual_collision == 0` for all committed states.
- **MANDATORY MOVEMENT PIPELINE:**
  $$\text{CURRENT STATE} \longrightarrow \text{DESIRED NEXT STATE} \longrightarrow \text{COLLISION PREDICTION} \longrightarrow \text{SAFETY VALIDATION} \longrightarrow \text{SAFE?} \begin{cases} \text{YES} \to \text{MOVE} \\ \text{NO} \to \text{HOLD/STOP} \end{cases}$$
- **PREDICT BEFORE MOVE:** Predicts candidate position/velocity; if unsafe (rear-end violation or conflicting intersection entry), position is held (`pos_next = pos`) and velocity set to 0. `collision_prevented_mask = 1`.
- **FORBIDDEN / OUT-OF-SCOPE FEATURES:** IDM driver models, stochastic driver behavior, random lane changing, route planning, ML traffic prediction.
- **FPGA-AUTHORITATIVE COMPUTATION:** `traffic_core.v`, `traffic_parallel_vehicle_engine.v`, `traffic_green_split_optimizer.v`, `traffic_queue_engine.v`, `traffic_emergency_corridor.v`, `traffic_fault_detector.v`.
- **SOFTWARE-ONLY FUNCTIONS:** ASCII traffic grid visualization, CLI command dispatch.
- **TEST STATUS:** PASS (Explicit safety test suite `tests/test_traffic_safety.py` covering TEST 1..8 executed and passed).
- **FINAL STATUS:** COMPLETE

### Scene 3: 3D Maze Runner
- **DIFFICULTY LEVEL:** INTERMEDIATE
- **PRIMARY COMPUTATION:** Real-time spatial reasoning + collision detection + graph search (BFS / A*).
- **REQUIRED FEATURES:** Player state/position, wall collision, boundary detection, goal detection, Manhattan distance, hardware BFS, hardware A*, path/route reasoning, 30-second game timer, win/timeout state machine.
- **FORBIDDEN / OUT-OF-SCOPE FEATURES:** SLAM, reinforcement learning, multi-agent planning, dynamic 3D physics engines.
- **FPGA-AUTHORITATIVE COMPUTATION:** `maze_core.v`, `maze_bfs_engine.v`, `maze_astar_engine.v`, `maze_collision_engine.v`, `maze_distance_engine.v`.
- **SOFTWARE-ONLY FUNCTIONS:** Maze terminal UI, user movement input sending.
- **TEST STATUS:** PASS
- **FINAL STATUS:** COMPLETE

### Scene 4: Solar Tracking Gimbal
- **DIFFICULTY LEVEL:** INTERMEDIATE
- **PRIMARY COMPUTATION:** 3D solar geometry + mathematical vector transformation pipeline + tracking control.
- **REQUIRED FEATURES:** Sun position, Sun vector calculation ($x,y,z$), Panel normal vector, vector dot product ($S \cdot N$), incident angle ($\theta = \arccos(S \cdot N)$), tracking error, Azimuth/Elevation control, $0^\circ-360^\circ$ angle wrapping, solar power estimation ($P = I_0 A \eta \cos\theta$), 4-channel panel array processing.
- **FORBIDDEN / OUT-OF-SCOPE FEATURES:** Dual-diode PV physics, thermal degradation models, weather forecasting, grid energy optimization.
- **FPGA-AUTHORITATIVE COMPUTATION:** `solar_gimbal_core.v`, `solar_vector_engine.v`, `solar_incident_angle_engine.v`, `solar_tracking_controller.v`, `solar_power_engine.v`, `solar_trig_table.v`.
- **SOFTWARE-ONLY FUNCTIONS:** Sun dataset playback, gimbal visualization dashboard.
- **TEST STATUS:** PASS
- **FINAL STATUS:** COMPLETE

### Scene 5: Mars Space Habitat
- **DIFFICULTY LEVEL:** ADVANCED
- **PRIMARY COMPUTATION:** Coupled landing physics + autonomous hazard processing + habitat protection.
- **REQUIRED CONCURRENT & COUPLED SUBSYSTEMS:**
  1. *Landing / Descent Dynamics:* $a = \frac{T - mg}{m}$, $v[n+1] = v[n] + a \cdot dt$, $h[n+1] = h[n] + v[n] \cdot dt$.
  2. *Retro-Thrust Controller:* Closed-loop altitude/velocity descent profile tracking.
  3. *8-Channel Parallel Meteorite Processing Engine:* Trajectory detection & impact localization.
  4. *Impact Energy Calculator:* $E = \frac{1}{2} m v^2$.
  5. *Structural Damage Assessment Engine:* Section A and Section B damage tracking.
  6. *Panel Isolation & Life Support System:* Emergency panel isolation and $O_2 / CO_2$ pressure regulation.
- **ADVANCED COUPLING:** Meteorite impacts damage habitat panels $\to$ triggers life-support pressure response $\to$ landing guidance & hazard supervisor adjust thrust profiles concurrently.
- **FPGA-AUTHORITATIVE COMPUTATION:** `mars_habitat_core.v`, `mars_landing_physics.v`, `meteorite_parallel_engine.v`, `impact_calculator.v`, `habitat_damage_engine.v`, `mars_life_support_engine.v`, `mars_thrust_controller.v`.
- **SOFTWARE-ONLY FUNCTIONS:** Habitat visualization console, telemetry logging.
- **TEST STATUS:** PASS
- **FINAL STATUS:** COMPLETE

---

## 4. Modified Files & System Changes

1. **`python/backends/laptop_fpga_backend.py`**
   - Implemented `get_backend_name()` method required by `BaseExecutionBackend` abstract contract.

2. **`python/scenes/solar_gimbal/__init__.py` & `python/scenes/traffic/__init__.py`**
   - Fixed missing `BASE_ADDRESS` package exports.

3. **`python/emulation/clock.py`**
   - Added `register_model()`, `start_autonomous_ticks()`, `stop_autonomous_ticks()`, `tick_count`, and `is_running` interface methods to `FPGASimulationClock`.

4. **`fpga_interface/verilog/traffic_parallel_vehicle_engine.v`**
   - Implemented 2-stage PREDICT $\to$ PREVENT vehicle movement pipeline.
   - Added `actual_collision` invariant flag and `collision_prevented_mask`.
   - Guaranteed `actual_collision == 0` for all committed states.

5. **`python/emulation/traffic_model.py`**
   - Updated Python RTL emulation model to replicate 2-stage PREDICT $\to$ PREVENT vehicle kinematics and zero-collision invariant.

6. **`tests/test_traffic_safety.py`**
   - Created dedicated Smart City safety verification test suite implementing TEST 1 through TEST 8 and mandatory `actual_collision == 0` assertions.

---

## 5. Verification & Test Execution Summary

| Test Suite | Target Component / Requirement | Result |
| :--- | :--- | :--- |
| `test_underwater_parallel_blocks.py` | Underwater Probe PID, drag, depth control | **PASS** |
| `test_traffic_parallel_blocks.py` | Smart City Traffic 7-state FSM & 16-channel engine | **PASS** |
| `test_traffic_safety.py` | Smart City Safety Verification (TEST 1..8, zero collision) | **PASS** |
| `test_maze_parallel_blocks.py` | 3D Maze Runner BFS & A* Pathfinding | **PASS** |
| `test_solar_parallel_blocks.py` | Solar Gimbal 3D Vector & Incident Angle Engine | **PASS** |
| `test_mars_parallel_blocks.py` | Mars Habitat Descent & 8-Channel Meteorite Coupling | **PASS** |
| `test_rtl_emulator_parity.py` | Bit-accurate RTL vs Emulator Parity | **PASS** |

---

COMPLETE —
IMPLEMENTATION COMPLETE; HARDWARE VERIFICATION PENDING
