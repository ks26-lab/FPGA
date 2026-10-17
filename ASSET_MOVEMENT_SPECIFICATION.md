# ASSET PLACEMENT + MOVEMENT CONSTRAINT MASTER SPECIFICATION

## GENERAL ARCHITECTURAL PRINCIPLE

Every asset in the simulation system MUST have a predefined spatial role and an explicit movement profile.

For every asset, the simulation defines:
1. **Spawn region**
2. **Allowed movement axis**
3. **Allowed movement direction**
4. **Movement envelope**
5. **Minimum / maximum speed**
6. **Acceleration / deceleration behavior**
7. **Boundary behavior** (`CLAMP`, `WRAP`, `DESPAWN`, `IMPACT`, `STOP_TURN`)
8. **Allowed orientation**
9. **Interaction / collision behavior**
10. **Conditions for spawning / despawning**

> **HARD CONSTRAINT**: If an asset does not have an explicit movement rule, **IT MUST NOT MOVE**.
> Never infer movement from visual appearance. Never create random drifting to make a scene look alive.

```
┌────────────────────────────────────────────────────────────────────────┐
│ THE WORLD DEFINES WHERE AN OBJECT CAN EXIST.                           │
│ THE MOVEMENT PROFILE DEFINES HOW IT CAN MOVE.                          │
│ THE ASSET DEFINES WHAT IT LOOKS LIKE.                                  │
│ THE STATE MACHINE DEFINES WHAT IT IS DOING.                            │
│ THE RENDERER ONLY DISPLAYS THE RESULT.                                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 1. UNDERWATER ENVIRONMENT

### 1.1 Underwater Probe / Rover (`PROBE_V1`)
- **Role**: Vertical underwater exploration vehicle.
- **Placement**: Central/lower portion of the water column.
- **Allowed Axis**: **Y-AXIS ONLY**.
- **Allowed Movement**:
  - `↑ ASCENDING`
  - `↓ DESCENDING`
- **Forbidden**:
  - ✗ Horizontal movement ($x = \text{constant}$)
  - ✗ Diagonal movement
  - ✗ Random drifting
  - ✗ Rotation while traveling
  - ✗ Teleportation
- **Movement Model**:
  $$x = \text{constant}$$
  $$y = y + v_y \cdot \Delta t$$
- **Speed**:
  - Normal: Controlled slow vertical movement
  - Exploration: Moderate vertical movement
  - Emergency: Faster vertical movement
- **Acceleration**: Smooth acceleration/deceleration between speed tiers.
- **Boundaries**: Top boundary (minimum depth) and bottom boundary (maximum depth).
- **Behavior at Boundary**: `CLAMP` (Probe stops completely at minimum and maximum depth; never partially exits viewport).
- **Orientation**: Fixed vertical orientation.
- **Interaction**: Sonar emitter, sensor scans, rigid collision body.

### 1.2 Small / Medium Fish (`FISH_S` / `FISH_M`)
- **Role**: Ambient aquatic life.
- **Placement**: Distributed throughout designated horizontal water lanes.
- **Allowed Axis**: **X-AXIS primarily**.
- **Allowed Movement**:
  - `→ LEFT TO RIGHT`
  - `← RIGHT TO LEFT`
  - Small bounded sinusoidal/vertical offset ($y = y_{\text{base}} + \Delta y_{\text{bounded}}$).
- **Forbidden**:
  - ✗ Traversal across vertical corridors
  - ✗ Diagonal traversal across the scene
  - ✗ Random teleportation
- **Speed**:
  - Small Fish: Faster horizontal velocity
  - Medium Fish: Slower horizontal velocity
- **Boundary Behavior**: `WRAP` via outer despawn & opposite boundary entry (never instant visible teleportation).
- **Orientation**:
  - Moving Right: `><(((°>`
  - Moving Left: `<°)))><`
- **Interaction**: Avoid probe bounding box; maintain bounded lane offset.

### 1.3 Fish School (`FISH_SCHOOL`)
- **Role**: Coordinated aquatic group.
- **Movement**: Primarily horizontal corridor movement (`→ → →`).
- **Formation Constraints**:
  - Minimum separation distance ($d_{\text{min}}$)
  - Maximum separation distance ($d_{\text{max}}$)
  - Common velocity and direction vector.
  - No random dispersal outside the school envelope.

### 1.4 Bubbles (`BUBBLE`)
- **Role**: Rising particle effects.
- **Placement**: Originates near probe exhaust, vents, or seabed machinery.
- **Allowed Axis**: **Y-AXIS UPWARD ONLY** ($v_y < 0$).
- **Allowed Movement**: Upward ascent with optional small micro-drift ($|\Delta x| \le 1$).
- **Forbidden**: Horizontal traveling across scene, downward movement.
- **Boundary Behavior**: `DESPAWN` upon reaching the water surface layer.

### 1.5 Sonar Pulse (`SONAR_PULSE`)
- **Role**: Active acoustic detection visualization.
- **Placement**: Originates from `PROBE_V1` center.
- **Movement Model**:
  - Translation: **NONE** (origin remains anchored to probe).
  - Expansion: $r = r + \dot{r} \cdot \Delta t$.
- **Boundary Behavior**: `DESPAWN` when $r \ge r_{\text{max}}$.

---

## 2. SOLAR ENVIRONMENT

### 2.1 Solar Panel Array (`SOLAR_PANEL`)
- **Role**: Anchored energy-generation hardware.
- **Placement**: Fixed ground foundation testbed.
- **Translational Movement**: **NONE** (Strictly $0$).
- **Allowed Dynamic Behavior**:
  - Azimuth rotation
  - Elevation tilt
  - Entire assembly rotates as ONE single rigid body.
- **Forbidden**:
  - ✗ Panel translation or drifting
  - ✗ Individual cell displacement
  - ✗ Structural decoupling from frame
- **Orientation**: Canonical states (`PANEL_0`, `PANEL_45`, `PANEL_90`).

### 2.2 Sun (`SUN`)
- **Role**: Celestial solar illumination source.
- **Placement**: Upper sky region.
- **Movement Model**: Deterministic single-axis trajectory along predefined arc ($X \to X + v_x \cdot \Delta t$).
- **Forbidden**: Sudden jumps, random wandering, shape stretching.

### 2.3 Solar Rays (`SOLAR_RAYS`)
- **Role**: Vector connection between Sun and Panel.
- **Placement**: Ray path between Sun origin and Panel aperture.
- **Movement**: No independent translation; updates deterministically with Sun position and Panel tilt angle.

---

## 3. MARS ENVIRONMENT

### 3.1 Mars Surface Rover (`ROVER_V1`)
- **Role**: Ground exploration mobility platform.
- **Placement**: Traversable Mars regolith surface.
- **Allowed Movement**:
  - Horizontal terrain traversal: `← LEFT` or `→ RIGHT`.
  - Vertical position constrained to terrain profile:
    $$y = \text{terrain\_height}(x) - \text{rover\_height}$$
- **Forbidden**:
  - ✗ Flight / airborne displacement
  - ✗ Diagonal movement off terrain
  - ✗ Arbitrary teleportation
- **Speed**: Controlled slow exploration, moderate traversal, emergency stop with acceleration ramps.
- **Boundary Behavior**: `STOP` or `TURN_AROUND` at navigable terrain limits.
- **Orientation**: Facing Right when $v_x > 0$, Facing Left when $v_x < 0$. Body, wheels, and mast move as one rigid asset.

### 3.2 Meteorites (`METEORITE_SMALL` / `METEORITE_LARGE`)
- **Role**: Ballistic atmospheric debris.
- **Placement**: Spawns in upper airspace above terrain.
- **Allowed Movement**: Downward trajectory ($\downarrow$, $\searrow$, or $\swarrow$) fixed at spawn time ($v_y > 0$). Direction cannot randomly change mid-flight.
- **Boundary & Collision**:
  - Bounding box collision with terrain.
  - Lifecycle: `METEORITE_FALLING` $\to$ `COLLISION` $\to$ `IMPACT_EFFECT` $\to$ `DUST_EFFECT` $\to$ `DESPAWN`.
  - Visual bounding geometry remains invariant during acceleration (no stretching).

### 3.3 Meteorite Trail (`METEORITE_TRAIL`)
- **Role**: Visual wake attached to falling meteorite.
- **Placement**: Pinned directly behind the meteorite's leading edge.
- **Movement**: Follows meteorite parent; not an independent entity.

### 3.4 Impact Effect (`IMPACT_EFFECT`)
- **Role**: Localized shockwave and dust eruption.
- **Placement**: Pinned to exact ground impact point $(x_{\text{hit}}, y_{\text{hit}})$.
- **Movement**: Stationary center; temporary expansion (`small` $\to$ `medium` $\to$ `large` $\to$ `despawn`).

---

## 4. SMART CITY TRAFFIC

### 4.1 Passenger Vehicles (`SEDAN` / `SUV`)
- **Role**: Road network traffic.
- **Placement**: Valid lane geometries only.
- **Movement**: Follows road vector ($\to$ or $\leftarrow$ according to lane assignment).
- **Forbidden**: Leaving road surface, sidewalk encroachment, random rotation, jumping across lanes.
- **Lane Changes**: Permitted only when explicitly commanded; must execute along a bounded continuous trajectory.

### 4.2 Public Transit Bus (`BUS`)
- **Role**: Scheduled transit vehicle.
- **Placement**: Designated transit lanes and routes.
- **Movement**: Route-graph following; turns only at street intersections; stops only at designated transit stops.

### 4.3 Heavy Cargo Truck (`TRUCK`)
- **Role**: Logistics transport.
- **Placement**: Freight-compatible road lanes.
- **Movement**: Slower acceleration/braking curves, enforced wide-turning radius.

### 4.4 Motorcycle (`MOTORCYCLE`)
- **Role**: Lightweight vehicular agent.
- **Placement**: Standard road lanes.
- **Movement**: Lane following with controlled intra-lane positioning.

### 4.5 Intersection Traffic Light (`TRAFFIC_LIGHT`)
- **Role**: Signal control fixture.
- **Placement**: Fixed intersection mast.
- **Translational Movement**: **STRICTLY NONE** ($v = 0$).
- **State Changes**: `RED`, `YELLOW`, `GREEN` governed by the FPGA FSM.

### 4.6 Pedestrians (`PEDESTRIAN`)
- **Role**: Human foot traffic.
- **Placement**: Sidewalks and designated pedestrian crosswalks.
- **Movement**: Constrained to sidewalk graph and crosswalk lanes; forbidden from entering open vehicular lanes outside crosswalk windows.

---

## 5. SUMMARY OF PHYSICS CONTRACTS

| Asset | Spatial Domain | Allowed Movement | Forbidden Behavior | Boundary Rule |
|---|---|---|---|---|
| **`PROBE_V1`** | Underwater Column | Vertical ($Y$) $\uparrow\downarrow$ | Horizontal / Diagonal / Drift | `CLAMP` |
| **`FISH_S / M`** | Water Lanes | Horizontal ($X$) $\leftarrow\rightarrow$ with micro $\Delta y$ | Large vertical traversal | `WRAP` |
| **`BUBBLE`** | Water Column | Vertical Upward $\uparrow$ ($v_y < 0$) | Downward / Horizontal crossing | `DESPAWN` |
| **`SONAR_PULSE`**| Probe Anchor | Radial Expansion ($r + \dot{r}\Delta t$) | World translation | `DESPAWN` |
| **`SOLAR_PANEL`**| Ground Foundation| Stationary tilt/azimuth rotation | Translation | `STATIONARY` |
| **`SUN`** | Upper Sky | Single-arc $X$ trajectory | Random jumps | `CLAMP` / `WRAP` |
| **`ROVER_V1`** | Mars Regolith | Horizontal along $y = f(x)$ | Airborne / Diagonal flight | `STOP` / `TURN` |
| **`METEORITE`** | Sky to Ground | Fixed vector descent ($v_y > 0$) | Mid-air trajectory shifts | `IMPACT` |
| **`SEDAN / SUV`**| Road Lanes | Lane-following ($X$) | Leaving road corridor | `LANE_CLAMP` |
| **`BUS`** | Transit Route | Route-graph following | Sidewalk/building collision | `ROUTE_CLAMP`|
| **`TRAFFIC_LIGHT`**| Intersection Mast| Stationary (FSM state change only) | Any movement | `STATIONARY` |
| **`PEDESTRIAN`** | Sidewalk / Crossing| Sidewalk graph following | Walking into traffic | `GRAPH_CLAMP`|
