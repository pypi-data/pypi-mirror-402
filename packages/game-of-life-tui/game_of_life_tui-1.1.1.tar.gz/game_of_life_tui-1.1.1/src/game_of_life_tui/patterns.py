"""Preset patterns for Game of Life."""

from typing import List, Tuple

# Pattern definitions as lists of (x, y) relative coordinates
PATTERNS = {
    "glider": [
        (1, 0),
        (2, 1),
        (0, 2),
        (1, 2),
        (2, 2),
    ],
    "blinker": [
        (0, 0),
        (1, 0),
        (2, 0),
    ],
    "toad": [
        (1, 0),
        (2, 0),
        (3, 0),
        (0, 1),
        (1, 1),
        (2, 1),
    ],
    "beacon": [
        (0, 0),
        (1, 0),
        (0, 1),
        (3, 2),
        (2, 3),
        (3, 3),
    ],
    "pulsar": [
        # Top section
        (2, 0), (3, 0), (4, 0), (8, 0), (9, 0), (10, 0),
        # Upper middle
        (0, 2), (5, 2), (7, 2), (12, 2),
        (0, 3), (5, 3), (7, 3), (12, 3),
        (0, 4), (5, 4), (7, 4), (12, 4),
        # Center gap
        (2, 5), (3, 5), (4, 5), (8, 5), (9, 5), (10, 5),
        (2, 7), (3, 7), (4, 7), (8, 7), (9, 7), (10, 7),
        # Lower middle
        (0, 8), (5, 8), (7, 8), (12, 8),
        (0, 9), (5, 9), (7, 9), (12, 9),
        (0, 10), (5, 10), (7, 10), (12, 10),
        # Bottom section
        (2, 12), (3, 12), (4, 12), (8, 12), (9, 12), (10, 12),
    ],
}


def place_pattern(grid, pattern_name: str, x: int, y: int):
    """Place a pattern on the grid at the specified position.

    Args:
        grid: GameGrid instance
        pattern_name: Name of pattern from PATTERNS dict
        x: X coordinate for pattern placement
        y: Y coordinate for pattern placement
    """
    if pattern_name not in PATTERNS:
        return

    pattern = PATTERNS[pattern_name]
    for dx, dy in pattern:
        # Apply toroidal wrapping
        nx = (x + dx) % grid.width
        ny = (y + dy) % grid.height
        grid.live_cells.add((nx, ny))
        grid.cell_ages[(nx, ny)] = 1


def get_pattern_names() -> List[str]:
    """Get list of available pattern names.

    Returns:
        List of pattern names
    """
    return list(PATTERNS.keys())
