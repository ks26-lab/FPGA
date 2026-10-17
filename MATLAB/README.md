# MATLAB Reference Model & Preprocessing Layer for FPGA Pipeline

This package provides:
1. **The Preprocessing & Filtering Layer** (`processScene.m`, `prepareFPGAInput.m`)
2. **The Golden Reference Model & Comparison Engine** (`runReferenceModel.m`, `compareResults.m`, `comparison_engine.py`)

---

## 1. System Architecture

### A. Preprocessing / Deployment Mode
```
CLI ──> Python ──> MATLAB (processScene) ──> Python ──> Zynq FPGA ──> Python ──> CLI
```

### B. Verification / Comparison Mode (MATLAB vs FPGA)
```
                  ┌───────────────────────────────┐
                  │       CLI / User Input        │
                  │  analyze depth=50 weight=75   │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │ Structured Input Vector │
                     └────────────┬────────────┘
                                  │
            ┌─────────────────────┴─────────────────────┐
            ▼                                           ▼
┌──────────────────────────────┐            ┌───────────────────────────┐
│ MATLAB Golden Reference      │            │ Zynq-7000 FPGA Hardware   │
│ (Double-Precision Float64)   │            │ (Fixed-Point Arithmetic)  │
│ - filterDepth / EMA          │            │ - DSP Blocks & Registers  │
│ - Error & PD Control Law     │            │ - Hardware Acceleration   │
│ - Intermediate Stage Logs    │            │ - UART/AXI Register Read  │
└──────────────┬───────────────┘            └─────────────┬─────────────┘
               │                                          │
               │ MATLAB Result                            │ FPGA Result
               └────────────────────┬─────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │  Python Comparison Engine   │
                     │  (Per-Signal Tolerances)    │
                     └──────────────┬──────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │ CLI Verification Report     │
                     │ PASS / FAIL & Stage Diffs   │
                     └─────────────────────────────┘
```

- **MATLAB is the Golden Reference Model**: Written for mathematical precision (`float64`), clarity, and strict physical correctness.
- **The FPGA is the Hardware Implementation**: Written in Verilog, operating with fixed-point DSP/register constraints.
- **Python is the Comparison Orchestrator**: Collects results from both paths, verifies whether hardware output matches reference within tolerance, and presents granular intermediate diffs.

---

## 2. Directory Layout

```
MATLAB/
├── processScene.m                 # Preprocessing & filtering dispatcher
├── prepareFPGAInput.m             # Centralized FPGA packet formatter
├── comparison_engine.py           # Python comparison runner & CLI presenter
├── matlab_engine_example.py       # Python MATLAB Engine example
│
├── reference/
│   ├── runReferenceModel.m        # Primary Golden Reference Model dispatcher
│   ├── referenceUnderwater.m      # Golden model for underwater ROV depth control
│   ├── referenceTraffic.m         # Golden model for smart city intersection control
│   └── referenceSpaceHabitat.m    # Golden model for Mars habitat life support
│
├── filtering/
│   ├── movingAverage.m            # Reference Causal Moving Average filter
│   ├── exponentialFilter.m        # Reference Exponential Moving Average (EMA)
│   ├── medianFilter.m             # Reference Sliding Median filter
│   ├── applyFilterKernel.m        # Core filter implementation
│   ├── filterDepth.m              # Depth sensor filter
│   ├── filterPressure.m           # Pressure sensor filter
│   ├── filterTemperature.m        # Temperature sensor filter
│   ├── filterVelocity.m           # Velocity filter
│   └── filterAcceleration.m       # Acceleration filter
│
├── preprocessing/
│   ├── normalizeData.m            # Zero-division safe normalization
│   └── calculateDerivedValues.m   # Physical & FPGA-oriented derived calculations
│
├── validation/
│   └── validateInput.m            # Strict input validation
│
├── comparison/
│   └── compareResults.m           # MATLAB comparison verification module
│
├── testing/
│   └── generateTestVectors.m      # 10 deterministic test stimulus vectors
│
└── tests/
    └── testFiltering.m            # Automated MATLAB test suite
```

---

## 3. Mathematical Reference Models

### A. Underwater Depth Control Scene (`referenceUnderwater.m`)
1. **Filtering**:
   $$d_{\text{filt}}[k] = \alpha \cdot d_{\text{raw}}[k] + (1 - \alpha) \cdot d_{\text{filt}}[k-1]$$
2. **Hydrostatic Conversion** (if pressure measured):
   $$h_{\text{hydro}} = \frac{P - P_0}{\rho g}$$
3. **Tracking Error**:
   $$e = d_{\text{target}} - d_{\text{filt}}$$
