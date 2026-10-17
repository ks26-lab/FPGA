"""Canonical CLI Asset Library V1.

Authoritative source of moving and dynamic assets for the simulation.
Implements the ANTI-GRAVITY / ASSET INTEGRITY MASTER INSTRUCTION:
- Fixed bounding boxes
- Preserved internal whitespace
- Canonical anchor points
- Predefined orientation variants
- No runtime character-level distortion
"""

from typing import List, Dict, Tuple, Optional


class CanonicalAsset:
    """Fixed-dimension immutable asset definition."""

    def __init__(
        self,
        key: str,
        category: str,
        raw_lines: List[str],
        anchor: Optional[Tuple[int, int]] = None,
        variants: Optional[Dict[str, List[str]]] = None
    ):
        self.key = key
        self.category = category
        self.height = len(raw_lines)
        self.width = max(len(line) for line in raw_lines) if raw_lines else 0
        
        # Pad all lines to uniform rectangular bounding box to preserve whitespace invariants
        self.lines = [line.ljust(self.width) for line in raw_lines]
        
        # Default anchor is center of bounding box if not specified
        if anchor is not None:
            self.anchor_x, self.anchor_y = anchor
        else:
            self.anchor_x = self.width // 2
            self.anchor_y = self.height // 2

        # Canonical orientation / state variants
        self.variants: Dict[str, List[str]] = {}
        if variants:
            for v_name, v_lines in variants.items():
                self.variants[v_name] = [vl.ljust(self.width) for vl in v_lines]

    def get_lines(self, variant: Optional[str] = None) -> List[str]:
        """Retrieve lines for the asset or a specific canonical variant."""
        if variant and variant in self.variants:
            return self.variants[variant]
        return self.lines


# =============================================================================
# 1. UNDERWATER ASSETS
# =============================================================================

PROBE_V1 = CanonicalAsset(
    key="PROBE_V1",
    category="UNDERWATER",
    raw_lines=[
        r"             ╭───────╮            ",
        r"          ╭──┤  ▣ ▣  ├──╮         ",
        r"        ╭─┤  ╰───┬───╯  ├─╮       ",
        r"       ╱  │   ◉══╪══◉   │  ╲      ",
        r"      │   │  ╭───┴───╮  │   │     ",
        r"      │   ╰──┤  ◉ ◉  ├──╯   │     ",
        r"       ╲     ╰───┬───╯      ╱     ",
        r"        ╰───╮    │    ╭────╯      ",
        r"            ╰────┴────╯           ",
        r"              ║ ║                 ",
        r"           ═══╝ ╚═══              "
    ],
    anchor=(17, 5)
)

FISH_S = CanonicalAsset(
    key="FISH_S",
    category="UNDERWATER",
    raw_lines=[
        r"><(((°>"
    ],
    anchor=(3, 0),
    variants={
        "RIGHT": [r"><(((°>"],
        "LEFT":  [r"<°)))><"]
    }
)

FISH_M = CanonicalAsset(
    key="FISH_M",
    category="UNDERWATER",
    raw_lines=[
        r"><(((°>",
        r"   ╲╲   "
    ],
    anchor=(3, 0),
    variants={
        "RIGHT": [
            r"><(((°>",
            r"   ╲╲   "
        ],
        "LEFT": [
            r"<°)))><",
            r"   ╱╱   "
        ]
    }
)

ALTERNATE_FISH = CanonicalAsset(
    key="ALTERNATE_FISH",
    category="UNDERWATER",
    raw_lines=[
        r"><(((°)))>"
    ],
    anchor=(5, 0),
    variants={
        "RIGHT": [r"><(((°)))>"],
        "LEFT":  [r"<(((°)))><"]
    }
)

FISH_SCHOOL = CanonicalAsset(
    key="FISH_SCHOOL",
    category="UNDERWATER",
    raw_lines=[
        r"><(((°>     ><(((°>        ",
        r"       ><(((°>       ><(((°>"
    ],
    anchor=(14, 1)
)

BUBBLES = CanonicalAsset(
    key="BUBBLES",
    category="UNDERWATER",
    raw_lines=[
        r"      ○    ",
        r"   °     ○ ",
        r"      ○    "
    ],
    anchor=(5, 1)
)

CABLE = CanonicalAsset(
    key="CABLE",
    category="UNDERWATER",
    raw_lines=[
        r"        │",
        r"        │",
        r"       ╱ ",
        r"      ╱  ",
        r"     ╱   ",
        r"    ╱    ",
        r"   ╱     "
    ],
    anchor=(8, 0)
)

