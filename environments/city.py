import curses
import time
import random
import math

# --- ASCII ART ASSETS & CITY TILES ---

# Building Block Silhouettes (Varied Heights, Architectural Typologies & Urban Footprints)
BUILDING_SKYSCRAPER = [
    r" ┌──▲──┐ ",
    r" │[::] │ ",
    r" │[::] │ ",
    r" │[::] │ ",
    r" │[::] │ ",
    r" └──┬──┘ "
]

BUILDING_OFFICE_MED = [
    r" ┌──────┐ ",
    r" │ [■■] │ ",
    r" │ [■■] │ ",
    r" └──────┘ "
]

BUILDING_COMMERCIAL = [
    r" ┌─────────┐ ",
    r" │ MALL-04 │ ",
    r" │ [■] [■] │ ",
    r" └─────────┘ "
]

BUILDING_RESIDENTIAL = [
    r"  /\___/\  ",
    r" ┌─┐ ┌─┐ │ ",
    r" │▓│ │▓│ │ ",
    r" └─┴─┴─┴─┘ "
]

BUILDING_TECH_HUB = [
    r" ┌──(TWR)──┐ ",
    r" │ DATA-01 │ ",
    r" │ ▓▓   ▓▓ │ ",
    r" └─────────┘ "
]

BUILDING_CIVIC_CENTER = [
    r"  .────────.  ",
    r" /  METRO   \ ",
    r" | ════════ | ",
    r" └──┴────┴──┘ "
]

# Top-Down Recognizable Car Silhouettes (Moving East, West, South, North)
CAR_EAST  = r"[►►]"   # Travelling East (Right)
CAR_WEST  = r"[◄◄]"   # Travelling West (Left)
CAR_SOUTH = r"[▼▼]"   # Travelling South (Down)
CAR_NORTH = r"[▲▲]"   # Travelling North (Up)

