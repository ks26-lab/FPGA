import curses
import time
import random
import math
import os
import csv

# --- DETAILED ASCII ART ASSETS STRICTLY MATCHING REFERENCE IMAGE ---

# Large Sun with starburst rays and top "ASCII" label
SUN_ART_LARGE = [
    r"         ASCII         ",
    r"       \   |   /       ",
    r"     \   \ | /   /     ",
    r"   ──── ( ☼☼☼☼ ) ────  ",
    r"     /   / | \   \     ",
    r"       /   |   \       "
]

# Distant Clouds in upper sky
CLOUD_SPRITE_1 = r".--.   .----.   .--."
CLOUD_SPRITE_2 = r"    .----.    .--.    "

# Mesa / Mountain Horizon Silhouettes
HORIZON_MESAS = [
    r"     __/\__          _/\_               ___/\___          /\_          ",
    r"____/      \________/    \_____________/        \________/   \_________"
]

# Left Array (4-Quadrant tracking module on gimbal mount with snaking conduit)
ARRAY_LEFT_ART = [
    r"   ┌────┬────┐   ",
    r"  ╱▓▓▓▓╱▓▓▓▓╱│   ",
    r" ├────┼────┤ │   ",
    r" │▓▓▓▓│▓▓▓▓│ │   ",
    r" └────┴────┘ │   ",
    r"    │  ║  │  │   ",
    r"    └──╩──┘──┘   ",
    r"       ║         ",
    r"      [GIMBAL-B] "
]

# Main Central Array (Multi-Cell Angled Gimbal Surface with mechanical pivot)
MAIN_ARRAY_OPTIMAL = [
    r"    ┌─────┬─────┬─────┬─────┐    ",
    r"   ╱ ▓▓▓ ╱ ▓▓▓ ╱ ▓▓▓ ╱ ▓▓▓ ╱│    ",
    r"  ├─────┼─────┼─────┼─────┤ │    ",
    r" ╱ ▓▓▓ ╱ ▓▓▓ ╱ ▓▓▓ ╱ ▓▓▓ ╱│ │    ",
    r"├─────┼─────┼─────┼─────┤ │ │    ",
    r"│ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │ │ │    ",
    r"└─────┴─────┴─────┴─────┘ │ │    ",
    r" │   [DUAL-AXIS GIMBAL A] │ │    ",
    r" └───┬───────────────┬────┘ │    ",
    r"     │     ┌───┐     │     ╱     ",
    r"     └─────┤ O ├─────┘────┘      ",
    r"           └───┘                 "
]

MAIN_ARRAY_TILT_LEFT = [
    r"      ┌─────┬─────┬─────┬─────┐  ",
    r"    .╱ ▓▓▓ ╱ ▓▓▓ ╱ ▓▓▓ ╱ ▓▓▓ ╱   ",
    r"   .├─────┼─────┼─────┼─────┤    ",
    r"  .╱ ▓▓▓ ╱ ▓▓▓ ╱ ▓▓▓ ╱ ▓▓▓ ╱     ",
    r" .├─────┼─────┼─────┼─────┤      ",
    r" │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │       ",
    r" └─────┴─────┴─────┴─────┘       ",
    r"  │   [AZIMUTH -25°]    │        ",
    r"  └───┬───────────┬─────┘        ",
    r"      │   ┌───┐   │              ",
    r"      └───┤ O ├───┘              "
]

MAIN_ARRAY_TILT_RIGHT = [
    r"  ┌─────┬─────┬─────┬─────┐      ",
    r"   ╲ ▓▓▓ ╲ ▓▓▓ ╲ ▓▓▓ ╲ ▓▓▓ ╲.    ",
    r"    ├─────┼─────┼─────┼─────┤.   ",
    r"     ╲ ▓▓▓ ╲ ▓▓▓ ╲ ▓▓▓ ╲ ▓▓▓ ╲.  ",
    r"      ├─────┼─────┼─────┼─────┤. ",
    r"      │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │  ",
    r"      └─────┴─────┴─────┴─────┘  ",
    r"       │   [AZIMUTH +25°]    │   ",
    r"       └───┬───────────┬─────┘   ",
    r"           │   ┌───┐   │         ",
    r"           └───┤ O ├───┘         "
]

# Right Array (Angled bank on desert hill)
ARRAY_RIGHT_ART = [
    r"  ┌──────┬──────┬──────┐  ",
    r" ╱ ▓▓▓▓ ╱ ▓▓▓▓ ╱ ▓▓▓▓ ╱│  ",
    r"├──────┼──────┼──────┤ │  ",
    r"│ ▓▓▓▓ │ ▓▓▓▓ │ ▓▓▓▓ │ │  ",
    r"└──────┴──────┴──────┘ │  ",
    r"   │     │     │       │  ",
    r"   └─────┴─────┴───────┘  ",
    r"        [GIMBAL-C]        "
]

# Distant Small Arrays on Hillslopes
ARRAY_DISTANT = [
    r" ┌─┬─┐ ",
    r" │▓│▓│ ",
    r" └─┴─┘ ",
    r"   │   "
]

# Rocky outcrop on right foreground
ROCK_FORMATION = [
    r"       _/\_       ",
    r"     _/    \      ",
    r"    /  /\   \     ",
    r"   /  /  \   \__  ",
    r" _/  /    \     \ ",
    r"/___/______\_____\ ",
]

# Personnel / Engineers
PERSON_1 = [
    r"  o  ",
    r" /|\ ",
    r" / \ "
]

PERSON_2 = [
    r" \o/ ",
    r"  |  ",
    r" / \ "
]

def draw_sprite(stdscr, sprite, start_y, start_x, color_pair=0, attrs=0):
    """Draws multi-line ASCII sprite safely within terminal bounds."""
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

# --- PHYSICAL SIMULATION CLASSES ---

class SunState:
    """Authoritative Sun Position & Irradiance State."""
    def __init__(self, azimuth=135.0, elevation=42.0, irradiance=1001.0):
        self.azimuth = float(azimuth)       # 0.0 to 360.0 degrees (180 = South, 90 = East, 270 = West)
        self.elevation = float(elevation)   # 0.0 (horizon) to 90.0 (zenith)
        self.irradiance = float(irradiance) # Base direct beam solar irradiance in W/m²
        self.mode = "MANUAL"                # "MANUAL", "AUTO", "DATASET"
        self.auto_start_time = time.time()

    def update_auto(self, now):
        """Generates smooth, physically continuous diurnal solar arc."""
        cycle_sec = 60.0  # 60s per complete day/night cycle
        cycle_progress = ((now - self.auto_start_time) % cycle_sec) / cycle_sec
        # Daytime: 70% of cycle (progress 0.0 to 0.7)
        if cycle_progress < 0.70:
            day_t = cycle_progress / 0.70
            # Azimuth sweeps from 75° (East-North-East) to 285° (West-North-West)
            self.azimuth = 75.0 + day_t * 210.0
            # Elevation follows smooth sine curve from 0° -> 68° peak -> 0°
            sin_val = math.sin(day_t * math.pi)
            self.elevation = max(0.0, sin_val * 68.0)
            self.irradiance = max(0.0, sin_val * 1024.0)
        else:
            # Nighttime: Sun below horizon
            night_t = (cycle_progress - 0.70) / 0.30
            self.azimuth = (285.0 + night_t * 150.0) % 360.0
            self.elevation = 0.0
            self.irradiance = 0.0


