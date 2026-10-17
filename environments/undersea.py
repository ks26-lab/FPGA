import curses
import time
import random
import math

# --- ASCII ART ASSETS ---

# Technical Research Vessel (Surface Carrier)
SHIP_ART = [
    r"                   |__                            ",
    r"                   |\/                            ",
    r"                   ---                            ",
    r"                   / | [RADAR]                    ",
    r"            !__   /  |           _O_ CRANE        ",
    r"           /___|_/___|__________//               ",
    r"          |  RESEARCH VESSEL-04 //               ",
    r"  .-------'                     //                ",
    r" /  [BRIDGE]  [WINCH: ACTIVE]  //===| [PROBE BAY] ",
    r"|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~//~~~~~~~~~~~~~~~~~~|",
    r" \___________________________//__________________/"
]

# Rigid Submersible Exploration Probe
PROBE_ART = [
    r"      .───════════════───.      ",
    r"   .─'   [●] SENSORS [●]  '─.   ",
    r"  /   ┌─────────────────┐   \  ",
    r" | <O>│ ARES PROBE // 01│<O> | ",
    r"  \   └─────────────────┘   /  ",
    r"   '─.   [ THRUSTERS ]   .─'   ",
    r"      '───═(o)═══(o)═───'      "
]

# Clouds for Surface Sky
CLOUD_1 = [
    r"    .---.    ",
    r"  .(     ).  ",
    r" (___.___) ) "
]

CLOUD_2 = [
    r"      .----.       ",
    r"   .+(      )+.    ",
    r"  (____.______) )  "
]

CLOUD_3 = [
    r"   .--.   ",
    r" .(    ). ",
    r"(___.__) )"
]

FISH_RIGHT_S = "><>"
FISH_LEFT_S = "<><"
FISH_RIGHT_M = "><(((('>"
FISH_LEFT_M = "<'))))><"
FISH_RIGHT_L = ">=─<((((((°>"
FISH_LEFT_L = "<°))))))>-─="

def draw_sprite(stdscr, sprite, start_y, start_x, color_pair=0, attrs=0):
    """Safely draws a multi-line ASCII sprite at coordinates without crashing."""
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

