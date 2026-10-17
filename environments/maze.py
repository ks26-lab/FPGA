import curses
import time
import random
import math
from collections import deque


# --- PATHFINDING & MAZE ALGORITHMIC ANALYSIS ---

def solve_maze_bfs(maze, start=(1, 1), end=None):
    """
    Computes the shortest path from start to end using Breadth-First Search (BFS).
    Returns list of (x, y) coordinates along the solution route, or empty list if blocked.
    """
    h = len(maze)
    w = len(maze[0])
    if end is None:
        end = (w - 2, h - 2)

    sx, sy = start
    ex, ey = end

    if maze[sy][sx] == '#' or maze[ey][ex] == '#':
        return []

    queue = deque([[(sx, sy)]])
    visited = {(sx, sy)}

    while queue:
        path = queue.popleft()
        cx, cy = path[-1]

        if (cx, cy) == (ex, ey):
            return path

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= ny < h and 0 <= nx < w:
                if maze[ny][nx] != '#' and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(path + [(nx, ny)])

    return []

def is_path_open(maze, start=(1, 1), end=None):
    """Checks whether any valid walking path exists between start and end."""
    return len(solve_maze_bfs(maze, start, end)) > 0

def find_dead_ends(maze):
    """Identifies dead-end corridor cells (3 or more solid wall neighbors)."""
    h = len(maze)
    w = len(maze[0])
    dead_ends = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if maze[r][c] not in ('#', 'S', 'E'):
                walls = sum(1 for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)] if maze[r + dy][c + dx] == '#')
                if walls >= 3:
                    dead_ends.append((c, r))
    return dead_ends