SONAR_PULSE_STATIC = CanonicalAsset(
    key="SONAR_PULSE_STATIC",
    category="UNDERWATER",
    raw_lines=[
        r"       ╭─────────╮      ",
        r"     ╭─╯    ◉    ╰─╮    ",
        r"    ╱               ╲   ",
        r"   ╱                 ╲  "
    ],
    anchor=(12, 1)
)

SONAR_PULSE_EXPANDING = CanonicalAsset(
    key="SONAR_PULSE_EXPANDING",
    category="UNDERWATER",
    raw_lines=[
        r"       ◉       ",
        r"      ╱ ╲      ",
        r"     ╱   ╲     ",
        r"    ╱     ╲    ",
        r"   ╱       ╲   "
    ],
    anchor=(7, 0)
)


# =============================================================================
# 2. SOLAR ASSETS
# =============================================================================

SOLAR_PANEL_V1 = CanonicalAsset(
    key="SOLAR_PANEL_V1",
    category="SOLAR",
    raw_lines=[
        r"       ╱══════════════════╲       ",
        r"      ╱ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ╲       ",
        r"     ╱ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ╲        ",
        r"    ╱ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ▦ ╲       ",
        r"   ╱═════════════════════════╲    ",
        r"              │                   ",
        r"              │                   ",
        r"             ╱│╲                  ",
        r"            ╱ │ ╲                 ",
        r"           ╱  │  ╲                "
    ],
    anchor=(14, 5)
)

ROTATABLE_PANEL = CanonicalAsset(
    key="ROTATABLE_PANEL",
    category="SOLAR",
    raw_lines=[
        r"        ╲          ",
        r"         ╲         ",
        r"          ╲══════════",
        r"           ▦ ▦ ▦ ▦ ▦ ",
        r"           ▦ ▦ ▦ ▦ ▦ ",
        r"           ▦ ▦ ▦ ▦ ▦ ",
        r"          ╱══════════",
        r"         ╱         ",
        r"        ╱          ",
        r"       ╱           "
    ],
    anchor=(10, 5)
)

SUN = CanonicalAsset(
    key="SUN",
    category="SOLAR",
    raw_lines=[
        r"        \  |  /        ",
        r"      ─── ☼ ───        ",
        r"        /  |  \        "
    ],
    anchor=(10, 1)
)

COMPACT_SUN = CanonicalAsset(
    key="COMPACT_SUN",
    category="SOLAR",
    raw_lines=[
        r"   \ | /   ",
        r" -- (☼) -- ",
        r"   / | \   "
    ],
    anchor=(5, 1)
)

SOLAR_RAYS = CanonicalAsset(
    key="SOLAR_RAYS",
    category="SOLAR",
    raw_lines=[
        r"\\\\\\\\\\\\\\\\",
        r" >>>>>>>>>>>>>>>",
        r"////////////////"
    ],
    anchor=(8, 1)
)


# =============================================================================
# 3. MARS ASSETS
# =============================================================================

ROVER_V1 = CanonicalAsset(
    key="ROVER_V1",
    category="MARS",
    raw_lines=[
        r"             ┌───────────┐            ",
        r"        ─────┤  ▣   ▣    ├─────       ",
        r"             └────┬──────┘            ",
        r"                  │                   ",
        r"             ╔════╧════╗              ",
        r"          ◉══╣         ╠══◉           ",
        r"             ╚═════════╝              "
    ],
    anchor=(19, 3)
)

ROVER_SIDE = CanonicalAsset(
    key="ROVER_SIDE",
    category="MARS",
    raw_lines=[
        r"       ┌─────────────┐     ",
        r"  ─────┤   ▣   ▣     ├──── ",
        r"       └──────┬──────┘     ",
        r"          ◉═══╧═══◉        "
    ],
    anchor=(13, 2),
    variants={
        "RIGHT": [
            r"       ┌─────────────┐     ",
            r"  ─────┤   ▣   ▣     ├──── ",
            r"       └──────┬──────┘     ",
            r"          ◉═══╧═══◉        "
        ],
        "LEFT": [
            r"     ┌─────────────┐       ",
            r" ────┤   ▣   ▣     ├─────  ",
            r"     └──────┬──────┘       ",
            r"        ◉═══╧═══◉          "
        ]
    }
)

COMMUNICATION_ANTENNA = CanonicalAsset(
    key="COMMUNICATION_ANTENNA",
    category="MARS",
    raw_lines=[
        r"        ╱╲        ",
        r"       ╱  ╲       ",
        r"      ╱────╲      ",
        r"         │        ",
        r"         │        ",
        r"      ┌──┴──┐     "
    ],
    anchor=(9, 5)
)

