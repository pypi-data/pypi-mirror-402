"""Conway's Game of Life logic implementation."""

import json
import random
from typing import List, Tuple, Set


class GameGrid:
    """Manages the Game of Life grid and rules."""

    def __init__(self, width: int = 50, height: int = 50):
        """Initialize grid with given dimensions.

        Args:
            width: Grid width (default 50)
            height: Grid height (default 50)
        """
        self.width = width
        self.height = height
        self.generation = 0

        # Two sets: one for live cells, one for cell ages
        self.live_cells: Set[Tuple[int, int]] = set()
        self.cell_ages: dict[Tuple[int, int], int] = {}

    def clear(self):
        """Clear all cells from the grid."""
        self.live_cells.clear()
        self.cell_ages.clear()
        self.generation = 0

    def toggle_cell(self, x: int, y: int):
        """Toggle cell state at position (x, y).

        Args:
            x: X coordinate
            y: Y coordinate
        """
        pos = (x, y)
        if pos in self.live_cells:
            self.live_cells.remove(pos)
            self.cell_ages.pop(pos, None)
        else:
            self.live_cells.add(pos)
            self.cell_ages[pos] = 1

    def is_alive(self, x: int, y: int) -> bool:
        """Check if cell at (x, y) is alive.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if cell is alive, False otherwise
        """
        return (x, y) in self.live_cells

    def get_age(self, x: int, y: int) -> int:
        """Get age of cell at (x, y).

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Age of cell (0 if dead, 1-5+ if alive)
        """
        return min(self.cell_ages.get((x, y), 0), 5)

    def count_neighbors(self, x: int, y: int) -> int:
        """Count live neighbors of cell at (x, y) with toroidal wrapping.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Number of live neighbors (0-8)
        """
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                # Toroidal wrapping
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                if (nx, ny) in self.live_cells:
                    count += 1
        return count

    def step(self):
        """Advance simulation by one generation using Conway's rules."""
        new_live_cells: Set[Tuple[int, int]] = set()
        new_cell_ages: dict[Tuple[int, int], int] = {}

        # Check all live cells and their neighbors
        cells_to_check = set()
        for x, y in self.live_cells:
            cells_to_check.add((x, y))
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx = (x + dx) % self.width
                    ny = (y + dy) % self.height
                    cells_to_check.add((nx, ny))

        # Apply Conway's rules
        for x, y in cells_to_check:
            neighbors = self.count_neighbors(x, y)
            is_alive = (x, y) in self.live_cells

            # Conway's rules:
            # 1. Live cell with 2-3 neighbors survives
            # 2. Dead cell with exactly 3 neighbors becomes alive
            # 3. All other cells die or stay dead
            if is_alive and neighbors in [2, 3]:
                new_live_cells.add((x, y))
                # Increment age
                new_cell_ages[(x, y)] = self.cell_ages.get((x, y), 0) + 1
            elif not is_alive and neighbors == 3:
                new_live_cells.add((x, y))
                # New cell starts at age 1
                new_cell_ages[(x, y)] = 1

        self.live_cells = new_live_cells
        self.cell_ages = new_cell_ages
        self.generation += 1

    def randomize(self, density: float = 0.25):
        """Fill grid with random live cells.

        Args:
            density: Proportion of cells to make alive (0.0-1.0)
        """
        self.clear()
        for x in range(self.width):
            for y in range(self.height):
                if random.random() < density:
                    self.live_cells.add((x, y))
                    self.cell_ages[(x, y)] = 1

    @property
    def population(self) -> int:
        """Get current number of live cells.

        Returns:
            Number of live cells
        """
        return len(self.live_cells)

    def save_to_file(self, filename: str):
        """Save grid state to JSON file.

        Args:
            filename: Path to save file
        """
        data = {
            "width": self.width,
            "height": self.height,
            "generation": self.generation,
            "live_cells": list(self.live_cells)
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filename: str):
        """Load grid state from JSON file.

        Args:
            filename: Path to load file
        """
        with open(filename, 'r') as f:
            data = json.load(f)

        self.width = data.get("width", 50)
        self.height = data.get("height", 50)
        self.generation = data.get("generation", 0)
        self.live_cells = set(tuple(cell) for cell in data.get("live_cells", []))

        # Reset ages for loaded cells
        self.cell_ages = {cell: 1 for cell in self.live_cells}
