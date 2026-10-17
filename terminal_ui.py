import curses
import os
import sys

# Set a global environment variable to explicitly declare software mode
os.environ["V_SPACE_SOFTWARE_ONLY"] = "1"

# A Mock FPGA Interface to inject into environments
class SoftwareOnlyFPGAInterface:
    def __init__(self):
        pass

    @property
    def is_hardware_active(self) -> bool:
        return False

    def get_status_badge(self):
        return ("[× SOFTWARE VISUALIZATION MODE — FPGA NOT REQUIRED]", "RED")

    def step_undersea_probe(self, *args, **kwargs):
        return {
            "hardware_active": False,
            "source": "SOFTWARE_VISUALIZATION",
            "fpga_depth": None,
            "fpga_velocity": None,
            "fpga_displacement_x": None,
            "fpga_thrust": None,
            "fpga_state": "SOFTWARE_ONLY",
            "fpga_collision": None,
            "latency_ms": None
        }

    def step_solar_gimbal(self, *args, **kwargs):
        return {
            "hardware_active": False,
            "source": "SOFTWARE_VISUALIZATION",
            "fpga_azimuth_error": None,
            "fpga_elevation_error": None,
            "fpga_actuator_az": None,
            "fpga_actuator_el": None,
            "fpga_state": "SOFTWARE_ONLY",
            "latency_ms": None
        }

    def step_traffic_grid(self, *args, **kwargs):
        return {
            "hardware_active": False,
            "source": "SOFTWARE_VISUALIZATION",
            "fpga_signal_phase": None,
            "fpga_green_time_s": None,
            "fpga_congestion_score": None,
            "fpga_state": "SOFTWARE_ONLY",
            "fpga_queue_north": None,
            "fpga_queue_south": None,
            "fpga_queue_east": None,
            "fpga_queue_west": None,
            "fpga_total_queue": None,
            "latency_ms": None
        }

    def step_mars_habitat(self, *args, **kwargs):
        return {
            "hardware_active": False,
            "source": "SOFTWARE_VISUALIZATION",
            "fpga_section_A": None,
            "fpga_section_B": None,
            "fpga_link": None,
            "fpga_landing_stage": None,
            "latency_ms": None
        }

    def step_maze_runner(self, *args, **kwargs):
        return {
            "hardware_active": False,
            "source": "SOFTWARE_VISUALIZATION",
            "fpga_move_valid": None,
            "fpga_collision": None,
            "fpga_timer_s": None,
            "fpga_state": "SOFTWARE_ONLY",
            "latency_ms": None
        }


# Inject the mock factory into the hardware module namespace
# This is a precaution, though we use explicit injection via kwargs
try:
    import hardware.fpga_interface
    
    # Overwrite the factory function
    def _mock_get_fpga_interface():
        return SoftwareOnlyFPGAInterface()
    
    hardware.fpga_interface.get_fpga_interface = _mock_get_fpga_interface
    hardware.fpga_interface.FPGAHardwareInterface = SoftwareOnlyFPGAInterface
except ImportError:
    pass


# Now we can safely import environments without hardware crashes
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
        {"id": "UNDERSEA", "name": "UNDERSEA WORLD (VISUALIZATION)", "launcher": launch_undersea},
        {"id": "CITY", "name": "SMART CITY (VISUALIZATION)", "launcher": launch_city},
        {"id": "MAZE", "name": "3D MAZE (VISUALIZATION)", "launcher": launch_maze},
        {"id": "SOLAR", "name": "SOLAR PANEL (VISUALIZATION)", "launcher": launch_solar},
        {"id": "SPACE", "name": "SPACE HABITAT (VISUALIZATION)", "launcher": launch_space}
    ]
    
    # Create the mock interface instance to inject
    software_fpga_hw = SoftwareOnlyFPGAInterface()
    
    while True:
        # Pass control to the menu system
        selected_env = run_menu(stdscr, environments)
        
        if selected_env is None:
            break # ESC pressed, exit loop and application
            
        # Clear screen before launching the environment
        stdscr.clear()
        stdscr.refresh()
        
        # Launch environment with explicit dependency injection
        selected_env["launcher"](stdscr, fpga_hw=software_fpga_hw)

if __name__ == "__main__":
    print("V_SPACE SOFTWARE VISUALIZATION MODE")
    print("-----------------------------------")
    print("WARNING: Hardware connectivity is explicitly disabled.")
    print("This mode is for terminal-native UI visualization only.")
    import time
    time.sleep(1.5)
    curses.wrapper(main)