METEORITE_SMALL = CanonicalAsset(
    key="METEORITE_SMALL",
    category="MARS",
    raw_lines=[
        r"     ◇    ",
        r"   ╱██╲   ",
        r"   ╲██╱   "
    ],
    anchor=(5, 1)
)

METEORITE_LARGE = CanonicalAsset(
    key="METEORITE_LARGE",
    category="MARS",
    raw_lines=[
        r"       ╭────╮       ",
        r"    ╭──╯████╰──╮    ",
        r"   ╱ ██████████ ╲   ",
        r"   ╲ ██████████ ╱   ",
        r"    ╰──╮████╭──╯    ",
        r"       ╰────╯       "
    ],
    anchor=(10, 3)
)

FALLING_METEORITE = CanonicalAsset(
    key="FALLING_METEORITE",
    category="MARS",
    raw_lines=[
        r"                  ◇   ",
        r"                 ╱    ",
        r"                ╱     ",
        r"               ╱      ",
        r"              ╱       ",
        r"             ╱        ",
        r"            ╱         ",
        r"           ╱          ",
        r"          ▼           "
    ],
    anchor=(10, 8)
)

METEORITE_TRAIL = CanonicalAsset(
    key="METEORITE_TRAIL",
    category="MARS",
    raw_lines=[
        r"            ◇         ",
        r"           ╱          ",
        r"          ╱           ",
        r"         ╱            ",
        r"        ╱             ",
        r"       ╱              ",
        r"      ╱               ",
        r"     ╱                ",
        r"   ╱╱╱╱               "
    ],
    anchor=(10, 8)
)

IMPACT = CanonicalAsset(
    key="IMPACT",
    category="MARS",
    raw_lines=[
        r"             ✦        ",
        r"          ╲  │  ╱     ",
        r"        ──── ◉ ────   ",
        r"          ╱  │  ╲     ",
        r"             ✦        "
    ],
    anchor=(13, 2)
)

DUST_EXPLOSION = CanonicalAsset(
    key="DUST_EXPLOSION",
    category="MARS",
    raw_lines=[
        r"       ·  ·     ·        ",
        r"    ·     ░░░     ·      ",
        r"  ·    ░░████░░     ·    ",
        r"       ░██████░          ",
        r"    ·   ░░██░░   ·       ",
        r"       ·   ·             "
    ],
    anchor=(12, 3)
)


# =============================================================================
# 4. SMART CITY TRAFFIC ASSETS
# =============================================================================

CAR_SEDAN_V1 = CanonicalAsset(
    key="CAR_SEDAN_V1",
    category="TRAFFIC",
    raw_lines=[
        r"       ______       ",
        r"  ____/|_||_\`.__   ",
        r" / _          _  \  ",
        r"( (_)        (_)  ) ",
        r" \______________/   "
    ],
    anchor=(10, 2),
    variants={
        "RIGHT": [
            r"       ______       ",
            r"  ____/|_||_\`.__   ",
            r" / _          _  \  ",
            r"( (_)        (_)  ) ",
            r" \______________/   "
        ],
        "LEFT": [
            r"       ______       ",
            r"  __.'/|_||_|\____  ",
            r" /  _          _ \  ",
            r"(  (_)        (_) ) ",
            r" \______________/   "
        ]
    }
)

COMPACT_SEDAN = CanonicalAsset(
    key="COMPACT_SEDAN",
    category="TRAFFIC",
    raw_lines=[
        r"    ______    ",
        r" __/|_||_\__  ",
        r"|  _      _  |",
        r"'-(_)----(_)-'"
    ],
    anchor=(7, 2)
)

SUV = CanonicalAsset(
    key="SUV",
    category="TRAFFIC",
    raw_lines=[
        r"      _________    ",
        r" ____/|_||_|\__   ",
        r"|   _       _   | ",
        r"'-(_ )-----(_ )-' "
    ],
    anchor=(9, 2)
)

BUS = CanonicalAsset(
    key="BUS",
    category="TRAFFIC",
    raw_lines=[
        r"   __________________   ",
        r" _/|                |\  ",
        r"|  |   ▣ ▣ ▣ ▣ ▣    | | ",
        r"|__|________________|_| ",
        r"   O              O     "
    ],
    anchor=(12, 2)
)

