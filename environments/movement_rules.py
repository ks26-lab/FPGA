"""Movement Constraint and Spatial Physics Contract Engine for V_SPACE.

Implements the ASSET PLACEMENT + MOVEMENT CONSTRAINT MASTER SPECIFICATION.
Guarantees that every asset follows its strict spatial role, movement envelope,
speed limits, and boundary behaviors.
"""

from enum import Enum
from typing import Dict, Any, Optional, Tuple, Set


class BoundaryBehavior(Enum):
    CLAMP = "CLAMP"            # Stop at boundary (probe, sun, rover edge)
    WRAP = "WRAP"              # Despawn at boundary and respawn on opposite entry (fish)
    DESPAWN = "DESPAWN"        # Delete upon reaching boundary (bubbles, sonar, meteorite impact)
    STOP_TURN = "STOP_TURN"    # Stop and reverse direction (rover terrain limits)
    STATIONARY = "STATIONARY"  # Translation strictly zero (solar panel, traffic light)
    LANE_CLAMP = "LANE_CLAMP"  # Confined to road vector (vehicles)


class MovementProfile:
    """Rigid spatial contract for a specific asset category."""

    def __init__(
        self,
        asset_name: str,
        allowed_axes: Set[str],            # e.g. {'Y'}, {'X'}, {'TERRAIN_X'}, set()
        allowed_directions: Set[str],      # e.g. {'UP', 'DOWN'}, {'LEFT', 'RIGHT'}
        boundary_behavior: BoundaryBehavior,
        min_speed: float,
        max_speed: float,
        accel: float = 1.0,
        can_rotate: bool = False,
        envelope: Optional[Tuple[float, float, float, float]] = None  # (xmin, xmax, ymin, ymax)
    ):
        self.asset_name = asset_name
        self.allowed_axes = allowed_axes
        self.allowed_directions = allowed_directions
        self.boundary_behavior = boundary_behavior
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.accel = accel
        self.can_rotate = can_rotate
        self.envelope = envelope

    def update(
        self,
        entity: Dict[str, Any],
        dt: float,
        world_width: int,
        world_height: int,
        terrain_fn: Optional[Any] = None
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Deterministically updates entity position according to its movement profile.
        Returns: (updated_entity, is_alive)
        """
        # If stationary, translation is strictly forbidden
        if self.boundary_behavior == BoundaryBehavior.STATIONARY or not self.allowed_axes:
            return entity, True

        x = entity.get("x", 0.0)
        y = entity.get("y", 0.0)
        vx = entity.get("vx", 0.0)
        vy = entity.get("vy", 0.0)

        # 1. Enforce allowed axes
        if "X" not in self.allowed_axes and "TERRAIN_X" not in self.allowed_axes:
            vx = 0.0
        if "Y" not in self.allowed_axes:
            vy = 0.0

        # 2. Enforce speed bounds
        current_speed = (vx**2 + vy**2)**0.5
        if current_speed > self.max_speed and current_speed > 0:
            scale = self.max_speed / current_speed
            vx *= scale
            vy *= scale

        # 3. Apply displacement
        new_x = x + vx * dt
        new_y = y + vy * dt

        # Special constraint: terrain follower (e.g. Mars Rover)
        if "TERRAIN_X" in self.allowed_axes and terrain_fn is not None:
            new_y = float(terrain_fn(new_x))

        # Special constraint: bounded vertical wobble for fish
        if entity.get("lane_base_y") is not None and "bounded_wave" in entity:
            import math
            entity["wave_phase"] = entity.get("wave_phase", 0.0) + dt * 2.0
            max_drift = entity.get("max_wave_amp", 1.5)
            new_y = entity["lane_base_y"] + math.sin(entity["wave_phase"]) * max_drift

        # 4. Enforce boundary behaviors
        is_alive = True
        env_xmin = self.envelope[0] if self.envelope else 0
        env_xmax = self.envelope[1] if self.envelope else world_width - 1
        env_ymin = self.envelope[2] if self.envelope else 0
        env_ymax = self.envelope[3] if self.envelope else world_height - 1

        width = entity.get("width", 1)
        height = entity.get("height", 1)

        if self.boundary_behavior == BoundaryBehavior.CLAMP:
            # Complete bounding box stays within envelope
            new_x = max(env_xmin, min(env_xmax - width + 1, new_x))
            new_y = max(env_ymin, min(env_ymax - height + 1, new_y))

        elif self.boundary_behavior == BoundaryBehavior.WRAP:
            # Wrap on left/right exit
            if new_x > env_xmax:
                new_x = env_xmin - width + 1
            elif new_x < env_xmin - width:
                new_x = env_xmax

        elif self.boundary_behavior == BoundaryBehavior.DESPAWN:
            # Despawn if outside bounds (e.g. bubbles reaching surface)
            if new_y < env_ymin or new_y > env_ymax or new_x < env_xmin or new_x > env_xmax:
                is_alive = False

        elif self.boundary_behavior == BoundaryBehavior.STOP_TURN:
            if new_x >= env_xmax - width:
                new_x = env_xmax - width
                vx = -abs(vx)
                entity["facing"] = "LEFT"
            elif new_x <= env_xmin:
                new_x = env_xmin
                vx = abs(vx)
                entity["facing"] = "RIGHT"

        entity["x"] = new_x
        entity["y"] = new_y
        entity["vx"] = vx
        entity["vy"] = vy

        # Enforce facing orientation according to velocity
        if vx > 0:
            entity["facing"] = "RIGHT"
        elif vx < 0:
            entity["facing"] = "LEFT"

        return entity, is_alive


# =============================================================================
# CANONICAL PREDEFINED ASSET PROFILES
# =============================================================================

PHYSICS_REGISTRY: Dict[str, MovementProfile] = {
    # 1. UNDERWATER ASSETS
    "PROBE_V1": MovementProfile(
        asset_name="PROBE_V1",
        allowed_axes={"Y"},
        allowed_directions={"UP", "DOWN"},
        boundary_behavior=BoundaryBehavior.CLAMP,
        min_speed=0.2,
        max_speed=2.5,
        accel=0.8,
        can_rotate=False
    ),
    "FISH_S": MovementProfile(
        asset_name="FISH_S",
        allowed_axes={"X"},
        allowed_directions={"LEFT", "RIGHT"},
        boundary_behavior=BoundaryBehavior.WRAP,
        min_speed=1.5,
        max_speed=4.0,
        accel=1.5
    ),
    "FISH_M": MovementProfile(
        asset_name="FISH_M",
        allowed_axes={"X"},
        allowed_directions={"LEFT", "RIGHT"},
        boundary_behavior=BoundaryBehavior.WRAP,
        min_speed=0.8,
        max_speed=2.0,
        accel=0.8
    ),
    "BUBBLE": MovementProfile(
        asset_name="BUBBLE",
        allowed_axes={"Y"},
        allowed_directions={"UP"},
        boundary_behavior=BoundaryBehavior.DESPAWN,
        min_speed=1.0,
        max_speed=3.0,
        accel=0.2
    ),
    "SONAR_PULSE": MovementProfile(
        asset_name="SONAR_PULSE",
        allowed_axes=set(),  # Translation strictly zero; radial expansion only
        allowed_directions=set(),
        boundary_behavior=BoundaryBehavior.DESPAWN,
        min_speed=0.0,
        max_speed=0.0
    ),

    # 2. SOLAR ASSETS
    "SOLAR_PANEL": MovementProfile(
        asset_name="SOLAR_PANEL",
        allowed_axes=set(),  # Translational movement forbidden; angular tilt only
        allowed_directions=set(),
        boundary_behavior=BoundaryBehavior.STATIONARY,
        min_speed=0.0,
        max_speed=0.0,
        can_rotate=True
    ),
    "SUN": MovementProfile(
        asset_name="SUN",
        allowed_axes={"X"},
        allowed_directions={"RIGHT"},
        boundary_behavior=BoundaryBehavior.CLAMP,
        min_speed=0.2,
        max_speed=0.8
    ),

    # 3. MARS ASSETS
    "ROVER_V1": MovementProfile(
        asset_name="ROVER_V1",
        allowed_axes={"TERRAIN_X"},
        allowed_directions={"LEFT", "RIGHT"},
        boundary_behavior=BoundaryBehavior.STOP_TURN,
        min_speed=0.5,
        max_speed=3.0,
        accel=1.2
    ),
    "METEORITE": MovementProfile(
        asset_name="METEORITE",
        allowed_axes={"X", "Y"},
        allowed_directions={"DOWN"},
        boundary_behavior=BoundaryBehavior.DESPAWN,
        min_speed=4.0,
        max_speed=12.0
    ),

    # 4. SMART CITY TRAFFIC ASSETS
    "VEHICLE_SEDAN": MovementProfile(
        asset_name="VEHICLE_SEDAN",
        allowed_axes={"X"},
        allowed_directions={"LEFT", "RIGHT"},
        boundary_behavior=BoundaryBehavior.LANE_CLAMP,
        min_speed=1.0,
        max_speed=5.0,
        accel=2.0
    ),
    "TRAFFIC_LIGHT": MovementProfile(
        asset_name="TRAFFIC_LIGHT",
        allowed_axes=set(),  # Fixed mast, state transitions only
        allowed_directions=set(),
        boundary_behavior=BoundaryBehavior.STATIONARY,
        min_speed=0.0,
        max_speed=0.0
    ),
    "PEDESTRIAN": MovementProfile(
        asset_name="PEDESTRIAN",
        allowed_axes={"X"},
        allowed_directions={"LEFT", "RIGHT"},
        boundary_behavior=BoundaryBehavior.CLAMP,
        min_speed=0.4,
        max_speed=1.2
    )
}


def get_physics_profile(asset_key: str) -> MovementProfile:
    """Retrieve canonical physics profile for an asset, enforcing strict constraints."""
    if asset_key not in PHYSICS_REGISTRY:
        raise KeyError(
            f"Asset '{asset_key}' has no defined movement profile. "
            f"Hard constraint violation: An asset without explicit rules must not move."
        )
    return PHYSICS_REGISTRY[asset_key]
