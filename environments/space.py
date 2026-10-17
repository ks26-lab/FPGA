import curses
import time
import random
import math


# --- ASCII ART ASSETS ---

# Grand Multi-Section Spacecraft (Carrier + Docked Mission Module)
SPACECRAFT_GRAND_DOCKED = [
    r"                   /\                   ",
    r"                  /  \   [ARES-VI]      ",
    r"                 /____\  [COMMAND HUB]  ",
    r"                /|    |\                ",
    r"               / |====| \               ",
    r"              |  |    |  |  [CRYOFUEL]  ",
    r"              |  |====|  |              ",
    r"              | ┌──────┐ |              ",
    r"              | │MODULE│ |  [HAB-LANDER]",
    r"              | └──────┘ |  [ATTACHED]  ",
    r"              |  |====|  |              ",
    r"              |__|____|__|              ",
    r"                /  ||  \                ",
    r"               /___||___\ [ION ENGINES] ",
    r"                // || \\  [PROPULSION]  ",
    r"               /// || \\\ [EXHAUST]     "
]

# Spacecraft Carrier after Module Separation (Empty Internal Bay)
SPACECRAFT_CARRIER_EMPTY = [
    r"                   /\                   ",
    r"                  /  \   [ARES-VI]      ",
    r"                 /____\  [COMMAND HUB]  ",
    r"                /|    |\                ",
    r"               / |====| \               ",
    r"              |  |    |  |  [CRYOFUEL]  ",
    r"              |  |====|  |              ",
    r"              | ┌░░░░░░┐ |              ",
    r"              | │[OPEN]│ |  [BAY EMPTY] ",
    r"              | └░░░░░░┘ |  [RELEASED]  ",
    r"              |  |====|  |              ",
    r"              |__|____|__|              ",
    r"                /  ||  \                ",
    r"               /___||___\ [ION ENGINES] ",
    r"                // || \\  [PARKING ORBIT]"
]

# 1. Habitat Module - Gear Retracted (High Altitude / Cruise)
HAB_MODULE_RETRACTED = [
    r"       .────────────.       ",
    r"      /  [HAB-ARES]  \      ",
    r"     |   COLONY CORE  |     ",
    r"     |  [AIRLOCK: OK] |     ",
    r"     └───┬────────┬───┘     ",
    r"         | [STOW] |   [RET] ",
    r"         \________/         "
]

# 2. Habitat Module - Gear Deploying (Mid Descent)
HAB_MODULE_DEPLOYING = [
    r"       .────────────.       ",
    r"      /  [HAB-ARES]  \      ",
    r"     |   COLONY CORE  |     ",
    r"     |  [AIRLOCK: OK] |     ",
    r"     └───┬────────┬───┘     ",
    r"        / |      | \  [GEAR]",
    r"       /  \______/  \ [DEP] ",
    r"      (o)            (o)    "
]

# 3. Habitat Module - Gear Locked (Final Approach & Touchdown)
HAB_MODULE_LOCKED = [
    r"       .────────────.       ",
    r"      /  [HAB-ARES]  \      ",
    r"     |   COLONY CORE  |     ",
    r"     |  [AIRLOCK: OK] |     ",
    r"     └───┬────────┬───┘     ",
    r"        /|        |\  [LOCK]",
    r"       / |  \__/  | \ [LEGS]",
    r"     ═(o)═  //\\  ═(o)═     "
]

# Default Alias for compatibility
HAB_MODULE_LANDER = HAB_MODULE_LOCKED

# Dynamic Thruster Burn Sprites
THRUST_LIGHT = [
    r"             ||             ",
    r"             ▼▼             "
]

THRUST_MEDIUM = [
    r"            /  \            ",
    r"           / || \           ",
    r"          ▼  ▼▼  ▼          "
]

THRUST_BRAKING = [
    r"           // || \\         ",
    r"          /// || \\\        ",
    r"         (▓▓)████(▓▓)       ",
    r"         ░░░░▒▒▒▒░░░░       "
]

THRUST_HOVER = [
    r"            \  /            ",
    r"            ░▒▒░            "
]

# Large Dominant Mars Planet with Textured Surface Curvature
MARS_PLANET_HUGE = [
    r"                   .───────────────────.                   ",
    r"              .───'                     '───.              ",
    r"           .─'     ░░░░░░░░░░░░░░░░░░        '─.           ",
    r"         .─'   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    '─.         ",
    r"        ╱    (CRATER OLYMPUS)  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓     ╲        ",
    r"       │    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │       ",
    r"       │   ▓▓▓▓▓▓▓▓▓▓▓    (VALLES MARINERIS)   ▓▓   │       ",
    r"       │    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │       ",
    r"        ╲     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓    (BASIN-04)    ╱        ",
    r"         '─.    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    .─'         ",
    r"           '─.     ░░░░░░░░░░░░░░░░░░        .─'           ",
    r"              '───.                     .───'              ",
    r"                   '───────────────────'                   "
]

# Curved Martian Planetary Horizon
CURVED_MARS_HORIZON = [
    r"                     .───────────────────────────────────.                     ",
    r"          .─────────'                                     '─────────.          ",
    r" .───────'    __/\__               (CRATER BASIN)                    '───────. ",
    r"/^^^^^\______/      \____/\__/\___/^^^^^^^^^^^^^^^\___/\__/\____/^^^^^\_______\\ ",
]

# Expanded Ant-Hill Colony Network
COLONY_NETWORK_ART = [
    r"                             [SOLAR ARRAY FARM]                             ",
    r"                                     │                                      ",
    r"                     ┌───────────────┴───────────────┐                      ",
    r"                     │                               │                      ",
    r"                 [HAB-01]═════════════════════════[LAB-01]                  ",
    r"                /   │   \                         /   \                     ",
    r"               /    │    \                       /     \                    ",
    r"          [LIFE] [POWER] [COM-01]            [LAB-02] [COM-02]              ",
    r"             │      │       │                    │        │                 ",
    r"          [HAB-02][GRID] [DATA-TETHER]       [SCIENCE] [RELAY]              ",
    r"             │      │       │                    │                          ",
    r"          [GREEN][STORAGE][ANTENNA]         [GEOLOGY]                       ",
    r"            \       │       /                                               ",
    r"             \──────┴──────/                                                "
]

# Mission Control Operational Assets (Ground Surface Assets)
SUN_LARGE_ART = [
    r"     \   |   /     ",
    r"   ' ┌───────┐ '   ",
    r" ──  │  SUN  │  ── ",
    r"   . └───────┘ .   ",
    r"     /   |   \     "
]

SOLAR_ARRAY_ART = [
    r"  [═══|═══|═══|═══|═══]  ",
    r"  |PV1|PV2|PV3|PV4|PV5|  ",
    r"  └───┴───┴───┴───┴───┘  ",
    r"          ││             ",
    r"      ════╧╧════         "
]

