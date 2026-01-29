# Game of Life TUI

A beautiful, interactive terminal-based implementation of Conway's Game of Life built with Python and Textual.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Vibrant Rainbow Colors** - Cells cycle through cyan→green→yellow→magenta→blue as they age
- **Zero Dependencies** - 100% pure Python, installs with a single pip command
- **Interactive TUI** - Beautiful terminal interface optimized for 80x24 screens
- **Theme Support** - Switch between multiple themes with Ctrl+\
- **Preset Patterns** - Spawn gliders, blinkers, and other classic patterns (keys 1-5)
- **Save/Load** - Persist your creations to JSON files
- **Cross-Platform** - Works on macOS, Linux, and Windows

## Installation

```bash
pip install game-of-life-tui
```

## Quick Start

After installation, run:

```bash
game-of-life
```

### First Steps

1. Press `R` to generate random cells
2. Press `P` to start the simulation
3. Press `+`/`-` to adjust speed
4. Press `Ctrl+\` to change themes

## Controls

| Key | Action |
|-----|--------|
| `P` | Play/Pause simulation |
| `S` | Step one generation (when paused) |
| `Space` | Toggle cell at cursor |
| `Arrow Keys` | Move cursor |
| `R` | Fill with random cells |
| `C` | Clear all cells |
| `1-5` | Spawn preset patterns |
| `+` / `-` | Adjust speed |
| `Ctrl+\` | Change theme |
| `Ctrl+S` | Save grid |
| `Ctrl+L` | Load grid |
| `Q` or `Esc` | Quit |

## Cell Colors (Meaningful Rainbow)

- **Cyan** (Age 1) - Newborn cells
- **Green** (Age 2) - Young cells
- **Yellow** (Age 3) - Mature cells
- **Magenta** (Age 4) - Old cells
- **Blue** (Age 5+) - Ancient survivors

Watch as patterns evolve and cells age through the rainbow spectrum!

## Game Rules

Conway's Game of Life follows these simple rules:

1. **Survival**: A live cell with 2-3 live neighbors survives
2. **Birth**: A dead cell with exactly 3 live neighbors becomes alive
3. **Death**: All other cells die or remain dead

The grid wraps around edges (toroidal topology) for seamless gameplay.

## Examples

### Spawn a Glider
```
1. Run game-of-life
2. Press 1 to place a glider
3. Press P to watch it travel
```

### Create Custom Patterns
```
1. Press P to pause
2. Use arrow keys to navigate
3. Press Space to toggle cells
4. Press P to run your creation
```

### Experiment with Chaos
```
1. Press R for random cells
2. Press P to start
3. Watch patterns emerge!
```

## Requirements

- Python 3.8 or higher
- textual >= 0.47.0 (automatically installed)

No system dependencies required!

## Links

- **GitHub**: https://github.com/josephvolmer/game-of-life-tui
- **Issues**: https://github.com/josephvolmer/game-of-life-tui/issues

## License

MIT License - see LICENSE file for details.

---

Made with Python and Textual
