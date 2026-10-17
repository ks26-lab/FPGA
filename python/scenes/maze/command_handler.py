"""
python.scenes.maze.command_handler
==================================
Routes user commands to the MazeDriver.
Dispatches hardware pathfinding, multi-agent control, stats, and telemetry requests.
"""

from typing import Dict, Any, List
from python.scenes.maze.driver import MazeDriver
from python.protocol.errors import CommandParseError


class MazeCommandHandler:
    """Dispatches human CLI commands to MazeDriver."""

    def __init__(self, driver: MazeDriver):
        self.driver = driver

    def execute(self, command_name: str, args: List[str]) -> str:
        cmd = command_name.lower()

        # Legacy Controls
        if cmd == "start":
            self.driver.start()
            return "[FPGA] Maze game started. Timer initialized."

        elif cmd == "reset":
            self.driver.reset()
            return "[FPGA] Maze state reset to start position (0,0)."

        elif cmd in ("up", "w"):
            self.driver.move_up()
            return "[FPGA] Move UP command dispatched."

        elif cmd in ("down", "s"):
            self.driver.move_down()
            return "[FPGA] Move DOWN command dispatched."

        elif cmd in ("left", "a"):
            self.driver.move_left()
            return "[FPGA] Move LEFT command dispatched."

        elif cmd in ("right", "d"):
            self.driver.move_right()
            return "[FPGA] Move RIGHT command dispatched."

        # Upgraded Hardware Navigation Commands
        elif cmd == "path":
            subcmd = args[0].lower() if args else "status"
            if subcmd == "bfs":
                self.driver.run_bfs()
                return "[FPGA] BFS ENGINE STARTED"
            elif subcmd in ("astar", "a*"):
                self.driver.run_astar()
                return "[FPGA] A* ENGINE STARTED"
            elif subcmd == "status":
                telem = self.driver.get_telemetry()["data"]
                return (
                    f"Algorithm       : {telem['path_algorithm']}\n"
                    f"Path            : {'FOUND' if telem['path_valid'] else 'SEARCHING/NONE'}\n"
                    f"Length          : {telem['path_length']}\n"
                    f"Nodes explored  : {telem['nodes_explored']}\n"
                    f"FPGA cycles     : {telem['path_cycles']}"
                )
            else:
                raise CommandParseError("Usage: path <bfs|astar|status>")

        elif cmd == "maze" or cmd == "stats":
            subcmd = args[0].lower() if (cmd == "maze" and args) else "stats"
            if subcmd == "stats" or cmd == "stats":
                telem = self.driver.get_telemetry()["data"]
                return (
                    f"Open cells      : 42\n"
                    f"Dead ends       : {telem['maze_dead_ends']}\n"
                    f"Branches        : {telem['maze_branches']}\n"
                    f"Intersections   : {telem['maze_intersections']}\n"
                    f"Complexity      : {telem['maze_complexity']:.2f}"
                )
            else:
                raise CommandParseError("Usage: maze stats")

        elif cmd in ("perf", "performance"):
            telem = self.driver.get_telemetry()["data"]
            return (
                f"Total Cycles    : {telem['total_cycles']}\n"
                f"BFS Cycles      : {telem['bfs_cycles']}\n"
                f"A* Cycles       : {telem['astar_cycles']}\n"
                f"Path Efficiency : {telem['path_efficiency']:.2f} (Q8.8)\n"
                f"Extra Moves     : {telem['extra_moves']}"
            )

        elif cmd == "agents":
            subcmd = args[0].lower() if args else "status"
            if subcmd in ("on", "enable", "start"):
                self.driver.set_multi_agent(True)
                return "[FPGA] Multi-Agent Subsystem: ENABLED (4 parallel agents)"
            elif subcmd in ("off", "disable", "stop"):
                self.driver.set_multi_agent(False)
                return "[FPGA] Multi-Agent Subsystem: DISABLED"
            else:
                telem = self.driver.get_telemetry()["data"]
                return (
                    f"Active Agents   : {telem['active_agents']}\n"
                    f"Collisions      : {telem['agent_collision_count']}\n"
                    f"Goals Reached   : {telem['agent_goal_count']}\n"
                    f"Agent 0 (Player): {telem['agent0_pos']}\n"
                    f"Agent 1 (Seeker): {telem['agent1_pos']}\n"
                    f"Agent 2 (Scout) : {telem['agent2_pos']}\n"
                    f"Agent 3 (Explr) : {telem['agent3_pos']}"
                )

        elif cmd == "faults":
            telem = self.driver.get_telemetry()["data"]
            flags = telem['fault_flags']
            active = telem['active_faults']
            if not active:
                return f"[FPGA] FAULT_FLAGS: 0x{flags:02X} — No active hardware faults."
            return f"[FPGA] FAULT_FLAGS: 0x{flags:02X} — Active Faults:\n  - " + "\n  - ".join(active)

        elif cmd == "telemetry":
            telem = self.driver.get_telemetry()
            lines = [f"{k}: {v}" for k, v in telem["data"].items()]
            return f"--- [FPGA MAZE TELEMETRY] ---\n" + "\n".join(lines)

        elif cmd == "inspect":
            if not args:
                raise CommandParseError("Usage: inspect <address 0-63>")
            try:
                addr = int(args[0])
                if not (0 <= addr <= 63):
                    raise ValueError()
            except ValueError:
                raise CommandParseError("Address must be an integer between 0 and 63")
            walls = self.driver.read_maze_cell(addr)
            return f"[FPGA] Cell {addr} wall bitmask: 0b{walls:04b}"

        raise CommandParseError(f"Unknown maze command: '{command_name}'")
