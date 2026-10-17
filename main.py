import curses
from cli.menu import run_menu
from environments.undersea import launch_undersea
from environments.city import launch_city
from environments.maze import launch_maze
from environments.solar import launch_solar
from environments.space import launch_space

def main(stdscr):
    # Setup curses settings
    curses.curs_set(0) # Hide cursor
    stdscr.nodelay(False) # Blocking input
    
    # Initialize default colors for the terminal
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_WHITE, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_GREEN, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    curses.init_pair(7, curses.COLOR_BLUE, -1)
    
    # Define environments
    environments = [
        {"id": "UNDERSEA", "name": "UNDERSEA WORLD", "launcher": launch_undersea},
        {"id": "CITY", "name": "SMART CITY", "launcher": launch_city},
        {"id": "MAZE", "name": "3D MAZE", "launcher": launch_maze},
        {"id": "SOLAR", "name": "SOLAR PANEL", "launcher": launch_solar},
        {"id": "SPACE", "name": "SPACE HABITAT", "launcher": launch_space}
    ]
    
    while True:
        # Pass control to the menu system
        selected_env = run_menu(stdscr, environments)
        
        if selected_env is None:
            break # ESC pressed, exit loop and application
            
        # Clear screen before launching the environment
        stdscr.clear()
        stdscr.refresh()
        
        # Launch environment
        selected_env["launcher"](stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
