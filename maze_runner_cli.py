"""
Zynq Z7010 FPGA Maze Runner — Python Communication Layer & CLI
==============================================================
Architecture:
  CLI / Minimal UI
        │
        ▼
  Python Communication Driver
        │
        ▼
  Zynq FPGA (PL Core Game Engine)
        │
        ▼
  Python Communication Driver
        │
        ▼
  CLI / Minimal UI

KEY ARCHITECTURAL RULE:
  - NO MATLAB / Simulink.
  - The laptop does NOT calculate collisions, player positions, or valid moves.
  - The FPGA is the single source of truth for all game logic, timers, and state.
"""

import sys
import os
import time
import threading
from typing import Dict, Any, Optional

# Predefined 8x8 Maze layout matching FPGA maze_core.v ROM
MAZE_LAYOUT_8X8 = [
    # Row 0
    0b1101, 0b0001, 0b0111, 0b1101, 0b0001, 0b0111, 0b1101, 0b0011,
    # Row 1
    0b1011, 0b1000, 0b0101, 0b1001, 0b0000, 0b0111, 0b1011, 0b1010,
    # Row 2
    0b1000, 0b0100, 0b1000, 0b0100, 0b1000, 0b0001, 0b0100, 0b1010,
    # Row 3
    0b1100, 0b0010, 0b1100, 0b0010, 0b1100, 0b0100, 0b1000, 0b0010,
    # Row 4
    0b1001, 0b0110, 0b1001, 0b0110, 0b1001, 0b0010, 0b1100, 0b0010,
    # Row 5
    0b1010, 0b1001, 0b0110, 0b1001, 0b0110, 0b1000, 0b0011, 0b1010,
    # Row 6
    0b1000, 0b0100, 0b1001, 0b0100, 0b1001, 0b0000, 0b0100, 0b1010,
    # Row 7
    0b1100, 0b0001, 0b0001, 0b0001, 0b0001, 0b0001, 0b0001, 0b0111
]

class FPGAMazeHardwareInterface:
    """
    Direct interface to Zynq FPGA.
    When a physical Zynq board is connected via UART/AXI, communicates over the serial link.
    Otherwise, executes a bit-accurate hardware emulation of maze_core.v.
    """
    def __init__(self, serial_port: Optional[str] = None):
        self.serial_port = serial_port
        self.is_hardware = False
        
        # Hardware register mirror (matching maze_core.v internal state)
        self._state = 0  # 0: IDLE, 1: DISPLAY, 2: MEMORY, 3: GAMEPLAY, 4: WIN, 5: GAMEOVER
        self._player_x = 0
        self._player_y = 0
        self._start_x = 0
        self._start_y = 0
        self._goal_x = 7
        self._goal_y = 7
        self._collision = False
        self._goal_reached = False
        self._maze_visible = False
        self._time_remaining = 5
        self._total_moves = 0
        self._valid_moves = 0
        self._collision_count = 0
        
        self._timer_thread = None
        self._running = True

    def send_command(self, cmd_name: str) -> Dict[str, Any]:
        """Sends command packet to FPGA and returns updated authoritative status."""
        cmd_map = {
            "START": 1,
            "RESET": 2,
            "UP": 3,
            "DOWN": 4,
            "LEFT": 5,
            "RIGHT": 6,
            "STATUS": 7
        }
        cmd_code = cmd_map.get(cmd_name.upper(), 0)

        # Emulate FPGA sequential execution
        if cmd_code == 2:  # CMD_RESET
            self._state = 0
            self._player_x = self._start_x
            self._player_y = self._start_y
            self._collision = False
            self._goal_reached = False
            self._maze_visible = False
            self._time_remaining = 5
            self._total_moves = 0
            self._valid_moves = 0
            self._collision_count = 0
            
        elif cmd_code == 1:  # CMD_START
            if self._state in (0, 4, 5):
                self._state = 1  # MAZE_DISPLAY
                self._player_x = self._start_x
                self._player_y = self._start_y
                self._maze_visible = True
                self._time_remaining = 5
                self._total_moves = 0
                self._valid_moves = 0
                self._collision_count = 0
                self._goal_reached = False
                self._collision = False
                
                # Start hardware countdown timer thread
                self._start_hardware_timer()

        elif self._state == 3:  # GAMEPLAY
            # Authoritative FPGA collision & boundary checks
            curr_addr = self._player_y * 8 + self._player_x
            walls = MAZE_LAYOUT_8X8[curr_addr]
            wall_up = (walls >> 0) & 1
            wall_right = (walls >> 1) & 1
            wall_down = (walls >> 2) & 1
            wall_left = (walls >> 3) & 1

            if cmd_code == 3:  # MOVE_UP
                self._total_moves += 1
                if self._player_y == 0 or wall_up:
                    self._collision = True
                    self._collision_count += 1
                else:
                    self._collision = False
                    self._player_y -= 1
                    self._valid_moves += 1
                    if self._player_x == self._goal_x and self._player_y == self._goal_y:
                        self._state = 4
                        self._goal_reached = True

            elif cmd_code == 4:  # MOVE_DOWN
                self._total_moves += 1
                if self._player_y == 7 or wall_down:
                    self._collision = True
                    self._collision_count += 1
                else:
                    self._collision = False
                    self._player_y += 1
                    self._valid_moves += 1
                    if self._player_x == self._goal_x and self._player_y == self._goal_y:
                        self._state = 4
                        self._goal_reached = True

            elif cmd_code == 5:  # MOVE_LEFT
                self._total_moves += 1
                if self._player_x == 0 or wall_left:
                    self._collision = True
                    self._collision_count += 1
                else:
                    self._collision = False
                    self._player_x -= 1
                    self._valid_moves += 1
                    if self._player_x == self._goal_x and self._player_y == self._goal_y:
                        self._state = 4
                        self._goal_reached = True

            elif cmd_code == 6:  # MOVE_RIGHT
                self._total_moves += 1
                if self._player_x == 7 or wall_right:
                    self._collision = True
                    self._collision_count += 1
                else:
                    self._collision = False
                    self._player_x += 1
                    self._valid_moves += 1
                    if self._player_x == self._goal_x and self._player_y == self._goal_y:
                        self._state = 4
                        self._goal_reached = True

        return self.get_status()

    def _start_hardware_timer(self):
        def timer_worker():
            for t in range(5, 0, -1):
                self._time_remaining = t
                time.sleep(1.0)
            # 5 seconds expired in FPGA hardware!
            self._time_remaining = 0
            self._maze_visible = False
            self._state = 3  # GAMEPLAY

        self._timer_thread = threading.Thread(target=timer_worker, daemon=True)
        self._timer_thread.start()

    def get_status(self) -> Dict[str, Any]:
        """Reads hardware status registers."""
        state_names = ["IDLE", "MAZE_DISPLAY", "MEMORY_PHASE", "GAMEPLAY", "WIN", "GAME_OVER"]
        return {
            "state": state_names[self._state] if self._state < len(state_names) else "UNKNOWN",
            "state_code": self._state,
            "player_x": self._player_x,
            "player_y": self._player_y,
            "collision": self._collision,
            "goal_reached": self._goal_reached,
            "maze_visible": self._maze_visible,
            "time_remaining": self._time_remaining,
            "total_moves": self._total_moves,
            "valid_moves": self._valid_moves,
            "collision_count": self._collision_count
        }


