<div align="center">

<img src="assets/logo.png" alt="Game of Life TUI Logo" width="300">

# Game of Life TUI

A beautiful, interactive terminal-based implementation of [Conway's Game of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life) built with Python and [Textual](https://textual.textualize.io/).

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![PyPI](https://img.shields.io/badge/pypi-game--of--life--tui-blue.svg)

</div>

---

## Screenshot

<div align="center">

![Game of Life TUI in action](assets/screenshot.png)

*Watch cells evolve through rainbow colors as they age - cyan (newborn) → green → yellow → magenta → blue (ancient)*

</div>

---

## Features

- **Vibrant Rainbow Colors** - Cells cycle through cyan→green→yellow→magenta→blue as they age, making pattern dynamics instantly visible
- **Theme Support** - Switch between multiple themes (Ctrl+\) while keeping meaningful cell colors
- **Zero System Dependencies** - 100% pure Python, installs with a single pip command
- **Interactive TUI** - Beautiful terminal interface optimized for standard 80×24 screens
- **Preset Patterns** - Spawn classic patterns like gliders, blinkers, pulsars with a single keypress
- **Manual Editing** - Pause and draw your own patterns with intuitive arrow key navigation
- **Save/Load** - Persist your creations to JSON files
- **Adjustable Speed** - Control simulation speed from 100-1000ms per generation
- **Cross-Platform** - Works on macOS, Linux, and Windows terminals

## Installation

### From PyPI (Recommended)

```bash
pip install game-of-life-tui
```

### From Source

```bash
git clone https://github.com/josephvolmer/game-of-life-tui.git
cd game-of-life-tui
pip install -e .
```

## Quick Start

After installation, launch the game:

```bash
game-of-life-tui
```

Or alternatively:

```bash
python -m game_of_life_tui
```

## Controls

### Simulation Control
| Key | Action |
|-----|--------|
| `P` | Play/Pause simulation |
| `S` | Step forward one generation (when paused) |
| `+` / `=` | Increase simulation speed |
| `-` | Decrease simulation speed |

### Navigation & Editing
| Key | Action |
|-----|--------|
| `Arrow Keys` | Move cursor around grid |
| `Space` | Toggle cell at cursor (alive ↔ dead) |

### Grid Operations
| Key | Action |
|-----|--------|
| `R` | Fill grid with random cells |
| `C` | Clear all cells |

### Preset Patterns
| Key | Pattern | Type | Description |
|-----|---------|------|-------------|
| `1` | Glider | Spaceship | Travels diagonally across the grid |
| `2` | Blinker | Oscillator | Period 2 oscillator |
| `3` | Toad | Oscillator | Period 2 oscillator |
| `4` | Beacon | Oscillator | Period 2 oscillator |
| `5` | Pulsar | Oscillator | Period 3 oscillator (13×13) |

### File Operations
| Key | Action |
|-----|--------|
| `Ctrl+S` | Save grid to timestamped JSON file |
| `Ctrl+L` | Load grid from `game_of_life.json` |

### Themes & Application
| Key | Action |
|-----|--------|
| `Ctrl+\` | Open theme picker (try nord, monokai, gruvbox!) |
| `Q` or `Esc` | Quit application |

## Cell Colors

One of the most unique features is the **meaningful color progression** that reveals cell dynamics:

```
█ = Live cell (color-coded by age)
· = Dead cell

Cell Age Colors (Rainbow Progression):
Bright Cyan (Age 1)    → Newborn cells, just born from 3 neighbors
Bright Green (Age 2)   → Young cells, survived first generation
Bright Yellow (Age 3)  → Mature cells, well-established
Bright Magenta (Age 4) → Old cells, long-lived survivors
Bright Blue (Age 5+)   → Ancient survivors, the rarest cells

Cursor (when paused):
Red background with white text
```

### Why Rainbow Colors?

The color progression isn't just pretty—it's **scientifically meaningful**:

- **Spot Oscillators**: See repeating color patterns
- **Track Gliders**: Watch colorful trails as they move
- **Identify Stable Regions**: Blue/magenta areas are stable
- **See Birth Rate**: Lots of cyan means high activity
- **Understand Dynamics**: Color distribution shows pattern evolution

## Game Rules

Conway's Game of Life is a zero-player game following these simple rules:

1. **Survival**: A live cell with 2-3 live neighbors survives to the next generation
2. **Birth**: A dead cell with exactly 3 live neighbors becomes alive
3. **Death**: All other cells die or remain dead

The grid is **toroidal** (wraps around edges), creating a seamless, infinite-like surface.

## Technical Details

- **Grid Size**: 50×20 cells (optimized for 80×24 terminal)
- **Topology**: Toroidal (wrapping edges)
- **Update Rate**: 100-1000ms per generation (adjustable)
- **Architecture**: Pure Python with Textual TUI framework
- **Cell Rendering**: Unicode block characters (`█` and `·`)
- **Color Support**: Standard 16-color ANSI (works everywhere)
- **Save Format**: JSON with live cell coordinates

## Requirements

- Python 3.8 or higher
- textual >= 0.47.0 (automatically installed)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **PyPI**: https://pypi.org/project/game-of-life-tui/
- **Issues**: https://github.com/josephvolmer/game-of-life-tui/issues

---

<div align="center">

Made with Python and Textual

</div>
