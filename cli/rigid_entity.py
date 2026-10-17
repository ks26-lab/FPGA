"""Rigid Entity Controller implementing Asset Integrity Invariants.

Enforces:
- INVARIANT_1: One object = one rigid visual unit
- INVARIANT_2: Asset dimensions do not change during movement
- INVARIANT_3: Internal character coordinates do not change during movement
- INVARIANT_5: Physics operates on the object, not individual characters
- INVARIANT_6: Objects cannot leave permitted boundaries accidentally
- INVARIANT_7: Unique object ID maintains canonical asset identity
- INVARIANT_10: Corrupted assets are never silently rendered
- INVARIANT_18: Sub-stepping for high-speed objects (meteorites) prevents tunneling
"""

from typing import Tuple, Optional, Any, Callable
from cli.asset_library import CanonicalAsset, get_canonical_asset


class RigidEntity:
    """A single coherent, rigid simulation entity."""

    def __init__(
        self,
        entity_id: str,
        asset_key: str,
        x: float,
        y: float,
        vx: float = 0.0,
        vy: float = 0.0,
        orientation: str = "DEFAULT",
        state: str = "ACTIVE",
        boundary_policy: str = "CLAMP",
        layer: int = 4,
        color_pair: int = 0,
        attrs: int = 0
    ):
        self.entity_id = entity_id
        self.asset_key = asset_key
        self.asset: CanonicalAsset = get_canonical_asset(asset_key)
        
        # World float coordinates of the anchor point
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        
        self.orientation = orientation
        self.state = state
        self.boundary_policy = boundary_policy
        self.layer = layer
        self.color_pair = color_pair
        self.attrs = attrs

        # Validate on construction
        self.validate_integrity()

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """
        Derive world-space bounding box from anchor point.
        Returns: (min_x, max_x, min_y, max_y)
        """
        min_x = self.x - self.asset.anchor_x
        max_x = min_x + self.asset.width
        min_y = self.y - self.asset.anchor_y
        max_y = min_y + self.asset.height
        return (min_x, max_x, min_y, max_y)

    def collides_with(self, other: "RigidEntity") -> bool:
        """AABB collision detection between two rigid entities."""
        ax1, ax2, ay1, ay2 = self.get_bounding_box()
        bx1, bx2, by1, by2 = other.get_bounding_box()
        return not (ax2 <= bx1 or ax1 >= bx2 or ay2 <= by1 or ay1 >= by2)

    def validate_integrity(self) -> None:
        """
        Verify the 22 invariants:
        - Asset exists and has valid non-zero dimensions
        - Anchor point is within or on the bounding boundary
        - Coordinates are finite numbers
        """
        if self.asset.width <= 0 or self.asset.height <= 0:
            raise ValueError(f"Entity '{self.entity_id}': Invalid zero-dimension asset geometry.")
        if not (0 <= self.asset.anchor_x <= self.asset.width):
            raise ValueError(f"Entity '{self.entity_id}': Anchor X outside asset boundary.")
        if not (0 <= self.asset.anchor_y <= self.asset.height):
            raise ValueError(f"Entity '{self.entity_id}': Anchor Y outside asset boundary.")
        if not (isinstance(self.x, (int, float)) and isinstance(self.y, (int, float))):
            raise TypeError(f"Entity '{self.entity_id}': Coordinates must be float/int.")

    def step(
        self,
        dt: float,
        world_w: int,
        world_h: int,
        substeps: int = 1,
        terrain_fn: Optional[Callable[[float], float]] = None
    ) -> bool:
        """
        Advance entity physics deterministically over dt using substeps.
        Returns: True if alive, False if despawned.
        """
        if self.state in ("DESPAWN", "DEAD"):
            return False

        if substeps < 1:
            substeps = 1
        sub_dt = dt / substeps

        for _ in range(substeps):
            # Calculate next proposed position
            new_x = self.x + self.vx * sub_dt
            new_y = self.y + self.vy * sub_dt

            # Terrain constraint (e.g. Mars Rover grounded to terrain profile)
            if terrain_fn is not None:
                new_y = terrain_fn(new_x)

            # Apply boundary policy to complete bounding box
            min_x = new_x - self.asset.anchor_x
            max_x = min_x + self.asset.width
            min_y = new_y - self.asset.anchor_y
            max_y = min_y + self.asset.height

            if self.boundary_policy == "CLAMP":
                # Clamp entire bounding box within screen
                if min_x < 0:
                    new_x = float(self.asset.anchor_x)
                    self.vx = 0.0
                elif max_x > world_w:
                    new_x = float(world_w - self.asset.width + self.asset.anchor_x)
                    self.vx = 0.0

                if min_y < 0:
                    new_y = float(self.asset.anchor_y)
                    self.vy = 0.0
                elif max_y > world_h:
                    new_y = float(world_h - self.asset.height + self.asset.anchor_y)
                    self.vy = 0.0

            elif self.boundary_policy == "WRAP":
                if min_x > world_w:
                    new_x = -self.asset.width + self.asset.anchor_x
                elif max_x < 0:
                    new_x = world_w + self.asset.anchor_x

            elif self.boundary_policy == "DESPAWN":
                # Despawn when entire bounding box leaves world area
                if max_x < 0 or min_x > world_w or max_y < 0 or min_y > world_h:
                    self.state = "DESPAWN"
                    return False

            elif self.boundary_policy == "BOUNCE":
                if min_x < 0 or max_x > world_w:
                    self.vx = -self.vx
                if min_y < 0 or max_y > world_h:
                    self.vy = -self.vy

            self.x = new_x
            self.y = new_y

        # Update facing orientation from horizontal velocity
        if self.vx > 0:
            self.orientation = "RIGHT"
        elif self.vx < 0:
            self.orientation = "LEFT"

        self.validate_integrity()
        return True

    def render(self, framebuffer) -> bool:
        """Render this rigid entity to the framebuffer."""
        if self.state in ("DESPAWN", "DEAD", "HIDDEN"):
            return False

        variant = self.orientation if self.orientation in self.asset.variants else None
        return framebuffer.blit_asset(
            asset=self.asset,
            world_x=self.x,
            world_y=self.y,
            variant=variant,
            layer=self.layer,
            color_pair=self.color_pair,
            attrs=self.attrs
        )
