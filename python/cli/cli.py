"""
python.cli.cli
==============
Interactive Universal Command-Line Interface for all 5 FPGA scenes.
"""

import sys
import os

from python.core.runtime import SystemRuntime
from python.cli.command_parser import UniversalCommandParser
from python.cli.renderer import CLIRenderer
from python.protocol.errors import (
    FPGACommunicationError,
    CommandParseError,
    SceneNotSelectedError,
    HardwareUnavailableError,
)


class UniversalCLI:
    """Universal interactive console for Zynq FPGA Control System."""

    def __init__(self, runtime: SystemRuntime):
        self.runtime = runtime
        self.running = True

    def run(self):
        """Main interactive loop."""
        is_hw = (self.runtime.mode.value == "HARDWARE")
        print(CLIRenderer.render_banner(is_hardware=is_hw))

        while self.running:
            try:
                active_scene = self.runtime.scene_mgr.active_scene
                prompt_tag = f"[{active_scene.value}]" if active_scene else ""
                prompt = f"FPGA{prompt_tag}> "

                user_input = input(prompt).strip()
                if not user_input:
                    continue

                cmd, args = UniversalCommandParser.parse_line(user_input)

                # 1. Exit Commands
                if cmd in ("exit", "quit"):
                    print("Shutting down FPGA Runtime...")
                    self.running = False
                    break

                # 2. Help
                elif cmd == "help":
                    print(CLIRenderer.render_help(active_scene=active_scene))

                # 3. Scene Selection
                elif cmd == "scene":
                    if not args:
                        print("Usage: scene <solar|maze|mars|underwater|traffic>")
                        continue
                    try:
                        msg = self.runtime.scene_mgr.select_scene(args[0])
                        print(msg)
                    except ValueError as e:
                        print(f"ERROR: {str(e)}")

                # 4. Deselect Scene (back)
                elif cmd == "back":
                    self.runtime.scene_mgr.active_scene = None
                    print("[SCENE] Deselected active scene. Back to top level.")

                # 5. Status Query
                elif cmd == "status":
                    try:
                        telem = self.runtime.scene_mgr.get_active_telemetry()
                        print(CLIRenderer.render_telemetry(telem))
                    except SceneNotSelectedError as e:
                        print(f"ERROR: {str(e)}")

                # 6. Reset
                elif cmd == "reset" and len(args) == 0:
                    try:
                        if self.runtime.scene_mgr.active_scene is None:
                            print("ERROR: No active scene. Use 'scene <name>' first.")
                        else:
                            driver = self.runtime.scene_mgr.get_driver(self.runtime.scene_mgr.active_scene)
                            driver.reset()
                            print(f"[FPGA] Reset pulse dispatched to {self.runtime.scene_mgr.active_scene.value} peripheral.")
                    except FPGACommunicationError as e:
                        print(f"ERROR: {str(e)}")

                # 7. Debug Controls
                elif cmd == "debug":
                    if not args:
                        print("Usage: debug <on|off|registers>")
                    elif args[0].lower() == "registers":
                        try:
                            dbg = self.runtime.scene_mgr.get_active_debug_registers()
                            print(CLIRenderer.render_debug_registers(dbg))
                        except SceneNotSelectedError as e:
                            print(f"ERROR: {str(e)}")
                    elif args[0].lower() == "on":
                        self.runtime.set_debug(True)
                        print("[DEBUG] Hardware register trace enabled.")
                    elif args[0].lower() == "off":
                        self.runtime.set_debug(False)
                        print("[DEBUG] Hardware register trace disabled.")
                    else:
                        print("Usage: debug <on|off|registers>")

                # 8. Scene-Specific Commands
                else:
                    try:
                        resp = self.runtime.scene_mgr.execute_command(cmd, args)
                        print(resp)
                        if self.runtime.debug_mode:
                            dbg = self.runtime.scene_mgr.get_active_debug_registers()
                            print(CLIRenderer.render_debug_registers(dbg))
                    except (CommandParseError, SceneNotSelectedError) as e:
                        print(f"ERROR: {str(e)}")
                    except FPGACommunicationError as e:
                        print(f"HARDWARE ERROR: {str(e)}")

            except (KeyboardInterrupt, EOFError):
                print("\nSession interrupted. Exiting.")
                break
            except Exception as ex:
                print(f"UNHANDLED EXCEPTION: {str(ex)}")

        self.runtime.shutdown()
