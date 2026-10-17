"""Deterministic 2D FrameBuffer for Terminal Simulation.

Implements the ANTI-GRAVITY / ASSET INTEGRITY MASTER INSTRUCTION:
- Frame buffer pipeline: SIMULATION -> OBJECT STATES -> WORLD FRAME -> FRAME BUFFER -> TERMINAL RENDER
- Prevents flickering, tearing, leftover characters, and ghosting
- Global cell quantization: round(anchor) applied uniformly to entire asset
- Deterministic layer ordering:
    1. Background
    2. Environment effects
    3. Large static objects
    4. Moving vessels
    5. Small objects
    6. Particles
    7. UI / Telemetry
- Differential terminal rendering for maximum performance and stability
"""

import curses
from typing import List, Optional, Tuple, Dict, Any
from cli.asset_library import CanonicalAsset


class RenderCell:
    """Single cell in the frame buffer."""
    __slots__ = ("char", "layer", "color_pair", "attrs")

    def __init__(self, char: str = " ", layer: int = 0, color_pair: int = 0, attrs: int = 0):
        self.char = char
        self.layer = layer
        self.color_pair = color_pair
        self.attrs = attrs


class FrameBuffer:
    """
    Double-buffered 2D terminal canvas ensuring atomic frame presentation.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.current_buffer: List[List[RenderCell]] = [
            [RenderCell() for _ in range(width)] for _ in range(height)
        ]
        self.prev_buffer: Optional[List[List[RenderCell]]] = None

    def resize(self, width: int, height: int) -> None:
        """Resize the buffer to new terminal dimensions."""
        if width == self.width and height == self.height:
            return
        self.width = width
        self.height = height
        self.current_buffer = [
            [RenderCell() for _ in range(width)] for _ in range(height)
        ]
        self.prev_buffer = None

    def clear(self, bg_char: str = " ") -> None:
        """Clear the current buffer for the next frame."""
        for y in range(self.height):
            for x in range(self.width):
                cell = self.current_buffer[y][x]
                cell.char = bg_char
                cell.layer = 0
                cell.color_pair = 0
                cell.attrs = 0

    def draw_text(
        self,
        y: int,
        x: int,
        text: str,
        layer: int = 7,
        color_pair: int = 0,
        attrs: int = 0
    ) -> None:
        """Draw string text into the buffer at the specified layer."""
        if y < 0 or y >= self.height:
            return
        for i, ch in enumerate(text):
            target_x = x + i
            if 0 <= target_x < self.width:
                cell = self.current_buffer[y][target_x]
                if layer >= cell.layer:
                    cell.char = ch
                    cell.layer = layer
                    cell.color_pair = color_pair
                    cell.attrs = attrs

    def blit_asset(
        self,
        asset: CanonicalAsset,
        world_x: float,
        world_y: float,
        variant: Optional[str] = None,
        layer: int = 4,
        color_pair: int = 0,
        attrs: int = 0,
        preserve_internal_spaces: bool = True
    ) -> bool:
        """
        Blit a complete canonical asset onto the frame buffer as a single rigid unit.

        Rules enforced:
        - Quantization: Entire asset is offset by round(world_x - anchor_x)
        - Invariant 1: One object = one rigid visual unit
        - Invariant 2: Dimensions do not change during movement
        - Invariant 19: Higher layers overwrite lower layers deterministically
        """
        lines = asset.get_lines(variant)
        
        # Calculate screen-space base position from anchor point
        base_x = int(round(world_x - asset.anchor_x))
        base_y = int(round(world_y - asset.anchor_y))

        # Check if asset completely outside screen
        if (
            base_x + asset.width <= 0 or base_x >= self.width or
            base_y + asset.height <= 0 or base_y >= self.height
        ):
            return False

        for row_idx, line in enumerate(lines):
            target_y = base_y + row_idx
            if 0 <= target_y < self.height:
                for col_idx, char in enumerate(line):
                    target_x = base_x + col_idx
                    if 0 <= target_x < self.width:
                        # If space: only draw if non-transparent internal whitespace
                        if char == " " and not preserve_internal_spaces:
                            continue
                        cell = self.current_buffer[target_y][target_x]
                        if layer >= cell.layer:
                            cell.char = char
                            cell.layer = layer
                            cell.color_pair = color_pair
                            cell.attrs = attrs
        return True

    def flush_to_curses(self, stdscr, force_redraw: bool = False) -> None:
        """
        Diff and render buffer to curses screen.
        Only updates characters that actually changed to eliminate flicker.
        """
        for y in range(self.height):
            for x in range(self.width):
                curr = self.current_buffer[y][x]
                # If force redraw or cell changed compared to previous frame
                if (
                    force_redraw or 
                    self.prev_buffer is None or 
                    self.prev_buffer[y][x].char != curr.char or
                    self.prev_buffer[y][x].color_pair != curr.color_pair or
                    self.prev_buffer[y][x].attrs != curr.attrs
                ):
                    try:
                        stdscr.addstr(
                            y,
                            x,
                            curr.char,
                            curses.color_pair(curr.color_pair) | curr.attrs
                        )
                    except curses.error:
                        pass

        stdscr.refresh()

        # Save snapshot for next frame diff
        if self.prev_buffer is None:
            self.prev_buffer = [
                [RenderCell() for _ in range(self.width)] for _ in range(self.height)
            ]

        for y in range(self.height):
            for x in range(self.width):
                c = self.current_buffer[y][x]
                p = self.prev_buffer[y][x]
                p.char = c.char
                p.layer = c.layer
                p.color_pair = c.color_pair
                p.attrs = c.attrs