class GimbalState:
    """Authoritative Dual-Axis Solar Gimbal Panel Orientation."""
    def __init__(self, azimuth=132.0, elevation=40.0):
        self.azimuth = float(azimuth)         # Actual panel azimuth in degrees
        self.elevation = float(elevation)     # Actual panel elevation in degrees
        self.target_azimuth = float(azimuth)
        self.target_elevation = float(elevation)
        self.tracking_enabled = True
        self.slew_rate = 14.0                 # Degrees per second realistic drive speed

    def update(self, dt, target_az, target_el):
        """Drives the gimbal servos toward target angles with realistic slew rate."""
        self.target_azimuth = target_az
        self.target_elevation = max(0.0, min(90.0, target_el))

        if self.tracking_enabled:
            # Shortest angular distance on circle for azimuth
            az_diff = ((self.target_azimuth - self.azimuth + 180.0) % 360.0) - 180.0
            el_diff = self.target_elevation - self.elevation

            max_step = self.slew_rate * dt
            if abs(az_diff) <= max_step:
                self.azimuth = self.target_azimuth
            else:
                self.azimuth = (self.azimuth + math.copysign(max_step, az_diff)) % 360.0

            if abs(el_diff) <= max_step:
                self.elevation = self.target_elevation
            else:
                self.elevation += math.copysign(max_step, el_diff)
                self.elevation = max(0.0, min(90.0, self.elevation))