# Side View Car for Cinematic Intro
CAR_SIDE = [
    r"      ______      ",
    r" ____/|_||_\`.__  ",
    r"/ _          _  \ ",
    r"'-(_)--------(_)-'"
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

def run_city_intro_cinematic(stdscr):
    """
    Cinematic sequence showing car approaching intersection, detection by sensors,
    and expanding camera settling into the full multi-intersection Smart City network.
    Pressing any key immediately skips to the permanent city control landing screen.
    """
    stdscr.clear()
    curses.curs_set(0)
    stdscr.nodelay(True)

    # Colors
    curses.init_pair(1, curses.COLOR_WHITE, -1)   # Neutral Road / Markings
    curses.init_pair(2, curses.COLOR_CYAN, -1)    # Connected Vehicle
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Warnings / Signals / Lanes
    curses.init_pair(4, curses.COLOR_RED, -1)     # Red Signals / Heavy Traffic
    curses.init_pair(5, curses.COLOR_GREEN, -1)   # Green Signals / Open Flow
    curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Urban Architecture / Buildings

    fps = 15
    frame_time = 1.0 / fps
    frame = 0

    h, w = stdscr.getmaxyx()
    road_y = max(6, h // 2)

    scene = "APPROACH"
    scene_start_time = time.time()
    car_x = -20.0
    road_offset = 0.0

    while True:
        loop_start = time.time()
        elapsed = time.time() - scene_start_time
        h, w = stdscr.getmaxyx()
        road_y = max(6, h // 2)

        # Instant skip support
        try:
            key = stdscr.getch()
            if key != -1:
                return
        except curses.error:
            pass

        stdscr.erase()

        if scene == "APPROACH":
            car_x += 2.2
            road_offset += 0.8
            if car_x >= w // 2 - 12:
                scene = "DETECTION"
                scene_start_time = time.time()
                car_x = float(w // 2 - 12)

        elif scene == "DETECTION":
            if elapsed > 1.8:
                scene = "GREEN_LIGHT"
                scene_start_time = time.time()

        elif scene == "GREEN_LIGHT":
            car_x += 3.0
            if car_x > w + 5:
                scene = "TRANSITION"
                scene_start_time = time.time()

        elif scene == "TRANSITION":
            if elapsed > 0.8:
                return

        # 1. Sky & Distant Skyline
        sky_line = r"  | |     _/\_          _/\_   |~|      ___/\___         _/\_   "
        try:
            stdscr.addstr(road_y - 6, 2, sky_line[:w - 4], curses.color_pair(6) | curses.A_DIM)
        except curses.error:
            pass

        # 2. Road surface
        try:
            stdscr.addstr(road_y, 0, "═" * (w - 1), curses.color_pair(1))
            dash = ("- - -   " * (w // 8 + 2))
            shift = int(road_offset) % 8
            stdscr.addstr(road_y + 1, 0, dash[shift:shift + w - 1], curses.color_pair(3))
            stdscr.addstr(road_y + 2, 0, "═" * (w - 1), curses.color_pair(1))
        except curses.error:
            pass

        # 3. Traffic Signal Pole
        sig_x = w // 2 + 10
        if 0 <= sig_x < w - 4:
            sig_color = 5 if scene == "GREEN_LIGHT" else 4
            sig_state = "GREEN" if scene == "GREEN_LIGHT" else "RED"
            try:
                stdscr.addstr(road_y - 5, sig_x, "┌──┐", curses.color_pair(1))
                stdscr.addstr(road_y - 4, sig_x, f"│{'●' if sig_state=='RED' else '○'} │", curses.color_pair(4) | curses.A_BOLD)
                stdscr.addstr(road_y - 3, sig_x, f"│{'●' if sig_state=='GREEN' else '○'} │", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr(road_y - 2, sig_x, "└──┘", curses.color_pair(1))
                stdscr.addstr(road_y - 1, sig_x + 1, "║", curses.color_pair(1))
            except curses.error:
                pass

        # 4. Approaching Car
        draw_sprite(stdscr, CAR_SIDE, road_y - 3, int(car_x), color_pair=2, attrs=curses.A_BOLD)

        # 5. Sensor Detection Banner
        if scene == "DETECTION":
            banner = [
                "┌── SMART CITY // SENSOR INTERLOCK ACTIVE ──────────────────┐",
                "│   OPTICAL RADAR: VEHICLE DETECTED AT STOP BAR              │",
                "│   V2X TELEMETRY: ALLOCATING GREEN PHASE WINDOW             │",
                "│   FPGA ARBITRATION: SWITCHING NORTH-SOUTH TRAFFIC PHASE    │",
                "└───────────────────────────────────────────────────────────┘"
            ]
            draw_sprite(stdscr, banner, 2, max(2, w // 2 - 32), color_pair=2, attrs=curses.A_BOLD)

        try:
            stdscr.addstr(h - 1, 2, "[PRESS ANY KEY TO SKIP INTRO TO SMART CITY CONTROL]", curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        frame += 1
        elapsed_loop = time.time() - loop_start
        if elapsed_loop < frame_time:
            time.sleep(frame_time - elapsed_loop)


# --- DYNAMIC TRAFFIC & NETWORK SIMULATION ENGINE ---

class TrafficSimulationEngine:
    """
    Manages non-symmetric road network, dynamic density levels, car-following physics,
    traffic signal queuing, and emergent congestion metrics.
    """
    DENSITY_LEVELS = ["LOW", "NORMAL", "HIGH", "HEAVY", "GRIDLOCK"]
    DENSITY_COUNTS = {
        "LOW": 10,
        "NORMAL": 22,
        "HIGH": 42,
        "HEAVY": 65,
        "GRIDLOCK": 85
    }

    def __init__(self):
        self.density_idx = 1  # Default to "NORMAL" (22 vehicles)
        self.vehicles = []
        self.next_id = 1
        self.avg_speed_kmh = 32
        self.congestion_pct = 22
        self.flow_status = "NORMAL FLOW"

    def get_density_name(self):
        return self.DENSITY_LEVELS[self.density_idx]

    def get_target_count(self):
        return self.DENSITY_COUNTS[self.get_density_name()]

    def increase_density(self):
        if self.density_idx < len(self.DENSITY_LEVELS) - 1:
            self.density_idx += 1
            return True
        return False

    def decrease_density(self):
        if self.density_idx > 0:
            self.density_idx -= 1
            return True
        return False

    def spawn_vehicle(self, route_name, routes_config):
        """Creates a new vehicle with valid position along an available road segment."""
        cfg = routes_config[route_name]
        is_horiz = cfg["axis"] == 'H'

        LANE_OFFSET = 2

        # Pick direction allowed on this route
        v_dir = random.choice(cfg["dirs"])
        base_speed = random.uniform(8.0, 13.0)

        if is_horiz:
            v_x = cfg["x_min"] if v_dir == 'E' else cfg["x_max"]
            v_y = cfg["y"] - (LANE_OFFSET // 2) if v_dir == 'W' else cfg["y"] + (LANE_OFFSET // 2)
        else:
            v_x = cfg["x"] - LANE_OFFSET - 2 if v_dir == 'S' else cfg["x"] + LANE_OFFSET - 1
            v_y = cfg["y_min"] if v_dir == 'S' else cfg["y_max"]

        v = {
            "id": self.next_id,
            "route": route_name,
            "axis": cfg["axis"],
            "dir": v_dir,
            "x": float(v_x),
            "y": float(v_y),
            "speed": base_speed,
            "max_speed": base_speed,
            "stopped": False,
            "color": random.choice([1, 2, 3, 5])  # White, Cyan, Yellow, Green
        }
        self.next_id += 1
        self.vehicles.append(v)

    def update(self, dt, routes_config, int_coords, intersections):
        """
        Executes microscopic car-following model:
        - Vehicles maintain minimum visual spacing (no overlap).
        - Stop and form queues at red traffic signals.
        - Accelerate when light turns green or space opens.
        - Calculates live network congestion metrics.
        """
        target_count = self.get_target_count()

        # Adjust vehicle count towards target density
        available_routes = list(routes_config.keys())
        while len(self.vehicles) < target_count:
            r_name = random.choice(available_routes)
            self.spawn_vehicle(r_name, routes_config)

        # Sort vehicles along each route to process car-following order
        routes_vehicles = {}
        for v in self.vehicles:
            routes_vehicles.setdefault((v["route"], v["dir"]), []).append(v)

        for (r_name, v_dir), group in routes_vehicles.items():
            cfg = routes_config[r_name]
            is_horiz = cfg["axis"] == 'H'

            # Sort by position in direction of travel (front vehicle first)
            if v_dir == 'E':
                group.sort(key=lambda item: item["x"], reverse=True)
            elif v_dir == 'W':
                group.sort(key=lambda item: item["x"])
            elif v_dir == 'S':
                group.sort(key=lambda item: item["y"], reverse=True)
            else:  # 'N'
                group.sort(key=lambda item: item["y"])

            # Process movement for each vehicle in the lane
            for idx, v in enumerate(group):
                lead_car = group[idx - 1] if idx > 0 else None

                # 1. Check Traffic Signal Stop Condition
                # Check intersections situated on this road segment
                must_stop_for_signal = False
                dist_to_signal = 999.0

                for int_id in cfg.get("intersections", []):
                    if int_id not in int_coords:
                        continue
                    ix, iy = int_coords[int_id]
                    int_data = intersections[int_id]
                    sig_state = int_data["signal"]

                    # Check if signal is RED for this movement axis
                    is_red = False
                    if is_horiz:
                        is_red = ("EW_GREEN" not in sig_state)
                        if v_dir == 'E' and 0 < (ix - v["x"]) <= 8:
                            dist_to_signal = ix - v["x"]
                            must_stop_for_signal = is_red
                        elif v_dir == 'W' and 0 < (v["x"] - ix) <= 8:
                            dist_to_signal = v["x"] - ix
                            must_stop_for_signal = is_red
                    else:
                        is_red = ("NS_GREEN" not in sig_state)
                        if v_dir == 'S' and 0 < (iy - v["y"]) <= 6:
                            dist_to_signal = iy - v["y"]
                            must_stop_for_signal = is_red
                        elif v_dir == 'N' and 0 < (v["y"] - iy) <= 6:
                            dist_to_signal = v["y"] - iy
                            must_stop_for_signal = is_red

                # 2. Compute Desired Speed based on Lead Car & Red Signals
                desired_speed = v["max_speed"]

                # If signal is red directly ahead and we are first in queue
                if must_stop_for_signal:
                    if dist_to_signal <= 4.0:
                        desired_speed = 0.0
                    else:
                        desired_speed = min(desired_speed, (dist_to_signal - 3.5) * 2.5)

                # Car-following distance constraint (Prevent overlap!)
                if lead_car:
                    if is_horiz:
                        gap = abs(lead_car["x"] - v["x"])
                        min_gap = 5.0  # 4-col car width + 1-col gap
                    else:
                        gap = abs(lead_car["y"] - v["y"])
                        min_gap = 2.0  # 1-row car height + 1-row gap

                    if gap < min_gap + 3.0:
                        desired_speed = min(desired_speed, lead_car["speed"])
                    if gap <= min_gap:
                        desired_speed = 0.0

                # 3. Update Vehicle Velocity & Position
                # Smooth acceleration / deceleration
                if desired_speed < v["speed"]:
                    v["speed"] = max(desired_speed, v["speed"] - 22.0 * dt)
                else:
                    v["speed"] = min(desired_speed, v["speed"] + 12.0 * dt)

                v["stopped"] = (v["speed"] < 0.8)

                if is_horiz:
                    LANE_OFFSET = 2
                    v["y"] = cfg["y"] - (LANE_OFFSET // 2) if v_dir == 'W' else cfg["y"] + (LANE_OFFSET // 2)
                    v["x"] += (v["speed"] if v_dir == 'E' else -v["speed"]) * dt
                    # Boundary wraps
                    if v_dir == 'E' and v["x"] > cfg["x_max"]:
                        if len(self.vehicles) > target_count:
                            self.vehicles.remove(v)
                        else:
                            v["x"] = cfg["x_min"]
                    elif v_dir == 'W' and v["x"] < cfg["x_min"]:
                        if len(self.vehicles) > target_count:
                            self.vehicles.remove(v)
                        else:
                            v["x"] = cfg["x_max"]
                else:
                    LANE_OFFSET = 2
                    v["x"] = cfg["x"] - LANE_OFFSET - 2 if v_dir == 'S' else cfg["x"] + LANE_OFFSET - 1
                    v["y"] += (v["speed"] if v_dir == 'S' else -v["speed"]) * dt
                    if v_dir == 'S' and v["y"] > cfg["y_max"]:
                        if len(self.vehicles) > target_count:
                            self.vehicles.remove(v)
                        else:
                            v["y"] = cfg["y_min"]
                    elif v_dir == 'N' and v["y"] < cfg["y_min"]:
                        if len(self.vehicles) > target_count:
                            self.vehicles.remove(v)
                        else:
                            v["y"] = cfg["y_max"]

        # 4. Update Global Network Telemetry
        active_cnt = len(self.vehicles)
        if active_cnt > 0:
            stopped_cnt = sum(1 for v in self.vehicles if v["stopped"])
            self.congestion_pct = int((stopped_cnt / active_cnt) * 100)
            avg_spd = sum(v["speed"] for v in self.vehicles) / active_cnt
            self.avg_speed_kmh = int(avg_spd * 3.2)
        else:
            self.congestion_pct = 0
            self.avg_speed_kmh = 45

        if self.congestion_pct < 20:
            self.flow_status = "NORMAL FLOW"
        elif self.congestion_pct < 45:
            self.flow_status = "MODERATE DENSITY"
        elif self.congestion_pct < 70:
            self.flow_status = "CONGESTION DETECTED"
        else:
            self.flow_status = "GRIDLOCK ALERT // SIGNAL OVERRIDE"


def launch_city(stdscr, fpga_hw=None):
    """
    Master entry point for the SMART CITY // DISTRIBUTED INTELLIGENT TRAFFIC GRID.
    - Non-symmetric, realistic urban road network
    - Dynamic user-controlled traffic density (LOW -> NORMAL -> HIGH -> HEAVY -> GRIDLOCK)
    - True car-following physics with visible queuing at red signals
    - Congestion propagation and emergent flow dynamics
    - Comprehensive FPGA traffic controller telemetry & CLI
    """
    # 1. Run Cinematic Introduction Sequence
    run_city_intro_cinematic(stdscr)

    # 2. Interactive Operational Mode Setup
    stdscr.nodelay(True)
    curses.curs_set(1)

    if fpga_hw is None:
        try:
            from hardware.fpga_interface import get_fpga_interface
            fpga_hw = get_fpga_interface()
        except ImportError:
            pass

    curses.init_pair(1, curses.COLOR_WHITE, -1)   # Neutral / Road Markings / Coordinates
    curses.init_pair(2, curses.COLOR_CYAN, -1)    # Selected Intersection / Connected Cars
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Warnings / Lane Markings / Yellow Signal
    curses.init_pair(4, curses.COLOR_RED, -1)     # Red Signals / Congested Queues
    curses.init_pair(5, curses.COLOR_GREEN, -1)   # Green Signals / Open Flow
    curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Urban Architecture / Buildings

    h, w = stdscr.getmaxyx()

    # 5 Connected Intersections with Unique Geometries (Non-Symmetric Network)
    intersections = {
        "01": {"name": "NORTH-WEST ARTERIAL",  "type": "4-WAY",            "signal": "NS_GREEN", "queue_ns": 2, "queue_ew": 5, "flow": "NORMAL"},
        "02": {"name": "TECH CAMPUS GATEWAY",   "type": "3-WAY T-JUNCTION", "signal": "EW_GREEN", "queue_ns": 4, "queue_ew": 1, "flow": "NORMAL"},
        "03": {"name": "CENTRAL PLAZA HUB",     "type": "OFFSET 4-WAY",     "signal": "NS_GREEN", "queue_ns": 6, "queue_ew": 7, "flow": "CONGESTED"},
        "04": {"name": "HARBOR COMMERCE BRANCH", "type": "3-WAY T-JUNCTION", "signal": "EW_GREEN", "queue_ns": 1, "queue_ew": 3, "flow": "NORMAL"},
        "05": {"name": "BENTHIC HIGHWAY FORK",  "type": "3-WAY TERMINATING","signal": "NS_GREEN", "queue_ns": 3, "queue_ew": 2, "flow": "NORMAL"}
    }

    selected_int_id = "03"  # Central Plaza selected by default

    # Traffic Engine
    traffic_sim = TrafficSimulationEngine()

    # CLI History Buffer
    cli_history = [
        ("SMART CITY // DISTRIBUTED TRAFFIC CONTROLLER", 1),
        ("CITY NETWORK : ONLINE [5 IRREGULAR INTERSECTIONS CONNECTED]", 5),
        ("INTERSECTION 03 SELECTED: CENTRAL PLAZA HUB (OFFSET 4-WAY)", 2),
        ("> status", 3),
        ("[FPGA CORE] SENSORS ONLINE. V2X ADAPTIVE BALANCING ACTIVE.", 5),
        ("[CONTROLS] USE [+ / -] TO ADJUST VEHICLE DENSITY (EMERGE QUEUES).", 3)
    ]
    cli_input_buffer = ""

    last_tick = time.time()
    last_signal_auto_tick = time.time()

    while True:
        now = time.time()
        dt = min(0.08, max(0.001, now - last_tick))
        last_tick = now

        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Viewport boundaries (Upper 68-72% visual Smart City, Lower section CLI panel)
        city_top = 1
        city_bottom = max(city_top + 16, int(h * 0.70))
        city_left = 1
        city_right = w - 2
        city_w = city_right - city_left
        city_h = city_bottom - city_top

        # -------------------------------------------------------------
        # 1. DEFINE NON-SYMMETRIC ROAD NETWORK GEOMETRY
        # -------------------------------------------------------------
        # Non-uniform coordinates for realistic, varied city layout
        ave_top_y = city_top + int(city_h * 0.28)
        ave_mid_y = city_top + int(city_h * 0.54)
        ave_bot_y = city_top + int(city_h * 0.80)

        boul_left_x  = city_left + int(city_w * 0.22)
        boul_mid_x   = city_left + int(city_w * 0.50)
        boul_right_x = city_left + int(city_w * 0.78)

        # 5 Intersections with Non-Symmetric Physical Coordinates
        int_coords = {
            "01": (boul_left_x, ave_top_y),                   # 4-WAY
            "02": (boul_right_x, ave_top_y),                  # 3-WAY (North closed)
            "03": (boul_mid_x, ave_mid_y),                    # OFFSET 4-WAY (Staggered Spine)
            "04": (boul_left_x, ave_bot_y),                   # 3-WAY (West closed)
            "05": (boul_right_x, ave_bot_y)                   # 3-WAY (East closed)
        }

        # Definition of Active Connected Road Segments for Vehicles
        # (Every road segment has valid entry, exit, lanes, and physical continuity)
        routes_config = {
            "H_NORTH": {
                "axis": 'H', "y": ave_top_y,
                "x_min": city_left + 2, "x_max": city_right - 4,
                "dirs": ['E', 'W'], "intersections": ["01", "02"]
            },
            "H_MID": {
                "axis": 'H', "y": ave_mid_y,
                "x_min": boul_left_x + 4, "x_max": city_right - 4,  # Starts from West Boulevard
                "dirs": ['E', 'W'], "intersections": ["03"]
            },
            "H_SOUTH": {
                "axis": 'H', "y": ave_bot_y,
                "x_min": boul_left_x - 2, "x_max": boul_right_x + 2,
                "dirs": ['E', 'W'], "intersections": ["04", "05"]
            },
            "V_WEST": {
                "axis": 'V', "x": boul_left_x,
                "y_min": city_top + 2, "y_max": ave_bot_y + 1,
                "dirs": ['S', 'N'], "intersections": ["01", "04"]
            },
            "V_MID_UPPER": {
                "axis": 'V', "x": boul_mid_x - 1,  # Staggered North Approach to Hub
                "y_min": city_top + 2, "y_max": ave_mid_y,
                "dirs": ['S', 'N'], "intersections": ["03"]
            },
            "V_MID_LOWER": {
                "axis": 'V', "x": boul_mid_x + 1,  # Staggered South Departure from Hub
                "y_min": ave_mid_y, "y_max": ave_bot_y + 1,
                "dirs": ['S', 'N'], "intersections": ["03"]
            },
            "V_EAST": {
                "axis": 'V', "x": boul_right_x,
                "y_min": ave_top_y, "y_max": city_bottom - 2,  # Starts from Int 02 T-Junction downwards
                "dirs": ['S', 'N'], "intersections": ["02", "05"]
            }
        }

        # Auto-cycle non-selected intersection signals slowly
        if now - last_signal_auto_tick > 6.5:
            last_signal_auto_tick = now
            for i_id, i_data in intersections.items():
                if i_id != selected_int_id:
                    i_data["signal"] = "EW_GREEN" if i_data["signal"] == "NS_GREEN" else "NS_GREEN"

        # -------------------------------------------------------------
        # EDGE ZYNQ Z7010 REAL HARDWARE STEP
        # -------------------------------------------------------------
        # Update Microscopic Traffic Simulation
        traffic_sim.update(dt, routes_config, int_coords, intersections)

        # Transact with FPGA traffic arbitration core
        sel_coords_tmp = int_coords.get(selected_int_id, (0, 0))
        q_ns_tmp = sum(1 for v in traffic_sim.vehicles if v["axis"] == 'V' and v["stopped"] and abs(v["x"] - sel_coords_tmp[0]) < 6)
        q_ew_tmp = sum(1 for v in traffic_sim.vehicles if v["axis"] == 'H' and v["stopped"] and abs(v["y"] - sel_coords_tmp[1]) < 3)
        if fpga_hw:
            hw_res = fpga_hw.step_traffic_grid(selected_int_id, q_ns_tmp, q_ew_tmp)
        else:
            hw_res = {"hardware_active": False, "fpga_signal_phase": None}
            
        if hw_res["hardware_active"] and hw_res.get("fpga_signal_phase") is not None:
            # Authoritative FPGA PL drives signal phase allocation
            intersections[selected_int_id]["signal"] = hw_res["fpga_signal_phase"]

        if fpga_hw:
            b_text, b_col = fpga_hw.get_status_badge()
            hw_col = 2 if b_col == "GREEN" else (6 if b_col == "RED" else 3)
            hw_badge = b_text
        else:
            hw_badge = "[× SOFTWARE VISUALIZATION MODE — FPGA NOT REQUIRED]"
            hw_col = 6

        # -------------------------------------------------------------
        # 2. RENDER CITY SKYLINE & URBAN ARCHITECTURE
        # -------------------------------------------------------------
        # City boundary frame
        try:
            stdscr.addstr(city_top, city_left, "┌" + "─" * (city_w - 1) + "┐", curses.color_pair(1))
            for r in range(city_top + 1, city_bottom):
                stdscr.addstr(r, city_left, "│", curses.color_pair(1))
                stdscr.addstr(r, city_right, "│", curses.color_pair(1))
            stdscr.addstr(city_bottom, city_left, "├" + "─" * (city_w - 1) + "┤", curses.color_pair(1))
        except curses.error:
            pass

        # City Title Badge in Top Border
        city_title = " SMART CITY // DISTRIBUTED INTELLIGENT TRAFFIC GRID "
        try:
            stdscr.addstr(city_top, max(2, w // 2 - len(city_title) // 2), city_title, curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

        # Irregular City Blocks & Varied Architecture Placement
        # Block 1 (North-West): Tall Civic & Office Cluster
        draw_sprite(stdscr, BUILDING_SKYSCRAPER,  city_top + 2, city_left + 4, color_pair=6, attrs=curses.A_DIM)
        draw_sprite(stdscr, BUILDING_OFFICE_MED,  city_top + 2, boul_left_x - 15, color_pair=6, attrs=curses.A_DIM)

        # Block 2 (North-Central): Commercial Mall & Data Center
        draw_sprite(stdscr, BUILDING_COMMERCIAL,  city_top + 2, boul_left_x + 8, color_pair=6, attrs=curses.A_DIM)
        draw_sprite(stdscr, BUILDING_TECH_HUB,    city_top + 2, boul_mid_x - 17, color_pair=6, attrs=curses.A_DIM)

        # Block 3 (North-East above Int 02 T-Junction): Tech Tower blocking north extension!
        draw_sprite(stdscr, BUILDING_TECH_HUB,    city_top + 2, boul_right_x - 5, color_pair=6, attrs=curses.A_BOLD)
        draw_sprite(stdscr, BUILDING_RESIDENTIAL, city_top + 2, boul_right_x + 10, color_pair=6, attrs=curses.A_DIM)

        # Block 4 (Central West): Office & Residential
        draw_sprite(stdscr, BUILDING_CIVIC_CENTER, ave_top_y + 3, city_left + 4, color_pair=6, attrs=curses.A_DIM)
        draw_sprite(stdscr, BUILDING_RESIDENTIAL,  ave_top_y + 3, boul_left_x + 8, color_pair=6, attrs=curses.A_DIM)

        # Block 5 (Central East): Skyscraper & Tech park
        draw_sprite(stdscr, BUILDING_SKYSCRAPER,   ave_top_y + 3, boul_mid_x + 10, color_pair=6, attrs=curses.A_DIM)
        draw_sprite(stdscr, BUILDING_OFFICE_MED,   ave_top_y + 3, boul_right_x - 12, color_pair=6, attrs=curses.A_DIM)

        # Block 6 (South-West before Mall-04): Terminating Harbor Complex
        draw_sprite(stdscr, BUILDING_COMMERCIAL,   ave_mid_y + 3, city_left + 4, color_pair=6, attrs=curses.A_DIM)
        draw_sprite(stdscr, BUILDING_SKYSCRAPER,   ave_mid_y + 3, boul_left_x + 8, color_pair=6, attrs=curses.A_DIM)

        # Block 7 (South-East Waterfront & Depot):
        draw_sprite(stdscr, BUILDING_TECH_HUB,     ave_mid_y + 3, boul_mid_x + 10, color_pair=6, attrs=curses.A_DIM)
        draw_sprite(stdscr, BUILDING_RESIDENTIAL,  ave_mid_y + 3, boul_right_x + 6, color_pair=6, attrs=curses.A_DIM)

        # -------------------------------------------------------------
        # 3. RENDER ASYMMETRIC ROAD NETWORK (Realistic Layout)
        # -------------------------------------------------------------
        # 1. North Avenue (Continuous East-West)
        r_cfg = routes_config["H_NORTH"]
        ay = r_cfg["y"]
        try:
            stdscr.addstr(ay - 2, r_cfg["x_min"], "═" * (r_cfg["x_max"] - r_cfg["x_min"]), curses.color_pair(1) | curses.A_DIM)
            dash = ("- - " * (city_w // 4 + 2))[:r_cfg["x_max"] - r_cfg["x_min"]]
            stdscr.addstr(ay, r_cfg["x_min"], dash, curses.color_pair(3) | curses.A_DIM)
            stdscr.addstr(ay + 2, r_cfg["x_min"], "═" * (r_cfg["x_max"] - r_cfg["x_min"]), curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        # 2. Central Avenue (Starts at West Boulevard, passes through Int 03 to East edge)
        r_cfg = routes_config["H_MID"]
        ay = r_cfg["y"]
        try:
            stdscr.addstr(ay - 2, r_cfg["x_min"], "═" * (r_cfg["x_max"] - r_cfg["x_min"]), curses.color_pair(1) | curses.A_DIM)
            dash = ("- - " * (city_w // 4 + 2))[:r_cfg["x_max"] - r_cfg["x_min"]]
            stdscr.addstr(ay, r_cfg["x_min"], dash, curses.color_pair(3) | curses.A_DIM)
            stdscr.addstr(ay + 2, r_cfg["x_min"], "═" * (r_cfg["x_max"] - r_cfg["x_min"]), curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        # 3. South Avenue (Connects Int 04 to Int 05)
        r_cfg = routes_config["H_SOUTH"]
        ay = r_cfg["y"]
        try:
            stdscr.addstr(ay - 2, r_cfg["x_min"], "═" * (r_cfg["x_max"] - r_cfg["x_min"]), curses.color_pair(1) | curses.A_DIM)
            dash = ("- - " * (city_w // 4 + 2))[:r_cfg["x_max"] - r_cfg["x_min"]]
            stdscr.addstr(ay, r_cfg["x_min"], dash, curses.color_pair(3) | curses.A_DIM)
            stdscr.addstr(ay + 2, r_cfg["x_min"], "═" * (r_cfg["x_max"] - r_cfg["x_min"]), curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        # 4. West Boulevard (Int 01 to Int 04)
        bx = boul_left_x
        for ry in range(city_top + 1, ave_bot_y + 2):
            if city_left < bx - 5 and bx + 5 < city_right:
                try:
                    stdscr.addstr(ry, bx - 5, "║", curses.color_pair(1) | curses.A_DIM)
                    stdscr.addstr(ry, bx + 5, "║", curses.color_pair(1) | curses.A_DIM)
                    if ry not in (ave_top_y, ave_mid_y, ave_bot_y):
                        stdscr.addstr(ry, bx, "┆", curses.color_pair(3) | curses.A_DIM)
                except curses.error:
                    pass

        # 5. Staggered Central Spine (Upper half enters hub at boul_mid_x - 1, Lower departs at boul_mid_x + 1)
        bx_u = boul_mid_x - 1
        for ry in range(city_top + 1, ave_mid_y):
            if city_left < bx_u - 5 and bx_u + 5 < city_right:
                try:
                    stdscr.addstr(ry, bx_u - 5, "║", curses.color_pair(1) | curses.A_DIM)
                    stdscr.addstr(ry, bx_u + 5, "║", curses.color_pair(1) | curses.A_DIM)
                    if ry != ave_top_y:
                        stdscr.addstr(ry, bx_u, "┆", curses.color_pair(3) | curses.A_DIM)
                except curses.error:
                    pass

        bx_l = boul_mid_x + 1
        for ry in range(ave_mid_y + 2, ave_bot_y + 2):
            if city_left < bx_l - 5 and bx_l + 5 < city_right:
                try:
                    stdscr.addstr(ry, bx_l - 5, "║", curses.color_pair(1) | curses.A_DIM)
                    stdscr.addstr(ry, bx_l + 5, "║", curses.color_pair(1) | curses.A_DIM)
                    if ry != ave_bot_y:
                        stdscr.addstr(ry, bx_l, "┆", curses.color_pair(3) | curses.A_DIM)
                except curses.error:
                    pass

        # 6. East Boulevard (Starts at Int 02 T-junction and goes south to city bottom)
        bx = boul_right_x
        for ry in range(ave_top_y, city_bottom - 1):
            if city_left < bx - 5 and bx + 5 < city_right:
                try:
                    stdscr.addstr(ry, bx - 5, "║", curses.color_pair(1) | curses.A_DIM)
                    stdscr.addstr(ry, bx + 5, "║", curses.color_pair(1) | curses.A_DIM)
                    if ry not in (ave_top_y, ave_mid_y, ave_bot_y):
                        stdscr.addstr(ry, bx, "┆", curses.color_pair(3) | curses.A_DIM)
                except curses.error:
                    pass

        # -------------------------------------------------------------
        # 4. RENDER INTERSECTION NODES & INDEPENDENT SIGNAL LAMPS
        # -------------------------------------------------------------
        for int_id, (ix, iy) in int_coords.items():
            data = intersections[int_id]
            is_selected = (int_id == selected_int_id)
            sig_state = data["signal"]
            i_type = data["type"]

            ns_color = 5 if "NS_GREEN" in sig_state else 4
            ew_color = 5 if "EW_GREEN" in sig_state else 4

            if 0 <= iy < h and 0 <= ix < w:
                try:
                    # Clear center box for wider double-lane intersection
                    for dy in [-1, 0, 1]:
                        stdscr.addstr(iy + dy, ix - 4, "         ", curses.color_pair(1))

                    # Non-symmetric signal lamps based on intersection structure
                    # Int 02 (T-Junction: North closed): Only South, West, East lamps
                    if int_id != "02":
                        stdscr.addstr(iy - 3, ix - 1, "●", curses.color_pair(ns_color) | curses.A_BOLD)  # North
                    # Int 04 (T-Junction: West closed): Only North, South, East lamps
                    if int_id != "04":
                        stdscr.addstr(iy - 1, ix - 6, "●", curses.color_pair(ew_color) | curses.A_BOLD)  # West
                    # Int 05 (Fork: East closed): Only North, South, West lamps
                    if int_id != "05":
                        stdscr.addstr(iy + 1, ix + 6, "●", curses.color_pair(ew_color) | curses.A_BOLD)  # East
                    # South lamp on all junctions
                    stdscr.addstr(iy + 3, ix + 1, "●", curses.color_pair(ns_color) | curses.A_BOLD)      # South

                    # Selected Intersection Highlighted Frame
                    if is_selected:
                        tag = f"[{int_id}]"
                        stdscr.addstr(iy, ix - 1, tag, curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE)
                        stdscr.addstr(iy - 3, ix - 5, "┌──", curses.color_pair(2) | curses.A_BOLD)
                        stdscr.addstr(iy - 3, ix + 3, "──┐", curses.color_pair(2) | curses.A_BOLD)
                        stdscr.addstr(iy + 3, ix - 5, "└──", curses.color_pair(2) | curses.A_BOLD)
                        stdscr.addstr(iy + 3, ix + 3, "──┘", curses.color_pair(2) | curses.A_BOLD)
                    else:
                        tag = f" {int_id} "
                        stdscr.addstr(iy, ix - 1, tag, curses.color_pair(1) | curses.A_BOLD)
                except curses.error:
                    pass

        # -------------------------------------------------------------
        # 5. RENDER CARS & QUEUES (Emergent Traffic Density)
        # -------------------------------------------------------------
        for v in traffic_sim.vehicles:
            vx = int(v["x"])
            vy = int(v["y"])

            if v["dir"] == 'E':
                v_sprite = CAR_EAST
            elif v["dir"] == 'W':
                v_sprite = CAR_WEST
            elif v["dir"] == 'S':
                v_sprite = CAR_SOUTH
            else:
                v_sprite = CAR_NORTH

            # Vehicle color: Red brake light if queued/stopped, else assigned vehicle color
            if v["stopped"]:
                car_col = 4  # Red brake highlight when queued at red signal!
            else:
                car_col = v["color"]

            if city_left < vx < city_right - 4 and city_top < vy < city_bottom:
                try:
                    stdscr.addstr(vy, vx, v_sprite, curses.color_pair(car_col) | (curses.A_BOLD if v["stopped"] else curses.A_NORMAL))
                except curses.error:
                    pass

        # -------------------------------------------------------------
        # 6. LOWER CONTROL PANEL & CLI (Persistent Landing Screen)
        # -------------------------------------------------------------
        panel_top = city_bottom + 1
        curr_data = intersections[selected_int_id]

        col1_x = 2
        col2_x = max(col1_x + 46, w // 2)

        # Count queues at currently selected intersection
        sel_coords = int_coords[selected_int_id]
        queue_ns = sum(1 for v in traffic_sim.vehicles if v["axis"] == 'V' and v["stopped"] and abs(v["x"] - sel_coords[0]) < 6 and abs(v["y"] - sel_coords[1]) < 8)
        queue_ew = sum(1 for v in traffic_sim.vehicles if v["axis"] == 'H' and v["stopped"] and abs(v["y"] - sel_coords[1]) < 3 and abs(v["x"] - sel_coords[0]) < 16)
        curr_data["queue_ns"] = queue_ns
        curr_data["queue_ew"] = queue_ew

        # Left Column: Comprehensive FPGA Traffic Status Readout
        try:
            stdscr.addstr(panel_top, col1_x, f"SMART CITY // CONTROL [INT {selected_int_id}]", curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(panel_top, col1_x + 36, hw_badge, curses.color_pair(hw_col) | curses.A_BOLD)

            hw_link_txt = "● CONNECTED (AXI 0x43C4)" if hw_res["hardware_active"] else "× NOT CONNECTED [SOFTWARE TIMERS]"
            stdscr.addstr(panel_top + 1, col1_x, f"HARDWARE LINK   : {hw_link_txt:<35}", curses.color_pair(5 if hw_res["hardware_active"] else 4) | curses.A_BOLD)
            stdscr.addstr(panel_top + 2, col1_x, f"NAME            : {curr_data['name']}", curses.color_pair(1))
            stdscr.addstr(panel_top + 3, col1_x, f"GEOMETRY TYPE   : {curr_data['type']}", curses.color_pair(3))
            
            dens_str = f"{traffic_sim.get_density_name()} [{len(traffic_sim.vehicles)} VEHICLES]"
            stdscr.addstr(panel_top + 4, col1_x, f"TRAFFIC DENSITY : {dens_str:<24} [+/-]", curses.color_pair(2) | curses.A_BOLD)

            cong_col = 5 if traffic_sim.congestion_pct < 30 else (3 if traffic_sim.congestion_pct < 60 else 4)
            cong_str = f"{traffic_sim.congestion_pct}% [{traffic_sim.flow_status}]"
            stdscr.addstr(panel_top + 5, col1_x, f"CONGESTION      : {cong_str}", curses.color_pair(cong_col) | curses.A_BOLD)

            stdscr.addstr(panel_top + 6, col1_x, f"AVG SPEED       : {traffic_sim.avg_speed_kmh} km/h │ ACTIVE Q: NS:{queue_ns} EW:{queue_ew}", curses.color_pair(1))

            sig_disp = "NORTH-SOUTH GREEN │ EAST-WEST RED" if "NS_GREEN" in curr_data['signal'] else "EAST-WEST GREEN │ NORTH-SOUTH RED"
            stdscr.addstr(panel_top + 7, col1_x, f"SIGNALS         : {sig_disp}", curses.color_pair(5) if "GREEN" in sig_disp else curses.color_pair(4))
        except curses.error:
            pass

        # Vertical Divider
        for r in range(panel_top, h - 1):
            try:
                stdscr.addstr(r, col2_x - 2, "│", curses.color_pair(1) | curses.A_DIM)
            except curses.error:
                pass

        # Right Column: Interactive CLI & Command History
        max_hist_lines = max(3, h - panel_top - 3)
        visible_hist = cli_history[-max_hist_lines:]

        for idx, (msg, col) in enumerate(visible_hist):
            ry = panel_top + idx
            if ry < h - 2:
                try:
                    stdscr.addstr(ry, col2_x, msg[:w - col2_x - 2], curses.color_pair(col) | (curses.A_BOLD if col in (2, 5) else curses.A_NORMAL))
                except curses.error:
                    pass

        # Command Prompt
        prompt_y = min(h - 2, panel_top + len(visible_hist))
        prompt_str = f"> {cli_input_buffer}"
        try:
            stdscr.addstr(prompt_y, col2_x, prompt_str[:w - col2_x - 2], curses.color_pair(3) | curses.A_BOLD)
            cur_x = min(w - 2, col2_x + len(prompt_str))
            stdscr.move(prompt_y, cur_x)
        except curses.error:
            pass

        # Quick Key Footer
        try:
            footer_keys = "[1-5]: Select Int   [SPACE]: Toggle Signal   [+ / -]: Traffic Density   [ESC]: Exit"
            stdscr.addstr(h - 1, 2, footer_keys[:w - 4], curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()

        # -------------------------------------------------------------
        # 7. PROCESS USER INPUT & CLI COMMANDS
        # -------------------------------------------------------------
        key = stdscr.getch()
        if key == 27:  # ESC -> return to menu
            break
        elif key in (10, 13):  # ENTER -> execute CLI command
            raw_cmd = cli_input_buffer.strip()
            cmd = raw_cmd.lower()
            cli_history.append((f"> {raw_cmd}", 3))
            cli_input_buffer = ""

            tokens = cmd.split()
            first = tokens[0] if tokens else ""

            if cmd in ("intersections", "list"):
                cli_history.append(("CONNECTED SMART INTERSECTIONS:", 2))
                for i_id, i_info in intersections.items():
                    cli_history.append((f"[{i_id}] {i_info['name']} ({i_info['type']})", 1))

            elif cmd.startswith("select"):
                if len(tokens) > 1:
                    target_id = tokens[1].zfill(2)
                    if target_id in intersections:
                        selected_int_id = target_id
                        cli_history.append((f"INTERSECTION {target_id} SELECTED: {intersections[target_id]['name']}", 5))
                    else:
                        cli_history.append((f"UNKNOWN INTERSECTION ID '{tokens[1]}'. CHOOSE 01-05.", 4))
                else:
                    cli_history.append(("USAGE: select <01-05> (e.g. select 02)", 3))

            elif cmd in ("cycle", "toggle"):
                cur_sig = intersections[selected_int_id]["signal"]
                new_sig = "EW_GREEN" if cur_sig == "NS_GREEN" else "NS_GREEN"
                intersections[selected_int_id]["signal"] = new_sig
                cli_history.append((f"SIGNAL TOGGLED FOR INT {selected_int_id} -> {new_sig}", 5))

            elif cmd in ("+", "increase"):
                if traffic_sim.increase_density():
                    cli_history.append((f"[TRAFFIC] DENSITY INCREASED: {traffic_sim.get_density_name()} ({len(traffic_sim.vehicles)} VEHICLES)", 5))
                else:
                    cli_history.append(("[TRAFFIC] ALREADY AT MAXIMUM DENSITY (GRIDLOCK).", 4))

            elif cmd in ("-", "decrease"):
                if traffic_sim.decrease_density():
                    cli_history.append((f"[TRAFFIC] DENSITY DECREASED: {traffic_sim.get_density_name()} ({len(traffic_sim.vehicles)} VEHICLES)", 5))
                else:
                    cli_history.append(("[TRAFFIC] ALREADY AT MINIMUM DENSITY (LOW).", 4))

            elif first in ("traffic", "density"):
                if len(tokens) > 1:
                    req_dens = tokens[1].upper()
                    if req_dens in traffic_sim.DENSITY_LEVELS:
                        traffic_sim.density_idx = traffic_sim.DENSITY_LEVELS.index(req_dens)
                        cli_history.append((f"[TRAFFIC] DENSITY SET TO {req_dens} ({traffic_sim.get_target_count()} VEHICLES)", 5))
                    else:
                        cli_history.append(("USAGE: density <low|normal|high|heavy|gridlock>", 4))
                else:
                    cli_history.append((f"TRAFFIC DENSITY: {traffic_sim.get_density_name()} ({len(traffic_sim.vehicles)} VEHICLES)", 1))

            elif cmd == "status":
                cli_history.append((f"STATUS FOR INT {selected_int_id} ({intersections[selected_int_id]['name']}):", 2))
                cli_history.append((f"TYPE: {intersections[selected_int_id]['type']} │ SIGNAL: {intersections[selected_int_id]['signal']}", 1))
                cli_history.append((f"TRAFFIC: {traffic_sim.get_density_name()} │ CONGESTION: {traffic_sim.congestion_pct}%", 1))

            elif cmd == "clear":
                cli_history = [("SMART CITY // CONTROL", 1)]
            elif cmd in ("exit", "quit"):
                break
            elif cmd == "help":
                cli_history.append(("COMMANDS: intersections, select <id>, cycle, density <lvl>, +, -, status, clear, exit", 1))
            elif cmd != "":
                cli_history.append((f"UNKNOWN COMMAND: '{cmd}'. TYPE 'help' OR 'intersections'.", 4))

        # Direct Hotkeys
        elif key == ord('1'):
            selected_int_id = "01"
            cli_history.append((f"INTERSECTION 01 SELECTED: {intersections['01']['name']} (4-WAY)", 5))
        elif key == ord('2'):
            selected_int_id = "02"
            cli_history.append((f"INTERSECTION 02 SELECTED: {intersections['02']['name']} (3-WAY T-JUNCTION)", 5))
        elif key == ord('3'):
            selected_int_id = "03"
            cli_history.append((f"INTERSECTION 03 SELECTED: {intersections['03']['name']} (OFFSET 4-WAY)", 5))
        elif key == ord('4'):
            selected_int_id = "04"
            cli_history.append((f"INTERSECTION 04 SELECTED: {intersections['04']['name']} (3-WAY T-JUNCTION)", 5))
        elif key == ord('5'):
            selected_int_id = "05"
            cli_history.append((f"INTERSECTION 05 SELECTED: {intersections['05']['name']} (3-WAY FORK)", 5))

        elif key == ord(' '):  # SPACE -> Quick toggle signal phase of selected intersection
            cur_sig = intersections[selected_int_id]["signal"]
            new_sig = "EW_GREEN" if cur_sig == "NS_GREEN" else "NS_GREEN"
            intersections[selected_int_id]["signal"] = new_sig
            cli_history.append((f"SIGNAL TOGGLED: INT {selected_int_id} -> {new_sig}", 5))

        # Dynamic Traffic Density Control Hotkeys (+ and -)
        elif key in (ord('+'), ord('='), curses.KEY_UP, curses.KEY_RIGHT):
            if traffic_sim.increase_density():
                cli_history.append((f"[TRAFFIC] DENSITY INCREASED: {traffic_sim.get_density_name()} ({traffic_sim.get_target_count()} VEHICLES)", 5))

        elif key in (ord('-'), ord('_'), curses.KEY_DOWN, curses.KEY_LEFT):
            if traffic_sim.decrease_density():
                cli_history.append((f"[TRAFFIC] DENSITY DECREASED: {traffic_sim.get_density_name()} ({traffic_sim.get_target_count()} VEHICLES)", 5))

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if len(cli_input_buffer) > 0:
                cli_input_buffer = cli_input_buffer[:-1]
        elif 32 <= key <= 126:
            if len(cli_input_buffer) < 40:
                cli_input_buffer += chr(key)

        time.sleep(0.035)  # ~28 FPS smooth operational rate
