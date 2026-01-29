"""Status bar widget for showing shortcuts and status."""

from textual.widgets import Static


class StatusBar(Static):
    """Status bar showing current state and keyboard shortcuts."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 3;
        background: $boost;
        border-top: double $primary;
        padding: 1 2;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overrides_count = 0
        self.multirun_count = None

    def update_status(self, overrides_count: int, multirun_count: int | None = None) -> None:
        """Update the status display."""
        self.overrides_count = overrides_count
        self.multirun_count = multirun_count
        self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the status bar content."""
        # Build left side (status info)
        left_parts = []
        if self.overrides_count > 0:
            left_parts.append(f"[bold yellow]✎ {self.overrides_count}[/bold yellow] modified")
        else:
            left_parts.append("[dim]No modifications[/dim]")

        # Add multirun info if applicable
        if self.multirun_count and self.multirun_count > 1:
            left_parts.append(f"[bold magenta]⚡ {self.multirun_count}[/bold magenta] experiments")

        left_text = "  ".join(left_parts)

        # Build right side (shortcuts)
        shortcuts = [
            "[bold cyan]↵[/bold cyan] Single",
            "[bold cyan]Space[/bold cyan] Multi",
            "[bold green]r[/bold green] Run",
            "[bold red]^C[/bold red] Quit",
        ]
        right_text = "  ".join(shortcuts)

        # Combine
        display_text = f"{left_text}    [dim]│[/dim]    {right_text}"
        self.update(display_text)

    def on_mount(self) -> None:
        """Initialize the display when mounted."""
        self.refresh_display()