class DatasetManager:
    """Loads, validates, and plays Sun trajectory datasets (CSV)."""
    def __init__(self):
        self.filepath = ""
        self.records = []
        self.current_step = 0
        self.is_active = False
        self.is_paused = False
        self.step_interval = 1.0  # seconds between timesteps during playback
        self.last_step_time = 0.0

    def load_file(self, filename):
        """Loads and validates a CSV file containing TIME, AZIMUTH, ELEVATION, IRRADIANCE."""
        path_to_try = filename
        if not os.path.isabs(path_to_try):
            path_to_try = os.path.join(os.getcwd(), filename)

        if not os.path.exists(path_to_try):
            return False, f"File not found: '{os.path.basename(filename)}'"

        try:
            with open(path_to_try, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    return False, "CSV file is empty"

                header_map = {}
                for idx, col in enumerate(header):
                    col_u = col.strip().upper()
                    if "TIME" in col_u: header_map["time"] = idx
                    elif "AZ" in col_u: header_map["azimuth"] = idx
                    elif "EL" in col_u: header_map["elevation"] = idx
                    elif "IRR" in col_u: header_map["irradiance"] = idx

                for req in ("time", "azimuth", "elevation", "irradiance"):
                    if req not in header_map:
                        return False, f"Missing required column '{req.upper()}'"

                records = []
                for row_idx, row in enumerate(reader, start=2):
                    if not row or not any(row):
                        continue
                    try:
                        t_str = row[header_map["time"]].strip()
                        az_val = float(row[header_map["azimuth"]].strip())
                        el_val = float(row[header_map["elevation"]].strip())
                        irr_val = float(row[header_map["irradiance"]].strip())

                        if math.isnan(az_val) or math.isnan(el_val) or math.isnan(irr_val):
                            return False, f"NaN value at row {row_idx}"
                        if az_val < 0.0 or az_val > 360.0:
                            return False, f"Invalid azimuth ({az_val}°) at row {row_idx}"
                        if el_val < -90.0 or el_val > 90.0:
                            return False, f"Invalid elevation ({el_val}°) at row {row_idx}"
                        if irr_val < 0.0:
                            return False, f"Negative irradiance ({irr_val}) at row {row_idx}"

                        records.append({
                            "time": t_str,
                            "azimuth": az_val,
                            "elevation": el_val,
                            "irradiance": irr_val
                        })
                    except (ValueError, IndexError) as err:
                        return False, f"Malformed data at row {row_idx}: {err}"

                if not records:
                    return False, "No valid data records found in dataset"

                self.records = records
                self.filepath = path_to_try
                self.current_step = 0
                self.is_active = False
                self.is_paused = False
                return True, f"Loaded {len(records)} timesteps from '{os.path.basename(path_to_try)}'"
        except Exception as ex:
            return False, f"Failed to load dataset: {str(ex)}"

    def get_current_record(self):
        if self.records and 0 <= self.current_step < len(self.records):
            return self.records[self.current_step]
        return None

    def advance(self):
        if not self.records:
            return None
        self.current_step = (self.current_step + 1) % len(self.records)
        return self.get_current_record()

    def restart(self):
        self.current_step = 0
        return self.get_current_record()


def calculate_solar_physics(sun: SunState, gimbal: GimbalState):
    """
    Computes rigorous 3D spherical incident angle, effective irradiance,
    captured power, tracking errors, and tracking quality score.
    ONE authoritative state drives everything.
    """
    s_az_rad = math.radians(sun.azimuth)
    s_el_rad = math.radians(sun.elevation)
    p_az_rad = math.radians(gimbal.azimuth)
    p_el_rad = math.radians(gimbal.elevation)

    # 3D Dot Product between Sun unit vector and Panel Normal unit vector:
    # cos(theta) = sin(el_s)*sin(el_p) + cos(el_s)*cos(el_p)*cos(az_s - az_p)
    cos_theta = (math.sin(s_el_rad) * math.sin(p_el_rad) +
                 math.cos(s_el_rad) * math.cos(p_el_rad) * math.cos(s_az_rad - p_az_rad))
    cos_theta_clamped = max(-1.0, min(1.0, cos_theta))
    incident_angle_deg = math.degrees(math.acos(cos_theta_clamped))

    # Clamp effective cosine factor: cos(theta) < 0 -> 0 (back-facing or below horizon)
    cos_factor = max(0.0, cos_theta)
    if sun.elevation <= 0.0:
        cos_factor = 0.0

    # Effective captured irradiance and output power (858.8 kW nominal at 1000 W/m²)
    effective_irr = sun.irradiance * cos_factor
    output_kw = (effective_irr / 1000.0) * 858.8

    # Individual and 3D tracking errors
    az_err = abs(((sun.azimuth - gimbal.azimuth + 180.0) % 360.0) - 180.0)
    el_err = abs(sun.elevation - gimbal.elevation)
    total_err = incident_angle_deg

    # Tracking quality indicator
    # 0–2°   -> excellent
    # 2–5°   -> good
    # 5–10°  -> degraded
    # >10°   -> poor
    if total_err <= 2.0:
        quality_pct = max(95.0, 100.0 - (total_err / 2.0) * 5.0)
        quality_label = "EXCELLENT"
        quality_color = 4  # Green
    elif total_err <= 5.0:
        quality_pct = 80.0 + ((5.0 - total_err) / 3.0) * 14.0
        quality_label = "GOOD"
        quality_color = 1  # Cyan
    elif total_err <= 10.0:
        quality_pct = 50.0 + ((10.0 - total_err) / 5.0) * 29.0
        quality_label = "DEGRADED"
        quality_color = 2  # Yellow
    else:
        quality_pct = max(0.0, 48.0 - (total_err - 10.0) * 1.5)
        quality_label = "POOR"
        quality_color = 6  # Red

    return {
        "incident_angle": incident_angle_deg,
        "cos_factor": cos_factor,
        "effective_irr": effective_irr,
        "output_kw": output_kw,
        "az_err": az_err,
        "el_err": el_err,
        "total_err": total_err,
        "quality_pct": quality_pct,
        "quality_label": quality_label,
        "quality_color": quality_color
    }


def draw_parallel_sun_rays(stdscr, sun_cx, sun_cy, panel_cx, panel_cy, incident_angle=0.0, effective_irr=1000.0, anim_tick=0, color_pair=1):
    """
    Renders a strictly parallel directional sunlight ray field originating from the Sun
    and traveling toward the solar panel surface.
    - Rays are parallel (identical directional vector dx, dy across all rays).
    - Ray characters tilt correctly: '\\' when Sun is left, '/' when Sun is right, '|' when overhead.
    - Photons visibly animate traveling from SUN -> PANEL.
    - Energy interception illuminates panel when aligned.
    """
    if effective_irr <= 1.0:
        return  # Night or back-facing: no incoming rays

    h, w = stdscr.getmaxyx()

    # Direction vector from Sun center to Panel center
    dx = panel_cx - sun_cx
    dy = panel_cy - sun_cy

    if dy <= 0:
        return

    # Select slant character based on ray direction:
    # If Sun is left of panel (dx > 3), rays travel down-right: '\\'
    # If Sun is right of panel (dx < -3), rays travel down-left: '/'
    # Overhead (|dx| <= 3): '│'
    if dx > 3:
        ray_ch = '\\'
    elif dx < -3:
        ray_ch = '/'
    else:
        ray_ch = '│'

    # Generate 5 parallel rays across the beam width
    # Offsets are parallel displacements across panel aperture
    offsets = [-10, -5, 0, 5, 10]
    steps = max(4, int(math.hypot(dx, dy)))

    for off in offsets:
        ox = sun_cx + off
        oy = sun_cy
        # Ray extends from clearance outside the Sun disk to the panel surface
        for s in range(3, steps):
            t = s / steps
            rx = int(ox + dx * t)
            ry = int(oy + dy * t)

            if 0 <= ry < h and 0 <= rx < w:
                # Animated photon pulse traveling SUN -> PANEL
                pulse = (s - anim_tick) % 4
                if pulse == 0:
                    # Traveling photon highlight
                    if incident_angle < 10.0 and effective_irr > 100.0:
                        pt_color = curses.color_pair(2) | curses.A_BOLD  # Solar gold pulse
                    else:
                        pt_color = curses.color_pair(1) | curses.A_BOLD  # Bright cyan pulse
                else:
                    pt_color = curses.color_pair(1) | curses.A_DIM      # Subtle parallel beam

                try:
                    stdscr.addstr(ry, rx, ray_ch, pt_color)
                except curses.error:
                    pass

        # Subtle energy absorption sparkle at panel intercept if alignment is good
        if incident_angle <= 12.0 and effective_irr > 150.0:
            spark_x = int(ox + dx * 0.98)
            spark_y = int(oy + dy * 0.98)
            if 0 <= spark_y < h and 0 <= spark_x < w:
                spark_char = "*" if (anim_tick % 2 == 0) else "░"
                try:
                    stdscr.addstr(spark_y, spark_x, spark_char, curses.color_pair(2) | curses.A_BOLD)
                except curses.error:
                    pass


def run_solar_intro_cinematic(stdscr):
    """
    Multi-stage engineering sequence explaining:
    1. Terrain and multi-array solar farm initialization
    2. Sun acquisition and solar irradiance vector emission
    3. Gimbal dual-axis orientation and maximum light incidence lock
    Pressing any key immediately skips into the operational CLI control mode.
    """
    stdscr.clear()
    curses.curs_set(0)
    stdscr.nodelay(True)

    # Initialize Colors
    curses.init_pair(1, curses.COLOR_CYAN, -1)    # Sunlight Rays / Viewport Frame
    curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Sun Body / Active Power Lines
    curses.init_pair(3, curses.COLOR_WHITE, -1)   # Clouds / Mountain Silhouettes / Text
    curses.init_pair(4, curses.COLOR_GREEN, -1)   # Telemetry / Status OK
    curses.init_pair(5, curses.COLOR_MAGENTA, -1) # Gimbal Mechanical Hubs

    fps = 15
    frame_time = 1.0 / fps
    frame = 0

    scene = "STAGE_01_INIT"
    scene_start_time = time.time()
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

        # Scene Sequencing
        if scene == "STAGE_01_INIT":
            if elapsed > 0.4 and init_step == 0: init_step = 1
            if elapsed > 0.8 and init_step == 1: init_step = 2
            if elapsed > 1.2 and init_step == 2: init_step = 3
            if elapsed > 1.6 and init_step == 3: init_step = 4
            if elapsed > 2.0 and init_step == 4: init_step = 5
            if elapsed > 2.6:
                scene = "STAGE_02_ACQUISITION"
                scene_start_time = time.time()

        elif scene == "STAGE_02_ACQUISITION":
            if elapsed > 2.8:
                scene = "STAGE_03_ALIGNMENT"
                scene_start_time = time.time()

        elif scene == "STAGE_03_ALIGNMENT":
            if elapsed > 3.0:
                return

        # Viewport boundaries
        view_top = 1
        view_bottom = max(view_top + 14, h - 8)
        view_left = 2
        view_right = w - 3

        # Frame border
        try:
            stdscr.addstr(view_top, view_left, "┌" + "─" * (view_right - view_left - 1) + "┐", curses.color_pair(1))
            for r in range(view_top + 1, view_bottom):
                stdscr.addstr(r, view_left, "│", curses.color_pair(1))
                stdscr.addstr(r, view_right, "│", curses.color_pair(1))
            stdscr.addstr(view_bottom, view_left, "└" + "─" * (view_right - view_left - 1) + "┘", curses.color_pair(1))
        except curses.error:
            pass

        # 1. Distant Clouds & Mesas
        draw_sprite(stdscr, [CLOUD_SPRITE_1], view_top + 2, view_left + 8, color_pair=3, attrs=curses.A_DIM)
        draw_sprite(stdscr, [CLOUD_SPRITE_2], view_top + 2, view_right - 28, color_pair=3, attrs=curses.A_DIM)
        draw_sprite(stdscr, HORIZON_MESAS, view_top + 4, view_left + 4, color_pair=3, attrs=curses.A_DIM)

        # 2. Sun Position
        sun_x = float(w // 2 - 14)
        sun_y = 3.0
        draw_sprite(stdscr, SUN_ART_LARGE, int(sun_y), int(sun_x), color_pair=2, attrs=curses.A_BOLD)

        # 3. Main Central Array
        main_cx = w // 2 - 3
        main_cy = view_bottom - 13

        if scene == "STAGE_01_INIT":
            draw_sprite(stdscr, MAIN_ARRAY_TILT_LEFT, main_cy, main_cx - 15, color_pair=3)
        elif scene == "STAGE_02_ACQUISITION":
            draw_sprite(stdscr, MAIN_ARRAY_TILT_LEFT, main_cy, main_cx - 15, color_pair=3)
            draw_parallel_sun_rays(stdscr, int(sun_x + 11), int(sun_y + 3), main_cx, main_cy + 2,
                                   incident_angle=25.0, effective_irr=850.0, anim_tick=frame)
        else:
            draw_sprite(stdscr, MAIN_ARRAY_OPTIMAL, main_cy, main_cx - 15, color_pair=2, attrs=curses.A_BOLD)
            draw_parallel_sun_rays(stdscr, int(sun_x + 11), int(sun_y + 3), main_cx, main_cy + 2,
                                   incident_angle=0.0, effective_irr=1000.0, anim_tick=frame)

        # 4. Flanking Arrays
        draw_sprite(stdscr, ARRAY_LEFT_ART, view_bottom - 11, view_left + 6, color_pair=3)
        draw_sprite(stdscr, ARRAY_RIGHT_ART, view_bottom - 11, view_right - 28, color_pair=3)

        # 5. Distant hillside arrays
        draw_sprite(stdscr, ARRAY_DISTANT, view_top + 7, view_left + 24, color_pair=3, attrs=curses.A_DIM)
        draw_sprite(stdscr, ARRAY_DISTANT, view_top + 6, w // 2 - 16, color_pair=3, attrs=curses.A_DIM)

        # 6. Sand Dunes & Rocky Crags
        try:
            dune_line_1 = r"  .~~~~~~~~~~~~~~~~~~.        .~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.       .~~~~~~~~."
            dune_line_2 = r" ~~~~~~~~~~~~~~~~~~~~~~.____.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.____.~~~~~~~~~~~~"
            stdscr.addstr(view_bottom - 4, view_left + 2, dune_line_1[:view_right - view_left - 3], curses.color_pair(2) | curses.A_DIM)
            stdscr.addstr(view_bottom - 2, view_left + 2, dune_line_2[:view_right - view_left - 3], curses.color_pair(2) | curses.A_DIM)
        except curses.error:
            pass

        draw_sprite(stdscr, ROCK_FORMATION, view_bottom - 7, view_right - 18, color_pair=3, attrs=curses.A_DIM)
        draw_sprite(stdscr, PERSON_1, view_bottom - 5, view_left + 4, color_pair=3)
        draw_sprite(stdscr, PERSON_2, view_bottom - 5, w // 2 - 12, color_pair=3)

        # 7. Intro Diagnostics Overlay Box
        if scene == "STAGE_01_INIT":
            info_box = [
                "┌── SOLAR GIMBAL // SYSTEM INITIALIZATION ──────────┐",
                f"│   TERRAIN TOPOLOGY .................... {'ONLINE' if init_step >= 1 else '...':>7}   │",
                f"│   SOLAR ARRAY NETWORK (A-E) ........... {'ONLINE' if init_step >= 2 else '...':>7}   │",
                f"│   DUAL-AXIS GIMBAL SERVOS ............. {'LOCKED' if init_step >= 3 else '...':>7}   │",
                f"│   HIGH-VOLTAGE POWER BUS .............. {'ONLINE' if init_step >= 4 else '...':>7}   │",
                f"│   SOLAR INCIDENCE SENSORS ............. {'ACTIVE' if init_step >= 5 else '...':>7}   │",
                "└───────────────────────────────────────────────────┘"
            ]
            draw_sprite(stdscr, info_box, view_top + 3, view_left + 4, color_pair=4, attrs=curses.A_BOLD)

        try:
            stdscr.addstr(h - 1, 2, "[PRESS ANY KEY TO SKIP INTRO TO SOLAR GIMBAL CONTROL]", curses.color_pair(3) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        frame += 1
        elapsed_loop = time.time() - loop_start
        if elapsed_loop < frame_time:
            time.sleep(frame_time - elapsed_loop)


def launch_solar(stdscr, fpga_hw=None):
    """
    Master entry point for the SOLAR GIMBAL environment.
    Unified physical simulation:
    - Authoritative Sun State (azimuth, elevation, irradiance)
    - Dynamic Solar Vectors and Parallel Directional Ray Field
    - True 3D Spherical Incident Angle & Cosine Effective Irradiance
    - Gimbal Closed-Loop Tracking (Target vs Actual, Tracking Quality)
    - Dataset loading and real-time playback timeline (CSV)
    - Full CLI interaction with retro FPGA telemetry dashboard
    """
    # 1. Multi-Stage Intro Cinematic
    run_solar_intro_cinematic(stdscr)

    # 2. Interactive Operational Mode Setup
    stdscr.nodelay(True)
    curses.curs_set(1)

    if fpga_hw is None:
        try:
            from hardware.fpga_interface import get_fpga_interface
            fpga_hw = get_fpga_interface()
        except ImportError:
            pass

    curses.init_pair(1, curses.COLOR_CYAN, -1)    # Sunlight Rays / Borders / Primary HUD
    curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Sun Body / Active Power / Highlights
    curses.init_pair(3, curses.COLOR_WHITE, -1)   # Mountains / Clouds / Panels / Normal text
    curses.init_pair(4, curses.COLOR_GREEN, -1)   # Status OK / Excellent Tracking
    curses.init_pair(5, curses.COLOR_MAGENTA, -1) # Gimbal Mechanical Hubs
    curses.init_pair(6, curses.COLOR_RED, -1)     # Warnings / Degraded / Alerts

    # ONE AUTHORITATIVE SIMULATION STATE
    sun = SunState(azimuth=135.0, elevation=42.0, irradiance=1001.0)
    gimbal = GimbalState(azimuth=132.0, elevation=40.0)
    dataset_mgr = DatasetManager()

    # Preload default dataset if present
    default_csv = "sun_dataset.csv"
    if os.path.exists(default_csv):
        dataset_mgr.load_file(default_csv)

    # CLI Command History & Input Buffer
    cli_history = [
        ("SOLAR GIMBAL // DUAL-AXIS CONTROL CORE", 1),
        ("> track", 3),
        ("[SOLAR] TRACKING: ENABLED, GIMBAL ALIGNING.", 4),
        ("> status", 3),
        ("[SOLAR] SUN POSITION: AZ 135° | EL 42° | IRR 1001 W/m²", 4),
        ("[SOLAR] GIMBAL: AZ 132° | EL 40° | INCIDENT ANGLE: 04°", 4),
        ("[SOLAR] PARALLEL RAY FIELD ACTIVE. POWER: 858.8 kW", 4),
        ("[SOLAR] READY. TYPE 'help' FOR COMMANDS.", 1)
    ]
    cli_input_buffer = ""

    last_tick = time.time()
    anim_frame = 0

    while True:
        now = time.time()
        dt = max(0.001, min(0.1, now - last_tick))
        last_tick = now
        anim_frame += 1

        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Viewport boundaries
        view_top = 1
        view_bottom = max(view_top + 15, h - 10)
        view_left = 1
        view_right = w - 2

        # -------------------------------------------------------------
        # 1. PROCESS SIMULATION STATE UPDATES
        # -------------------------------------------------------------
        if sun.mode == "AUTO":
            sun.update_auto(now)
        elif sun.mode == "DATASET" and dataset_mgr.is_active and not dataset_mgr.is_paused:
            if now - dataset_mgr.last_step_time >= dataset_mgr.step_interval:
                dataset_mgr.last_step_time = now
                rec = dataset_mgr.advance()
                if rec:
                    sun.azimuth = rec["azimuth"]
                    sun.elevation = rec["elevation"]
                    sun.irradiance = rec["irradiance"]

        # Gimbal updates towards Sun position
        gimbal.update(dt, sun.azimuth, sun.elevation)

        # -------------------------------------------------------------
        # EDGE ZYNQ Z7010 REAL HARDWARE STEP
        # -------------------------------------------------------------
        if fpga_hw:
            hw_res = fpga_hw.step_solar_gimbal(sun.azimuth, sun.elevation, gimbal.azimuth, gimbal.elevation)
        else:
            hw_res = {"hardware_active": False, "fpga_actuator_az": None, "fpga_actuator_el": None}
            
        if hw_res["hardware_active"] and hw_res.get("fpga_actuator_az") is not None:
            # Live FPGA PL tracking controller output
            gimbal.azimuth = (gimbal.azimuth + hw_res["fpga_actuator_az"] * dt) % 360.0
            gimbal.elevation = max(0.0, min(90.0, gimbal.elevation + hw_res["fpga_actuator_el"] * dt))

        if fpga_hw:
            b_text, b_col = fpga_hw.get_status_badge()
            hw_col = 2 if b_col == "GREEN" else (6 if b_col == "RED" else 3)
            hw_badge = b_text
        else:
            hw_badge = "[× SOFTWARE VISUALIZATION MODE — FPGA NOT REQUIRED]"
            hw_col = 6

        # Physics derivation from the ONE authoritative state
        physics = calculate_solar_physics(sun, gimbal)

        # -------------------------------------------------------------
        # 2. COMPUTE VISUAL COORDINATES
        # -------------------------------------------------------------
        # Sky viewport bounds:
        # Sun sweeps horizontally from East (az ~60°) on left to West (az ~300°) on right.
        hud_box_width = 46
        sky_min_x = view_left + 4
        sky_max_x = max(sky_min_x + 20, view_right - hud_box_width - 26)

        # Map azimuth [45°, 315°] across sky_min_x .. sky_max_x
        norm_az = (sun.azimuth - 45.0) / 270.0
        norm_az = max(0.0, min(1.0, norm_az))
        sun_screen_x = int(sky_min_x + norm_az * (sky_max_x - sky_min_x))

        # Vertical elevation: 0° (horizon near mesas) to 90° (zenith near top)
        horizon_y = view_top + 7
        zenith_y = view_top + 1
        norm_el = max(0.0, min(90.0, sun.elevation)) / 90.0
        sun_screen_y = int(horizon_y - norm_el * (horizon_y - zenith_y))

        # Main Array Coordinates
        main_cx = w // 2 - 3
        main_cy = view_bottom - 13

        # -------------------------------------------------------------
        # 3. RENDER TOP VIEWPORT
        # -------------------------------------------------------------
        # Viewport Outer Border Box with Live Hardware Status Badge
        try:
            stdscr.addstr(view_top, view_left, "┌" + "─" * (view_right - view_left - 1) + "┐", curses.color_pair(1))
            # Display real hardware connection status badge on top right of viewport
            stdscr.addstr(view_top, max(view_left + 4, view_right - len(hw_badge) - 3), hw_badge, curses.color_pair(hw_col) | curses.A_BOLD)
            for r in range(view_top + 1, view_bottom):
                stdscr.addstr(r, view_left, "│", curses.color_pair(1))
                stdscr.addstr(r, view_right, "│", curses.color_pair(1))
            stdscr.addstr(view_bottom, view_left, "└" + "─" * (view_right - view_left - 1) + "┘", curses.color_pair(1))
        except curses.error:
            pass

        # Atmospheric Background (Mesas & Clouds)
        draw_sprite(stdscr, [CLOUD_SPRITE_1], view_top + 2, view_left + 6, color_pair=3, attrs=curses.A_DIM)
        draw_sprite(stdscr, [CLOUD_SPRITE_2], view_top + 2, sky_max_x - 10, color_pair=3, attrs=curses.A_DIM)
        draw_sprite(stdscr, HORIZON_MESAS, view_top + 4, view_left + 3, color_pair=3, attrs=curses.A_DIM)

        # Distant Background Solar Arrays on Hillslopes
        draw_sprite(stdscr, ARRAY_DISTANT, view_top + 8, view_left + 22, color_pair=3, attrs=curses.A_DIM)
        draw_sprite(stdscr, ARRAY_DISTANT, view_top + 7, w // 2 - 18, color_pair=3, attrs=curses.A_DIM)
        draw_sprite(stdscr, ARRAY_DISTANT, view_top + 8, view_right - 40, color_pair=3, attrs=curses.A_DIM)

        # Draw Sun if above horizon
        if sun.elevation > 0.0:
            draw_sprite(stdscr, SUN_ART_LARGE, sun_screen_y, sun_screen_x, color_pair=2, attrs=curses.A_BOLD)
            # Parallel Directional Sunlight Ray Field
            sun_center_x = sun_screen_x + 11
            sun_center_y = sun_screen_y + 3
            draw_parallel_sun_rays(stdscr, sun_center_x, sun_center_y, main_cx, main_cy + 2,
                                   incident_angle=physics["incident_angle"],
                                   effective_irr=physics["effective_irr"],
                                   anim_tick=anim_frame)

        # Determine Main Array Tilt Sprite based on gimbal azimuth
        rel_az = gimbal.azimuth - 180.0
        if rel_az < -14.0:
            main_sprite = MAIN_ARRAY_TILT_LEFT
        elif rel_az > 14.0:
            main_sprite = MAIN_ARRAY_TILT_RIGHT
        else:
            main_sprite = MAIN_ARRAY_OPTIMAL

        # Solar Panel Active Capture State Visualization:
        # Highlight panel when actively capturing energy with high alignment
        if physics["effective_irr"] > 100.0 and physics["incident_angle"] <= 12.0:
            array_color = 2  # Active Solar Gold
            array_attrs = curses.A_BOLD
        elif physics["effective_irr"] > 0.0:
            array_color = 3  # Normal white
            array_attrs = curses.A_NORMAL
        else:
            array_color = 3  # Dimmed night state
            array_attrs = curses.A_DIM

        draw_sprite(stdscr, main_sprite, main_cy, main_cx - 15, color_pair=array_color, attrs=array_attrs)

        # Flanking Arrays
        draw_sprite(stdscr, ARRAY_LEFT_ART, view_bottom - 11, view_left + 5, color_pair=3)
        draw_sprite(stdscr, ARRAY_RIGHT_ART, view_bottom - 11, view_right - 28, color_pair=3)

        # Snaking Electrical Cables
        cable_points_b = [
            (view_left + 16, view_bottom - 4),
            (view_left + 20, view_bottom - 3),
            (view_left + 26, view_bottom - 3),
            (view_left + 32, view_bottom - 4),
            (main_cx - 14,   view_bottom - 3)
        ]
        for cpx, cpy in cable_points_b:
            if 0 <= cpy < h and 0 <= cpx < w:
                try: stdscr.addstr(cpy, cpx, "═", curses.color_pair(2) | curses.A_BOLD)
                except curses.error: pass

        cable_points_c = [
            (view_right - 29, view_bottom - 4),
            (view_right - 35, view_bottom - 3),
            (main_cx + 14,    view_bottom - 3)
        ]
        for cpx, cpy in cable_points_c:
            if 0 <= cpy < h and 0 <= cpx < w:
                try: stdscr.addstr(cpy, cpx, "═", curses.color_pair(2) | curses.A_BOLD)
                except curses.error: pass

        # Sand Dunes
        try:
            dune_line_1 = r"  .~~~~~~~~~~~~~~~~~~.        .~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.       .~~~~~~~~."
            dune_line_2 = r" ~~~~~~~~~~~~~~~~~~~~~~.____.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.____.~~~~~~~~~~~~"
            stdscr.addstr(view_bottom - 4, view_left + 2, dune_line_1[:view_right - view_left - 3], curses.color_pair(2) | curses.A_DIM)
            stdscr.addstr(view_bottom - 2, view_left + 2, dune_line_2[:view_right - view_left - 3], curses.color_pair(2) | curses.A_DIM)
        except curses.error:
            pass

        # Rock Formation & Personnel
        draw_sprite(stdscr, ROCK_FORMATION, view_bottom - 7, view_right - 18, color_pair=3, attrs=curses.A_DIM)
        draw_sprite(stdscr, PERSON_1, view_bottom - 5, view_left + 3, color_pair=3)
        draw_sprite(stdscr, PERSON_2, view_bottom - 5, w // 2 - 13, color_pair=3)

        # -------------------------------------------------------------
        # 4. TOP-RIGHT TELEMETRY & GIMBAL HUD
        # -------------------------------------------------------------
        hud_x = view_right - hud_box_width - 1
        hud_y = view_top + 1

        # Tracking Quality Bar: 10 segments
        filled_bars = int(round(physics["quality_pct"] / 10.0))
        filled_bars = max(0, min(10, filled_bars))
        quality_bar_str = "█" * filled_bars + "░" * (10 - filled_bars)

        # Build HUD telemetry with authoritative FPGA hardware diagnostics
        hw_tag = "● CONNECTED (AXI 0x43C3)" if hw_res["hardware_active"] else "× NOT CONNECTED [SOFTWARE]"
        fpga_az_str = f"{hw_res['fpga_azimuth_error']:+05.1f}°" if hw_res.get('fpga_azimuth_error') is not None else "N/A"
        fpga_el_str = f"{hw_res['fpga_elevation_error']:+05.1f}°" if hw_res.get('fpga_elevation_error') is not None else "N/A"

        hud_lines = [
            "┌── TELEMETRY & GIMBAL STATE ───────────────┐",
            f"│ HARDWARE : {hw_tag:<30} │",
            f"│ FPGA ERR : AZ {fpga_az_str:<7} EL {fpga_el_str:<7} [AXI 0x14] │",
            f"│ SUN      : AZ {sun.azimuth:+06.1f}°  EL {sun.elevation:+05.1f}°        │",
            f"│ GIMBAL   : AZ {gimbal.azimuth:+06.1f}°  EL {gimbal.elevation:+05.1f}°        │",
            f"│ ERROR    : AZ {physics['az_err']:04.1f}°  EL {physics['el_err']:04.1f}° (TOT {physics['total_err']:04.1f}°) │",
            f"│ TRACKING : [{quality_bar_str}] {physics['quality_pct']:02.0f}% ({physics['quality_label']:<9})│",
            f"│ CAPTURE  : INC {sun.irradiance:04.0f} W/m² │ EFF {physics['effective_irr']:04.0f} W/m² │",
            f"│ POWER    : OUTPUT {physics['output_kw']:05.1f} kW (θ = {physics['incident_angle']:04.1f}°) │"
        ]

        if dataset_mgr.records:
            cur_step_idx = dataset_mgr.current_step + 1
            tot_steps = len(dataset_mgr.records)
            rec = dataset_mgr.get_current_record()
            time_str = rec["time"] if rec else "--:--"
            ds_progress = cur_step_idx / tot_steps
            ds_filled = max(0, min(8, int(round(ds_progress * 8))))
            ds_bar = "█" * ds_filled + "░" * (8 - ds_filled)
            status_tag = "ACTIVE" if (dataset_mgr.is_active and not dataset_mgr.is_paused) else ("PAUSED" if dataset_mgr.is_paused else "LOADED")

            hud_lines.extend([
                "├── DATASET PLAYBACK TIMELINE ──────────────┤",
                f"│ DATASET  : [{ds_bar}] {int(ds_progress*100):02d}% ({status_tag:<6}) │",
                f"│ TIMELINE : {time_str:<5} │ STEP {cur_step_idx:02d} / {tot_steps:02d}          │",
                "│ CONTROLS : [SPACE] PAUSE/RUN  [N] NEXT    │"
            ])

        hud_lines.append("└───────────────────────────────────────────┘")

        for idx, line in enumerate(hud_lines):
            hy = hud_y + idx
            if hy < view_bottom - 2 and hud_x > 0:
                try:
                    c_pair = 1
                    if "TRACKING" in line:
                        c_pair = physics["quality_color"]
                    elif "POWER" in line or "CAPTURE" in line:
                        c_pair = 2
                    elif "SUN" in line:
                        c_pair = 2
                    stdscr.addstr(hy, hud_x, line, curses.color_pair(c_pair) | curses.A_BOLD)
                except curses.error:
                    pass

        # -------------------------------------------------------------
        # 5. LOWER SECTION: OPERATIONAL CLI
        # -------------------------------------------------------------
        cli_start_y = view_bottom + 1
        max_history_lines = max(3, h - cli_start_y - 2)
        visible_history = cli_history[-max_history_lines:]

        for idx, (msg, col) in enumerate(visible_history):
            row_y = cli_start_y + idx
            if row_y < h - 1:
                try:
                    stdscr.addstr(row_y, 1, msg[:w - 3], curses.color_pair(col) | (curses.A_BOLD if col in (1, 4) else curses.A_NORMAL))
                except curses.error:
                    pass

        # Active CLI Command Prompt
        prompt_y = min(h - 1, cli_start_y + len(visible_history))
        prompt_str = f"> {cli_input_buffer}"
        try:
            stdscr.addstr(prompt_y, 1, prompt_str[:w - 3], curses.color_pair(3) | curses.A_BOLD)
            cursor_pos_x = min(w - 2, 1 + len(prompt_str))
            stdscr.move(prompt_y, cursor_pos_x)
        except curses.error:
            pass

        stdscr.refresh()

        # -------------------------------------------------------------
        # 6. PROCESS KEYBOARD & COMMAND INPUT
        # -------------------------------------------------------------
        key = stdscr.getch()
        if key == 27:  # ESC -> Exit to main menu
            break
        elif key in (10, 13):  # ENTER -> execute CLI command
            raw_cmd = cli_input_buffer.strip()
            cmd = raw_cmd.lower()
            cli_history.append((f"> {raw_cmd}", 3))
            cli_input_buffer = ""

            tokens = cmd.split()
            first = tokens[0] if tokens else ""

            if cmd == "track":
                gimbal.tracking_enabled = not gimbal.tracking_enabled
                if gimbal.tracking_enabled:
                    cli_history.append(("[SOLAR] TRACKING: ENABLED, GIMBAL ALIGNING.", 4))
                else:
                    cli_history.append(("[SOLAR] TRACKING: DISABLED (MANUAL HOLD).", 6))

            elif cmd == "status":
                cli_history.append((f"[SOLAR] SUN STATE    : AZ {sun.azimuth:.1f}° | EL {sun.elevation:.1f}° | IRR {sun.irradiance:.0f} W/m² (MODE: {sun.mode})", 4))
                cli_history.append((f"[SOLAR] GIMBAL STATE : TARGET AZ {gimbal.target_azimuth:.1f}°, EL {gimbal.target_elevation:.1f}° │ ACTUAL AZ {gimbal.azimuth:.1f}°, EL {gimbal.elevation:.1f}°", 4))
                cli_history.append((f"[SOLAR] TELEMETRY    : INCIDENT ANGLE: {physics['incident_angle']:.1f}° │ ERROR: {physics['total_err']:.1f}° │ QUALITY: {physics['quality_pct']:.0f}%", 4))
                cli_history.append((f"[SOLAR] POWER OUTPUT : EFFECTIVE IRR: {physics['effective_irr']:.1f} W/m² │ OUTPUT: {physics['output_kw']:.1f} kW", 4))

            elif cmd.startswith("tilt"):
                if len(tokens) > 1:
                    try:
                        gimbal.elevation = float(tokens[1])
                        gimbal.target_elevation = gimbal.elevation
                        gimbal.tracking_enabled = False
                        cli_history.append((f"[SOLAR] MAIN GIMBAL [A] MANUAL ELEVATION SET TO {gimbal.elevation:.1f}° (TRACKING DISABLED).", 4))
                    except ValueError:
                        cli_history.append(("[SOLAR] USAGE: tilt <deg> (e.g. tilt 45)", 6))
                else:
                    cli_history.append(("[SOLAR] USAGE: tilt <deg>", 6))

            elif cmd == "align":
                gimbal.tracking_enabled = True
                gimbal.azimuth = sun.azimuth
                gimbal.elevation = sun.elevation
                gimbal.target_azimuth = sun.azimuth
                gimbal.target_elevation = sun.elevation
                cli_history.append(("[SOLAR] RAPID ALIGNMENT COMPLETE: 90° NORMAL INCIDENCE LOCKED.", 4))

            # SUN COMMANDS
            elif first == "sun":
                if len(tokens) == 1:
                    cli_history.append(("[SOLAR] USAGE: sun <azimuth> <elevation> | sun auto | sun azimuth <deg> | sun elevation <deg>", 1))
                elif tokens[1] == "auto":
                    sun.mode = "AUTO"
                    sun.auto_start_time = time.time()
                    cli_history.append(("[SOLAR] AUTO SUN TRAJECTORY ACTIVE (SMOOTH DIURNAL ARC).", 4))
                elif tokens[1] == "manual":
                    sun.mode = "MANUAL"
                    cli_history.append(("[SOLAR] MANUAL SUN CONTROL ACTIVE.", 4))
                elif tokens[1] == "azimuth" and len(tokens) > 2:
                    try:
                        sun.azimuth = float(tokens[2]) % 360.0
                        sun.mode = "MANUAL"
                        cli_history.append(("[SOLAR] SUN POSITION UPDATED", 4))
                        cli_history.append((f"[SOLAR] AZIMUTH   : {sun.azimuth:03.0f}°", 4))
                        cli_history.append(("[SOLAR] GIMBAL TARGET UPDATED", 4))
                        cli_history.append(("[SOLAR] TRACKING ACTIVE", 4))
                    except ValueError:
                        cli_history.append(("[SOLAR] ERROR: Invalid azimuth angle.", 6))
                elif tokens[1] == "elevation" and len(tokens) > 2:
                    try:
                        sun.elevation = max(0.0, min(90.0, float(tokens[2])))
                        sun.mode = "MANUAL"
                        cli_history.append(("[SOLAR] SUN POSITION UPDATED", 4))
                        cli_history.append((f"[SOLAR] ELEVATION : {sun.elevation:02.0f}°", 4))
                        cli_history.append(("[SOLAR] GIMBAL TARGET UPDATED", 4))
                        cli_history.append(("[SOLAR] TRACKING ACTIVE", 4))
                    except ValueError:
                        cli_history.append(("[SOLAR] ERROR: Invalid elevation angle.", 6))
                elif tokens[1] == "irradiance" and len(tokens) > 2:
                    try:
                        sun.irradiance = max(0.0, float(tokens[2]))
                        cli_history.append((f"[SOLAR] BASE SOLAR IRRADIANCE SET TO {sun.irradiance:.0f} W/m².", 4))
                    except ValueError:
                        cli_history.append(("[SOLAR] ERROR: Invalid irradiance value.", 6))
                elif len(tokens) >= 3:
                    try:
                        sun.azimuth = float(tokens[1]) % 360.0
                        sun.elevation = max(0.0, min(90.0, float(tokens[2])))
                        sun.mode = "MANUAL"
                        if dataset_mgr.is_active:
                            dataset_mgr.is_paused = True
                        cli_history.append(("[SOLAR] SUN POSITION UPDATED", 4))
                        cli_history.append((f"[SOLAR] AZIMUTH   : {sun.azimuth:03.0f}°", 4))
                        cli_history.append((f"[SOLAR] ELEVATION : {sun.elevation:02.0f}°", 4))
                        cli_history.append(("[SOLAR] GIMBAL TARGET UPDATED", 4))
                        cli_history.append(("[SOLAR] TRACKING ACTIVE", 4))
                    except ValueError:
                        cli_history.append(("[SOLAR] USAGE: sun <azimuth> <elevation> (e.g. sun 180 45)", 6))
                else:
                    cli_history.append(("[SOLAR] USAGE: sun <azimuth> <elevation> | sun auto", 6))

            # DATASET COMMANDS
            elif first == "dataset":
                sub = tokens[1] if len(tokens) > 1 else ""
                if sub == "load":
                    fname = tokens[2] if len(tokens) > 2 else "sun_dataset.csv"
                    ok, msg = dataset_mgr.load_file(fname)
                    if ok:
                        cli_history.append(("[SOLAR] DATASET LOADED", 4))
                        cli_history.append((f"[SOLAR] FILE: {os.path.basename(dataset_mgr.filepath)} ({len(dataset_mgr.records)} TIMESTEPS)", 4))
                        cli_history.append(("[SOLAR] USE 'dataset start' OR [SPACE] TO BEGIN PLAYBACK.", 4))
                    else:
                        cli_history.append(("[SOLAR] DATASET ERROR", 6))
                        cli_history.append((f"[SOLAR] {msg}", 6))

                elif sub == "start":
                    if not dataset_mgr.records:
                        cli_history.append(("[SOLAR] NO DATASET LOADED. USE 'dataset load <file>'.", 6))
                    else:
                        dataset_mgr.is_active = True
                        dataset_mgr.is_paused = False
                        dataset_mgr.last_step_time = time.time()
                        sun.mode = "DATASET"
                        rec = dataset_mgr.get_current_record()
                        if rec:
                            sun.azimuth = rec["azimuth"]
                            sun.elevation = rec["elevation"]
                            sun.irradiance = rec["irradiance"]
                        cli_history.append(("[SOLAR] SUN TRAJECTORY ACTIVE", 4))
                        cli_history.append((f"[SOLAR] TIMESTEP: {dataset_mgr.current_step + 1} / {len(dataset_mgr.records)}", 4))

                elif sub == "pause":
                    if dataset_mgr.is_active:
                        dataset_mgr.is_paused = True
                        cli_history.append(("[SOLAR] DATASET PLAYBACK PAUSED", 2))
                    else:
                        cli_history.append(("[SOLAR] DATASET IS NOT RUNNING.", 6))

                elif sub == "stop":
                    dataset_mgr.is_active = False
                    dataset_mgr.is_paused = False
                    dataset_mgr.current_step = 0
                    sun.mode = "MANUAL"
                    cli_history.append(("[SOLAR] DATASET PLAYBACK STOPPED", 6))

                elif sub == "next":
                    if not dataset_mgr.records:
                        cli_history.append(("[SOLAR] NO DATASET LOADED.", 6))
                    else:
                        rec = dataset_mgr.advance()
                        if rec:
                            sun.azimuth = rec["azimuth"]
                            sun.elevation = rec["elevation"]
                            sun.irradiance = rec["irradiance"]
                            sun.mode = "DATASET"
                            cli_history.append((f"[SOLAR] TIMESTEP: {dataset_mgr.current_step + 1} / {len(dataset_mgr.records)} [TIME: {rec['time']}]", 4))
                            cli_history.append((f"[SOLAR] SUN: AZ {sun.azimuth:.1f}° | EL {sun.elevation:.1f}° | IRR {sun.irradiance:.0f} W/m²", 4))

                elif sub == "status":
                    if dataset_mgr.records:
                        rec = dataset_mgr.get_current_record()
                        t_str = rec["time"] if rec else "--:--"
                        st = "ACTIVE" if (dataset_mgr.is_active and not dataset_mgr.is_paused) else ("PAUSED" if dataset_mgr.is_paused else "STOPPED")
                        cli_history.append((f"[SOLAR] DATASET: {os.path.basename(dataset_mgr.filepath)} | STATUS: {st}", 4))
                        cli_history.append((f"[SOLAR] TIMESTEP: {dataset_mgr.current_step + 1} / {len(dataset_mgr.records)} (TIME: {t_str})", 4))
                    else:
                        cli_history.append(("[SOLAR] NO DATASET LOADED.", 6))

                elif sub == "clear":
                    dataset_mgr.records = []
                    dataset_mgr.is_active = False
                    dataset_mgr.is_paused = False
                    dataset_mgr.current_step = 0
                    sun.mode = "MANUAL"
                    cli_history.append(("[SOLAR] DATASET CLEARED. REVERTED TO MANUAL MODE.", 4))
                else:
                    cli_history.append(("[SOLAR] USAGE: dataset load|start|pause|stop|next|status|clear", 1))

            elif cmd == "clear":
                cli_history = [("SOLAR GIMBAL // CONTROL CORE", 1)]
            elif cmd in ("exit", "quit"):
                break
            elif cmd == "help":
                cli_history.append(("[SOLAR] COMMANDS:", 1))
                cli_history.append(("  sun <az> <el>      : Set Sun azimuth & elevation (e.g. sun 180 45)", 3))
                cli_history.append(("  sun auto           : Enable automatic diurnal solar arc", 3))
                cli_history.append(("  dataset load <csv> : Load solar CSV dataset", 3))
                cli_history.append(("  dataset start      : Start dataset trajectory playback", 3))
                cli_history.append(("  dataset pause|next : Pause or advance 1 timestep", 3))
                cli_history.append(("  track              : Toggle gimbal tracking on/off", 3))
                cli_history.append(("  align              : Rapid gimbal lock to Sun vector", 3))
                cli_history.append(("  tilt <deg>         : Set manual panel elevation angle", 3))
                cli_history.append(("  status             : Display complete physics & gimbal state", 3))
                cli_history.append(("  clear | exit       : Clear history or exit to main menu", 3))
                cli_history.append(("HOTKEYS (when prompt is empty):", 1))
                cli_history.append(("  [SPACE] Pause/resume dataset  │  [N] Next step  │  [R] Restart", 3))
                cli_history.append(("  [ARROWS] Adjust Sun position  │  [ESC] Exit", 3))
            elif cmd != "":
                cli_history.append((f"[SOLAR] UNKNOWN COMMAND: '{cmd}'. TYPE 'help' FOR LIST.", 6))

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if len(cli_input_buffer) > 0:
                cli_input_buffer = cli_input_buffer[:-1]

        # Hotkeys when prompt buffer is empty
        elif key == ord(' ') and len(cli_input_buffer) == 0:
            if dataset_mgr.records:
                if dataset_mgr.is_active:
                    dataset_mgr.is_paused = not dataset_mgr.is_paused
                    cli_history.append((f"[SOLAR] DATASET PLAYBACK {'PAUSED' if dataset_mgr.is_paused else 'RESUMED'}", 2 if dataset_mgr.is_paused else 4))
                else:
                    dataset_mgr.is_active = True
                    dataset_mgr.is_paused = False
                    dataset_mgr.last_step_time = time.time()
                    sun.mode = "DATASET"
                    cli_history.append(("[SOLAR] SUN TRAJECTORY ACTIVE", 4))

        elif key in (ord('n'), ord('N')) and len(cli_input_buffer) == 0:
            if dataset_mgr.records:
                rec = dataset_mgr.advance()
                if rec:
                    sun.azimuth = rec["azimuth"]
                    sun.elevation = rec["elevation"]
                    sun.irradiance = rec["irradiance"]
                    sun.mode = "DATASET"
                    cli_history.append((f"[SOLAR] TIMESTEP: {dataset_mgr.current_step + 1} / {len(dataset_mgr.records)} [TIME: {rec['time']}]", 4))

        elif key in (ord('r'), ord('R')) and len(cli_input_buffer) == 0:
            if dataset_mgr.records:
                rec = dataset_mgr.restart()
                if rec:
                    sun.azimuth = rec["azimuth"]
                    sun.elevation = rec["elevation"]
                    sun.irradiance = rec["irradiance"]
                    sun.mode = "DATASET"
                    cli_history.append(("[SOLAR] DATASET RESTARTED AT TIMESTEP 1 / " + str(len(dataset_mgr.records)), 4))

        elif key == curses.KEY_LEFT:
            sun.azimuth = (sun.azimuth - 2.5) % 360.0
            sun.mode = "MANUAL"
        elif key == curses.KEY_RIGHT:
            sun.azimuth = (sun.azimuth + 2.5) % 360.0
            sun.mode = "MANUAL"
        elif key == curses.KEY_UP:
            sun.elevation = min(90.0, sun.elevation + 2.0)
            sun.mode = "MANUAL"
        elif key == curses.KEY_DOWN:
            sun.elevation = max(0.0, sun.elevation - 2.0)
            sun.mode = "MANUAL"

        elif 32 <= key <= 126:
            if len(cli_input_buffer) < 45:
                cli_input_buffer += chr(key)

        time.sleep(0.035)  # ~28 FPS smooth simulation & animation