HABITAT_BASE_ART = [
    r" [HAB-01 PRIMARY CORE]       [BIO-DOME GREENHOUSE]      [COMM-TOWER 01] ",
    r" ┌────────────────────┐     ┌─────────────────────┐    ┌───────────────┐",
    r" │ [ARES BASE ALPHA]  │═════│ [GREEN-01 ECO-CELL] │════│ [DEEP SPACE]  │",
    r" │ AIRLOCK: PRESSURIZED│     │ O2 GENERATOR: 100%  │    │ S-BAND: LOCKED│",
    r" └─────────┬──────────┘     └──────────┬──────────┘    └───────┬───────┘",
    r"           │                           │                       │        ",
    r" ══════════╧═══════════════════════════╧═══════════════════════╧════════"
]

ROVER_ART_STOWED = [
    r"     ┌─────────────┐ [STOWED] ",
    r" ────┤ ROVER ARES-1├────────  ",
    r"     └─(O)─────(O)─┘          "
]

ROVER_ART_DEPLOYING = [
    r"        ┌─┐                   ",
    r"       /   \ [ARM EXTENDING]  ",
    r" ┌────┤ ROVER ARES-1 ├─────── ",
    r" └───(O)─────────(O)───────── "
]

ROVER_ART_DEPLOYED = [
    r"         \══\ [MODULE DEPLOYED] ",
    r"          \  \                  ",
    r" ┌─────────\─┴──────────┐       ",
    r" │ ROVER ARES-1 [LOCKED]│ [PAD] ",
    r" └──(O)═════════════(O)─┴──[OK] "
]


def draw_sprite(stdscr, sprite, start_y, start_x, color_pair=0, attrs=0):
    """Draws a multi-line ASCII sprite safely within terminal bounds."""
    if not sprite:
        return
    h, w = stdscr.getmaxyx()
    for idx, line in enumerate(sprite):
        y = int(start_y) + idx
        x = int(start_x)
        if 0 <= y < h and 0 <= x < w:
            visible_line = line[:max(0, w - x - 1)]
            if visible_line:
                try:
                    stdscr.addstr(y, x, visible_line, curses.color_pair(color_pair) | attrs)
                except curses.error:
                    pass


def draw_stars(stdscr, stars, h, w):
    """Safely renders and flickers background stellar field."""
    for star in stars:
        if 0 <= star[1] < h and 0 <= star[0] < w:
            char = star[2]
            if random.random() < 0.05:
                char = ' ' if char != ' ' else '*'
            try:
                stdscr.addstr(int(star[1]), int(star[0]), char, curses.color_pair(1) | curses.A_DIM)
            except curses.error:
                pass


