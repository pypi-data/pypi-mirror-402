"""Main Textual application for Game of Life TUI."""

import datetime
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container
from textual import events
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style

from .game import GameGrid
from .patterns import place_pattern, get_pattern_names


class GridWidget(Static):
    """Widget to display the Game of Life grid."""

    cursor_x = reactive(25)
    cursor_y = reactive(10)

    def __init__(self, grid: GameGrid):
        """Initialize grid widget.

        Args:
            grid: GameGrid instance to display
        """
        super().__init__()
        self.grid = grid
        # Vibrant color palette for cell ages (1-5) - rainbow gradient
        self.age_colors = [
            "bright_cyan",      # Age 1 (newborn - bright cyan)
            "bright_green",     # Age 2 (young - bright green)
            "bright_yellow",    # Age 3 (mature - bright yellow)
            "bright_magenta",   # Age 4 (old - bright magenta)
            "bright_blue",      # Age 5+ (ancient - bright blue)
        ]

    def render(self) -> Text:
        """Render the grid with colored cells based on age."""
        text = Text()

        for y in range(self.grid.height):
            for x in range(self.grid.width):
                is_alive = self.grid.is_alive(x, y)
                is_cursor = (x == self.cursor_x and y == self.cursor_y)

                if is_cursor and not self.app.is_playing:
                    # Highlight cursor position when paused with bright background
                    if is_alive:
                        text.append("█", style="bold bright_white on bright_red")
                    else:
                        text.append("·", style="bold bright_white on bright_red")
                elif is_alive:
                    age = self.grid.get_age(x, y)
                    color_idx = min(age - 1, 4)  # 0-4 index
                    text.append("█", style=self.age_colors[color_idx])
                else:
                    text.append("·", style="grey35")

            text.append("\n")

        return text


