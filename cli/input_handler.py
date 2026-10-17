import curses

def get_input(stdscr):
    """
    Waits for and translates raw keyboard events into semantic actions.
    """
    key = stdscr.getch()
    
    if key == curses.KEY_UP:
        return "UP"
    elif key == curses.KEY_DOWN:
        return "DOWN"
    elif key in [curses.KEY_ENTER, 10, 13]:
        return "ENTER"
    elif key == 27: # ESC key
        return "ESC"
    elif key == curses.KEY_RESIZE:
        return "RESIZE"
        
    return "UNKNOWN"