TRUCK = CanonicalAsset(
    key="TRUCK",
    category="TRAFFIC",
    raw_lines=[
        r"       __________       ",
        r"  ____|          |__    ",
        r" |    |          |  |   ",
        r" |____|__________|__|   ",
        r"     O            O     "
    ],
    anchor=(12, 2)
)

MOTORCYCLE = CanonicalAsset(
    key="MOTORCYCLE",
    category="TRAFFIC",
    raw_lines=[
        r"       __    ",
        r"  ____/  \__ ",
        r" O          O"
    ],
    anchor=(6, 1)
)

TRAFFIC_LIGHT = CanonicalAsset(
    key="TRAFFIC_LIGHT",
    category="TRAFFIC",
    raw_lines=[
        r"   ╔═══╗   ",
        r"   ║ ● ║   ",
        r"   ║ ○ ║   ",
        r"   ║ ○ ║   ",
        r"   ╚═╤═╝   ",
        r"     │     ",
        r"     │     ",
        r"    ═╧═    "
    ],
    anchor=(5, 3),
    variants={
        "RED": [
            r"   ╔═══╗   ",
            r"   ║ ● ║   ",
            r"   ║ ○ ║   ",
            r"   ║ ○ ║   ",
            r"   ╚═╤═╝   ",
            r"     │     ",
            r"     │     ",
            r"    ═╧═    "
        ],
        "YELLOW": [
            r"   ╔═══╗   ",
            r"   ║ ○ ║   ",
            r"   ║ ● ║   ",
            r"   ║ ○ ║   ",
            r"   ╚═╤═╝   ",
            r"     │     ",
            r"     │     ",
            r"    ═╧═    "
        ],
        "GREEN": [
            r"   ╔═══╗   ",
            r"   ║ ○ ║   ",
            r"   ║ ○ ║   ",
            r"   ║ ● ║   ",
            r"   ╚═╤═╝   ",
            r"     │     ",
            r"     │     ",
            r"    ═╧═    "
        ]
    }
)

PEDESTRIAN = CanonicalAsset(
    key="PEDESTRIAN",
    category="TRAFFIC",
    raw_lines=[
        r"  O  ",
        r" /|\ ",
        r" / \ "
    ],
    anchor=(2, 1)
)


# Registry mapping
ASSET_REGISTRY: Dict[str, CanonicalAsset] = {
    # Underwater
    "PROBE_V1": PROBE_V1,
    "FISH_S": FISH_S,
    "FISH_M": FISH_M,
    "ALTERNATE_FISH": ALTERNATE_FISH,
    "FISH_SCHOOL": FISH_SCHOOL,
    "BUBBLES": BUBBLES,
    "CABLE": CABLE,
    "SONAR_PULSE_STATIC": SONAR_PULSE_STATIC,
    "SONAR_PULSE_EXPANDING": SONAR_PULSE_EXPANDING,

    # Solar
    "SOLAR_PANEL_V1": SOLAR_PANEL_V1,
    "ROTATABLE_PANEL": ROTATABLE_PANEL,
    "SUN": SUN,
    "COMPACT_SUN": COMPACT_SUN,
    "SOLAR_RAYS": SOLAR_RAYS,

    # Mars
    "ROVER_V1": ROVER_V1,
    "ROVER_SIDE": ROVER_SIDE,
    "COMMUNICATION_ANTENNA": COMMUNICATION_ANTENNA,
    "METEORITE_SMALL": METEORITE_SMALL,
    "METEORITE_LARGE": METEORITE_LARGE,
    "FALLING_METEORITE": FALLING_METEORITE,
    "METEORITE_TRAIL": METEORITE_TRAIL,
    "IMPACT": IMPACT,
    "DUST_EXPLOSION": DUST_EXPLOSION,

    # Traffic
    "CAR_SEDAN_V1": CAR_SEDAN_V1,
    "COMPACT_SEDAN": COMPACT_SEDAN,
    "SUV": SUV,
    "BUS": BUS,
    "TRUCK": TRUCK,
    "MOTORCYCLE": MOTORCYCLE,
    "TRAFFIC_LIGHT": TRAFFIC_LIGHT,
    "PEDESTRIAN": PEDESTRIAN
}


def get_canonical_asset(key: str) -> CanonicalAsset:
    """Retrieve canonical asset definition by key. Fails fast if unrecognized."""
    if key not in ASSET_REGISTRY:
        raise KeyError(
            f"Asset '{key}' not found in Canonical Asset Library V1. "
            f"Hard constraint violation: Assets must not be dynamically invented."
        )
    return ASSET_REGISTRY[key]