def draw_wave_layer(stdscr, y, width, pattern, offset, color_pair=1, attrs=curses.A_NORMAL):
    """Draws a repeating, offset wave layer for parallax depth."""
    h, w = stdscr.getmaxyx()
    if 0 <= y < h:
        repeated = (pattern * (width // len(pattern) + 3))
        start_idx = int(offset) % len(pattern)
        chunk = repeated[start_idx:start_idx + width - 1]
        try:
            stdscr.addstr(y, 0, chunk, curses.color_pair(color_pair) | attrs)
        except curses.error:
            pass

# --- UNDERSEA PHYSICS & AUTONOMOUS CONTROL ENGINE ---

class UnderseaPhysicsEngine:
    """
    Simulates vertical/lateral forces, mass, buoyancy, drag, thrusters,
    closed-loop autonomous depth control, and collision avoidance vectors.
    """
    def __init__(self, depth=70.0, target_depth=70.0):
        self.mass = 320.0             # kg
        self.depth = float(depth)     # Current depth in meters (0 to 500m)
        self.target_depth = float(target_depth)
        self.vel_z = 0.0              # Vertical velocity in m/s (+ = descending)
        self.accel_z = 0.0            # Vertical acceleration in m/s²
        self.vel_x = 0.0              # Lateral velocity in cols/s
        self.buoyancy_bias = 0.12     # Net passive buoyancy in kN (+ = upwards trim)
        self.drag_coeff = 45.0        # Hydrodynamic drag coefficient

        # Operational limits
        self.min_depth = 0.0
        self.max_depth = 500.0
        self.limit_clamped = False

        # Autonomous Control
        self.control_mode = "DEPTH HOLD"  # "DEPTH HOLD", "MANUAL", "EVASIVE"
        self.kp_thrust = 120.0            # Proportional gain (N / m)
        self.kd_damping = 260.0           # Derivative damping gain (N / (m/s))
        self.max_thrust = 1400.0          # Max thruster force in Newtons
        self.thrust_force = 0.0

        # Environmental Disturbance state
        self.disturbance_active = False
        self.disturbance_type = "NONE"
        self.disturbance_dir = "NONE"
        self.disturbance_mag = 0.0
        self.disturbance_timer = 0.0

        # Avoidance State
        self.avoidance_active = False
        self.avoidance_target_name = "NONE"
        self.avoidance_range = 0.0
        self.sonar_bearing = 0

    def set_target_depth(self, new_target):
        """Sets target depth with strict limit enforcement."""
        if new_target > self.max_depth:
            self.target_depth = self.max_depth
            self.limit_clamped = True
        elif new_target < self.min_depth:
            self.target_depth = self.min_depth
            self.limit_clamped = True
        else:
            self.target_depth = round(new_target, 1)
            self.limit_clamped = False

    def trigger_disturbance(self, dist_type=None):
        """Generates an environmental impact, current surge, or creature encounter."""
        types = ["STRONG CURRENT", "DEEP PRESSURE SURGE", "HOSTILE CREATURE", "BENTHIC TURBULENCE"]
        self.disturbance_type = dist_type if dist_type else random.choice(types)
        self.disturbance_dir = random.choice(["PORT", "STARBOARD", "UPWARD SURGE", "DOWNWELLING"])
        self.disturbance_mag = round(random.uniform(0.65, 0.95), 2)
        self.disturbance_timer = random.uniform(3.5, 6.0)
        self.disturbance_active = True
        self.control_mode = "EVASIVE"

    def update(self, dt, manual_z_cmd=0.0, manual_x_cmd=0.0, fishes=None, probe_cx=0, probe_cy=0):
        """Calculates physical forces, integration step, and depth controller response."""
        # 1. Disturbance decay and external forces
        f_dist_z = 0.0
        f_dist_x = 0.0
        if self.disturbance_active:
            self.disturbance_timer -= dt
            if self.disturbance_timer <= 0:
                self.disturbance_active = False
                self.disturbance_type = "NONE"
                self.disturbance_dir = "NONE"
                self.disturbance_mag = 0.0
                if self.control_mode == "EVASIVE":
                    self.control_mode = "DEPTH HOLD"
            else:
                # Continuous disturbance force pushing probe
                strength = self.disturbance_mag * 750.0
                if "UPWARD" in self.disturbance_dir:
                    f_dist_z = -strength
                elif "DOWNWELLING" in self.disturbance_dir:
                    f_dist_z = strength
                elif "PORT" in self.disturbance_dir:
                    f_dist_x = -strength * 0.12
                    f_dist_z = -strength * 0.25
                elif "STARBOARD" in self.disturbance_dir:
                    f_dist_x = strength * 0.12
                    f_dist_z = -strength * 0.25

        # 2. Autonomous Collision Avoidance against moving Marine Fauna
        f_avoid_x = 0.0
        f_avoid_z = 0.0
        self.avoidance_active = False
        closest_dist = 999.0

        if fishes:
            for f in fishes:
                # Distance in screen col/row space
                dx = probe_cx - (f["x"] + 4.0)
                dy = (probe_cy - f["y"]) * 2.2  # Aspect ratio compensation
                dist = math.hypot(dx, dy)

                if dist < closest_dist:
                    closest_dist = dist
                    self.sonar_bearing = int((math.degrees(math.atan2(dx, -dy)) + 360) % 360)

                # Safe bubble radius: 14 columns
                safe_bubble = 14.0
                if dist < safe_bubble:
                    self.avoidance_active = True
                    self.avoidance_target_name = f"BIOLOGICAL [{f['size']}]"
                    self.avoidance_range = dist
                    if self.control_mode != "MANUAL":
                        self.control_mode = "EVASIVE"

                    # Inverse distance avoidance force
                    inv_dist = max(1.0, dist)
                    repel_strength = (safe_bubble - dist) * 70.0
                    f_avoid_x += (dx / inv_dist) * repel_strength
                    f_avoid_z += (dy / inv_dist) * (repel_strength * 2.5)

                    # Fish also reacts and veers away!
                    f["x"] -= (dx / inv_dist) * 1.5
                    f["y"] -= (dy / (inv_dist * 2.2)) * 0.4

        # 3. Depth Control Thruster Calculation
        depth_error = self.target_depth - self.depth  # positive = descend

        if self.control_mode in ("DEPTH HOLD", "EVASIVE"):
            # Closed-Loop PD Depth Controller
            # Desired vertical thrust counters buoyancy bias and drives error to zero
            target_thrust = (self.kp_thrust * depth_error) - (self.kd_damping * self.vel_z)
            # Add passive buoyancy offset (+0.12 kN = 120 N upward bias)
            target_thrust += (self.buoyancy_bias * 1000.0)
            self.thrust_force = max(-self.max_thrust, min(self.max_thrust, target_thrust))
        else:  # MANUAL MODE
            self.thrust_force = manual_z_cmd * self.max_thrust

        # 4. Fluid Dynamics Net Force Calculation
        # Drag opposing vertical motion: F_drag = 0.5 * rho * Cd * A * v * |v|
        f_drag_z = math.copysign(self.drag_coeff * (self.vel_z ** 2), self.vel_z)
        # Buoyancy force (upward bias)
        f_buoyancy = - (self.buoyancy_bias * 1000.0)

        # Total Net Vertical Force
        f_net_z = self.thrust_force + f_buoyancy - f_drag_z + f_dist_z + f_avoid_z

        # F = m * a
        self.accel_z = f_net_z / self.mass
        self.vel_z += self.accel_z * dt
        # Velocity damping / terminal velocity clamp
        self.vel_z = max(-4.5, min(4.5, self.vel_z))

        # Position integration
        self.depth += self.vel_z * dt
        # Physical boundary clamp [0, 500m]
        if self.depth <= self.min_depth:
            self.depth = self.min_depth
            self.vel_z = max(0.0, self.vel_z)
        elif self.depth >= self.max_depth:
            self.depth = self.max_depth
            self.vel_z = min(0.0, self.vel_z)

        # Lateral movement
        lateral_thrust = manual_x_cmd * 35.0 + f_avoid_x * 0.08 + f_dist_x
        self.vel_x = lateral_thrust
        delta_x = self.vel_x * dt

        # Return to Depth Hold once evasive conditions normalize
        if self.control_mode == "EVASIVE" and not self.disturbance_active and not self.avoidance_active:
            if abs(depth_error) < 0.8 and abs(self.vel_z) < 0.4:
                self.control_mode = "DEPTH HOLD"

        return delta_x


def draw_vertical_depth_ruler(stdscr, view_top, view_bottom, ruler_x, current_depth, target_depth):
    """
    Renders a Physical Linear Instrumentation Depth Ruler on the right side of the screen.
    - Vertical scale line with major and minor depth ticks
    - Real-time probe marker [● PROBE] aligned with current depth
    - Real-time target marker [► TARGET] aligned with target depth
    - Dynamic window scrolling as probe climbs or dives
    """
    h, w = stdscr.getmaxyx()
    ruler_h = view_bottom - view_top
    if ruler_h < 8 or ruler_x >= w - 4:
        return

    mid_y = (view_top + view_bottom) // 2
    meters_per_line = 2.0  # 2 meters per terminal row

    # Ruler Header
    try:
        stdscr.addstr(view_top, ruler_x - 1, "┌── DEPTH RULER ──┐", curses.color_pair(1) | curses.A_BOLD)
    except curses.error:
        pass

    # Draw Tick marks and Depth scale lines
    for y in range(view_top + 1, view_bottom):
        row_depth = current_depth + (y - mid_y) * meters_per_line

        # Major tick every 10 meters, minor tick every 5 meters
        depth_int = int(round(row_depth))
        is_major = (depth_int % 10 == 0) and abs(row_depth - depth_int) < 1.0
        is_minor = (depth_int % 5 == 0) and not is_major and abs(row_depth - depth_int) < 1.0

        if 0 <= row_depth <= 500:
            if is_major:
                tick_str = f"{depth_int:4d}m ───────┤"
                tick_color = curses.color_pair(1) | curses.A_BOLD
            elif is_minor:
                tick_str = f"      ───┤"
                tick_color = curses.color_pair(1) | curses.A_DIM
            else:
                tick_str = f"         │"
                tick_color = curses.color_pair(5) | curses.A_DIM
        else:
            tick_str = f"         │"
            tick_color = curses.color_pair(5) | curses.A_DIM

        try:
            stdscr.addstr(y, ruler_x - 1, "│ " + tick_str, tick_color)
            stdscr.addstr(y, ruler_x + 17, "│", curses.color_pair(1))
        except curses.error:
            pass

    # Draw TARGET DEPTH Marker [► TGT]
    target_offset_lines = int(round((target_depth - current_depth) / meters_per_line))
    target_y = mid_y + target_offset_lines
    if view_top + 1 <= target_y < view_bottom:
        try:
            tgt_badge = f"► TGT {target_depth:04.0f}m"
            stdscr.addstr(target_y, ruler_x + 6, tgt_badge, curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

    # Draw CURRENT PROBE Marker [● PROBE] at ruler center
    try:
        probe_badge = f"● PROBE"
        stdscr.addstr(mid_y, ruler_x + 6, probe_badge, curses.color_pair(3) | curses.A_BOLD | curses.A_REVERSE)
    except curses.error:
        pass

    # Ruler Footer
    try:
        stdscr.addstr(view_bottom, ruler_x - 1, "└─────────────────┘", curses.color_pair(1) | curses.A_BOLD)
    except curses.error:
        pass


def run_undersea_cinematic(stdscr):
    """
    Continuous cinematic story introduction:
    SURFACE (Sky + Clouds + Ship) -> DEPLOYMENT (Crane/Cable) -> CAMERA FOLLOWS DOWN -> UNDERWATER
    Pressing any key immediately skips to the operational control panel.
    """
    stdscr.clear()
    curses.curs_set(0)
    stdscr.nodelay(True)

    curses.init_pair(1, curses.COLOR_CYAN, -1)    # Ocean Surface / Waves / Water
    curses.init_pair(2, curses.COLOR_WHITE, -1)   # Ship / Crane / Cable / Clouds
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Sun / Probe Body
    curses.init_pair(4, curses.COLOR_GREEN, -1)   # Status / Diagnostic
    curses.init_pair(5, curses.COLOR_BLUE, -1)    # Deep Ocean Gradient
    curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Sonar / Alerts

    fps = 15
    frame_time = 1.0 / fps
    frame = 0

    h, w = stdscr.getmaxyx()
    water_y = max(8, int(h * 0.40))

    clouds = [
        {"x": float(w * 0.1), "y": 1, "sprite": CLOUD_1, "speed": 1.2},
        {"x": float(w * 0.45), "y": 2, "sprite": CLOUD_2, "speed": 0.8},
        {"x": float(w * 0.78), "y": 1, "sprite": CLOUD_3, "speed": 1.5}
    ]

    ship_w = len(SHIP_ART[0])
    ship_x = float(w // 2 - ship_w // 2)
    ship_y = float(water_y - len(SHIP_ART) + 2)

    probe_w = len(PROBE_ART[0])
    probe_h = len(PROBE_ART)
    probe_x = float(ship_x + 36)
    probe_y = float(water_y - 2)

    camera_y = 0.0
    scene = "SURFACE_IDLE"
    scene_start_time = time.time()
    probe_deployed = False

    particles = [[random.randint(0, w - 1), random.randint(water_y + 2, water_y + 60), random.choice(['.', '·', '°', '*'])] for _ in range(40)]
    bubbles = []

    init_step = 0

    while True:
        loop_start = time.time()
        elapsed = time.time() - scene_start_time
        h, w = stdscr.getmaxyx()

        # Instant skip support
        try:
            key = stdscr.getch()
            if key != -1:
                return
        except curses.error:
            pass

        stdscr.erase()

        # Sequence Logic
        if scene == "SURFACE_IDLE":
            if elapsed > 2.0:
                scene = "DEPLOYMENT"
                scene_start_time = time.time()
                probe_deployed = True

        elif scene == "DEPLOYMENT":
            probe_y += 0.8
            if probe_y > water_y + 5:
                scene = "CAMERA_DESCENT"
                scene_start_time = time.time()

        elif scene == "CAMERA_DESCENT":
            probe_y += 1.4
            camera_y += 1.1
            if camera_y >= water_y - 3:
                camera_y = float(water_y - 3)
                scene = "INITIALIZATION"
                scene_start_time = time.time()

        elif scene == "INITIALIZATION":
            probe_y += 0.15
            if elapsed > 0.4 and init_step == 0: init_step = 1
            if elapsed > 0.8 and init_step == 1: init_step = 2
            if elapsed > 1.2 and init_step == 2: init_step = 3
            if elapsed > 1.6 and init_step == 3: init_step = 4
            if elapsed > 2.0 and init_step == 4: init_step = 5
            if elapsed > 2.4 and init_step == 5: init_step = 6
            if elapsed > 3.0:
                return

        # Render Sky / Clouds
        if camera_y < water_y:
            for c in clouds:
                c["x"] = (c["x"] + c["speed"] * 0.2) % w
                cy = int(c["y"] - camera_y)
                if 0 <= cy < h:
                    draw_sprite(stdscr, c["sprite"], cy, int(c["x"]), color_pair=2)

        # Render Water Surface
        screen_water_y = int(water_y - camera_y)
        if 0 <= screen_water_y < h:
            draw_wave_layer(stdscr, screen_water_y, w, "~.~'~^~", frame * 0.4, color_pair=1, attrs=curses.A_BOLD)

        # Render Ship
        screen_ship_y = int(ship_y - camera_y)
        if screen_ship_y + len(SHIP_ART) > 0 and screen_ship_y < h:
            draw_sprite(stdscr, SHIP_ART, screen_ship_y, int(ship_x), color_pair=2, attrs=curses.A_BOLD)

        # Winch Cable
        screen_probe_y = int(probe_y - camera_y)
        if probe_deployed:
            cable_x = int(probe_x + probe_w // 2)
            cable_top = max(0, int(screen_ship_y + len(SHIP_ART) - 2))
            cable_bottom = min(h, screen_probe_y)
            for cy in range(cable_top, cable_bottom):
                if 0 <= cy < h and 0 <= cable_x < w:
                    try: stdscr.addstr(cy, cable_x, "║", curses.color_pair(2) | curses.A_DIM)
                    except curses.error: pass

        # Probe
        if -probe_h < screen_probe_y < h:
            draw_sprite(stdscr, PROBE_ART, screen_probe_y, int(probe_x), color_pair=3, attrs=curses.A_BOLD)

        # Init Box
        if scene == "INITIALIZATION":
            init_box = [
                "┌── UNDERSEA WORLD // SYSTEM INITIALIZING ────────────────────────┐",
                "│                                                                │",
                f"│   [SHIP TELEMETRY LINK ................... {'OK' if init_step >= 1 else '...':>6}]          │",
                f"│   [WINCH PROBE DEPLOYMENT ................ {'OK' if init_step >= 2 else '...':>6}]          │",
                f"│   [HYDROSTATIC DEPTH SENSOR .............. {'OK' if init_step >= 3 else '...':>6}]          │",
                f"│   [HIGH-PRESSURE SEAL INTEGRITY .......... {'OK' if init_step >= 4 else '...':>6}]          │",
                f"│   [SONAR PHASED ARRAY .................... {'OK' if init_step >= 5 else '...':>6}]          │",
                f"│   [FIBER-OPTIC DATA TETHER ............... {'OK' if init_step >= 6 else '...':>6}]          │",
                "│                                                                │",
                f"│   >>> {'ALL SYSTEMS NOMINAL // TRANSITIONING TO CONTROL PANEL' if init_step >= 6 else 'CALIBRATING ACOUSTIC TELEMETRY...':<57}│",
                "└────────────────────────────────────────────────────────────────┘"
            ]
            draw_sprite(stdscr, init_box, max(2, h // 2 - len(init_box) // 2), max(2, w // 2 - 33), color_pair=4, attrs=curses.A_BOLD)

        try:
            stdscr.addstr(h - 1, 2, "[PRESS ANY KEY TO SKIP INTRO TO MISSION CONTROL]", curses.color_pair(2) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        frame += 1
        elapsed_loop = time.time() - loop_start
        if elapsed_loop < frame_time:
            time.sleep(frame_time - elapsed_loop)


def launch_undersea(stdscr, fpga_hw=None):
    """
    Entry point for the UNDERSEA WORLD environment.
    Unified physical simulation:
    - Target Depth specification & Autonomous Depth Control
    - Lightweight fluid-dynamics model (buoyancy, gravity, drag, thrust)
    - Right-Side Linear Depth Ruler with dynamic scrolling & probe/target alignment
    - Environmental Disturbances & Autonomous Recovery
    - Marine fauna with collision avoidance and safety bubble
    - Comprehensive mission control telemetry & diagnostics
    """
    # 1. Run Cinematic Introduction
    run_undersea_cinematic(stdscr)

    # 2. Operational Control Setup
    stdscr.nodelay(True)
    curses.curs_set(0)

    curses.init_pair(1, curses.COLOR_CYAN, -1)    # Water / Live View Frame / Ruler
    curses.init_pair(2, curses.COLOR_GREEN, -1)   # Target Depth / Normal Status / OK
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Probe / Active Thrusters / Highlighting
    curses.init_pair(4, curses.COLOR_WHITE, -1)   # Borders / Text / Tethers
    curses.init_pair(5, curses.COLOR_BLUE, -1)    # Deep Ocean Gradient / Secondary Ruler Ticks
    curses.init_pair(6, curses.COLOR_RED, -1)     # Warnings / Alerts / Collisions / Alarms
    curses.init_pair(7, curses.COLOR_MAGENTA, -1) # Creature Contacts / Sonar Beacons

    h, w = stdscr.getmaxyx()

    # Physics Core
    physics = UnderseaPhysicsEngine(depth=70.0, target_depth=70.0)

    if fpga_hw is None:
        try:
            from hardware.fpga_interface import get_fpga_interface
            fpga_hw = get_fpga_interface()
        except ImportError:
            pass

    # Probe Dimensions & Screen Positioning
    probe_w = len(PROBE_ART[0])
    probe_h = len(PROBE_ART)
    probe_x = float(w // 2 - probe_w // 2 - 8)
    probe_y = float(max(5, (h - 11) // 2 - probe_h // 2))

    # Sonar Ping state
    sonar_ping_active = False
    sonar_ping_radius = 0
    sonar_ping_max = 26
    sonar_ping_center = (0, 0)
    sonar_mode = "ACTIVE PASSIVE ARRAY"

    # Marine Environment
    bubbles = []
    particles = [
        {"x": random.randint(4, w - 24), "y": random.randint(4, h - 12), "char": random.choice(['.', '·', '°', '*']),
         "speed": random.uniform(1.0, 3.5), "depth": random.choice(["NEAR", "MID", "FAR"])}
        for _ in range(45)
    ]

    # Dynamic Autonomous Fish Entities
    fishes = [
        {"x": float(random.randint(6, w - 30)), "y": float(random.randint(6, max(7, h - 14))), "vx": 10.0, "vy": 0.0, "dir": 1, "size": "M"},
        {"x": float(random.randint(6, w - 30)), "y": float(random.randint(6, max(7, h - 14))), "vx": 15.0, "vy": 0.0, "dir": -1, "size": "S"},
        {"x": float(random.randint(6, w - 30)), "y": float(random.randint(6, max(7, h - 14))), "vx": 8.0, "vy": 0.0, "dir": 1, "size": "L"},
        {"x": float(random.randint(6, w - 30)), "y": float(random.randint(6, max(7, h - 14))), "vx": 12.0, "vy": 0.0, "dir": -1, "size": "M"}
    ]

    last_tick = time.time()
    last_disturbance_check = time.time()
    battery_pct = 88.5

    # Main Interactive Simulation Loop
    while True:
        now = time.time()
        dt = min(0.08, max(0.001, now - last_tick))
        last_tick = now

        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Layout boundaries
        view_top = 3
        view_bottom = max(view_top + 10, h - 11)
        view_left = 2
        ruler_x = w - 20
        view_right = ruler_x - 2

        # -------------------------------------------------------------
        # 1. PROCESS ENVIRONMENTAL DISTURBANCES & TIMERS
        # -------------------------------------------------------------
        # Periodic chance of autonomous ocean disturbance every 18-25 seconds
        if now - last_disturbance_check > 22.0:
            last_disturbance_check = now
            if random.random() < 0.40 and not physics.disturbance_active:
                physics.trigger_disturbance()

        # -------------------------------------------------------------
        # 2. RUN PHYSICS INTEGRATION & AUTONOMOUS AVOIDANCE
        # -------------------------------------------------------------
        probe_center_x = probe_x + probe_w // 2
        probe_center_y = probe_y + probe_h // 2

        delta_x = physics.update(dt, manual_z_cmd=0.0, manual_x_cmd=0.0,
                                 fishes=fishes, probe_cx=probe_center_x, probe_cy=probe_center_y)
        probe_x += delta_x

        # Screen vertical position responds dynamically to depth rate
        # Probe center slightly shifts up/down relative to neutral view center based on velocity
        desired_scr_y = ((view_top + view_bottom) // 2 - probe_h // 2) + (physics.vel_z * 2.2)
        probe_y += (desired_scr_y - probe_y) * 0.12

        # Clamp probe within Live Water Viewport (left of ruler)
        probe_x = max(view_left + 1, min(view_right - probe_w - 1, probe_x))
        probe_y = max(view_top + 1, min(view_bottom - probe_h - 1, probe_y))

        # Dynamic Marine Snow
        for p in particles:
            p["y"] -= p["speed"] * dt
            if p["y"] <= view_top:
                p["y"] = view_bottom - 1
                p["x"] = random.randint(view_left + 1, view_right - 1)

        # Dynamic Swimming Fish with natural depth variation and boundary turns
        for f in fishes:
            f["x"] += f["dir"] * f["vx"] * dt
            # Subtle depth oscillation
            f["y"] += math.sin(now * 1.5 + f["x"] * 0.1) * 0.08
            f["y"] = max(view_top + 2, min(view_bottom - 2, f["y"]))

            # Turn around at viewport boundaries
            if f["dir"] == 1 and f["x"] > view_right - 6:
                f["dir"] = -1
            elif f["dir"] == -1 and f["x"] < view_left + 2:
                f["dir"] = 1

        # Vent thruster aeration bubbles
        if random.random() < 0.35 or abs(physics.vel_z) > 0.4:
            bx = probe_x + random.choice([8, 14, probe_w - 9])
            by = probe_y + probe_h
            bubbles.append([float(bx), float(by), random.choice(['o', '°', '○']), random.uniform(8.0, 16.0)])

        active_bubbles = []
        for b in bubbles:
            b[1] -= b[3] * dt
            b[0] += math.sin(now * 3.0 + b[1]) * 0.4
            if b[1] > view_top and view_left < b[0] < view_right:
                active_bubbles.append(b)
        bubbles = active_bubbles

        # Sonar Ping wave propagation
        if sonar_ping_active:
            sonar_ping_radius += 2
            if sonar_ping_radius > sonar_ping_max:
                sonar_ping_active = False

        # Physical calculations for telemetry
        depth_m = physics.depth
        pressure_mpa = depth_m * 0.1005 + 0.1013  # Hydrostatic pressure
        temperature_c = max(1.4, 5.2 - (depth_m / 100.0) * 0.75)
        battery_pct = max(12.0, battery_pct - dt * 0.003)

        # -------------------------------------------------------------
        # EDGE ZYNQ Z7010 REAL HARDWARE STEP
        # -------------------------------------------------------------
        d_code = 1 if "CREATURE" in physics.disturbance_type else (2 if "PRESSURE" in physics.disturbance_type else (3 if "TURBULENCE" in physics.disturbance_type else 0))
        if fpga_hw:
            hw_res = fpga_hw.step_undersea_probe(
                current_depth_m=physics.depth,
                target_depth_m=physics.target_depth,
                current_strength_pct=int(physics.disturbance_mag * 100) if physics.disturbance_active else 0,
                disturb_type=d_code
            )
        else:
            hw_res = {"hardware_active": False, "fpga_depth": None}

        if hw_res["hardware_active"] and hw_res["fpga_depth"] is not None:
            # Authoritative FPGA PL drives depth & thrust registers
            physics.depth = hw_res["fpga_depth"]
            physics.vel_z = hw_res["fpga_velocity"]
            physics.thrust_force = hw_res["fpga_thrust"]

        if fpga_hw:
            b_text, b_col = fpga_hw.get_status_badge()
            hw_col = 2 if b_col == "GREEN" else (6 if b_col == "RED" else 3)
            hw_badge = b_text
        else:
            hw_badge = "[× SOFTWARE VISUALIZATION MODE — FPGA NOT REQUIRED]"
            hw_col = 6

        # -------------------------------------------------------------
        # 3. TOP HEADER BAR WITH AUTHORITATIVE HARDWARE BADGE
        # -------------------------------------------------------------
        header_text = " UNDERSEA PROBE // OPERATIONAL MISSION CONTROL "
        try:
            stdscr.addstr(0, 0, "┌" + "─" * (w - 2) + "┐", curses.color_pair(1))
            stdscr.addstr(1, 0, "│", curses.color_pair(1))
            stdscr.addstr(1, 2, header_text, curses.color_pair(1) | curses.A_BOLD)
            # Display real hardware connection status badge on top right
            stdscr.addstr(1, max(len(header_text) + 4, w - len(hw_badge) - 2), hw_badge, curses.color_pair(hw_col) | curses.A_BOLD)
            stdscr.addstr(1, w - 1, "│", curses.color_pair(1))
            stdscr.addstr(2, 0, "├" + "─" * (w - 2) + "┤", curses.color_pair(1))
        except curses.error:
            pass

        # -------------------------------------------------------------
        # 4. LIVE UNDERWATER VIEWPORT
        # -------------------------------------------------------------
        for r in range(view_top, view_bottom):
            try:
                stdscr.addstr(r, 0, "│", curses.color_pair(1))
                stdscr.addstr(r, w - 1, "│", curses.color_pair(1))
            except curses.error:
                pass

        # Waterline text
        water_surface_txt = "≈≈≈ LIVE UNDERWATER FEED // CAM-01 [AUTONOMOUS DEPTH CONTROLLER] ≈≈≈"
        try:
            stdscr.addstr(view_top, max(2, (view_right - len(water_surface_txt)) // 2), water_surface_txt, curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        # Distant seabed ridges in background
        ridge_y = view_bottom - 1
        ridge_pat = r"____/\____/^^^\___/\__/\____/^^^^^\____/\__"
        ridge_line = (ridge_pat * (view_right // len(ridge_pat) + 2))[:view_right - view_left - 1]
        try:
            stdscr.addstr(ridge_y, view_left + 1, ridge_line, curses.color_pair(5) | curses.A_DIM)
        except curses.error:
            pass

        # Suspended Marine Snow & Floating Particles
        for p in particles:
            px_val, py_val = int(p["x"]), int(p["y"])
            if view_top < py_val < view_bottom and view_left < px_val < view_right:
                p_attr = curses.color_pair(1) | curses.A_BOLD if p["depth"] == "NEAR" else curses.color_pair(5) | curses.A_DIM
                try: stdscr.addstr(py_val, px_val, p["char"], p_attr)
                except curses.error: pass

        # Swimming Marine Fauna
        for f in fishes:
            fx, fy = int(f["x"]), int(f["y"])
            if view_top < fy < view_bottom:
                if f["size"] == "S":
                    f_str = FISH_RIGHT_S if f["dir"] == 1 else FISH_LEFT_S
                    f_color = curses.color_pair(4) | curses.A_DIM
                elif f["size"] == "M":
                    f_str = FISH_RIGHT_M if f["dir"] == 1 else FISH_LEFT_M
                    f_color = curses.color_pair(1) | curses.A_BOLD
                else:
                    f_str = FISH_RIGHT_L if f["dir"] == 1 else FISH_LEFT_L
                    f_color = curses.color_pair(7) | curses.A_BOLD

                # Sonar highlight if close to probe
                dist_to_probe = math.hypot(probe_center_x - fx, probe_center_y - fy)
                if dist_to_probe < 16.0:
                    f_color = curses.color_pair(6) | curses.A_BOLD

                if view_left < fx < view_right - len(f_str):
                    try: stdscr.addstr(fy, fx, f_str, f_color)
                    except curses.error: pass

        # Surface Winch Tether Cable
        cable_cx = int(probe_x + probe_w // 2)
        for cy in range(view_top + 1, int(probe_y)):
            if cy < view_bottom and 0 <= cable_cx < view_right:
                try: stdscr.addstr(cy, cable_cx, "║", curses.color_pair(4) | curses.A_DIM)
                except curses.error: pass

        # Rising Aeration Bubbles
        for b in bubbles:
            bx, by = int(b[0]), int(b[1])
            if view_top < by < view_bottom and view_left < bx < view_right:
                try: stdscr.addstr(by, bx, b[2], curses.color_pair(1) | curses.A_BOLD)
                except curses.error: pass

        # Sonar Ping Echo Rings
        if sonar_ping_active:
            scx, scy = sonar_ping_center
            r = sonar_ping_radius
            for angle_deg in range(0, 360, 20):
                rad = math.radians(angle_deg)
                sx = int(scx + r * math.cos(rad) * 1.8)
                sy = int(scy + r * math.sin(rad))
                if view_top < sy < view_bottom and view_left < sx < view_right:
                    try: stdscr.addstr(sy, sx, "·", curses.color_pair(2) | curses.A_BOLD)
                    except curses.error: pass

        # Draw Exploration Probe
        draw_sprite(stdscr, PROBE_ART, int(probe_y), int(probe_x), color_pair=3, attrs=curses.A_BOLD)

        # Disturbance Warning Banner in Viewport
        if physics.disturbance_active:
            warn_box = f" ! DISTURBANCE DETECTED: {physics.disturbance_type} [{physics.disturbance_dir} MAG:{physics.disturbance_mag}] !"
            try:
                stdscr.addstr(view_top + 1, view_left + 2, warn_box[:view_right - view_left - 4], curses.color_pair(6) | curses.A_BOLD | curses.A_BLINK)
            except curses.error:
                pass
        elif physics.avoidance_active:
            avoid_box = f" >> AVOIDANCE ACTIVE: STEERING CLEAR OF {physics.avoidance_target_name} [RANGE:{physics.avoidance_range:.1f}m] <<"
            try:
                stdscr.addstr(view_top + 1, view_left + 2, avoid_box[:view_right - view_left - 4], curses.color_pair(7) | curses.A_BOLD)
            except curses.error:
                pass

        # -------------------------------------------------------------
        # 5. RIGHT-SIDE PHYSICAL LINEAR DEPTH RULER
        # -------------------------------------------------------------
        draw_vertical_depth_ruler(stdscr, view_top, view_bottom, ruler_x, physics.depth, physics.target_depth)

        # -------------------------------------------------------------
        # 6. LOWER TELEMETRY & PILOT CONTROLS HUD
        # -------------------------------------------------------------
        sep_y = view_bottom
        try:
            stdscr.addstr(sep_y, 0, "├" + "─" * (w - 2) + "┤", curses.color_pair(1))
        except curses.error:
            pass

        col1_x = 3
        col2_x = max(col1_x + 48, w // 2 + 2)

        # Left Column: Comprehensive Physics & Depth Control Telemetry
        depth_err = physics.target_depth - physics.depth
        status_tag = "LIMIT CLAMPED" if physics.limit_clamped else ("STABILIZING" if abs(depth_err) > 0.4 else "DEPTH STABLE")

        try:
            stdscr.addstr(sep_y + 1, col1_x, "SYSTEM STATUS & FPGA HARDWARE DIAGNOSTICS", curses.color_pair(2) | curses.A_BOLD)
            
            hw_src_txt = "● FPGA HARDWARE ACTIVE (AXI 0x43C0_0000)" if hw_res["hardware_active"] else "× FPGA NOT CONNECTED (SOFTWARE-ONLY MODE)"
            hw_src_col = 5 if hw_res["hardware_active"] else 4
            stdscr.addstr(sep_y + 2, col1_x, f"HARDWARE LINK: {hw_src_txt:<35}", curses.color_pair(hw_src_col) | curses.A_BOLD)

            fpga_depth_txt = f"{hw_res['fpga_depth']:.1f} m" if hw_res['fpga_depth'] is not None else "N/A"
            fpga_thrust_txt = f"{hw_res['fpga_thrust']:.0f} N" if hw_res['fpga_thrust'] is not None else "N/A"
            stdscr.addstr(sep_y + 3, col1_x, f"FPGA TELEMETRY: DEPTH: {fpga_depth_txt:<7} │ THRUST: {fpga_thrust_txt:<7} │ FSM: {hw_res.get('fpga_state', 'OFFLINE')}", curses.color_pair(5 if hw_res["hardware_active"] else 3))

            stdscr.addstr(sep_y + 4, col1_x, f"DEPTH        : {physics.depth:06.1f} m  │ TARGET: {physics.target_depth:06.1f} m", curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(sep_y + 5, col1_x, f"DEPTH ERROR  : {depth_err:+05.1f} m   │ VERT SPEED: {physics.vel_z:+04.1f} m/s", curses.color_pair(2 if abs(depth_err) < 0.8 else 3))
            stdscr.addstr(sep_y + 6, col1_x, f"BUOYANCY     : +{physics.buoyancy_bias:.2f} kN │ ACCEL: {physics.accel_z:+04.2f} m/s²", curses.color_pair(4))
            stdscr.addstr(sep_y + 7, col1_x, f"PRESSURE     : {pressure_mpa:05.2f} MPa │ TEMP : {temperature_c:04.1f} °C", curses.color_pair(4))
            stdscr.addstr(sep_y + 8, col1_x, f"CONTROL MODE : {physics.control_mode:<10} │ BATTERY: {battery_pct:04.1f} %", curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

        # Vertical Divider
        for r in range(sep_y + 1, h - 1):
            try:
                stdscr.addstr(r, col2_x - 3, "│", curses.color_pair(1))
                stdscr.addstr(r, 0, "│", curses.color_pair(1))
                stdscr.addstr(r, w - 1, "│", curses.color_pair(1))
            except curses.error:
                pass

        # Right Column: Pilot Controls
        try:
            stdscr.addstr(sep_y + 1, col2_x, "OPERATIONAL PILOT CONTROLS", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(sep_y + 2, col2_x, "[W / S] or [UP / DOWN] : Adjust Target Depth (±1m)", curses.color_pair(4))
            stdscr.addstr(sep_y + 3, col2_x, "[Z / X]                : Coarse Target Depth (±10m)", curses.color_pair(4))
            stdscr.addstr(sep_y + 4, col2_x, "[A / D] or [LEFT / RG] : Maneuver Probe Thrusters", curses.color_pair(4))
            stdscr.addstr(sep_y + 5, col2_x, "[R]                    : Lock Current Depth as Target", curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(sep_y + 6, col2_x, "[D]                    : Trigger Ocean Disturbance Surge", curses.color_pair(6))
            stdscr.addstr(sep_y + 7, col2_x, "[SPACE]                : Pulse Active Acoustic Sonar", curses.color_pair(4))
            stdscr.addstr(sep_y + 8, col2_x, "[ESC]                  : Safe Disconnect & Exit", curses.color_pair(6) | curses.A_BOLD)
        except curses.error:
            pass

        try:
            stdscr.addstr(h - 1, 0, "└" + "─" * (w - 2) + "┘", curses.color_pair(1))
        except curses.error:
            pass

        stdscr.refresh()

        # -------------------------------------------------------------
        # 7. PROCESS PILOT INTERACTION INPUTS
        # -------------------------------------------------------------
        key = stdscr.getch()
        if key == 27:  # ESC -> return to menu
            break

        # Adjust Target Depth (Fine: ±1m)
        elif key in (ord('w'), ord('W'), curses.KEY_UP):
            physics.set_target_depth(physics.target_depth - 1.0)
            if physics.control_mode == "MANUAL":
                physics.control_mode = "DEPTH HOLD"

        elif key in (ord('s'), ord('S'), curses.KEY_DOWN):
            physics.set_target_depth(physics.target_depth + 1.0)
            if physics.control_mode == "MANUAL":
                physics.control_mode = "DEPTH HOLD"

        # Coarse Target Depth (±10m)
        elif key in (ord('z'), ord('Z')):
            physics.set_target_depth(physics.target_depth - 10.0)
            if physics.control_mode == "MANUAL":
                physics.control_mode = "DEPTH HOLD"

        elif key in (ord('x'), ord('X')):
            physics.set_target_depth(physics.target_depth + 10.0)
            if physics.control_mode == "MANUAL":
                physics.control_mode = "DEPTH HOLD"

        # Lateral Thruster Maneuver
        elif key in (ord('a'), ord('A'), curses.KEY_LEFT):
            probe_x -= 3.5

        elif key in (ord('d'), ord('D'), curses.KEY_RIGHT):
            probe_x += 3.5

        # Return to Current Depth Hold
        elif key in (ord('r'), ord('R')):
            physics.set_target_depth(physics.depth)
            physics.control_mode = "DEPTH HOLD"

        # Trigger Ocean Disturbance
        elif key in (ord('d'), ord('D')):
            physics.trigger_disturbance()

        # Toggle Control Mode
        elif key in (ord('m'), ord('M')):
            physics.control_mode = "MANUAL" if physics.control_mode != "MANUAL" else "DEPTH HOLD"

        # Active Sonar Ping
        elif key in (ord(' '), ord('p'), ord('P')):
            sonar_ping_active = True
            sonar_ping_radius = 2
            sonar_ping_center = (int(probe_x + probe_w // 2), int(probe_y + probe_h // 2))

        time.sleep(0.035)  # ~28 FPS smooth simulation
