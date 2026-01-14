"""Status bar component."""

from textual.widgets import Static


class StatusBar(Static):
    """Status bar showing model, working directory, token usage, and status."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._model = ""
        self._working_dir = ""
        self._tokens = 0
        self._status = "ready"

    def update_status(
        self,
        model: str | None = None,
        working_dir: str | None = None,
        tokens: int | None = None,
        status: str | None = None,
    ) -> None:
        """Update status bar."""
        if model:
            self._model = model
        if working_dir:
            self._working_dir = working_dir
        if tokens is not None:
            self._tokens = tokens
        if status:
            self._status = status

        # Status indicator with color
        status_display = self._format_status(self._status)

        parts = [status_display, f"[bold]{self._model}[/bold]"]
        if self._tokens > 0:
            parts.append(f"[cyan]{self._tokens:,}[/cyan] tokens")
        parts.append(self._working_dir)

        self.update(" │ ".join(parts))

    def _format_status(self, status: str) -> str:
        """Format status with appropriate color and icon."""
        status_lower = status.lower()
        if status_lower == "ready":
            return "[green]● ready[/green]"
        elif status_lower == "thinking":
            return "[yellow]◐ thinking[/yellow]"
        elif status_lower.startswith("running:"):
            tool_name = status_lower.replace("running:", "").strip()
            return f"[cyan]⚙ {tool_name}[/cyan]"
        elif status_lower == "error":
            return "[red]✗ error[/red]"
        else:
            return f"[dim]{status}[/dim]"