4. **PD Ballast & Vertical Thrust Law**:
   $$u_{\text{raw}} = 50.0 + K_p \cdot e - K_d \cdot v$$
   $$u = \min(100.0, \max(0.0, u_{\text{raw}}))$$
   where $K_p = 1.25$, $K_d = 0.50$.
5. **State**:
   - $e > 0.5 \implies \text{DESCENDING}$
   - $e < -0.5 \implies \text{ASCENDING}$
   - Otherwise $\implies \text{HOLDING}$

### B. Intelligent Traffic Scene (`referenceTraffic.m`)
1. **Velocity Filtering & Conversion**:
   $$v_{\text{kmh}} = v_{\text{filt}} \times 3.6$$
2. **Dynamic Green Time Allocation**:
   $$t_{\text{green}} = \text{clamp}(30.0 + 1.50 \cdot q - 0.50 \cdot (v_{\text{kmh}} - 30.0), 10.0, 90.0)$$

### C. Space Habitat Environmental Scene (`referenceSpaceHabitat.m`)
1. **Atmospheric Error**:
   $$e_P = P_{\text{target}} - P_{\text{filt}}, \quad e_T = T_{\text{target}} - T_{\text{filt}}$$
2. **Life Support Actuation**:
   $$u_{\text{valve}} = \text{clamp}(50.0 + 10.0 \cdot e_P, 0.0, 100.0)$$
   $$u_{\text{thermal}} = \text{clamp}(50.0 + 5.0 \cdot e_T, 0.0, 100.0)$$

---

## 4. Per-Field Tolerances for FPGA Verification

Because the FPGA utilizes fixed-point math ($Q16.16$ or 16-bit integer registers) and MATLAB runs in IEEE 754 `float64`, the comparison engine evaluates each physical quantity against domain-specific tolerances:

| Signal | Absolute Tolerance | Relative Tolerance | Verification Criteria |
|---|---|---|---|
| **Depth** | $\pm 0.05\text{ m}$ | $\pm 2.0\%$ | $|d_M - d_F| \le 0.05$ OR $\frac{|d_M - d_F|}{|d_M|} \le 0.02$ |
| **Control Output** | $\pm 0.50\%$ | $\pm 1.0\%$ | $|u_M - u_F| \le 0.50$ OR $\frac{|u_M - u_F|}{|u_M|} \le 0.01$ |
| **Velocity** | $\pm 0.10\text{ m/s}$ | $\pm 2.0\%$ | Magnitude difference |
| **Pressure** | $\pm 0.10\text{ kPa}$ | $\pm 2.0\%$ | Atmospheric / hydrostatic |
| **Temperature**| $\pm 0.10^\circ\text{C}$ | $\pm 2.0\%$ | Thermal sensor channel |
| **Operational State**| Exact Match | — | Strings must match identically |

---

## 5. Running the Python Comparison Engine

You can execute the comparison directly from the command line:

```bash
python MATLAB/comparison_engine.py analyze depth=50 weight=75 height=10
```

### CLI Output Presentation:

```
========================================
        MATLAB vs FPGA
========================================

INPUT
Depth       : 50.00 m
Weight      : 75.00 kg
Height      : 10.00 m

OUTPUT                 MATLAB       FPGA
----------------------------------------
Filtered Depth         48.730       48.721
Control Output         63.420       63.401
State                  DESCENDING   DESCENDING

ERROR
----------------------------------------
Depth Error             0.009 m
Control Error           0.019 %
Maximum Error           0.019 %

VERDICT
----------------------------------------
PASS
FPGA matches MATLAB reference
========================================

INTERMEDIATE-VALUE DEBUGGING
-----------------------------------------------------
Stage                  MATLAB       FPGA       Error     
-----------------------------------------------------
Filtered Depth         48.73        48.72      0.01      
Error                  1.27         1.28       0.01      
Control Output         63.42        63.40      0.02      
-----------------------------------------------------
```

---

## 6. Test Vectors (`generateTestVectors.m`)

Run in MATLAB:
```matlab
vectors = generateTestVectors('test_vectors.json');
```

Generates 10 standard test cases:
1. `Normal_Underwater_Descent`: Nominal operating condition
2. `Minimum_Boundary_Surface`: Zero depth boundary
3. `Maximum_Boundary_Deep`: 10,900 m trench upper boundary
4. `Zero_Error_Holding`: Exact target match
5. `Noisy_Sensor_Stream`: Multi-sample noise burst
6. `Impulsive_Sensor_Outlier`: Corrupted 450 m spike
7. `Ascending_Overshoot`: Ascent state recovery
8. `Traffic_Intersection_Congestion`: Vehicle queue allocation
9. `Space_Habitat_Pressure_Drop`: Environmental valve actuation
10. `Micro_Precision_Delta`: Sub-millimeter float64 quantization boundary
