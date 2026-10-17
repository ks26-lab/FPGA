"""
tests.test_maze_parallel_blocks
================================
Comprehensive verification test suite verifying all upgraded FPGA hardware engines:
- Parallel collision checking & neighbor generation
- Hardware BFS pathfinding engine
- Hardware A* pathfinding accelerator
- Distance map & route quality evaluation
- Dead-end, branch & intersection detection
- Maze difficulty analyzer
- Multi-agent 4-agent parallel subsystem
- Fault detector & hardware performance counters
- 32-register AXI telemetry decoding
"""

import unittest
import sys
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.backends.laptop_fpga_backend import LaptopFPGAEmulator
from python.core.backend_adapter import BackendAXIAdapter
from python.scenes.maze.driver import MazeDriver
from python.scenes.maze.command_handler import MazeCommandHandler
from python.scenes.maze.register_map import (
    BASE_ADDRESS,
    ALGO_BFS,
    ALGO_ASTAR,
    FAULT_POSITION,
    FAULT_GOAL_FAULT,
)


class TestMazeParallelBlocks(unittest.TestCase):

    def setUp(self):
        self.emulator = LaptopFPGAEmulator(enable_autonomous_clock=False)
        self.emulator.open()
        self.adapter = BackendAXIAdapter(self.emulator, base_addr=BASE_ADDRESS)
        self.driver = MazeDriver(self.adapter, base_address=BASE_ADDRESS)
        self.handler = MazeCommandHandler(self.driver)
        self.driver.reset()

    def tearDown(self):
        self.emulator.close()

    def test_legacy_gameplay_and_backward_compatibility(self):
        """Verify legacy start, reset, movement and FSM transitions remain intact."""
        telem = self.driver.get_telemetry()
        self.assertEqual(telem["state"], "IDLE")
        self.assertEqual(telem["data"]["player_x"], 0)
        self.assertEqual(telem["data"]["player_y"], 0)

        # Start game
        self.driver.start()
        telem = self.driver.get_telemetry()
        self.assertIn(telem["state"], ("MAZE_DISPLAY", "GAMEPLAY"))
        self.assertTrue(telem["data"]["maze_visible"])

        # Reset game
        self.driver.reset()
        telem = self.driver.get_telemetry()
        self.assertEqual(telem["state"], "IDLE")
        self.assertEqual(telem["data"]["total_moves"], 0)

    def test_parallel_collision_and_neighbor_engine(self):
        """Verify parallel 4-way direction validity and topology classification."""
        self.driver.start()
        telem = self.driver.get_telemetry()
        d = telem["data"]

        # Cell (0,0) in 8x8 maze:
        # Check that neighbor flags are booleans and neighbor count matches sum
        expected_cnt = (1 if d["valid_up"] else 0) + (1 if d["valid_right"] else 0) + \
                       (1 if d["valid_down"] else 0) + (1 if d["valid_left"] else 0)
        self.assertEqual(d["neighbor_count"], expected_cnt)

        # (0,0) is at top-left boundary, valid_up and valid_left must be False
        self.assertFalse(d["valid_up"])
        self.assertFalse(d["valid_left"])

    def test_hardware_bfs_pathfinding(self):
        """Verify FPGA hardware BFS finds shortest path, nodes explored, and cycle counters."""
        self.driver.start()
        self.driver.run_bfs()

        telem = self.driver.get_telemetry()
        d = telem["data"]

        self.assertEqual(d["path_algorithm"], "BFS")
        self.assertTrue(d["path_valid"], "Hardware BFS must find a valid path to goal")
        self.assertTrue(d["path_complete"])
        self.assertGreater(d["path_length"], 0, "BFS shortest path length must be positive")
        self.assertGreater(d["nodes_explored"], 0, "BFS explored nodes must be non-zero")
        self.assertGreater(d["path_cycles"], 0, "BFS hardware cycles must be non-zero")
        self.assertGreater(d["bfs_cycles"], 0, "BFS performance counter must be incremented")

    def test_hardware_astar_pathfinding_parity(self):
        """Verify FPGA hardware A* achieves identical shortest path length as BFS."""
        self.driver.start()

        # Run BFS first
        self.driver.run_bfs()
        bfs_len = self.driver.get_telemetry()["data"]["path_length"]

        # Run A*
        self.driver.run_astar()
        telem = self.driver.get_telemetry()
        d = telem["data"]

        self.assertEqual(d["path_algorithm"], "A*")
        self.assertTrue(d["path_valid"])
        self.assertEqual(d["path_length"], bfs_len, "A* path length must match BFS shortest path length")
        self.assertGreater(d["nodes_explored"], 0)
        self.assertGreater(d["path_cycles"], 0)
        self.assertGreater(d["astar_cycles"], 0)

    def test_distance_map_and_route_quality_analyzer(self):
        """Verify dynamic distance to goal, path efficiency fixed-point, and extra moves."""
        self.driver.start()
        telem = self.driver.get_telemetry()
        d = telem["data"]

        # Player at (0,0), Goal at (7,7) -> Manhattan distance = 14
        self.assertEqual(d["current_distance"], 14)
        self.assertGreaterEqual(d["path_efficiency"], 0.0)
        self.assertLessEqual(d["path_efficiency"], 1.0)
        self.assertIn(d["route_status"], ("OPTIMAL", "GOOD", "INEFFICIENT"))

    def test_maze_difficulty_engine(self):
        """Verify maze dead-ends, branches, intersections, and complexity score."""
        telem = self.driver.get_telemetry()
        d = telem["data"]

        self.assertGreater(d["maze_dead_ends"], 0, "8x8 maze must contain dead-ends")
        self.assertGreater(d["maze_branches"], 0, "8x8 maze must contain branches")
        self.assertGreater(d["maze_intersections"], 0, "8x8 maze must contain intersections")
        self.assertGreater(d["maze_complexity"], 0.0, "Complexity score must be non-zero")

    def test_multi_agent_parallel_engine(self):
        """Verify parallel 4-agent tracking subsystem."""
        # Enable multi-agent engine
        self.driver.set_multi_agent(True)
        self.emulator.run_ticks(10)

        telem = self.driver.get_telemetry()
        d = telem["data"]

        self.assertEqual(d["active_agents"], 4)
        self.assertIsInstance(d["agent0_pos"], tuple)
        self.assertIsInstance(d["agent1_pos"], tuple)
        self.assertIsInstance(d["agent2_pos"], tuple)
        self.assertIsInstance(d["agent3_pos"], tuple)

        # Disable multi-agent
        self.driver.set_multi_agent(False)
        telem = self.driver.get_telemetry()
        self.assertFalse(self.driver.read32(0x58) & 1)

    def test_fault_detection_engine(self):
        """Verify hardware fault flags mask behavior."""
        telem = self.driver.get_telemetry()
        d = telem["data"]
        # Normal operation: No faults
        self.assertEqual(d["fault_flags"], 0)
        self.assertEqual(len(d["active_faults"]), 0)

    def test_cli_command_handler(self):
        """Verify CLI dispatch of all upgraded commands."""
        # path bfs
        res = self.handler.execute("path", ["bfs"])
        self.assertIn("BFS ENGINE STARTED", res)

        # path astar
        res = self.handler.execute("path", ["astar"])
        self.assertIn("A* ENGINE STARTED", res)

        # path status
        res = self.handler.execute("path", ["status"])
        self.assertIn("Algorithm", res)
        self.assertIn("Length", res)

        # maze stats
        res = self.handler.execute("maze", ["stats"])
        self.assertIn("Open cells", res)
        self.assertIn("Dead ends", res)

        # performance
        res = self.handler.execute("performance", [])
        self.assertIn("Total Cycles", res)

        # agents
        res = self.handler.execute("agents", ["on"])
        self.assertIn("ENABLED", res)
        res = self.handler.execute("agents", ["off"])
        self.assertIn("DISABLED", res)

        # faults
        res = self.handler.execute("faults", [])
        self.assertIn("FAULT_FLAGS", res)


if __name__ == "__main__":
    unittest.main()
