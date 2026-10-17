# ANTI-GRAVITY / ASSET INTEGRITY MASTER SPECIFICATION

## PURPOSE & HARD ARCHITECTURAL CONSTRAINT
All vessels, vehicles, probes, rovers, spacecraft, drones, meteorites, and moving entities in this CLI simulation must behave as **SINGLE, RIGID, COHERENT OBJECTS**.

An object must **NEVER** visually break apart, stretch, deform, rotate incorrectly, teleport unexpectedly, lose characters, or have its individual components drift away from its body while moving.

```
┌────────────────────────────────────────────────────────────────────────┐
│ ONE OBJECT = ONE RIGID VISUAL UNIT                                     │
│ Characters inside an asset NEVER participate independently in physics.  │
│ Physics operates strictly on the object's canonical bounding box.      │
│ The renderer converts whole-asset coordinates to terminal cells.       │
│ If visual effects conflict with asset integrity: INTEGRITY ALWAYS WINS.│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 1. THE RIGID OBJECT ARCHITECTURE

A vessel or vehicle is **NOT** a collection of independent characters.

### Incorrect Model (Prohibited):
```
body    -> moves independently
wheel   -> moves independently
antenna -> moves independently
sensor  -> moves independently
```

### Canonical Model (Mandatory):
```
VESSEL
  ├── Canonical Visual Representation (Preserved Rectangular Grid)
  ├── Fixed Bounding Box (width × height)
  ├── Canonical Anchor Point (anchor_x, anchor_y)
  ├── World Position (float x, float y)
  ├── World Velocity (vx, vy)
  ├── Canonical Orientation (predefined variant)
  └── Discrete State (IDLE, MOVING, IMPACT, etc.)
```

The entire visual representation moves as **one inseparable unit**.

---

## 2. FIXED BOUNDING BOX & WHITESPACE PRESERVATION
Every asset must have a strictly fixed rectangular bounding box ($W \times H$).
- Empty spaces inside the rectangle are intentional and must be preserved.
- **NEVER** trim whitespace from individual frames or lines.
- **NEVER** allow bounding box dimensions to change during movement.
- **NEVER** allow different parts of an object to use different coordinates.

---

## 3. CANONICAL ANCHOR POINT
Every asset defines one single anchor point:
```
           ┌──────────────┐
           │   ASSET      │
           └──────┬───────┘
                  ● (anchor_x, anchor_y)
```
- The simulation stores and updates **only** the anchor position `(x, y)`.
- The renderer derives the position of every character from the anchor:
  $$\text{screen\_x} = \text{round}(x - \text{anchor\_x}) + \text{char\_col}$$
  $$\text{screen\_y} = \text{round}(y - \text{anchor\_y}) + \text{char\_row}$$
- Individual characters **never** possess independent world coordinates.

---

## 4. DETERMINISTIC MOVEMENT & SUB-STEPPING
Movement must be continuous and deterministic:
$$x_{\text{new}} = x + v_x \cdot \Delta t$$
$$y_{\text{new}} = y + v_y \cdot \Delta t$$

### High-Speed Objects (Meteorites, Projectiles)
To prevent tunneling and visual discontinuities, movement must be subdivided into substeps:
$$\text{Frame} \longrightarrow \text{Substep 1} \longrightarrow \text{Substep 2} \longrightarrow \text{Substep 3} \longrightarrow \text{Final Position}$$
Maximum displacement per substep is clamped to prevent jumps larger than the object's collision envelope.

---

## 5. BOUNDARY ENFORCEMENT POLICIES

| Policy | Rule | Canonical Applied Assets |
|---|---|---|
| **`CLAMP`** | Complete bounding box is clamped to valid area $[0, \text{world} - \text{dim}]$. Never allow an asset to partially escape. | `PROBE_V1`, `ROVER_V1` |
| **`WRAP`** | Despawn upon crossing outer exit bound, re-enter smoothly on opposite entry boundary. | `FISH_S`, `FISH_M` |
| **`DESPAWN`** | Extinguish and free entity upon reaching boundary condition. | `BUBBLE` (surface), `SONAR_PULSE` ($r_{\text{max}}$), `IMPACT_EFFECT` |
| **`BOUNCE`** | Invert velocity component upon collision with boundary. | Test probes |
| **`EXIT_ALLOWED`** | Permitted to cross boundary to despawn off-screen without distortion. | `METEORITE` |
| **`LANE_CLAMP`** | Constrained to road lane vector. Cannot leave road geometry. | `CAR_SEDAN_V1`, `BUS_V1`, `TRUCK_V1` |
| **`STATIONARY`** | Translation strictly prohibited ($v = 0$). Dynamic changes restricted to discrete orientation/state. | `SOLAR_PANEL_V1`, `TRAFFIC_LIGHT` |

---

## 6. FRAMEBUFFER RENDERING PIPELINE

To prevent flickering, tearing, leftover characters, and ghosting:
```
SIMULATION ENGINE
       ↓
