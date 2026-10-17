import curses
from cli.renderer import draw_menu
from cli.input_handler import get_input

def run_menu(stdscr, environments):
    """
    Coordinates the rendering and input handling for the main menu.
    """
    current_selection = 0
    
    while True:
        # 1. Render the current state
        draw_menu(stdscr, environments, current_selection)
        
        # 2. Wait for user input
        action = get_input(stdscr)
        
        # 3. Handle the input event
        if action == "UP":
            current_selection = max(0, current_selection - 1)
        elif action == "DOWN":
            current_selection = min(len(environments) - 1, current_selection + 1)
        elif action == "ENTER":
            return environments[current_selection]
        elif action == "ESC":
            return None
        elif action == "RESIZE":
            # Handled inherently by redrawing the menu on the next tick
            pass
