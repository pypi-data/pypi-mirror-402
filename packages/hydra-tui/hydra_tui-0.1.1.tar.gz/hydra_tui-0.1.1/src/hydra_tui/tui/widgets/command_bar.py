"""Command preview and run bar widget."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static


class CommandBar(Horizontal):
    """Bar showing command preview and run button."""

    DEFAULT_CSS = """
    CommandBar {
        height: 5;
        background: $boost;
        border-top: double $accent;
        border-bottom: solid $primary;
        padding: 0 2;
        align: center middle;
    }
    
    #command-preview {
        width: 1fr;
        height: 1;
        content-align: left middle;
        padding: 0 1;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    #run-button {
        width: auto;
        min-width: 20;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_text = ""

    def compose(self) -> ComposeResult:
        """Compose the command bar."""
        yield Static("[dim]Loading command...[/dim]", id="command-preview")
        yield Button("▶ Run (r)", variant="success", id="run-button")

    def update_command(self, command: list[str], overrides: list[str], multirun_count: int | None = None) -> None:
        """Update the command preview."""
        # Build command string
        cmd_parts = list(command)

        # Add -m flag if multirun is active and not already present
        if multirun_count and multirun_count > 1:
            if "-m" not in cmd_parts and "--multirun" not in cmd_parts:
                cmd_parts.append("-m")

        if overrides:
            cmd_parts.extend(overrides)

        # Format the command with syntax highlighting
        cmd_str = " ".join(cmd_parts)

        # Apply syntax highlighting to overrides
        for override in overrides:
            if override.startswith("~"):
                # Deletion (red)
                cmd_str = cmd_str.replace(override, f"[red]{override}[/red]", 1)
            elif override.startswith("+"):
                # New config group (green)
                cmd_str = cmd_str.replace(override, f"[green]{override}[/green]", 1)
            else:
                # Regular override (yellow)
                cmd_str = cmd_str.replace(override, f"[yellow]{override}[/yellow]", 1)

        # Highlight -m flag if present
        if multirun_count and multirun_count > 1:
            if " -m " in cmd_str:
                cmd_str = cmd_str.replace(" -m ", " [magenta]-m[/magenta] ", 1)

        # Truncate if too long (after adding markup)
        max_length = 200  # Higher limit to account for markup
        if len(cmd_str) > max_length:
            cmd_str = cmd_str[: max_length - 3] + "..."

        # Add icon and styling
        if multirun_count and multirun_count > 1:
            prefix = f"[bold magenta]⚡ {multirun_count}x[/bold magenta] "
        else:
            prefix = "[bold cyan]$[/bold cyan] "

        self.command_text = f"{prefix}{cmd_str}"

        # Update the preview widget
        try:
            preview = self.query_one("#command-preview", Static)
            preview.update(self.command_text)
        except Exception:
            pass  # Widget might not be mounted yet