RIGID ENTITY STATES & INTEGRITY VALIDATION
       ↓
SORT INTO DETERMINISTIC LAYER ORDER
       ↓
WRITE TO 2D FRAMEBUFFER MATRIX (BUFFER_B)
       ↓
DIFF & BLIT TO TERMINAL (BUFFER_A ← BUFFER_B)
```

### Deterministic Layer Order
1. Background
2. Environmental terrain & effects
3. Large static fixtures
4. Moving vessels & vehicles
5. Small secondary entities
6. Particles (bubbles, dust)
7. UI / Telemetry overlays

---

## 7. THE 22 NON-NEGOTIABLE INVARIANTS

1. **`INVARIANT_1`**: One object = one rigid visual unit.
2. **`INVARIANT_2`**: Asset dimensions do not change during movement.
3. **`INVARIANT_3`**: Internal character coordinates do not change during movement.
4. **`INVARIANT_4`**: Only the object's transform, orientation, or discrete state changes.
5. **`INVARIANT_5`**: Physics operates on the object bounding box, never individual characters.
6. **`INVARIANT_6`**: Objects cannot leave permitted boundaries accidentally.
7. **`INVARIANT_7`**: The same asset ID always represents the same visual identity.
8. **`INVARIANT_8`**: Rendering is deterministic and reproducible.
9. **`INVARIANT_9`**: Previous-frame characters must never remain after movement.
10. **`INVARIANT_10`**: A corrupted asset must never be silently rendered.
11. **`INVARIANT_11`**: No arbitrary character rotations; use canonical orientation variants.
12. **`INVARIANT_12`**: Whitespace inside the asset rectangle is sacred and preserved.
13. **`INVARIANT_13`**: Maximum per-frame movement is bounded by velocity $\times \Delta t$.
14. **`INVARIANT_14`**: World coordinates use floating-point numbers; cell quantization occurs globally at render.
15. **`INVARIANT_15`**: Teleportation between arbitrary coordinates is forbidden unless explicitly defined as a scenario event.
16. **`INVARIANT_16`**: State transitions must proceed through defined lifecycles (`SPAWN` $\to$ `ACTIVE` $\to$ `EVENT` $\to$ `DESPAWN`).
17. **`INVARIANT_17`**: Assets must not morph into unrelated visual forms.
18. **`INVARIANT_18`**: Sub-stepping is required for high-speed entities to prevent tunneling.
19. **`INVARIANT_19`**: Layered rendering prevents permanent overwriting of asset identities.
20. **`INVARIANT_20`**: Randomness may control spawn position, velocity, and timing, but NEVER asset geometry.
21. **`INVARIANT_21`**: All assets must come from the canonical Asset Library.
22. **`INVARIANT_22`**: If visual effects conflict with asset integrity, **ASSET INTEGRITY ALWAYS WINS**.