def generate_solvable_maze(width=17, height=11):
    """
    Generates a procedural maze guaranteed to have a clear navigable path.
    Uses '#' for walls, '.' for open corridor cells, 'S' for Start, 'E' for Exit.
    """
    w = width if width % 2 == 1 else width + 1
    h = height if height % 2 == 1 else height + 1

    grid = [['#' for _ in range(w)] for _ in range(h)]

    # Randomized depth-first search
    start_x, start_y = 1, 1
    grid[start_y][start_x] = '.'
    stack = [(start_x, start_y)]

    while stack:
        cx, cy = stack[-1]
        neighbors = []
        for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
            nx, ny = cx + dx, cy + dy
            if 1 <= nx < w - 1 and 1 <= ny < h - 1 and grid[ny][nx] == '#':
                neighbors.append((nx, ny, dx, dy))

        if neighbors:
            nx, ny, dx, dy = random.choice(neighbors)
            grid[ny][nx] = '.'
            grid[cy + dy // 2][cx + dx // 2] = '.'
            stack.append((nx, ny))
        else:
            stack.pop()

    # Clear Start and Exit positions
    grid[1][1] = 'S'
    grid[h - 2][w - 2] = 'E'
    grid[h - 2][w - 3] = '.'
    grid[h - 3][w - 2] = '.'

    return grid


# --- VIEW RENDERING ENGINES ---

def render_top_view(stdscr, maze, cursor_x, cursor_y, px, py, pdir, ghost_active,
                    solution_set, show_solution, debug_mode, dead_ends,
                    feedback_msg, view_top, view_left):
    """
    Renders the Large, Centered Top-Down Architectural Maze View.
    Occupies 60-75% screen width, with color-coded boundaries, inner walls,
    solution route, start/exit gates, player marker, and compact legend.
    """
    h, w = stdscr.getmaxyx()
    m_h = len(maze)
    m_w = len(maze[0])

    cell_w = 4  # 4 characters wide for proper visual proportion

    maze_pixel_w = m_w * cell_w
    maze_pixel_h = m_h

    # Centering calculations
    avail_h = max(m_h + 4, h - 8 - view_top)
    start_x = max(view_left + 1, (w - maze_pixel_w) // 2)
    start_y = view_top + max(1, (avail_h - maze_pixel_h - 2) // 2)

    # Frame Header
    header_str = "┌── TOP-DOWN ARCHITECTURAL GRID // 3D MAZE PLANNER ─────────────────┐"
    try:
        stdscr.addstr(view_top, max(2, start_x - 4), header_str[:w - start_x], curses.color_pair(3) | curses.A_BOLD)
    except curses.error:
        pass

    # Column coordinate labels above maze
    coord_cols = "     " + "".join([f"{c:02d}  " for c in range(m_w)])
    try:
        stdscr.addstr(start_y - 1, start_x - 4, coord_cols[:w - start_x + 3], curses.color_pair(1) | curses.A_DIM)
    except curses.error:
        pass

    # Render Centered Maze Grid
    for r in range(m_h):
        draw_y = start_y + r
        if draw_y >= h - 7:
            break

        # Row coordinate label
        try:
            stdscr.addstr(draw_y, max(1, start_x - 4), f"{r:02d} │", curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        for c in range(m_w):
            draw_x = start_x + c * cell_w
            if draw_x + cell_w >= w - 1:
                continue

            cell_val = maze[r][c]
            is_cursor = (r == cursor_y and c == cursor_x)
            is_player = (r == py and c == px)
            is_outer = (r == 0 or r == m_h - 1 or c == 0 or c == m_w - 1)
            is_sol = (c, r) in solution_set and show_solution
            is_dead = (c, r) in dead_ends and debug_mode

            # Determine Cell Appearance & Color
            if is_cursor:
                if ghost_active:
                    cell_str = "[░░]" if cell_val != '#' else "[  ]"
                    cell_color = curses.color_pair(7) | curses.A_BOLD
                else:
                    cell_str = "[++]" if cell_val == '.' else "[##]"
                    cell_color = curses.color_pair(3) | curses.A_REVERSE | curses.A_BOLD
            elif is_player:
                # Player marker with direction arrow
                arrows = ["▲", "►", "▼", "◄"]
                cell_str = f"[{arrows[pdir]}P]"
                cell_color = curses.color_pair(3) | curses.A_BOLD | curses.A_REVERSE
            elif cell_val == 'S':
                cell_str = "[S ]"
                cell_color = curses.color_pair(2) | curses.A_BOLD
            elif cell_val == 'E':
                cell_str = "[★E]"
                cell_color = curses.color_pair(5) | curses.A_BOLD
            elif cell_val == '#':
                if is_outer:
                    # Outer Boundary Wall (Cyan solid frame)
                    cell_str = "████"
                    cell_color = curses.color_pair(3) | curses.A_BOLD
                else:
                    # Inner Maze Wall (Purple/Magenta structure)
                    cell_str = "▓▓▓▓"
                    cell_color = curses.color_pair(5)
            elif is_sol:
                # Solution path highlighted in bright green
                cell_str = " ══ "
                cell_color = curses.color_pair(2) | curses.A_BOLD
            elif is_dead:
                # Dead-end cell highlighted in debug mode
                cell_str = " ×· "
                cell_color = curses.color_pair(6) | curses.A_BOLD
            else:
                # Walkable Corridor floor with subtle illumination
                cell_str = "  · "
                cell_color = curses.color_pair(1) | curses.A_DIM

            try:
                stdscr.addstr(draw_y, draw_x, cell_str, cell_color)
            except curses.error:
                pass

    # Compact Legend below maze
    legend_y = start_y + m_h + 1
    if legend_y < h - 7:
        legend_parts = [
            ("● START", 2), ("   ", 1),
            ("● PLAYER", 3), ("   ", 1),
            ("★ EXIT", 5), ("   ", 1),
            ("██ OUTER BOUNDARY", 3), ("   ", 1),
            ("▓▓ INNER WALL", 5), ("   ", 1),
            ("·· WALKABLE", 1), ("   ", 1),
            ("══ SOLUTION PATH", 2)
        ]
        curr_lx = max(2, start_x - 2)
        for text, c_pair in legend_parts:
            if curr_lx + len(text) < w - 2:
                try:
                    stdscr.addstr(legend_y, curr_lx, text, curses.color_pair(c_pair) | (curses.A_BOLD if c_pair in (2, 3, 5) else curses.A_DIM))
                    curr_lx += len(text)
                except curses.error:
                    pass


def render_isometric_3d_view(stdscr, maze, cursor_x, cursor_y, px, py, solution_set, show_solution, view_top, view_left):
    """
    Renders the Isometric 3D Solid Structure View.
    Distinguishes cyan outer boundary blocks from purple inner walls.
    """
    h, w = stdscr.getmaxyx()
    m_h = len(maze)
    m_w = len(maze[0])

    try:
        stdscr.addstr(view_top, view_left, "┌── ISOMETRIC 3D SOLID STRUCTURE VIEW // DEPTH PROJECTION ──────────┐", curses.color_pair(3) | curses.A_BOLD)
    except curses.error:
        pass

    start_iso_y = view_top + 2
    iso_center_x = max(view_left + 24, w // 2 - 10)

    for r in range(m_h):
        for c in range(m_w):
            px_scr = iso_center_x + (c - r) * 2
            py_scr = start_iso_y + (c + r) // 2

            if not (view_top + 1 < py_scr < h - 8 and view_left < px_scr < w - 6):
                continue

            cell_val = maze[r][c]
            is_cursor = (r == cursor_y and c == cursor_x)
            is_player = (r == py and c == px)
            is_outer = (r == 0 or r == m_h - 1 or c == 0 or c == m_w - 1)
            is_sol = (c, r) in solution_set and show_solution

            if cell_val == '#':
                # Outer walls cyan, inner walls purple
                wall_pair = 3 if is_outer else 5
                try:
                    stdscr.addstr(py_scr - 1, px_scr, "┌──┐", curses.color_pair(wall_pair) | curses.A_BOLD)
                    stdscr.addstr(py_scr,     px_scr, "│██│/", curses.color_pair(wall_pair))
                    stdscr.addstr(py_scr + 1, px_scr, "└──┘/", curses.color_pair(1) | curses.A_DIM)
                except curses.error:
                    pass
            elif is_player:
                try:
                    stdscr.addstr(py_scr, px_scr, "[●P]", curses.color_pair(3) | curses.A_BOLD | curses.A_REVERSE)
                except curses.error:
                    pass
            elif cell_val == 'S':
                try:
                    stdscr.addstr(py_scr, px_scr, "[S ]", curses.color_pair(2) | curses.A_BOLD)
                except curses.error:
                    pass
            elif cell_val == 'E':
                try:
                    stdscr.addstr(py_scr, px_scr, "[★E]", curses.color_pair(5) | curses.A_BOLD)
                except curses.error:
                    pass
            elif is_sol:
                try:
                    stdscr.addstr(py_scr, px_scr, "====", curses.color_pair(2) | curses.A_BOLD)
                except curses.error:
                    pass
            else:
                floor_char = "· " if not is_cursor else "<>"
                f_color = curses.color_pair(1) | curses.A_DIM if not is_cursor else curses.color_pair(3) | curses.A_BOLD
                try:
                    stdscr.addstr(py_scr, px_scr, floor_char, f_color)
                except curses.error:
                    pass


def render_front_gate_view(stdscr, maze, view_top, view_left):
    """
    Renders the Front Gate Entrance View physically connected to the maze structure.
    Shows the illuminated entrance arch, Start beacon, and deep corridor perspective.
    """
    h, w = stdscr.getmaxyx()
    gx = max(view_left + 4, w // 2 - 28)
    gy = view_top + 2

    gate_art = [
        r"             .─────────────────────────────────────────.             ",
        r"            /│   3D COMPUTATIONAL MAZE // ENTRANCE     │\            ",
        r"           / │            PORTAL TERMINAL              │ \           ",
        r"          /__│═════════════════════════════════════════│__\          ",
        r"          │  │ [BEACON: ONLINE]       [SECURITY: OPEN] │  │          ",
        r"          │  └────────────────────┬────────────────────┘  │          ",
        r"          │   ▓▓▓▓▓▓▓▓▓▓          │          ▓▓▓▓▓▓▓▓▓▓   │          ",
        r"          │   ▓▓  ┌───────────────┴───────────────┐  ▓▓   │          ",
        r"          │   ▓▓  │  >>> ENTER CONSTRUCTED MAZE   │  ▓▓   │          ",
        r"          │   ▓▓  │                               │  ▓▓   │          ",
        r"          │   ▓▓  │    /\                   /\    │  ▓▓   │          ",
        r"          │   ▓▓  │   /  \    [START GATE] /  \   │  ▓▓   │          ",
        r"          │   ▓▓  │  /    \      ●===>    /    \  │  ▓▓   │          ",
        r"          └───┴───┴─/______\─────────────/______\_┴───┴───┘          ",
        r"          ═════════════════════════════════════════════════          "
    ]

    for idx, line in enumerate(gate_art):
        y = gy + idx
        if y < h - 7:
            try:
                col = 2 if idx in (11, 12) else (3 if idx < 5 else 4)
                stdscr.addstr(y, gx, line[:w - gx - 1], curses.color_pair(col) | (curses.A_BOLD if idx < 5 else curses.A_NORMAL))
            except curses.error:
                pass

    try:
        stdscr.addstr(gy + len(gate_art) + 1, gx + 8, "PHYSICAL ENTRANCE ALIGNED TO [START: CELL (01, 01)]", curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(gy + len(gate_art) + 2, gx + 8, "PRESS [E] OR [ENTER] TO STEP THROUGH THE GATE INTO FIRST-PERSON 3D", curses.color_pair(7) | curses.A_BOLD)
    except curses.error:
        pass


def render_first_person_3d_view(stdscr, maze, px, py, pdir, solution_set, show_solution, exit_dist, view_top, view_left):
    """
    Renders the Enhanced First-Person 3D Perspective inside the maze.
    - Outer boundary walls are distinctly CYAN.
    - Inner partition walls are PURPLE/MAGENTA.
    - Walkable corridor floor is dark with depth illumination.
    - Solution path is illuminated with GREEN glowing floor markers.
    - Start Entrance and Exit Portal beacons are clearly visible.
    - Top-down Minimap in upper-right corner keeps spatial awareness constant.
    - Compass & Telemetry HUD in upper-left.
    """
    h, w = stdscr.getmaxyx()
    m_h = len(maze)
    m_w = len(maze[0])

    cx = w // 2 - 6  # Shift slightly left to accommodate the minimap on the right
    cy = (view_top + (h - 7)) // 2

    # Movement vectors
    dx = [0, 1, 0, -1]
    dy = [-1, 0, 1, 0]
    dir_names = ["NORTH [-Y]", "EAST [+X]", "SOUTH [+Y]", "WEST [-X]"]

    vp_top = view_top + 1
    vp_bottom = h - 8
    vp_w = w - 4

    # Horizon and subtle ceiling/floor depth shading
    for y in range(vp_top, vp_bottom):
        if y < cy:
            grad = " " * (vp_w - 2)
            try:
                stdscr.addstr(y, 2, grad, curses.color_pair(1) | curses.A_DIM)
            except curses.error:
                pass
        else:
            floor_char = "·" if y % 2 == 0 else " "
            grad = (floor_char * 2) * (vp_w // 2)
            try:
                stdscr.addstr(y, 2, grad[:vp_w - 2], curses.color_pair(4) | curses.A_DIM)
            except curses.error:
                pass

    # Step depths: 3=far, 2=mid, 1=near, 0=current
    depths = [
        (int(vp_w * 0.78), int((vp_bottom - vp_top) * 0.82)),
        (int(vp_w * 0.54), int((vp_bottom - vp_top) * 0.58)),
        (int(vp_w * 0.32), int((vp_bottom - vp_top) * 0.36)),
        (int(vp_w * 0.12), int((vp_bottom - vp_top) * 0.14))
    ]

    # Render depth planes back-to-front
    for d in range(3, -1, -1):
        fx = px + dx[pdir] * d
        fy = py + dy[pdir] * d

        if not (0 <= fy < m_h and 0 <= fx < m_w):
            continue

        left_dir = (pdir - 1) % 4
        right_dir = (pdir + 1) % 4

        lx, ly = fx + dx[left_dir], fy + dy[left_dir]
        rx, ry = fx + dx[right_dir], fy + dy[right_dir]

        wall_front = (maze[fy][fx] == '#')
        wall_left = (0 <= ly < m_h and 0 <= lx < m_w and maze[ly][lx] == '#')
        wall_right = (0 <= ry < m_h and 0 <= rx < m_w and maze[ry][rx] == '#')

        is_front_outer = (fx == 0 or fx == m_w - 1 or fy == 0 or fy == m_h - 1)
        is_left_outer = (lx == 0 or lx == m_w - 1 or ly == 0 or ly == m_h - 1)
        is_right_outer = (rx == 0 or rx == m_w - 1 or ry == 0 or ry == m_h - 1)

        dw, dh = depths[d]
        x1, x2 = cx - dw // 2, cx + dw // 2
        y1, y2 = cy - dh // 2, cy + dh // 2

        # Color distinction: Outer Boundary = Cyan (3), Inner Walls = Purple (5)
        color_front = 3 if is_front_outer else 5
        color_left  = 3 if is_left_outer else 5
        color_right = 3 if is_right_outer else 5

        if wall_front:
            # Front facing 3D wall surface
            wall_char = "█" if is_front_outer else "▓"
            for y in range(max(vp_top, y1), min(vp_bottom, y2)):
                wall_line = wall_char * max(0, x2 - x1)
                try:
                    stdscr.addstr(y, x1, wall_line, curses.color_pair(color_front) | (curses.A_BOLD if d <= 1 else curses.A_NORMAL))
                except curses.error:
                    pass
        else:
            # Side corridor walls
            if d < 3:
                ndw, ndh = depths[d + 1]
                nx1, nx2 = cx - ndw // 2, cx + ndw // 2
                ny1, ny2 = cy - ndh // 2, cy + ndh // 2

                if wall_left:
                    side_char = "█" if is_left_outer else "▓"
                    for y in range(max(vp_top, ny1), min(vp_bottom, ny2)):
                        try:
                            stdscr.addstr(y, x1, side_char * max(0, nx1 - x1), curses.color_pair(color_left) | curses.A_DIM)
                        except curses.error:
                            pass

                if wall_right:
                    side_char = "█" if is_right_outer else "▓"
                    for y in range(max(vp_top, ny1), min(vp_bottom, ny2)):
                        try:
                            stdscr.addstr(y, nx2, side_char * max(0, x2 - nx2), curses.color_pair(color_right) | curses.A_DIM)
                        except curses.error:
                            pass

            # Floor illuminated markings along corridor
            # Green solution path illumination on floor
            if (fx, fy) in solution_set and show_solution and not wall_front:
                floor_y = min(vp_bottom - 1, y2 - 1)
                sol_line = "▲▲▲ [SOLUTION ROUTE] ▲▲▲"
                if len(sol_line) < (x2 - x1):
                    pad = ((x2 - x1) - len(sol_line)) // 2
                    try:
                        stdscr.addstr(floor_y, x1 + pad, sol_line, curses.color_pair(2) | curses.A_BOLD)
                    except curses.error:
                        pass

            # Exit Portal beacon in 3D
            if fx == m_w - 2 and fy == m_h - 2:
                portal_y = max(vp_top + 1, cy - 2)
                portal_label = "★ EXIT PORTAL ★"
                try:
                    stdscr.addstr(portal_y, cx - len(portal_label) // 2, portal_label, curses.color_pair(5) | curses.A_BOLD | curses.A_BLINK)
                except curses.error:
                    pass

            # Start Gate in 3D
            if fx == 1 and fy == 1:
                start_label = "[START ENTRANCE GATE]"
                try:
                    stdscr.addstr(cy - 2, cx - len(start_label) // 2, start_label, curses.color_pair(2) | curses.A_BOLD)
                except curses.error:
                    pass

    # -------------------------------------------------------------
    # TOP-RIGHT CORNER: LIVE 3D MINIMAP
    # -------------------------------------------------------------
    mm_w = m_w + 2
    mm_h = m_h + 2
    mm_x = max(cx + depths[0][0] // 2 + 2, w - mm_w - 3)
    mm_y = vp_top + 1

    try:
        stdscr.addstr(mm_y - 1, mm_x, "┌── MINIMAP ────────┐"[:mm_w + 2], curses.color_pair(3) | curses.A_BOLD)
        for mr in range(m_h):
            row_chars = []
            for mc in range(m_w):
                if (mc, mr) == (px, py):
                    # Player orientation arrow
                    arrows = ["▲", "►", "▼", "◄"]
                    row_chars.append((arrows[pdir], 3, curses.A_BOLD | curses.A_REVERSE))
                elif (mc, mr) == (1, 1):
                    row_chars.append(("S", 2, curses.A_BOLD))
                elif (mc, mr) == (m_w - 2, m_h - 2):
                    row_chars.append(("E", 5, curses.A_BOLD))
                elif (mc, mr) in solution_set and show_solution:
                    row_chars.append(("·", 2, curses.A_BOLD))
                elif maze[mr][mc] == '#':
                    if mr == 0 or mr == m_h - 1 or mc == 0 or mc == m_w - 1:
                        row_chars.append(("█", 3, curses.A_BOLD))
                    else:
                        row_chars.append(("▓", 5, curses.A_NORMAL))
                else:
                    row_chars.append((" ", 1, curses.A_NORMAL))

            stdscr.addstr(mm_y + mr, mm_x, "│", curses.color_pair(3))
            for c_idx, (ch, cp, attrs) in enumerate(row_chars):
                stdscr.addstr(mm_y + mr, mm_x + 1 + c_idx, ch, curses.color_pair(cp) | attrs)
            stdscr.addstr(mm_y + mr, mm_x + 1 + len(row_chars), "│", curses.color_pair(3))

        stdscr.addstr(mm_y + m_h, mm_x, "└───────────────────┘"[:mm_w + 2], curses.color_pair(3))
    except curses.error:
        pass

    # -------------------------------------------------------------
    # TOP-LEFT CORNER: SPATIAL ORIENTATION COMPASS & HUD
    # -------------------------------------------------------------
    hud_lx = 4
    hud_ly = vp_top + 1

    # Compass Rose with dynamic heading highlight
    c_n = curses.color_pair(2) | curses.A_BOLD if pdir == 0 else curses.color_pair(1) | curses.A_DIM
    c_e = curses.color_pair(2) | curses.A_BOLD if pdir == 1 else curses.color_pair(1) | curses.A_DIM
    c_s = curses.color_pair(2) | curses.A_BOLD if pdir == 2 else curses.color_pair(1) | curses.A_DIM
    c_w = curses.color_pair(2) | curses.A_BOLD if pdir == 3 else curses.color_pair(1) | curses.A_DIM

    try:
        stdscr.addstr(hud_ly, hud_lx, "┌── SPATIAL ORIENTATION ────────┐", curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(hud_ly + 1, hud_lx, "│   COMPASS:       ", curses.color_pair(1))
        stdscr.addstr(hud_ly + 1, hud_lx + 19, "[N]" if pdir == 0 else " N ", c_n)
        stdscr.addstr(hud_ly + 1, hud_lx + 32, "│", curses.color_pair(3))

        stdscr.addstr(hud_ly + 2, hud_lx, "│               ", curses.color_pair(1))
        stdscr.addstr(hud_ly + 2, hud_lx + 16, "[W]" if pdir == 3 else " W ", c_w)
        stdscr.addstr(hud_ly + 2, hud_lx + 19, "─┼─", curses.color_pair(3))
        stdscr.addstr(hud_ly + 2, hud_lx + 22, "[E]" if pdir == 1 else " E ", c_e)
        stdscr.addstr(hud_ly + 2, hud_lx + 32, "│", curses.color_pair(3))

        stdscr.addstr(hud_ly + 3, hud_lx, "│                  ", curses.color_pair(1))
        stdscr.addstr(hud_ly + 3, hud_lx + 19, "[S]" if pdir == 2 else " S ", c_s)
        stdscr.addstr(hud_ly + 3, hud_lx + 32, "│", curses.color_pair(3))

        stdscr.addstr(hud_ly + 4, hud_lx, f"│ HEADING : {dir_names[pdir]:<19} │", curses.color_pair(3))
        stdscr.addstr(hud_ly + 5, hud_lx, f"│ POS     : X:{px:02d}  Y:{py:02d}  Z:01       │", curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(hud_ly + 6, hud_lx, f"│ EXIT DST: {exit_dist:02d} CELLS             │", curses.color_pair(7) | curses.A_BOLD)
        sol_tag = "VISIBLE [P]" if show_solution else "HIDDEN [P]"
        stdscr.addstr(hud_ly + 7, hud_lx, f"│ PATH    : {sol_tag:<19} │", curses.color_pair(2 if show_solution else 1))
        stdscr.addstr(hud_ly + 8, hud_lx, "└───────────────────────────────┘", curses.color_pair(3) | curses.A_BOLD)
    except curses.error:
        pass

    # Exit notification if reached
    if px == m_w - 2 and py == m_h - 2:
        try:
            stdscr.addstr(cy, cx - 14, "★ EXIT PORTAL REACHED! ★", curses.color_pair(5) | curses.A_BOLD | curses.A_BLINK)
        except curses.error:
            pass


def run_gate_transition_sequence(stdscr, maze, px=1, py=1):
    """
    Deliberate camera entrance transition:
    1. Focus on Start Gate in Top View
    2. Camera lowers into Entrance Portal
    3. Portal energy fields expand
    4. First-Person 3D coupling lock
    """
    stdscr.nodelay(True)
    h, w = stdscr.getmaxyx()

    stages = [
        ("STAGE 1: ACQUIRING START GATE TELEMETRY [CELL 01, 01]...", 3),
        ("STAGE 2: ALIGNING OPTICAL VECTOR TO ARCHITECTURAL PORTAL...", 7),
        ("STAGE 3: COUPLING FIRST-PERSON INERTIAL SENSOR RIG...", 2),
        ("STAGE 4: ENTERING CONSTRUCTED 3D CORRIDOR...", 2)
    ]

    for stage_idx, (text, col) in enumerate(stages):
        loop_start = time.time()
        while time.time() - loop_start < 0.22:
            try:
                k = stdscr.getch()
                if k != -1:
                    return  # Instant skip
            except curses.error:
                pass

            stdscr.erase()
            # Portal expansion animation
            box_w = 40 + stage_idx * 6
            box_h = 10 + stage_idx * 2
            bx = max(2, (w - box_w) // 2)
            by = max(2, (h - box_h) // 2)

            try:
                stdscr.addstr(by, bx, "┌" + "─" * (box_w - 2) + "┐", curses.color_pair(col) | curses.A_BOLD)
                for r in range(by + 1, by + box_h - 1):
                    stdscr.addstr(r, bx, "│", curses.color_pair(col))
                    stdscr.addstr(r, bx + box_w - 1, "│", curses.color_pair(col))
                stdscr.addstr(by + box_h - 1, bx, "└" + "─" * (box_w - 2) + "┘", curses.color_pair(col) | curses.A_BOLD)

                stdscr.addstr(by + box_h // 2 - 1, bx + 4, "3D COMPUTATIONAL MAZE // GATE TRANSITION", curses.color_pair(3) | curses.A_BOLD)
                stdscr.addstr(by + box_h // 2 + 1, bx + 4, text[:box_w - 8], curses.color_pair(col) | curses.A_BOLD)
                stdscr.addstr(h - 2, 4, "[PRESS ANY KEY TO SKIP TRANSITION]", curses.color_pair(1) | curses.A_DIM)
            except curses.error:
                pass

            stdscr.refresh()
            time.sleep(0.04)


def run_construction_intro(stdscr, maze):
    """
    Dynamic intro: Walls physically rise into place from an empty grid,
    then camera smoothly pans toward the completed structure.
    Pressing any key immediately skips to interactive construction.
    """
    stdscr.clear()
    curses.curs_set(0)
    stdscr.nodelay(True)

    h, w = stdscr.getmaxyx()
    m_h = len(maze)
    m_w = len(maze[0])

    wall_coords = [(r, c) for r in range(m_h) for c in range(m_w) if maze[r][c] == '#']
    random.shuffle(wall_coords)

    building_maze = [['.' for _ in range(m_w)] for _ in range(m_h)]
    building_maze[1][1] = 'S'
    building_maze[m_h - 2][m_w - 2] = 'E'

    step = 0
    total_walls = len(wall_coords)
    batch_size = max(2, total_walls // 15)

    while step < total_walls:
        try:
            key = stdscr.getch()
            if key != -1:
                return  # Skip immediately to interactive mode
        except curses.error:
            pass

        for _ in range(batch_size):
            if step < total_walls:
                wr, wc = wall_coords[step]
                building_maze[wr][wc] = '#'
                step += 1

        stdscr.erase()
        pct = int((step / total_walls) * 100)

        try:
            stdscr.addstr(1, 4, "3D COMPUTATIONAL MAZE // PHYSICAL CONSTRUCTION SEQUENCE", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(2, 4, f"ASSEMBLING WALL BLOCKS: {pct}% COMPLETE [{step}/{total_walls} BLOCKS]", curses.color_pair(1))
        except curses.error:
            pass

        render_isometric_3d_view(stdscr, building_maze, cursor_x=1, cursor_y=1, px=1, py=1,
                                 solution_set=set(), show_solution=False, view_top=3, view_left=3)

        try:
            stdscr.addstr(h - 2, 4, "[PRESS ANY KEY TO SKIP INTRO TO INTERACTIVE BUILDER]", curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.07)

    time.sleep(0.3)
    
def render_win_animation(stdscr, phase):
    h, w = stdscr.getmaxyx()
    msg = [
        r"  _____ _   _  _____ _____ _____  _____  _____ ",
        r" /  ___| | | |/  __ \/  __ \  ___|/  ___|/  ___|",
        r" \ `--.| | | || /  \/| /  \/| |__  \ `--. \ `--. ",
        r"  `--. \ | | || |    | |    |  __|  `--. \ `--. \ ",
        r" /\__/ / |_| || \__/\| \__/\| |___ /\__/ /\__/ /",
        r" \____/ \___/  \____/ \____/\____/ \____/\____/ "
    ]
    
    color = curses.color_pair(5) | curses.A_BLINK if phase % 10 < 5 else curses.color_pair(2) | curses.A_BOLD
    by = h // 2 - 3
    bx = max(0, w // 2 - 25)
    
    try:
        stdscr.addstr(by - 2, bx + 10, f"*** 3D MAZE COMPLETED! [PHASE {phase:03d}] ***", color)
        for i, line in enumerate(msg):
            stdscr.addstr(by + i, bx, line[:w-1], color)
        stdscr.addstr(by + 7, bx + 5, "[PRESS ESC TO EXIT OR R TO RESTART]", curses.color_pair(1) | curses.A_DIM)
    except curses.error:
        pass

def render_lose_animation(stdscr, phase):
    h, w = stdscr.getmaxyx()
    msg = [
        r"  _____ _____ ___  ___ _____ _____  _   _  _____ ",
        r" |_   _|_   _||  \/  ||  ___|  _  || | | ||_   _|",
        r"   | |   | |  | .  . || |__ | | | || | | |  | |  ",
        r"   | |   | |  | |\/| ||  __|| | | || | | |  | |  ",
        r"   | |  _| |_ | |  | || |___\ \_/ /| |_| |  | |  ",
        r"   \_/  \___/ \_|  |_/\____/ \___/  \___/   \_/  "
    ]
    color = curses.color_pair(6) | curses.A_BOLD if phase % 4 < 2 else curses.color_pair(1) | curses.A_DIM
    by = h // 2 - 3
    bx = max(0, w // 2 - 25)
    
    try:
        stdscr.addstr(by - 2, bx + 14, f"*** TIMEOUT! [PHASE {phase:03d}] ***", color)
        for i, line in enumerate(msg):
            stdscr.addstr(by + i, bx, line[:w-1], color)
        stdscr.addstr(by + 7, bx + 5, "[PRESS ESC TO EXIT OR R TO RESTART]", curses.color_pair(1) | curses.A_DIM)
    except curses.error:
        pass



def launch_maze(stdscr, fpga_hw=None):
    """
    Master entry point for the 3D MAZE environment.
    Unified physical representation:
    - Large, Centered TOP VIEW (Architectural Grid & Block placement)
    - 3D ISOMETRIC VIEW (Inspection & Wall physics)
    - FRONT GATE VIEW (Architectural Entrance)
    - ENHANCED FIRST-PERSON NAVIGATION (with Minimap, Compass, Color Guidance)
    """
    curses.curs_set(0)

    # 7 Distinct Color Pairs strictly matching requirement color system
    curses.init_pair(1, curses.COLOR_WHITE, -1)    # Neutral Grid / Coordinates / Corridor dots
    curses.init_pair(2, curses.COLOR_GREEN, -1)    # Start / Solution Path / Success
    curses.init_pair(3, curses.COLOR_CYAN, -1)     # Outer Boundary / Player / Primary Frames
    curses.init_pair(4, curses.COLOR_BLUE, -1)     # Dark Neutral Corridor Illumination
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # Inner Partition Walls / Exit Portal
    curses.init_pair(6, curses.COLOR_RED, -1)      # Alerts / Collisions / Dead-Ends
    curses.init_pair(7, curses.COLOR_YELLOW, -1)   # Gate Beacons / Warnings / Accents

    # 1. Generate Solvable Procedural Baseline Maze
    m_w, m_h = 17, 11
    maze = generate_solvable_maze(m_w, m_h)

    # Precalculate initial solution route and dead ends
    solution_path = solve_maze_bfs(maze)
    solution_set = set(solution_path)
    dead_ends = find_dead_ends(maze)

    # 2. Dynamic Construction Sequence (skippable)
    run_construction_intro(stdscr, maze)

    # 3. Interactive State Initialization
    stdscr.nodelay(True)
    stdscr.clear()

    camera_mode = "TOP"  # "TOP", "3D", "GATE", "FIRST_PERSON"

    # Top View Cursor
    cursor_x, cursor_y = 2, 2
    ghost_active = True
    feedback_msg = "LARGE ARCHITECTURAL GRID ACTIVE. [SPACE]: PLACE/REMOVE WALL. [E]: ENTER 3D."
    feedback_color = 2

    # First-Person Navigator Position & Direction
    px, py, pdir = 1, 1, 1  # Start at (1, 1) facing East (+X)

    # Navigation Guidance Toggles
    show_solution = True   # Green solution path visible by default
    debug_mode = False     # Debug/analysis algorithmic metrics

    if fpga_hw is None:
        try:
            from hardware.fpga_interface import get_fpga_interface
            fpga_hw = get_fpga_interface()
        except ImportError:
            pass

    game_state = "RUNNING"
    timer_s = 30
    anim_state = "NONE"
    anim_phase = 0
    last_tick_time = time.time()
    anim_tick_time = time.time()

    # Main Interactive Event Loop
    while True:
        now = time.time()
        
        # 0. Hardware / Software Telemetry Sync
        if fpga_hw and getattr(fpga_hw, 'is_hardware_active', False):
            if hasattr(fpga_hw, 'read_maze_state'):
                hw_state = fpga_hw.read_maze_state()
                if hw_state.get("hardware_active"):
                    game_state = hw_state.get("game_state", game_state)
                    timer_s = hw_state.get("remaining_time_s", timer_s)
                    anim_state = hw_state.get("animation_state", anim_state)
                    anim_phase = hw_state.get("animation_phase", anim_phase)
        else:
            # Software fallback simulation for VISUALIZATION MODE
            if game_state == "RUNNING" and camera_mode == "FIRST_PERSON":
                if now - last_tick_time >= 1.0:
                    timer_s = max(0, timer_s - 1)
                    last_tick_time = now
                    if timer_s == 0:
                        game_state = "TIMEOUT"
                        anim_state = "LOSE"
                        anim_phase = 0
                        anim_tick_time = now
                
                # Check win condition manually if software only
                if (px, py) == (m_w - 2, m_h - 2):
                    game_state = "WIN"
                    anim_state = "WIN"
                    anim_phase = 0
                    anim_tick_time = now

            if anim_state != "NONE":
                if now - anim_tick_time >= 0.1:
                    anim_phase = (anim_phase + 1) % 256
                    anim_tick_time = now

        h, w = stdscr.getmaxyx()
        stdscr.erase()

        view_top = 1
        view_left = 2

        # Count live statistics
        wall_count = sum(row.count('#') for row in maze)
        path_count = sum(row.count('.') for row in maze) + 2  # S and E
        outer_walls = 2 * m_w + 2 * (m_h - 2)
        inner_walls = max(0, wall_count - outer_walls)

        # Update solution path
        solution_path = solve_maze_bfs(maze, start=(1, 1), end=(m_w - 2, m_h - 2))
        solution_set = set(solution_path)
        path_open = len(solution_path) > 0

        # Calculate distance to exit from current player position
        player_to_exit_path = solve_maze_bfs(maze, start=(px, py), end=(m_w - 2, m_h - 2))
        exit_dist = max(0, len(player_to_exit_path) - 1) if player_to_exit_path else 999

        # -------------------------------------------------------------
        # 1. TOP STATUS BAR (FPGA Architectural Pipeline)
        # -------------------------------------------------------------
        title_bar = " 3D MAZE BUILDER & SIMULATOR // FPGA ARCHITECTURAL PIPELINE "
        try:
            stdscr.addstr(0, 0, "┌" + "─" * (w - 2) + "┐", curses.color_pair(3))
            stdscr.addstr(1, 0, "│", curses.color_pair(3))
            stdscr.addstr(1, 2, title_bar, curses.color_pair(3) | curses.A_BOLD)
            # Hardware Status Badge in Top Bar
            if fpga_hw:
                b_text, b_color_code = fpga_hw.get_status_badge()
                badge_cp = 2 if b_color_code == "GREEN" else (6 if b_color_code == "RED" else 7)
            else:
                b_text = "[× SOFTWARE VISUALIZATION MODE — FPGA NOT REQUIRED]"
                badge_cp = 6
            stdscr.addstr(1, max(2, w - len(b_text) - 3), b_text, curses.color_pair(badge_cp) | curses.A_BOLD)
            stdscr.addstr(1, w - 1, "│", curses.color_pair(3))
            stdscr.addstr(2, 0, "├" + "─" * (w - 2) + "┤", curses.color_pair(3))
        except curses.error:
            pass

        # -------------------------------------------------------------
        # 2. ACTIVE VIEWPORT RENDERING
        # -------------------------------------------------------------
        if anim_state == "WIN":
            render_win_animation(stdscr, anim_phase)
        elif anim_state == "LOSE":
            render_lose_animation(stdscr, anim_phase)
        else:
            if camera_mode == "TOP":
                render_top_view(stdscr, maze, cursor_x, cursor_y, px, py, pdir, ghost_active,
                                solution_set, show_solution, debug_mode, dead_ends,
                                feedback_msg, view_top=3, view_left=view_left)
            elif camera_mode == "3D":
                render_isometric_3d_view(stdscr, maze, cursor_x, cursor_y, px, py,
                                         solution_set, show_solution, view_top=3, view_left=view_left)
            elif camera_mode == "GATE":
                render_front_gate_view(stdscr, maze, view_top=3, view_left=view_left)
            elif camera_mode == "FIRST_PERSON":
                render_first_person_3d_view(stdscr, maze, px, py, pdir, solution_set, show_solution,
                                            exit_dist, view_top=3, view_left=view_left)

        # -------------------------------------------------------------
        # 3. LOWER HUD: TELEMETRY & MULTI-VIEW CONTROLS
        # -------------------------------------------------------------
        hud_top = h - 6
        try:
            stdscr.addstr(hud_top, 0, "├" + "─" * (w - 2) + "┤", curses.color_pair(3))

            # Row 1: View Selectors & Spatial Coordinates
            v_top_tag = "[● 1: TOP]" if camera_mode == "TOP" else "[○ 1: TOP]"
            v_3d_tag  = "[● 2: 3D-ISO]" if camera_mode == "3D" else "[○ 2: 3D-ISO]"
            v_gate_tag = "[● 3: GATE]" if camera_mode == "GATE" else "[○ 3: GATE]"
            v_fp_tag   = "[● 4: FIRST-PERSON]" if camera_mode == "FIRST_PERSON" else "[○ 4: FIRST-PERSON]"

            dir_abbrev = ["NORTH", "EAST", "SOUTH", "WEST"][pdir]
            timer_str = f"│ TIMER: {timer_s:02d}s" if camera_mode == "FIRST_PERSON" else ""
            hud_row1 = f"VIEW: {v_top_tag} {v_3d_tag} {v_gate_tag} {v_fp_tag} │ POS: X:{px:02d} Y:{py:02d} Z:01 │ HEADING: {dir_abbrev} {timer_str}"
            stdscr.addstr(hud_top + 1, 2, hud_row1[:w - 4], curses.color_pair(3) | curses.A_BOLD)

            # Row 2: Navigation Telemetry & Path Guidance & Hardware Execution Mode
            if fpga_hw:
                try:
                    from hardware.fpga_health import get_hardware_state
                    hw_state = get_hardware_state()
                    hw_is_connected = hw_state.is_connected
                    hw_tag = f"[● FPGA: {hw_state.device} ({hw_state.last_response_ms}ms)]" if hw_is_connected else "[× SOFTWARE-ONLY MODE]"
                except Exception:
                    hw_is_connected = False
                    hw_tag = "[× HARDWARE API ERROR]"
            else:
                hw_is_connected = False
                hw_tag = "[× SOFTWARE-ONLY MODE]"

            sol_status = f"ON ROUTE (REM: {exit_dist:02d} CELLS)" if (px, py) in solution_set else f"OFF-ROUTE (EXIT DST: {exit_dist:02d} CELLS)"
            path_vis_tag = "PATH: [P]" if show_solution else "PATH: OFF"
            hud_row2 = f"GRID: {m_w}x{m_h} │ WALLS: {wall_count:02d} │ {sol_status} │ {path_vis_tag} │ {hw_tag}"
            stdscr.addstr(hud_top + 2, 2, hud_row2[:w - 4], curses.color_pair(2 if hw_is_connected else 6))

            # Row 3: Action Feedback Message
            stdscr.addstr(hud_top + 3, 2, f">> {feedback_msg}", curses.color_pair(feedback_color) | curses.A_BOLD)

            # Row 4: Keybinding Controls
            if camera_mode in ("TOP", "3D"):
                ctrl_str = "[ARROWS/WASD]: Move Cursor │ [SPACE/ENTER]: Build/Remove Block │ [P]: Path Toggle │ [E]: Enter 3D │ [ESC]: Exit"
            elif camera_mode == "GATE":
                ctrl_str = "[E / ENTER]: Step Through Portal Into 3D Maze │ [1]: Top View │ [2]: 3D Iso │ [ESC]: Exit"
            else:  # FIRST_PERSON
                ctrl_str = "[W/S]: Forward/Back │ [A/D]: Turn │ [P]: Path Toggle │ [HOME/H]: Recenter │ [1]: Top View │ [ESC]: Exit"
            stdscr.addstr(hud_top + 4, 2, ctrl_str[:w - 4], curses.color_pair(1) | curses.A_DIM)

            stdscr.addstr(h - 1, 0, "└" + "─" * (w - 2) + "┘", curses.color_pair(3))
        except curses.error:
            pass

        stdscr.refresh()

        # -------------------------------------------------------------
        # 4. USER INPUT PROCESSING
        # -------------------------------------------------------------
        key = stdscr.getch()
        if key == 27:  # ESC -> exit to main menu
            break

        # Universal View Mode Toggles
        elif key in (ord('v'), ord('V'), ord('1')):
            if anim_state == "NONE":
                camera_mode = "TOP"
                feedback_msg = "SWITCHED TO CENTERED TOP-DOWN MAZE DESIGN VIEW"
                feedback_color = 3
        elif key in (ord('c'), ord('C'), ord('2')):
            if anim_state == "NONE":
                camera_mode = "3D"
                feedback_msg = "SWITCHED TO 3D ISOMETRIC PHYSICAL WALL VIEW"
                feedback_color = 3
        elif key in (ord('g'), ord('G'), ord('3')):
            if anim_state == "NONE":
                camera_mode = "GATE"
                feedback_msg = "CAMERA ALIGNED TO ARCHITECTURAL ENTRANCE GATE"
                feedback_color = 7
        elif key in (ord('e'), ord('E'), ord('4')):
            if anim_state == "NONE":
                if camera_mode != "FIRST_PERSON":
                    # Smooth animated gate transition into the 3D world
                    run_gate_transition_sequence(stdscr, maze, px, py)
                    camera_mode = "FIRST_PERSON"
                    feedback_msg = "ENTERED CONSTRUCTED MAZE: FIRST-PERSON 3D PERSPECTIVE LOCKED"
                    feedback_color = 2
                else:
                    camera_mode = "TOP"
                    feedback_msg = "RETURNED TO TOP-DOWN ARCHITECTURAL VIEW"
                    feedback_color = 3

        # Restart game shortcut
        elif key in (ord('r'), ord('R')):
            # Reset player to start, reset timer
            px, py, pdir = 1, 1, 1
            camera_mode = "GATE"
            game_state = "RUNNING"
            timer_s = 30
            anim_state = "NONE"
            anim_phase = 0
            feedback_msg = "SIMULATION RESTARTED"
            feedback_color = 2

        # Solution Path Toggle [P]
        elif key in (ord('p'), ord('P')):
            show_solution = not show_solution
            feedback_msg = f"SOLUTION NAVIGATION PATH: {'ENABLED (GREEN ROUTE VISIBLE)' if show_solution else 'DISABLED (NORMAL MAZE MODE)'}"
            feedback_color = 2 if show_solution else 1

        # Debug / Analysis Mode Toggle [D]
        elif key in (ord('d'), ord('D')):
            debug_mode = not debug_mode
            dead_ends = find_dead_ends(maze)
            feedback_msg = f"ALGORITHMIC MAZE ANALYSIS: {'ACTIVE (SHOWING DEAD-ENDS & METRICS)' if debug_mode else 'DEACTIVATED (CLEAN MODE)'}"
            feedback_color = 7 if debug_mode else 1

        # Camera Recenter / Recovery [HOME] or [H]
        elif key in (curses.KEY_HOME, ord('h'), ord('H')):
            # Re-orient player to look down the open corridor or toward the exit
            dx_map = [0, 1, 0, -1]
            dy_map = [-1, 0, 1, 0]
            # Find best open direction
            best_dir = pdir
            # First check if forward is blocked
            if maze[py + dy_map[pdir]][px + dx_map[pdir]] == '#':
                # Find an open corridor neighbor
                for test_dir in range(4):
                    tx, ty = px + dx_map[test_dir], py + dy_map[test_dir]
                    if 0 <= ty < m_h and 0 <= tx < m_w and maze[ty][tx] != '#':
                        best_dir = test_dir
                        break
            pdir = best_dir
            feedback_msg = f"CAMERA RECENTERED: ORIENTED TOWARD {['NORTH', 'EAST', 'SOUTH', 'WEST'][pdir]} OPEN CORRIDOR"
            feedback_color = 2

        # Context Action: TOP & 3D DESIGN MODE
        elif camera_mode in ("TOP", "3D"):
            if key in (curses.KEY_UP, ord('w'), ord('W')):
                cursor_y = max(1, cursor_y - 1)
            elif key in (curses.KEY_DOWN, ord('s'), ord('S')):
                cursor_y = min(m_h - 2, cursor_y + 1)
            elif key in (curses.KEY_LEFT, ord('a'), ord('A')):
                cursor_x = max(1, cursor_x - 1)
            elif key in (curses.KEY_RIGHT, ord('d'), ord('D')):
                cursor_x = min(m_w - 2, cursor_x + 1)
            elif key in (ord(' '), 10, 13):  # SPACE or ENTER
                # Protect Start and Exit gates
                if (cursor_x, cursor_y) in ((1, 1), (m_w - 2, m_h - 2)):
                    feedback_msg = "PROTECTED GATE: CANNOT OVERWRITE START (S) OR EXIT (E) PORTAL"
                    feedback_color = 6
                else:
                    target_val = '#' if maze[cursor_y][cursor_x] != '#' else '.'
                    prev_val = maze[cursor_y][cursor_x]

                    # Test placement against solvability contract
                    maze[cursor_y][cursor_x] = target_val
                    if target_val == '#' and not is_path_open(maze):
                        # Revert illegal blocking move
                        maze[cursor_y][cursor_x] = prev_val
                        feedback_msg = "INVALID WALL: PLACEMENT WOULD COMPLETELY SEAL START-TO-EXIT ROUTE"
                        feedback_color = 6
                    else:
                        dead_ends = find_dead_ends(maze)
                        if target_val == '#':
                            feedback_msg = f"3D WALL CONSTRUCTED AT [{cursor_y:02d}, {cursor_x:02d}]. INTEGRITY: VERIFIED"
                            feedback_color = 2
                        else:
                            feedback_msg = f"WALL REMOVED AT [{cursor_y:02d}, {cursor_x:02d}]. CORRIDOR EXPANDED"
                            feedback_color = 7

        # Context Action: GATE MODE
        elif camera_mode == "GATE":
            if key in (10, 13, ord(' ')):  # ENTER / SPACE -> step into maze
                run_gate_transition_sequence(stdscr, maze, px, py)
                camera_mode = "FIRST_PERSON"
                feedback_msg = "PASSED THROUGH PORTAL INTO LIVE FIRST-PERSON 3D NAVIGATION"
                feedback_color = 2

        # Context Action: FIRST-PERSON NAVIGATION MODE
        elif camera_mode == "FIRST_PERSON" and anim_state == "NONE":
            dx_map = [0, 1, 0, -1]
            dy_map = [-1, 0, 1, 0]

            if key in (ord('w'), ord('W'), curses.KEY_UP):
                dir_name = ["UP", "RIGHT", "DOWN", "LEFT"][pdir]
                hw_resp = fpga_hw.step_maze_runner(px, py, dir_name) if fpga_hw else {"hardware_active": False}
                nx = px + dx_map[pdir]
                ny = py + dy_map[pdir]

                # If FPGA hardware is online, use its authoritative arbitration
                if hw_resp.get("hardware_active"):
                    can_move = hw_resp.get("fpga_move_valid", False)
                    hw_source = f"[FPGA FSM:{hw_resp.get('fpga_state', 'OK')}]"
                else:
                    can_move = (0 <= ny < m_h and 0 <= nx < m_w and maze[ny][nx] != '#')
                    hw_source = "[SOFTWARE]"

                if can_move:
                    px, py = nx, ny
                    feedback_msg = f"ADVANCED TO CELL ({px:02d}, {py:02d}) {hw_source} │ REMAINING: {exit_dist:02d} CELLS"
                    feedback_color = 2 if (px, py) in solution_set else 1
                else:
                    is_boundary = (nx <= 0 or nx >= m_w - 1 or ny <= 0 or ny >= m_h - 1)
                    feedback_msg = f"COLLISION {hw_source}: {'OUTER BOUNDARY LIMIT' if is_boundary else 'INNER PARTITION WALL'}"
                    feedback_color = 6
            elif key in (ord('s'), ord('S'), curses.KEY_DOWN):
                rev_dir = (pdir + 2) % 4
                dir_name = ["UP", "RIGHT", "DOWN", "LEFT"][rev_dir]
                if fpga_hw:
                    hw_resp = fpga_hw.step_maze_runner(px, py, dir_name)
                else:
                    hw_resp = {"hardware_active": False}
                nx = px - dx_map[pdir]
                ny = py - dy_map[pdir]

                if hw_resp.get("hardware_active"):
                    can_move = hw_resp.get("fpga_move_valid", False)
                    hw_source = f"[FPGA FSM:{hw_resp.get('fpga_state', 'OK')}]"
                else:
                    can_move = (0 <= ny < m_h and 0 <= nx < m_w and maze[ny][nx] != '#')
                    hw_source = "[SOFTWARE]"

                if can_move:
                    px, py = nx, ny
                    feedback_msg = f"REVERSED TO CELL ({px:02d}, {py:02d}) {hw_source} │ REMAINING: {exit_dist:02d} CELLS"
                    feedback_color = 1
                else:
                    feedback_msg = f"COLLISION {hw_source}: SOLID WALL BEHIND"
                    feedback_color = 6
            elif key in (ord('a'), ord('A'), curses.KEY_LEFT):
                pdir = (pdir - 1) % 4
                feedback_msg = f"TURNED LEFT → HEADING {['NORTH', 'EAST', 'SOUTH', 'WEST'][pdir]}"
                feedback_color = 3
            elif key in (ord('d'), ord('D'), curses.KEY_RIGHT):
                pdir = (pdir + 1) % 4
                feedback_msg = f"TURNED RIGHT → HEADING {['NORTH', 'EAST', 'SOUTH', 'WEST'][pdir]}"
                feedback_color = 3

        time.sleep(0.035)  # Smooth operational rate
