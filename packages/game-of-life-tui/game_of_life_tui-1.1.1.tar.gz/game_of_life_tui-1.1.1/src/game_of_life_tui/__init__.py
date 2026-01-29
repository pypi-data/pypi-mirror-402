"""Conway's Game of Life - Terminal User Interface.

A pip-installable Game of Life implementation with an interactive TUI.
"""

__version__ = "1.1.1"
__author__ = "Joseph Volmer"

from .app import GameOfLifeApp, main
from .game import GameGrid
from .patterns import PATTERNS, place_pattern, get_pattern_names

__all__ = [
    "GameOfLifeApp",
    "GameGrid",
    "PATTERNS",
    "place_pattern",
    "get_pattern_names",
    "main",
]
