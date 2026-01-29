"""Confirmation screen for command execution."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmRunScreen(ModalScreen[bool]):
    """Modal screen to confirm command execution."""

    BINDINGS = [
        Binding("r", "confirm", "Run", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    ConfirmRunScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.6);
    }
    
    #dialog {
        width: 90;
        height: auto;
        border: double $success;
        background: $surface;
        padding: 2 3;
    }
    
    #title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $success;
        margin-bottom: 2;
        text-align: center;
    }
    
    .info-box {
        width: 100%;
        height: auto;
        border: solid $accent;
        background: $boost;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    #overrides-box {
        width: 100%;
        height: auto;
        max-height: 20;
        border: solid $primary;
        background: $boost;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    #buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    Button {
        margin: 0 2;
        min-width: 20;
    }
    """

    def __init__(self, original_command: list[str], overrides: list[str], multirun_count: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self.original_command = original_command
        self.overrides = overrides
        self.multirun_count = multirun_count

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        # Build the final command string
        final_command = " ".join(self.original_command)
        if self.overrides:
            final_command += " " + " ".join(self.overrides)

        with Container(id="dialog"):
            # Title with multirun info
            if self.multirun_count and self.multirun_count > 1:
                title = f"🚀 Ready to launch {self.multirun_count} experiments"
            else:
                title = "🚀 Ready to run command"
            yield Static(title, id="title")

            # Show overrides
            if self.overrides:
                overrides_text = "[bold cyan]Overrides:[/bold cyan]\n\n"
                for i, override in enumerate(self.overrides, 1):
                    if override.startswith("~"):
                        # Deletion (red)
                        overrides_text += f"  [red]•[/red] [red]{override}[/red]\n"
                    elif override.startswith("+"):
                        # New config group (green)
                        overrides_text += f"  [green]•[/green] [green]{override}[/green]\n"
                    else:
                        # Regular override (yellow)
                        overrides_text += f"  [yellow]•[/yellow] [yellow]{override}[/yellow]\n"
                yield Static(overrides_text.strip(), id="overrides-box")
            else:
                yield Static(
                    "[bold cyan]Overrides:[/bold cyan]\n\n[dim italic]No modifications made[/dim italic]",
                    id="overrides-box",
                )

            # Show final command
            yield Static(
                f"[bold cyan]Command:[/bold cyan]\n\n[bold yellow]{final_command}[/bold yellow]", classes="info-box"
            )

            # Buttons
            with Vertical(id="buttons"):
                yield Button("✓ Run (r)", variant="success", id="confirm")
                yield Button("✗ Cancel (Esc)", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Focus the confirm button when mounted."""
        self.query_one("#confirm", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        event.stop()
        if event.button.id == "confirm":
            self.action_confirm()
        else:
            self.action_cancel()

    def action_confirm(self) -> None:
        """Confirm and close."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel and close."""
        self.dismiss(False)