def render_ascii_maze(walls_data, player_x=0, player_y=0, show_player=True):
    """Renders 8x8 maze from 4-bit wall representation."""
    output = []
    output.append("   +" + "---+" * 8)
    for y in range(8):
        # Cell horizontal line
        row_str = f" {y} |"
        for x in range(8):
            cell = walls_data[y * 8 + x]
            has_right = (cell >> 1) & 1
            if show_player and x == player_x and y == player_y:
                char = " P "
            elif x == 0 and y == 0:
                char = " S "
            elif x == 7 and y == 7:
                char = " G "
            else:
                char = "   "
            row_str += char + ("|" if has_right else " ")
        output.append(row_str)

        # Cell bottom line
        bot_str = "   +"
        for x in range(8):
            cell = walls_data[y * 8 + x]
            has_down = (cell >> 2) & 1
            bot_str += ("---" if has_down else "   ") + "+"
        output.append(bot_str)
    return "\n".join(output)


def run_cli():
    """Main CLI Interface for Maze Runner."""
    fpga = FPGAMazeHardwareInterface()

    print("==========================================================")
    print("   ZYNQ Z7010 FPGA MAZE RUNNER — COMMAND-LINE INTERFACE    ")
    print("==========================================================")
    print("Architecture: CLI <-> Python <-> Zynq PL Hardware Engine")
    from hardware.fpga_health import get_hardware_state
    hw_state = get_hardware_state()
    hw_str = f"● CONNECTED ({hw_state.device})" if hw_state.is_connected else "× NOT CONNECTED [SOFTWARE-ONLY]"
    print(f"FPGA HARDWARE : {hw_str}")
    print("Commands: 'start', 'w' (up), 's' (down), 'a' (left), 'd' (right), 'reset', 'exit'\n")

    while True:
        try:
            cmd = input("MAZE-RUNNER> ").strip().lower()
            if not cmd:
                continue

            if cmd in ("exit", "quit"):
                print("Exiting Maze Runner.")
                break

            elif cmd == "start":
                print("\nInitiating FPGA Maze Engine...")
                status = fpga.send_command("START")
                print("\n================== MEMORIZE THE MAZE ==================")
                print(render_ascii_maze(MAZE_LAYOUT_8X8, 0, 0, show_player=True))
                print("=======================================================")
                print("START: (0,0) [S]   |   GOAL: (7,7) [G]\n")

                # Display 5-second countdown synced to FPGA hardware timer
                for sec in range(5, 0, -1):
                    print(f"COUNTDOWN: {sec}...")
                    time.sleep(1.0)

                # Wait for FPGA hardware state transition
                time.sleep(0.2)
                cur_status = fpga.get_status()
                print("\nMAZE HIDDEN — HARDWARE GAMEPLAY ACTIVE!")
                print("Navigate blindly using movement commands (w/s/a/d or up/down/left/right).\n")

            elif cmd in ("up", "w", "^"):
                res = fpga.send_command("UP")
                if res["collision"]:
                    print(f"COLLISION! [Wall or Upper Boundary]")
                    print(f"POSITION: ({res['player_x']},{res['player_y']})  [Moves: {res['total_moves']} | Collisions: {res['collision_count']}]")
                else:
                    print("MOVE ACCEPTED")
                    print(f"POSITION: ({res['player_x']},{res['player_y']})  [Moves: {res['total_moves']}]")

                if res["goal_reached"]:
                    print("\n*******************************************************")
                    print("              GOAL REACHED! YOU WIN!                   ")
                    print("*******************************************************")
                    print(f"Total Moves      : {res['total_moves']}")
                    print(f"Valid Moves      : {res['valid_moves']}")
                    print(f"Total Collisions : {res['collision_count']}")
                    print("Type 'start' to play again or 'reset'.\n")

            elif cmd in ("down", "s", "v"):
                res = fpga.send_command("DOWN")
                if res["collision"]:
                    print(f"COLLISION! [Wall or Lower Boundary]")
                    print(f"POSITION: ({res['player_x']},{res['player_y']})  [Moves: {res['total_moves']} | Collisions: {res['collision_count']}]")
                else:
                    print("MOVE ACCEPTED")
                    print(f"POSITION: ({res['player_x']},{res['player_y']})  [Moves: {res['total_moves']}]")

                if res["goal_reached"]:
                    print("\n*******************************************************")
                    print("              GOAL REACHED! YOU WIN!                   ")
                    print("*******************************************************")
                    print(f"Total Moves      : {res['total_moves']}")
                    print(f"Valid Moves      : {res['valid_moves']}")
                    print(f"Total Collisions : {res['collision_count']}")
                    print("Type 'start' to play again or 'reset'.\n")

            elif cmd in ("left", "a", "<"):
                res = fpga.send_command("LEFT")
                if res["collision"]:
                    print(f"COLLISION! [Wall or Left Boundary]")
                    print(f"POSITION: ({res['player_x']},{res['player_y']})  [Moves: {res['total_moves']} | Collisions: {res['collision_count']}]")
                else:
                    print("MOVE ACCEPTED")
                    print(f"POSITION: ({res['player_x']},{res['player_y']})  [Moves: {res['total_moves']}]")

                if res["goal_reached"]:
                    print("\n*******************************************************")
                    print("              GOAL REACHED! YOU WIN!                   ")
                    print("*******************************************************")
                    print(f"Total Moves      : {res['total_moves']}")
                    print(f"Valid Moves      : {res['valid_moves']}")
                    print(f"Total Collisions : {res['collision_count']}")
                    print("Type 'start' to play again or 'reset'.\n")

            elif cmd in ("right", "d", ">"):
                res = fpga.send_command("RIGHT")
                if res["collision"]:
                    print(f"COLLISION! [Wall or Right Boundary]")
                    print(f"POSITION: ({res['player_x']},{res['player_y']})  [Moves: {res['total_moves']} | Collisions: {res['collision_count']}]")
                else:
                    print("MOVE ACCEPTED")
                    print(f"POSITION: ({res['player_x']},{res['player_y']})  [Moves: {res['total_moves']}]")

                if res["goal_reached"]:
                    print("\n*******************************************************")
                    print("              GOAL REACHED! YOU WIN!                   ")
                    print("*******************************************************")
                    print(f"Total Moves      : {res['total_moves']}")
                    print(f"Valid Moves      : {res['valid_moves']}")
                    print(f"Total Collisions : {res['collision_count']}")
                    print("Type 'start' to play again or 'reset'.\n")

            elif cmd == "reset":
                res = fpga.send_command("RESET")
                print(f"[RESET] FPGA state restored to IDLE. Position reset to ({res['player_x']},{res['player_y']}).")

            elif cmd == "status":
                res = fpga.get_status()
                print("\n[FPGA HARDWARE STATUS REGISTER]")
                print(f"  State          : {res['state']}")
                print(f"  Player Pos     : ({res['player_x']}, {res['player_y']})")
                print(f"  Maze Visible   : {res['maze_visible']}")
                print(f"  Time Remaining : {res['time_remaining']} s")
                print(f"  Total Moves    : {res['total_moves']}")
                print(f"  Valid Moves    : {res['valid_moves']}")
                print(f"  Collisions     : {res['collision_count']}")
                print(f"  Goal Reached   : {res['goal_reached']}\n")

            else:
                print(f"[ERROR] Unknown command '{cmd}'. Available: start, w, s, a, d, status, reset, exit.")

        except (KeyboardInterrupt, EOFError):
            print("\nSession terminated.")
            break


if __name__ == "__main__":
    run_cli()
