# Environments Package Initialization
from .movement_rules import MovementProfile, BoundaryBehavior, PHYSICS_REGISTRY, get_physics_profile

__all__ = [
    "MovementProfile",
    "BoundaryBehavior",
    "PHYSICS_REGISTRY",
    "get_physics_profile"
]
