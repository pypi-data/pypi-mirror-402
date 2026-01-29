"""Main Textual application for Hydra TUI."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Input

from .models import HydraConfig
from .widgets.command_bar import CommandBar
from .widgets.config_tree import ConfigGroupTree, ConfigValueTree
from .widgets.confirm_screen import ConfirmRunScreen
from .widgets.status_bar import StatusBar


class HydraApp(App[list[str] | None]):
    """Textual app for interactive Hydra configuration.

    Returns list of override strings or None if cancelled.
    """

    TITLE = "Hydra TUI"
    SUB_TITLE = "Interactive Configuration Editor"

    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
        padding: 0 1;
    }

    ConfigGroupTree {
        width: 100%;
        height: auto;
        border: heavy $accent;
        border-title-color: $accent;
        margin-bottom: 1;
        padding: 1;
        background: $panel;
    }
    
    ConfigGroupTree:focus {
        border: heavy $success;
    }

    ConfigValueTree {
        width: 100%;
        height: auto;
        border: heavy $primary;
        border-title-color: $primary;
        padding: 1;
        background: $panel;
    }
    
    ConfigValueTree:focus {
        border: heavy $success;
    }
    
    #inline-edit {
        dock: bottom;
        width: 100%;
        height: 3;
        border: double $accent;
        background: $boost;
        padding: 0 1;
    }
    
    #inline-edit:focus {
        border: double $success;
    }
    """

    BINDINGS = [
        Binding("r", "run_command", "Run", show=True),
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("q", "quit", "Quit", show=False),
        Binding("question_mark", "show_help", "Help", show=False),
    ]

    def __init__(self, config: HydraConfig, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.should_execute = False
        self.editing_path: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the main UI."""
        yield Header(show_clock=False)

        with VerticalScroll(id="main-container"):
            yield ConfigGroupTree(self.config, id="config-groups")
            yield ConfigValueTree(self.config, id="config-values")

        yield CommandBar(id="command-bar")
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        self.update_status()

    def update_status(self) -> None:
        """Update the status bar and command preview with current info."""
        count = self.config.get_modified_count()
        multirun_count = self.config.get_multirun_count()
        overrides = self.config.get_overrides()

        # Update status bar
        self.query_one(StatusBar).update_status(count, multirun_count)

        # Update command preview
        self.query_one(CommandBar).update_command(self.config.command, overrides, multirun_count)

    def select_option_single(self, group_name: str, option_name: str) -> None:
        """Select option as single choice (Enter key)."""
        group = self.config.groups.get(group_name)
        if not group:
            return

        # Single select: replace and disable multirun
        group.selected = [option_name]
        group.multirun = False

        # Refresh the tree (update in place, no jitter!)
        groups_tree = self.query_one(ConfigGroupTree)
        groups_tree.refresh_tree()
        self.update_status()

    def toggle_option_multirun(self, group_name: str, option_name: str) -> None:
        """Toggle option in multirun list (Spacebar key)."""
        group = self.config.groups.get(group_name)
        if not group:
            return

        # Enable multirun mode and toggle
        group.multirun = True
        if option_name in group.selected:
            group.selected.remove(option_name)
        else:
            group.selected.append(option_name)

        # Refresh the tree (update in place, no jitter!)
        groups_tree = self.query_one(ConfigGroupTree)
        groups_tree.refresh_tree()
        self.update_status()

    def on_config_group_tree_option_selected(self, message: ConfigGroupTree.OptionSelected) -> None:
        """Handle option selection from the config groups tree."""
        if message.is_multirun:
            # Space: toggle in multirun list
            self.toggle_option_multirun(message.group_name, message.option_name)
        else:
            # Enter: single select
            self.select_option_single(message.group_name, message.option_name)

    async def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "run-button":
            # Trigger the run command action
            await self.action_run_command()

    async def action_run_command(self) -> None:
        """Show confirmation screen and execute the command with overrides."""
        overrides = self.config.get_overrides()
        multirun_count = self.config.get_multirun_count()

        def check_result(result):
            """Callback to handle result."""
            if result is True:
                self.should_execute = True
                self.exit(overrides)

        # Show confirmation screen
        self.push_screen(
            ConfirmRunScreen(original_command=self.config.command, overrides=overrides, multirun_count=multirun_count),
            check_result,
        )

    async def action_quit(self) -> None:
        """Quit without running."""
        self.should_execute = False
        self.exit(None)

    async def action_show_help(self) -> None:
        """Show help dialog."""
        help_text = """
        Hydra TUI Help
        ==============
        
        Navigation:
        - ↑↓: Move through tree
        - Mouse: Click to select
        
        Editing (Config Groups):
        - Enter/Click: Single choice (replaces current)
        - Space: Toggle in multirun list
        
        Editing (Config Values):
        - Enter/Click: Edit value (inline)
        - Esc: Cancel edit
        
        Commands:
        - r: Run command with overrides
        - Ctrl+C / q: Quit without running
        - ?: Show this help
        """
        self.notify(help_text)

    async def on_tree_node_selected(self, event) -> None:
        """Handle tree node selection for config values (mouse click)."""
        # Config groups tree handles its own selection via custom messages
        # Only handle config values tree here
        if isinstance(event.node.tree, ConfigValueTree):
            selected = event.node.tree.get_selected_item()
            if selected and selected[0] == "value":
                await self.start_inline_edit(selected[1])

    async def start_inline_edit(self, path: str) -> None:
        """Start inline editing of a config value."""
        config_value = self.config.values.get(path)
        if not config_value:
            return

        # Remove existing input if any
        try:
            existing = self.query("#inline-edit")
            for widget in existing:
                await widget.remove()
        except Exception:
            pass

        self.editing_path = path

        # Create an inline input widget
        # Use get_display_value() to properly format the value (None -> null, etc.)
        input_widget = Input(value=config_value.get_display_value(), placeholder=path, id="inline-edit")
        await self.mount(input_widget)
        input_widget.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle inline edit submission."""
        if event.input.id == "inline-edit" and self.editing_path:
            config_value = self.config.values.get(self.editing_path)
            if config_value:
                new_value = event.value

                # Try to convert to appropriate type
                try:
                    if isinstance(config_value.original_value, bool):
                        config_value.value = new_value.lower() in ("true", "1", "yes")
                    elif isinstance(config_value.original_value, int):
                        config_value.value = int(new_value)
                    elif isinstance(config_value.original_value, float):
                        config_value.value = float(new_value)
                    else:
                        config_value.value = new_value
                except (ValueError, AttributeError):
                    config_value.value = new_value

                # Refresh tree and status
                values_tree = self.query_one(ConfigValueTree)
                values_tree.refresh_tree()
                self.update_status()

            # Remove the input widget
            event.input.remove()
            self.editing_path = None

            # Focus back on the values tree
            self.query_one(ConfigValueTree).focus()

    def on_key(self, event) -> None:
        """Handle escape to cancel inline editing."""
        if event.key == "escape" and self.editing_path:
            inputs = self.query("#inline-edit")
            for input_widget in inputs:
                input_widget.remove()
            self.editing_path = None
            try:
                self.query_one(ConfigValueTree).focus()
            except Exception:
                pass


def run_tui(config: HydraConfig) -> tuple[bool, list[str]]:
    """Run the TUI and return results.

    Returns:
        Tuple of (should_execute, overrides)
    """
    app = HydraApp(config)
    result = app.run()

    if result is None:
        return (False, [])

    return (app.should_execute, result)
