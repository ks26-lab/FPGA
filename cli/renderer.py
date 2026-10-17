import curses

def draw_menu(stdscr, environments, selected_idx):
    """
    Renders the menu centered dynamically on the screen.
    """
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    # Render Subdued Header
    title = "SIMULATION ENVIRONMENT CONTROL"
    try:
        stdscr.addstr(h // 5, w // 2 - len(title) // 2, title, curses.A_DIM)
    except curses.error:
        pass # Ignore errors if terminal is too small
        
    # Calculate vertical start position for menu items
    start_y = h // 2 - len(environments) // 2
    
    # Render Menu Options
    for idx, env in enumerate(environments):
        name = env["name"]
        y = start_y + idx
        
        if idx == selected_idx:
            # Visually dominant selection effect
            text = f">>> {name} <<<"
            x = w // 2 - len(text) // 2
            try:
                stdscr.attron(curses.A_BOLD | curses.color_pair(1))
                stdscr.addstr(y, x, text)
                stdscr.attroff(curses.A_BOLD | curses.color_pair(1))
            except curses.error:
                pass
        else:
            # Subdued unselected effect
            text = f"    {name}    "
            x = w // 2 - len(text) // 2
            try:
                stdscr.addstr(y, x, text, curses.A_DIM)
            except curses.error:
                pass
                
    # Render Subtle Footer
    footer = "↑ ↓  SELECT        ENTER  INITIALIZE        ESC  EXIT"
    try:
        stdscr.addstr(h - 2, w // 2 - len(footer) // 2, footer, curses.A_DIM)
    except curses.error:
        pass

    # Render Authoritative EDGE ZYNQ Z7010 Hardware Status
    try:
        from hardware.fpga_health import render_hardware_status_box, format_hardware_badge
        badge_txt, badge_col = format_hardware_badge()
        stdscr.addstr(h // 5 - 2, w // 2 - len(badge_txt) // 2, badge_txt, curses.color_pair(badge_col) | curses.A_BOLD)

        hw_box = render_hardware_status_box(width=38)
        box_x = max(2, w - 42)
        box_y = max(2, h // 5)
        if w > 85 and h > 20:
            for i, (line, col) in enumerate(hw_box):
                if box_y + i < h - 3:
                    stdscr.addstr(box_y + i, box_x, line, curses.color_pair(col) | (curses.A_BOLD if col in (2, 5) else curses.A_NORMAL))
    except Exception:
        pass

    stdscr.refresh()