class GameOfLifeApp(App):
    """Conway's Game of Life TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #grid-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    GridWidget {
        width: auto;
        height: auto;
        background: $surface;
    }

    #status-bar {
        dock: bottom;
        height: 3;
        background: $panel;
        color: $warning;
        padding: 1;
    }

    Header {
        background: $panel;
    }

    Footer {
        background: $panel;
    }
    """

    BINDINGS = [
        ("p", "toggle_play", "Play"),
        ("s", "step", "Step"),
        ("space", "toggle_cell", "Draw"),
        ("r", "randomize", "Random"),
        ("c", "clear", "Clear"),
        ("1,2,3,4,5", "pattern_1", "Patterns"),  # Shows hint, all work
        ("q", "quit", "Quit"),
        # Hidden bindings (not shown in footer but still work)
        ("escape", "quit", ""),
        ("up", "move_up", ""),
        ("down", "move_down", ""),
        ("left", "move_left", ""),
        ("right", "move_right", ""),
        ("plus", "speed_up", ""),
        ("minus", "slow_down", ""),
        ("equal", "speed_up", ""),  # + without shift
        ("2", "pattern_2", ""),
        ("3", "pattern_3", ""),
        ("4", "pattern_4", ""),
        ("5", "pattern_5", ""),
        ("ctrl+s", "save_grid", ""),
        ("ctrl+l", "load_grid", ""),
    ]

    is_playing = reactive(False)
    generation = reactive(0)
    population = reactive(0)
    speed = reactive(500)  # milliseconds per generation

    def __init__(self):
        """Initialize the application."""
        super().__init__()
        self.title = "game-of-life-tui"
        self.grid = GameGrid(50, 20)  # 50 wide, 20 tall for 80x24 terminal
        self.update_timer = None
        self.save_counter = 0

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()
        with Container(id="grid-container"):
            self.grid_widget = GridWidget(self.grid)
            yield self.grid_widget
        yield Static(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Handle app mount event."""
        self.update_status_bar()

    def update_status_bar(self) -> None:
        """Update the status bar with current game info."""
        from rich.text import Text as RichText

        status = self.query_one("#status-bar", Static)

        # Create colorful status text
        text = RichText()

        if self.is_playing:
            text.append("▶ PLAYING", style="bold bright_green")
        else:
            text.append("⏸ PAUSED", style="bold bright_yellow")

        text.append("  │  ", style="bright_blue")
        text.append(f"Gen: ", style="bright_cyan")
        text.append(f"{self.grid.generation}", style="bold bright_white")

        text.append("  │  ", style="bright_blue")
        text.append(f"Pop: ", style="bright_magenta")
        text.append(f"{self.grid.population}", style="bold bright_white")

        text.append("  │  ", style="bright_blue")
        text.append(f"Speed: ", style="bright_yellow")
        text.append(f"{self.speed}ms", style="bold bright_white")

        text.append("  │  ", style="bright_blue")
        text.append("Arrows", style="grey70")
        text.append("=move ", style="grey50")
        text.append("Space", style="grey70")
        text.append("=draw ", style="grey50")
        text.append("+/-", style="grey70")
        text.append("=speed", style="grey50")

        status.update(text)

    def action_toggle_play(self) -> None:
        """Toggle play/pause state."""
        self.is_playing = not self.is_playing

        if self.is_playing:
            self.start_simulation()
        else:
            self.stop_simulation()

        self.update_status_bar()

    def start_simulation(self) -> None:
        """Start the simulation timer."""
        if self.update_timer is not None:
            self.update_timer.stop()

        self.update_timer = self.set_interval(
            self.speed / 1000.0,
            self.simulation_step,
            pause=False
        )

    def stop_simulation(self) -> None:
        """Stop the simulation timer."""
        if self.update_timer is not None:
            self.update_timer.stop()
            self.update_timer = None

    def simulation_step(self) -> None:
        """Advance simulation by one step."""
        self.grid.step()
        self.grid_widget.refresh()
        self.update_status_bar()

    def action_step(self) -> None:
        """Advance one generation when paused."""
        if not self.is_playing:
            self.simulation_step()

    def action_randomize(self) -> None:
        """Fill grid with random cells."""
        self.grid.randomize()
        self.grid_widget.refresh()
        self.update_status_bar()

    def action_clear(self) -> None:
        """Clear all cells from grid."""
        self.grid.clear()
        self.grid_widget.refresh()
        self.update_status_bar()

    def action_move_up(self) -> None:
        """Move cursor up."""
        self.grid_widget.cursor_y = (self.grid_widget.cursor_y - 1) % self.grid.height
        self.grid_widget.refresh()

    def action_move_down(self) -> None:
        """Move cursor down."""
        self.grid_widget.cursor_y = (self.grid_widget.cursor_y + 1) % self.grid.height
        self.grid_widget.refresh()

    def action_move_left(self) -> None:
        """Move cursor left."""
        self.grid_widget.cursor_x = (self.grid_widget.cursor_x - 1) % self.grid.width
        self.grid_widget.refresh()

    def action_move_right(self) -> None:
        """Move cursor right."""
        self.grid_widget.cursor_x = (self.grid_widget.cursor_x + 1) % self.grid.width
        self.grid_widget.refresh()

    def action_toggle_cell(self) -> None:
        """Toggle cell at cursor position."""
        self.grid.toggle_cell(self.grid_widget.cursor_x, self.grid_widget.cursor_y)
        self.grid_widget.refresh()
        self.update_status_bar()

    def action_speed_up(self) -> None:
        """Increase simulation speed."""
        self.speed = max(100, self.speed - 100)
        if self.is_playing:
            self.stop_simulation()
            self.start_simulation()
        self.update_status_bar()

    def action_slow_down(self) -> None:
        """Decrease simulation speed."""
        self.speed = min(1000, self.speed + 100)
        if self.is_playing:
            self.stop_simulation()
            self.start_simulation()
        self.update_status_bar()

    def action_pattern_1(self) -> None:
        """Place glider pattern."""
        place_pattern(self.grid, "glider", self.grid_widget.cursor_x, self.grid_widget.cursor_y)
        self.grid_widget.refresh()
        self.update_status_bar()

    def action_pattern_2(self) -> None:
        """Place blinker pattern."""
        place_pattern(self.grid, "blinker", self.grid_widget.cursor_x, self.grid_widget.cursor_y)
        self.grid_widget.refresh()
        self.update_status_bar()

    def action_pattern_3(self) -> None:
        """Place toad pattern."""
        place_pattern(self.grid, "toad", self.grid_widget.cursor_x, self.grid_widget.cursor_y)
        self.grid_widget.refresh()
        self.update_status_bar()

    def action_pattern_4(self) -> None:
        """Place beacon pattern."""
        place_pattern(self.grid, "beacon", self.grid_widget.cursor_x, self.grid_widget.cursor_y)
        self.grid_widget.refresh()
        self.update_status_bar()

    def action_pattern_5(self) -> None:
        """Place pulsar pattern."""
        place_pattern(self.grid, "pulsar", self.grid_widget.cursor_x, self.grid_widget.cursor_y)
        self.grid_widget.refresh()
        self.update_status_bar()

    def action_save_grid(self) -> None:
        """Save current grid to file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_of_life_{timestamp}.json"
        try:
            self.grid.save_to_file(filename)
            self.notify(f"Grid saved to {filename}", severity="information")
        except Exception as e:
            self.notify(f"Error saving: {str(e)}", severity="error")

    def action_load_grid(self) -> None:
        """Load grid from file."""
        # For simplicity, we'll try to load from a default filename
        # In a more advanced version, we'd use a file picker
        try:
            self.grid.load_from_file("game_of_life.json")
            self.grid_widget.refresh()
            self.update_status_bar()
            self.notify("Grid loaded from game_of_life.json", severity="information")
        except FileNotFoundError:
            self.notify("File 'game_of_life.json' not found", severity="error")
        except Exception as e:
            self.notify(f"Error loading: {str(e)}", severity="error")


def main():
    """Entry point for the application."""
    app = GameOfLifeApp()
    app.run()


if __name__ == "__main__":
    main()