def run_mars_landing_sequence(stdscr, fpga_hw=None):
    """
    Continuous Deterministic Cinematic & Landing State Machine:
    STATE_APPROACH         -> Interplanetary deep space cruise
    STATE_DESCENT          -> Mars orbital approach and module separation
    STATE_ACTION           -> Atmospheric entry with debris/plasma hazard sequence
    STATE_ACTION_COMPLETE  -> Hazard cleared, ablative shield jettisoned
    STATE_LANDING_PREP     -> Altimeter lock acquired, gear deployment initiates
    STATE_POWERED_DESCENT  -> Multistage retro-burn with intermediate altitudes and thrust flicker
    STATE_FINAL_APPROACH   -> Hover cushion braking near surface, legs fully locked
    STATE_TOUCHDOWN        -> Physical contact with ground, impact camera shake & expanding dust plume
    STATE_LANDING_CONFIRM  -> System verification box and habitat security telemetry
    STATE_DEPLOYMENT       -> Colony network grid power-up
    """
    stdscr.clear()
    curses.curs_set(0)
    stdscr.nodelay(True)

    # Initialize Colors
    curses.init_pair(1, curses.COLOR_WHITE, -1)   # Stars / Neutral / Lines
    curses.init_pair(2, curses.COLOR_RED, -1)     # Mars Planet / Entry Glow / Exhaust / Dust
    curses.init_pair(3, curses.COLOR_CYAN, -1)    # Spacecraft Structure / Carrier / Telemetry
    curses.init_pair(4, curses.COLOR_GREEN, -1)   # Online Colony / Systems Active / Locked
    curses.init_pair(5, curses.COLOR_YELLOW, -1)  # Engines / Module Thrusters / Alerts / Flares
    curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Heavy Machinery / Terrain Bedrock

    fps = 16
    frame_time = 1.0 / fps
    frame = 0

    h, w = stdscr.getmaxyx()
    stars = [[random.randint(0, w - 1), random.randint(0, h - 1), random.choice(['.', '*', '·', '°'])] for _ in range(50)]

    # Explicit State Machine States
    STATE_APPROACH = "STATE_APPROACH"
    STATE_DESCENT = "STATE_DESCENT"
    STATE_ACTION = "STATE_ACTION"
    STATE_ACTION_COMPLETE = "STATE_ACTION_COMPLETE"
    STATE_LANDING_PREP = "STATE_LANDING_PREP"
    STATE_POWERED_DESCENT = "STATE_POWERED_DESCENT"
    STATE_FINAL_APPROACH = "STATE_FINAL_APPROACH"
    STATE_TOUCHDOWN = "STATE_TOUCHDOWN"
    STATE_LANDING_CONFIRM = "STATE_LANDING_CONFIRM"
    STATE_DEPLOYMENT = "STATE_DEPLOYMENT"

    current_state = STATE_APPROACH
    state_start_time = time.time()

    # Craft & Module Positions
    craft_x = float(w // 2 - 20)
    craft_y = -18.0
    carrier_x = float(w // 2 - 20)
    carrier_y = float(h // 4)
    module_x = float(w // 2 - 14)
    module_y = 2.0

    # Dynamic Landing Physics Variables
    altitude_m = 1250.0
    vert_speed_ms = -42.0
    thrust_pct = 40
    gear_state = "RETRACTED"
    attitude = "STABILIZING"
    dust_stage = 0
    dust_timer = 0.0
    colony_power_step = 0

    # Hazards / Debris particles
    hazard_particles = []
    cam_shake_x = 0
    cam_shake_y = 0



    while True:
        loop_start = time.time()
        elapsed_state = time.time() - state_start_time
        h, w = stdscr.getmaxyx()
        ground_y = max(10, h - 5)

        # Transact with Zynq FPGA hardware layer for landing FSM & telemetry
        fpga_resp = fpga_hw.step_mars_habitat(
            altitude_m=altitude_m,
            velocity_ms=vert_speed_ms,
            impact_trigger=(current_state == STATE_ACTION),
            impact_target="A"
        ) if fpga_hw else {"hardware_active": False}

        # Bounds-safe input check
        try:
            key = stdscr.getch()
            if key == 27:  # ESC -> clean return to menu
                return
            elif key != -1:
                # User skip handling: never abort with error or blank screen.
                # Fast-forward deterministically to landing prep/descent!
                if current_state in (STATE_APPROACH, STATE_DESCENT, STATE_ACTION):
                    current_state = STATE_LANDING_PREP
                    state_start_time = time.time()
                    module_y = 3.0
                    altitude_m = 750.0
                    vert_speed_ms = -28.0
                    thrust_pct = 65
                    gear_state = "DEPLOYING..."
                elif current_state == STATE_LANDING_CONFIRM:
                    current_state = STATE_DEPLOYMENT
                    state_start_time = time.time()
                elif current_state == STATE_DEPLOYMENT:
                    return
        except curses.error:
            pass

        stdscr.erase()

        # -------------------------------------------------------------
        # STATE MACHINE UPDATE LOGIC
        # -------------------------------------------------------------
        if current_state == STATE_APPROACH:
            # Grand Spacecraft moves smoothly into view
            if craft_y < h // 4:
                craft_y += 5.5 * frame_time
            elif elapsed_state > 3.0:
                current_state = STATE_DESCENT
                state_start_time = time.time()
                carrier_x = craft_x
                carrier_y = craft_y
                module_x = carrier_x + 6
                module_y = carrier_y + 7

        elif current_state == STATE_DESCENT:
            # Module physically unlatches from carrier
            module_y += 3.8 * frame_time
            carrier_y -= 0.6 * frame_time
            if elapsed_state > 3.2:
                current_state = STATE_ACTION
                state_start_time = time.time()
                module_x = float(w // 2 - 14)
                module_y = 2.0
                hazard_particles = []

        elif current_state == STATE_ACTION:
            # Action / Hazard Sequence: Atmospheric entry with plasma heating & micrometeoroids
            module_y += 2.2 * frame_time
            # Generate fiery plasma streaks
            if random.random() < 0.65:
                hazard_particles.append([
                    random.randint(int(module_x - 8), int(module_x + 32)),
                    random.randint(0, h - 2),
                    random.choice(['/', '\\', '|', '✦']),
                    random.choice([2, 5])
                ])
            # Update hazard particles
            for p in hazard_particles:
                p[1] += 14 * frame_time
            hazard_particles = [p for p in hazard_particles if p[1] < h - 1]

            # Slight turbulent vibration
            cam_shake_x = random.choice([-1, 0, 1]) if frame % 2 == 0 else 0
            cam_shake_y = 0

            if elapsed_state > 4.2:
                current_state = STATE_ACTION_COMPLETE
                state_start_time = time.time()
                cam_shake_x = 0
                cam_shake_y = 0

        elif current_state == STATE_ACTION_COMPLETE:
            # Hazard cleared: Ablative heat shield jettisoned, radar lock acquired
            module_y += 1.8 * frame_time
            if elapsed_state > 2.0:
                current_state = STATE_LANDING_PREP
                state_start_time = time.time()
                module_y = max(2.0, h * 0.15)
                altitude_m = 842.0
                vert_speed_ms = -31.0
                thrust_pct = 72
                gear_state = "DEPLOYING..."
                attitude = "VERTICAL LOCK"

        elif current_state == STATE_LANDING_PREP:
            # Landing gear starts deploying, terrain becomes prominent
            gear_state = "DEPLOYING..."
            altitude_m = max(520.0, altitude_m - 95.0 * frame_time)
            vert_speed_ms = -24.0
            thrust_pct = 78
            module_y += 1.6 * frame_time
            if elapsed_state > 2.5:
                current_state = STATE_POWERED_DESCENT
                state_start_time = time.time()
                gear_state = "LOCKED"

        elif current_state == STATE_POWERED_DESCENT:
            # Heavy module descent with visible intermediate positions & retro-braking
            target_hover_y = ground_y - len(HAB_MODULE_LOCKED) - 1
            progress = min(1.0, elapsed_state / 4.5)
            
            # Smoothly calculate altitude and vertical speed reduction
            altitude_m = max(42.0, 520.0 * (1.0 - progress))
            vert_speed_ms = -24.0 + 20.0 * progress  # Decelerates to -4 m/s
            thrust_pct = int(75 + 15 * math.sin(progress * math.pi))  # Peak throttle during braking!
            attitude = "STABLE"
            
            # Dynamic camera shake proportional to braking thruster power
            if progress < 0.8:
                cam_shake_x = random.choice([-1, 0, 1]) if frame % 3 == 0 else 0
                cam_shake_y = random.choice([0, 1]) if frame % 4 == 0 else 0
            else:
                cam_shake_x = 0
                cam_shake_y = 0

            # Step module position downward
            module_y = (h * 0.22) + (target_hover_y - (h * 0.22)) * progress

            if elapsed_state > 4.5:
                current_state = STATE_FINAL_APPROACH
                state_start_time = time.time()
                cam_shake_x = 0
                cam_shake_y = 0

        elif current_state == STATE_FINAL_APPROACH:
            # Terminal hover just above Martian terrain (5-10m)
            target_touchdown_y = ground_y - len(HAB_MODULE_LOCKED)
            progress = min(1.0, elapsed_state / 2.5)
            altitude_m = max(2.0, 42.0 * (1.0 - progress))
            vert_speed_ms = -4.0 * (1.0 - progress)
            thrust_pct = int(60 * (1.0 - progress) + 20)
            module_y = (ground_y - len(HAB_MODULE_LOCKED) - 1) + 1.0 * progress

            if elapsed_state > 2.5:
                current_state = STATE_TOUCHDOWN
                state_start_time = time.time()
                module_y = float(ground_y - len(HAB_MODULE_LOCKED))
                altitude_m = 0.0
                vert_speed_ms = 0.0
                thrust_pct = 0
                dust_stage = 1
                dust_timer = time.time()
                # Touchdown impact shockwave
                cam_shake_y = 1
                cam_shake_x = 0

        elif current_state == STATE_TOUCHDOWN:
            # Module settles solidly on regolith, dust billows outward
            module_y = float(ground_y - len(HAB_MODULE_LOCKED))
            altitude_m = 0.0
            vert_speed_ms = 0.0
            thrust_pct = 0
            gear_state = "LOCKED"
            attitude = "TOUCHDOWN CONFIRMED"

            # Decay touchdown shockwave
            if elapsed_state > 0.3:
                cam_shake_y = 0
                cam_shake_x = 0

            # Advance dust stage
            if elapsed_state > 0.4 and dust_stage == 1:
                dust_stage = 2
            elif elapsed_state > 1.2 and dust_stage == 2:
                dust_stage = 3
            elif elapsed_state > 2.2 and dust_stage == 3:
                dust_stage = 4

            if elapsed_state > 3.2:
                current_state = STATE_LANDING_CONFIRM
                state_start_time = time.time()
                dust_stage = 0

        elif current_state == STATE_LANDING_CONFIRM:
            # Dedicated landing confirmation telemetry window
            if elapsed_state > 3.5:
                current_state = STATE_DEPLOYMENT
                state_start_time = time.time()

        elif current_state == STATE_DEPLOYMENT:
            # Progressive colony network deployment
            if elapsed_state > 0.8 and colony_power_step == 0: colony_power_step = 1
            if elapsed_state > 1.6 and colony_power_step == 1: colony_power_step = 2
            if elapsed_state > 2.4 and colony_power_step == 2: colony_power_step = 3
            if elapsed_state > 3.2 and colony_power_step == 3: colony_power_step = 4
            if elapsed_state > 4.2:
                return  # Deterministically transition to operational mode!

        # -------------------------------------------------------------
        # SCENE RENDERING PIPELINE
        # -------------------------------------------------------------
        draw_stars(stdscr, stars, h, w)

        # 1. Background Celestial Objects
        if current_state == STATE_APPROACH:
            # Deep space cruise with grand multi-section craft
            draw_sprite(stdscr, SPACECRAFT_GRAND_DOCKED, int(craft_y + cam_shake_y), int(craft_x + cam_shake_x), color_pair=3, attrs=curses.A_BOLD)
            # Exhaust glow
            try:
                ex_y = int(craft_y + len(SPACECRAFT_GRAND_DOCKED) - 2 + cam_shake_y)
                stdscr.addstr(ex_y, int(craft_x + 14 + cam_shake_x), "░▒▓██▓▒░", curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass

        elif current_state == STATE_DESCENT:
            # Large Mars Planet behind carrier and separating module
            mars_x = max(2, w // 2 - 29)
            draw_sprite(stdscr, MARS_PLANET_HUGE, int(h * 0.15), mars_x, color_pair=2, attrs=curses.A_DIM)
            draw_sprite(stdscr, SPACECRAFT_CARRIER_EMPTY, int(carrier_y), int(carrier_x), color_pair=3, attrs=curses.A_BOLD)
            draw_sprite(stdscr, HAB_MODULE_RETRACTED, int(module_y), int(module_x), color_pair=5, attrs=curses.A_BOLD)

        elif current_state in (STATE_ACTION, STATE_ACTION_COMPLETE):
            # Curved Martian Horizon & Re-entry Plasma
            draw_sprite(stdscr, CURVED_MARS_HORIZON, int(h * 0.52), max(2, w // 2 - 39), color_pair=2, attrs=curses.A_BOLD)
            # Draw hazard debris / plasma
            for p in hazard_particles:
                px, py, pch, pcol = int(p[0]), int(p[1]), p[2], p[3]
                if 0 <= py < h and 0 <= px < w:
                    try:
                        stdscr.addstr(py, px, pch, curses.color_pair(pcol) | curses.A_BOLD)
                    except curses.error:
                        pass
            draw_sprite(stdscr, HAB_MODULE_RETRACTED, int(module_y + cam_shake_y), int(module_x + cam_shake_x), color_pair=5, attrs=curses.A_BOLD)

        elif current_state in (STATE_LANDING_PREP, STATE_POWERED_DESCENT, STATE_FINAL_APPROACH, STATE_TOUCHDOWN, STATE_LANDING_CONFIRM):
            # Mars Surface & Basin Terrain (Physical contact ground)
            # Mountain Ridge Horizon
            draw_sprite(stdscr, CURVED_MARS_HORIZON, max(2, ground_y - 8), max(2, w // 2 - 39), color_pair=2, attrs=curses.A_DIM)

            # Continuous Solid Regolith Ground Bedrock
            ground_str = "═" * (w - 1)
            try:
                stdscr.addstr(ground_y, 0, ground_str, curses.color_pair(2) | curses.A_BOLD)
                sub_str = " · · · (CRATER BASIN-04) · · · (OLYMPUS REGOLITH BEDROCK) · · · " * (w // 55 + 2)
                stdscr.addstr(ground_y + 1, 0, sub_str[:w - 1], curses.color_pair(2) | curses.A_DIM)
                stdscr.addstr(ground_y + 2, 0, "▓" * (w - 1), curses.color_pair(6) | curses.A_DIM)
            except curses.error:
                pass

            # Select Appropriate Lander Sprite based on Gear State
            if gear_state == "RETRACTED":
                lander_sprite = HAB_MODULE_RETRACTED
            elif "DEPLOY" in gear_state:
                lander_sprite = HAB_MODULE_DEPLOYING
            else:
                lander_sprite = HAB_MODULE_LOCKED

            # Draw Habitat Lander Module
            draw_sprite(stdscr, lander_sprite, int(module_y + cam_shake_y), int(module_x + cam_shake_x), color_pair=3, attrs=curses.A_BOLD)

            # Draw Thrusters below module (if firing)
            if thrust_pct > 0 and current_state != STATE_TOUCHDOWN:
                thrust_y = int(module_y + len(lander_sprite) + cam_shake_y)
                if thrust_pct > 70:
                    thrust_sprite = THRUST_BRAKING
                    thrust_col = 5
                elif thrust_pct > 35:
                    thrust_sprite = THRUST_MEDIUM
                    thrust_col = 5
                else:
                    thrust_sprite = THRUST_HOVER
                    thrust_col = 2
                draw_sprite(stdscr, thrust_sprite, thrust_y, int(module_x + cam_shake_x), color_pair=thrust_col, attrs=curses.A_BOLD)

            # Draw Touchdown Dust Plume Effect (Multi-stage expanding billow)
            if dust_stage == 1:
                # Immediate Contact Sparks
                try:
                    stdscr.addstr(ground_y - 1, int(module_x - 3), "* ✦ *", curses.color_pair(5) | curses.A_BOLD)
                    stdscr.addstr(ground_y - 1, int(module_x + 22), "* ✦ *", curses.color_pair(5) | curses.A_BOLD)
                except curses.error:
                    pass
            elif dust_stage == 2:
                # Rising Regolith Billow
                try:
                    stdscr.addstr(ground_y - 2, int(module_x - 6), " ░░▒▒▓▓ ", curses.color_pair(2) | curses.A_BOLD)
                    stdscr.addstr(ground_y - 1, int(module_x - 10), "░░▒▒▓▓██▓▒░", curses.color_pair(2) | curses.A_BOLD)
                    stdscr.addstr(ground_y - 2, int(module_x + 22), " ▓▓▒▒░░ ", curses.color_pair(2) | curses.A_BOLD)
                    stdscr.addstr(ground_y - 1, int(module_x + 22), "░▒▓██▓▓▒▒░░", curses.color_pair(2) | curses.A_BOLD)
                except curses.error:
                    pass
            elif dust_stage == 3:
                # Expanding Dust Cloud
                try:
                    stdscr.addstr(ground_y - 1, int(module_x - 14), " ~~~~~~~~~~~~~~~~~~ ", curses.color_pair(2))
                    stdscr.addstr(ground_y - 1, int(module_x + 20), " ~~~~~~~~~~~~~~~~~~ ", curses.color_pair(2))
                except curses.error:
                    pass
            elif dust_stage == 4:
                # Dissipating Settling Dust
                try:
                    stdscr.addstr(ground_y - 1, int(module_x - 8), " ... · · · ", curses.color_pair(2) | curses.A_DIM)
                    stdscr.addstr(ground_y - 1, int(module_x + 22), " · · · ... ", curses.color_pair(2) | curses.A_DIM)
                except curses.error:
                    pass

        elif current_state == STATE_DEPLOYMENT:
            # Expanding Ant-Hill Colony Network
            col_x = max(2, w // 2 - 38)
            col_y = max(1, h // 2 - 7)
            col_color = 4 if colony_power_step > 1 else 3
            draw_sprite(stdscr, COLONY_NETWORK_ART, col_y, col_x, color_pair=col_color, attrs=curses.A_BOLD)

            # Progressive System Activation Log
            log_messages = [
                ("PRIMARY HABITAT CORE ..... [CONNECTED & SECURE]", 1),
                ("LANDING STRUTS & SEALS .... [PRESSURE NOMINAL]", 2),
                ("LIFE SUPPORT & O2 SYSTEMS . [BALANCED 20.8%]", 3),
                ("COLONY NETWORK INTERCONNECT [SYNCHRONIZED]", 4)
            ]

            try:
                stdscr.addstr(h - 6, 2, "┌── COLONY NETWORK INITIALIZATION SEQUENCE ─────────────────┐", curses.color_pair(1))
                for i, (msg, step_req) in enumerate(log_messages):
                    status_col = curses.color_pair(4) | curses.A_BOLD if colony_power_step >= step_req else curses.color_pair(1) | curses.A_DIM
                    stdscr.addstr(h - 5 + i, 4, msg, status_col)
                stdscr.addstr(h - 1, 2, "└───────────────────────────────────────────────────────────┘", curses.color_pair(1))
            except curses.error:
                pass

        # -------------------------------------------------------------
        # MISSION TELEMETRY HUD OVERLAY (Terminal Aesthetic)
        # -------------------------------------------------------------
        if current_state in (STATE_LANDING_PREP, STATE_POWERED_DESCENT, STATE_FINAL_APPROACH, STATE_TOUCHDOWN):
            try:
                stdscr.addstr(1, 2, "┌── POWERED LANDING TELEMETRY // HAB-ARES ──────────────────┐", curses.color_pair(1))
                stdscr.addstr(2, 2, f"│ ALTITUDE       : {int(altitude_m):<6} m                               │", curses.color_pair(3) | curses.A_BOLD)
                stdscr.addstr(3, 2, f"│ VERTICAL SPEED : {vert_speed_ms:<6.1f} m/s                             │", curses.color_pair(5 if vert_speed_ms < -15 else 4) | curses.A_BOLD)
                stdscr.addstr(4, 2, f"│ THRUST         : {thrust_pct:<3} %     [RETRO-BRAKING ACTIVE]          │", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr(5, 2, f"│ ATTITUDE       : {attitude:<20}              │", curses.color_pair(4) | curses.A_BOLD)
                stdscr.addstr(6, 2, f"│ LANDING GEAR   : {gear_state:<20}              │", curses.color_pair(4 if gear_state == 'LOCKED' else 5) | curses.A_BOLD)
                stdscr.addstr(7, 2, f"│ TERRAIN RANGE  : {int(altitude_m):<6} m   [BASIN-04 RADAR LOCK]         │", curses.color_pair(1))
                if fpga_resp.get("hardware_active"):
                    stdscr.addstr(8, 2, f"│ FPGA HARDWARE  : ● CONNECTED [{fpga_resp.get('fpga_landing_stage', 'LIVE')}]                  │", curses.color_pair(4) | curses.A_BOLD)
                else:
                    stdscr.addstr(8, 2, "│ FPGA HARDWARE  : × NOT CONNECTED (SOFTWARE-ONLY)          │", curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(9, 2, "└───────────────────────────────────────────────────────────┘", curses.color_pair(1))
            except curses.error:
                pass

        elif current_state == STATE_LANDING_CONFIRM:
            # Landing Confirmation Box Window
            conf_box = [
                "┌───────────────────────────────────────────────────────────┐",
                "│                 TOUCHDOWN CONFIRMED                       │",
                "│                                                           │",
                "│                 HAB-ARES MODULE                           │",
                "│                 LANDING STABLE                            │",
                "│                                                           │",
                "│   LANDING LEGS ........ LOCKED IN REGOLITH                │",
                "│   STRUCTURE ........... NOMINAL [100%]                    │",
                "│   HABITAT CORE ........ SECURE                            │",
                "│   POWER SYSTEM ........ STANDBY                           │",
                "│   ATMOSPHERE .......... PURGE COMPLETE                    │",
                "└───────────────────────────────────────────────────────────┘"
            ]
            draw_sprite(stdscr, conf_box, max(2, h // 2 - 8), max(2, w // 2 - 31), color_pair=4, attrs=curses.A_BOLD)

        elif current_state == STATE_ACTION:
            try:
                stdscr.addstr(1, 2, "┌── HAZARD ALERT // ATMOSPHERIC RE-ENTRY ───────────────────┐", curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(2, 2, "│ STATUS    : HYPERSONIC PLASMA ENVELOPE DETECTED           │", curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(3, 2, "│ TRAJECTORY: MICROMETEOROID CROSS-STREAM ENCOUNTERED       │", curses.color_pair(5))
                stdscr.addstr(4, 2, "│ RCS JETS  : EVASIVE VECTOR MANEUVER EXECUTED              │", curses.color_pair(3) | curses.A_BOLD)
                stdscr.addstr(5, 2, "│ THERMAL   : ABLATIVE HEAT SHIELD AT PEAK TOLERANCE        │", curses.color_pair(2))
                stdscr.addstr(6, 2, "└───────────────────────────────────────────────────────────┘", curses.color_pair(2))
            except curses.error:
                pass

        elif current_state == STATE_ACTION_COMPLETE:
            try:
                stdscr.addstr(1, 2, "┌── HAZARD CLEARED // TRANSITION TO TERMINAL LANDING ───────┐", curses.color_pair(4) | curses.A_BOLD)
                stdscr.addstr(2, 2, "│ STATUS     : ATMOSPHERIC REGIME STABILIZED                │", curses.color_pair(4) | curses.A_BOLD)
                stdscr.addstr(3, 2, "│ SHIELD     : ABLATIVE HEAT SHIELD JETTISONED              │", curses.color_pair(3))
                stdscr.addstr(4, 2, "│ RADAR      : BASIN-04 TERRAIN ALTIMETER LOCKED            │", curses.color_pair(4) | curses.A_BOLD)
                stdscr.addstr(5, 2, "│ PROPULSION : MAIN RETRO-THRUST INITIATING                 │", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr(6, 2, "└───────────────────────────────────────────────────────────┘", curses.color_pair(4))
            except curses.error:
                pass

        # Hardware Status Badge & Skip Indicator
        try:
            if fpga_hw:
                b_text, b_color_code = fpga_hw.get_status_badge()
                badge_cp = 4 if b_color_code == "GREEN" else (2 if b_color_code == "RED" else 5)
            else:
                b_text = "[× SOFTWARE VISUALIZATION MODE — FPGA NOT REQUIRED]"
                badge_cp = 2
            stdscr.addstr(0, 2, b_text, curses.color_pair(badge_cp) | curses.A_BOLD)
            stdscr.addstr(0, max(2, w - 46), "[PRESS ANY KEY TO SKIP TO LANDING / ESC: EXIT]", curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        frame += 1
        elapsed_loop = time.time() - loop_start
        if elapsed_loop < frame_time:
            time.sleep(frame_time - elapsed_loop)


def launch_space(stdscr, fpga_hw=None):
    """
    Master Entry Point for the SPACE HABITAT environment.
    Runs continuous cinematic sequence into dramatic multi-stage landing,
    then transitions directly into the full operational Mars habitat simulation.
    """
    if fpga_hw is None:
        try:
            from hardware.fpga_interface import get_fpga_interface
            fpga_hw = get_fpga_interface()
        except ImportError:
            pass

    # 1. Run Continuous Cinematic & Dramatic Powered Landing Sequence
    run_mars_landing_sequence(stdscr, fpga_hw)

    # 2. Steady State / High-Fidelity Operational Simulation Loop
    stdscr.nodelay(True)
    curses.curs_set(0)

    # Initialize color pairs
    curses.init_pair(1, curses.COLOR_WHITE, -1)   # Stars / Text / Neutral
    curses.init_pair(2, curses.COLOR_RED, -1)     # Mars Regolith / Craters / Fiery trails
    curses.init_pair(3, curses.COLOR_CYAN, -1)    # Base Structures / Panels / Active UI
    curses.init_pair(4, curses.COLOR_GREEN, -1)   # Greenhouse Plants / Operational Status
    curses.init_pair(5, curses.COLOR_YELLOW, -1)  # Large Sun / Impact Flash / Lever Knob
    curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Heavy Rover & Modular Machinery

    temp = -61.3
    pressure = 0.75
    wind = 18.0

    # State controls
    workflow_mode = 0  # 0: COMPARISON, 1: FILTERING
    module_deploy_state = 0  # 0: STOWED, 1: RELEASE, 2: EXTENDING, 3: LOCKED_DEPLOYED
    deploy_timer = time.time()

    # Atmospheric elements
    h, w = stdscr.getmaxyx()
    stars = [[random.randint(0, w - 1), random.randint(0, max(2, int(h * 0.28))), random.choice(['.', '·', '*'])] for _ in range(40)]
    dust = [[random.randint(0, w - 1), random.randint(int(h * 0.3), h - 1)] for _ in range(35)]

    # Dynamic Meteoroids: [{"x": float, "y": float, "vx": float, "vy": float, "size": str, "trail": list, "impact_y": int}]
    meteoroids = []
    # Dynamic Impacts: [{"x": int, "y": int, "size": str, "age": int}]
    impacts = []
    # Surface persistent craters
    craters = [
        {"x": 12, "y": int(h * 0.65), "size": "MEDIUM"},
        {"x": int(w * 0.42), "y": int(h * 0.78), "size": "LARGE"},
        {"x": int(w * 0.75), "y": int(h * 0.85), "size": "MEDIUM"}
    ]

    last_meteor_spawn = time.time()
    last_deploy_tick = time.time()



    while True:
        h, w = stdscr.getmaxyx()
        stdscr.erase()
        now = time.time()

        horizon_y = max(7, int(h * 0.28))

        # -------------------------------------------------------------
        # 1. UPPER SKY: STARS & LARGE GLOWING SUN & SOLAR ARRAY
        # -------------------------------------------------------------
        for s in stars:
            if s[1] < horizon_y:
                try:
                    stdscr.addstr(int(s[1]), int(s[0] % w), s[2], curses.color_pair(1) | curses.A_DIM)
                except curses.error:
                    pass

        # Draw Large Glowing Sun at Upper Center
        sun_x = max(2, (w // 2) - 15)
        sun_y = 1
        draw_sprite(stdscr, SUN_LARGE_ART, sun_y, sun_x, color_pair=5, attrs=curses.A_BOLD)

        # Draw Solar Energy Radiating down to Solar Array
        array_y = sun_y + len(SUN_LARGE_ART)
        draw_sprite(stdscr, SOLAR_ARRAY_ART, array_y, sun_x - 2, color_pair=3, attrs=curses.A_BOLD)

        # -------------------------------------------------------------
        # 2. METEOROID SPAWN & TRAJECTORY SYSTEM
        # -------------------------------------------------------------
        if now - last_meteor_spawn > random.uniform(0.6, 1.4):
            last_meteor_spawn = now
            m_size = random.choice(["SMALL", "SMALL", "MEDIUM", "LARGE"])
            start_x = random.randint(int(w * 0.15), w - 5)
            if m_size == "SMALL":
                m_vx = random.uniform(-1.8, -1.1)
                m_vy = random.uniform(1.2, 1.8)
            elif m_size == "MEDIUM":
                m_vx = random.uniform(-1.4, -0.8)
                m_vy = random.uniform(1.0, 1.5)
            else:
                m_vx = random.uniform(-1.1, -0.6)
                m_vy = random.uniform(0.8, 1.2)

            impact_target_y = random.randint(horizon_y + 3, h - 3)
            meteoroids.append({
                "x": float(start_x),
                "y": 1.0,
                "vx": m_vx,
                "vy": m_vy,
                "size": m_size,
                "trail": [],
                "impact_y": impact_target_y
            })

        active_meteors = []
        for m in meteoroids:
            m["trail"].append((int(m["x"]), int(m["y"])))
            if len(m["trail"]) > (7 if m["size"] == "LARGE" else (4 if m["size"] == "MEDIUM" else 2)):
                m["trail"].pop(0)

            m["x"] += m["vx"]
            m["y"] += m["vy"]

            # Fiery trail
            for idx, pt in enumerate(m["trail"]):
                tx, ty = pt
                if 0 <= ty < h and 0 <= tx < w:
                    trail_char = '╱' if m["size"] in ("MEDIUM", "LARGE") else '·'
                    trail_color = 2 if idx > len(m["trail"]) // 2 else 5
                    try:
                        stdscr.addstr(ty, tx, trail_char, curses.color_pair(trail_color) | (curses.A_BOLD if idx > 2 else curses.A_DIM))
                    except curses.error:
                        pass

            # Meteoroid head
            mx, my = int(m["x"]), int(m["y"])
            if 0 <= my < h and 0 <= mx < w:
                if m["size"] == "SMALL":
                    try:
                        stdscr.addstr(my, mx, "·", curses.color_pair(5) | curses.A_BOLD)
                    except curses.error:
                        pass
                elif m["size"] == "MEDIUM":
                    try:
                        stdscr.addstr(my, mx, "◆", curses.color_pair(5) | curses.A_BOLD)
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addstr(my, mx, "(█)", curses.color_pair(2) | curses.A_BOLD)
                    except curses.error:
                        pass

            # Surface impact trigger
            if m["y"] >= m["impact_y"] or m["y"] >= h - 2 or m["x"] <= 1:
                impacts.append({
                    "x": int(m["x"]),
                    "y": min(h - 2, int(m["y"])),
                    "size": m["size"],
                    "age": 0
                })
            else:
                active_meteors.append(m)
        meteoroids = active_meteors

        # -------------------------------------------------------------
        # 3. CONTINUOUS LAYERED MARS TERRAIN (Crater Basin & Bedrock)
        # -------------------------------------------------------------
        ridge_pattern = r"/^\__/\___/^^^^^\____/\__/\____/^^^\_____/\__/\____/^^^^^\___"
        ridge_full = (ridge_pattern * (w // len(ridge_pattern) + 2))[:w - 1]
        try:
            stdscr.addstr(horizon_y, 0, ridge_full, curses.color_pair(2) | curses.A_DIM)
        except curses.error:
            pass

        for row in range(horizon_y + 1, min(h - 1, horizon_y + 4)):
            dune_chars = []
            for col in range(w):
                val = math.sin(col * 0.15 + row) + math.cos(col * 0.05)
                if val > 1.2: dune_chars.append("▓")
                elif val > 0.6: dune_chars.append("▒")
                elif val > 0.0: dune_chars.append("░")
                else: dune_chars.append(" ")
            try:
                stdscr.addstr(row, 0, "".join(dune_chars)[:w - 1], curses.color_pair(2) | curses.A_DIM)
            except curses.error:
                pass

        for row in range(horizon_y + 4, h - 2):
            ground_str = "".join([("·" if random.random() < 0.08 else " ") for _ in range(w - 1)])
            try:
                stdscr.addstr(row, 0, ground_str, curses.color_pair(2) | curses.A_DIM)
            except curses.error:
                pass

        for cr in craters:
            cx, cy, csz = cr["x"], cr["y"], cr["size"]
            if 0 <= cy < h - 2 and 0 <= cx < w - 12:
                cr_str = "(▓▓════════▓▓)" if csz == "LARGE" else ("(═______═)" if csz == "MEDIUM" else "(__)")
                try:
                    stdscr.addstr(cy, cx, cr_str, curses.color_pair(2) | curses.A_BOLD)
                except curses.error:
                    pass

        # -------------------------------------------------------------
        # 4. IMPACT EVENTS: FLASH -> DUST/DEBRIS -> CRATER FORMATION
        # -------------------------------------------------------------
        active_impacts = []
        for imp in impacts:
            ix, iy, isz, iage = imp["x"], imp["y"], imp["size"], imp["age"]
            if 0 <= iy < h - 1 and 0 <= ix < w - 6:
                if iage == 0:
                    if isz == "SMALL":
                        try: stdscr.addstr(iy, ix, "*", curses.color_pair(5) | curses.A_BOLD)
                        except curses.error: pass
                    elif isz == "MEDIUM":
                        try: stdscr.addstr(iy, max(0, ix - 1), "✦ ◉ ✦", curses.color_pair(5) | curses.A_BOLD)
                        except curses.error: pass
                    else:
                        try:
                            stdscr.addstr(max(0, iy - 1), max(0, ix - 2), r"\ │ /", curses.color_pair(5) | curses.A_BOLD)
                            stdscr.addstr(iy, max(0, ix - 3), "─── ◉ ───", curses.color_pair(1) | curses.A_BOLD)
                            stdscr.addstr(min(h - 1, iy + 1), max(0, ix - 2), r"/ │ \ ", curses.color_pair(5) | curses.A_BOLD)
                        except curses.error: pass
                elif iage in (1, 2, 3):
                    plume_y = max(0, iy - iage)
                    if isz == "SMALL":
                        try: stdscr.addstr(plume_y, ix, "·", curses.color_pair(2))
                        except curses.error: pass
                    elif isz == "MEDIUM":
                        try: stdscr.addstr(plume_y, max(0, ix - 2), "░░░", curses.color_pair(2) | curses.A_BOLD)
                        except curses.error: pass
                    else:
                        try:
                            stdscr.addstr(plume_y, max(0, ix - 3), "░░██░░", curses.color_pair(2) | curses.A_BOLD)
                            stdscr.addstr(iy, max(0, ix - 2), "░░░░░", curses.color_pair(2))
                        except curses.error: pass
                else:
                    if len(craters) < 16:
                        craters.append({"x": ix, "y": iy, "size": isz})

            imp["age"] += 1
            if imp["age"] <= 4:
                active_impacts.append(imp)
        impacts = active_impacts

        # -------------------------------------------------------------
        # 5. BASE STRUCTURE: HABITAT ALPHA + GREENHOUSE
        # -------------------------------------------------------------
        base_y = min(h - 12, horizon_y + 3)
        base_x = max(10, w // 2 - 38)
        if len(HABITAT_BASE_ART) > 0:
            try:
                stdscr.addstr(base_y, base_x, HABITAT_BASE_ART[0][:w - base_x - 1], curses.color_pair(4) | curses.A_BOLD)
            except curses.error:
                pass
        for l_idx, line in enumerate(HABITAT_BASE_ART[1:], start=1):
            ly = base_y + l_idx
            if 0 <= ly < h and 0 <= base_x < w:
                try:
                    stdscr.addstr(ly, base_x, line[:w - base_x - 1], curses.color_pair(3) | curses.A_BOLD)
                except curses.error:
                    pass

        # Greenhouse interior plants
        green_y = base_y + 2
        green_x = base_x + 47
        try:
            stdscr.addstr(green_y, green_x, "Ψ  Ψ  Ψ", curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(green_y + 2, green_x, "Ψ  Ψ  Ψ", curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass

        # -------------------------------------------------------------
        # 6. PLANETARY EXPLORATION ROVER WITH MODULE DEPLOYMENT
        # -------------------------------------------------------------
        rover_y = min(h - 7, base_y + 7)
        rover_x = max(4, w // 2 - 25)

        if now - last_deploy_tick > 3.5:
            last_deploy_tick = now
            module_deploy_state = (module_deploy_state + 1) % 4

        if module_deploy_state == 0:
            rover_sprite = ROVER_ART_STOWED
            deploy_msg = "[ROVER STATUS: STATIONARY // MODULE STOWED IN BAY]"
        elif module_deploy_state == 1:
            rover_sprite = ROVER_ART_DEPLOYING
            deploy_msg = "[DEPLOYMENT: BAY UNLATCHED -> MECHANICAL ARM EXTENDING]"
        elif module_deploy_state == 2:
            rover_sprite = ROVER_ART_DEPLOYED
            deploy_msg = "[DEPLOYMENT: ARES-1 MODULE LOWERING TO REGOLITH]"
        else:
            rover_sprite = ROVER_ART_DEPLOYED
            deploy_msg = "[DEPLOYMENT COMPLETE: ARES-1 LOCKED // UMBILICAL ACTIVE]"

        draw_sprite(stdscr, rover_sprite, rover_y, rover_x, color_pair=6, attrs=curses.A_BOLD)

        # -------------------------------------------------------------
        # 7. TOP HEADER & WORKFLOW LEVER (COMPARISON <-> FILTERING)
        # -------------------------------------------------------------
        try:
            stdscr.addstr(0, 0, "┌───────────────────────────────────────────────┐", curses.color_pair(3))
            stdscr.addstr(1, 0, "│ MARS HABITAT // MISSION CONTROL               │", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(2, 0, "└───────────────────────────────────────────────┘", curses.color_pair(3))
        except curses.error:
            pass

        lever_y = 3
        lever_x = 2
        try:
            stdscr.addstr(lever_y, lever_x, "WORKFLOW: ", curses.color_pair(1) | curses.A_DIM)
            if workflow_mode == 0:
                stdscr.addstr("[COMPARISON]", curses.color_pair(3) | curses.A_BOLD)
                stdscr.addstr(" ◀════", curses.color_pair(1))
                stdscr.addstr("[■]", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr("────────▶  ", curses.color_pair(1))
                stdscr.addstr("FILTERING", curses.color_pair(1) | curses.A_DIM)
            else:
                stdscr.addstr("COMPARISON", curses.color_pair(1) | curses.A_DIM)
                stdscr.addstr("  ◀────────", curses.color_pair(1))
                stdscr.addstr("[■]", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr("════▶ ", curses.color_pair(1))
                stdscr.addstr("[FILTERING]", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr("  [TAB: FLIP]", curses.color_pair(3) | curses.A_DIM)
        except curses.error:
            pass

        # -------------------------------------------------------------
        # 8. TELEMETRY OVERLAYS
        # -------------------------------------------------------------
        if random.random() < 0.1: temp += random.uniform(-0.1, 0.1)
        if random.random() < 0.1: pressure += random.uniform(-0.01, 0.01)
        if random.random() < 0.1: wind += random.uniform(-0.4, 0.4)

        env_panel = [
            "┌── ENVIRONMENT ──────────────┐",
            f"│ TEMP       {temp:.1f} °C         │",
            f"│ PRESSURE   {pressure:.2f} kPa         │",
            f"│ WIND       {wind:.1f} m/s         │",
            "│ DUST       NOMINAL          │",
            "└─────────────────────────────┘"
        ]
        draw_sprite(stdscr, env_panel, 5, 2, color_pair=3)

        sys_panel = [
            "┌── LIFE SUPPORT ─────────────┐",
            "│ O2         20.8 %           │",
            "│ CO2        0.04 %           │",
            "│ HUMIDITY   41 %             │",
            "│ STATUS     NOMINAL          │",
            "└─────────────────────────────┘"
        ]
        draw_sprite(stdscr, sys_panel, 12, 2, color_pair=3)

        # Draw Hardware Badge at top right
        try:
            if fpga_hw:
                b_text, b_color_code = fpga_hw.get_status_badge()
                badge_cp = 4 if b_color_code == "GREEN" else (2 if b_color_code == "RED" else 5)
            else:
                b_text = "[× SOFTWARE VISUALIZATION MODE — FPGA NOT REQUIRED]"
                badge_cp = 2
            stdscr.addstr(1, max(2, w - len(b_text) - 2), b_text, curses.color_pair(badge_cp) | curses.A_BOLD)
        except curses.error:
            pass

        if fpga_hw:
            fpga_op_resp = fpga_hw.step_mars_habitat(altitude_m=0.0, velocity_ms=0.0, impact_trigger=(len(impacts) > 0))
            try:
                from hardware.fpga_health import get_hardware_state
                hw_state = get_hardware_state()
                hw_state_is_connected = hw_state.is_connected
            except Exception:
                hw_state = None
                hw_state_is_connected = False
        else:
            fpga_op_resp = {"hardware_active": False}
            hw_state = None
            hw_state_is_connected = False

        if hw_state_is_connected and hw_state:
            hw_panel = [
                "┌── FPGA HARDWARE ────────────┐",
                f"│ DEVICE   : {hw_state.device[:16]:<16} │",
                "│ STATUS   : ● CONNECTED      │",
                f"│ LATENCY  : {hw_state.last_response_ms:<3} ms            │",
                "│ CORE     : MARS_HABITAT_CORE│",
                f"│ SECT A/B : {str(fpga_op_resp.get('fpga_section_A', 'SECURE'))[:16]:<16} │",
                "└─────────────────────────────┘"
            ]
            draw_sprite(stdscr, hw_panel, 19, 2, color_pair=4)
        else:
            hw_panel = [
                "┌── FPGA HARDWARE ────────────┐",
                f"│ DEVICE   : {'NONE':<16} │",
                "│ STATUS   : × NOT CONNECTED  │",
                "│ TELEMETRY: UNAVAILABLE      │",
                "│ MODE     : SOFTWARE-ONLY    │",
                "└─────────────────────────────┘"
            ]
            draw_sprite(stdscr, hw_panel, 19, 2, color_pair=2)

        # Status Readouts & Controls in Footer
        try:
            stdscr.addstr(h - 3, 2, deploy_msg, curses.color_pair(6) | curses.A_BOLD)
            stdscr.addstr(h - 2, 2, "SYSTEM STATUS: OPERATIONAL // HAB-ARES TOUCHDOWN NOMINAL", curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(h - 1, 2, "[PRESS ESC TO EXIT]    [TAB/W: WORKFLOW LEVER]    [D: DEPLOY MODULE]", curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()

        # Process User Input
        key = stdscr.getch()
        if key == 27:  # ESC -> clean exit to menu
            break
        elif key in (9, ord('w'), ord('W'), curses.KEY_LEFT, curses.KEY_RIGHT):
            workflow_mode = 1 - workflow_mode
        elif key in (ord('d'), ord('D'), ord(' ')):
            module_deploy_state = (module_deploy_state + 1) % 4
            last_deploy_tick = now

        time.sleep(0.08)  # ~12.5 FPS operational simulation rate
