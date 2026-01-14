"""Status bar component."""

from textual.widgets import Static


class StatusBar(Static):
    """Status bar showing model, working directory, and token usage."""

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

    def update_status(
        self,
        model: str | None = None,
        working_dir: str | None = None,
        tokens: int | None = None,
    ) -> None:
        """Update status bar."""
        if model:
            self._model = model
        if working_dir:
            self._working_dir = working_dir
        if tokens is not None:
            self._tokens = tokens

        parts = [f"[bold]{self._model}[/bold]"]
        if self._tokens > 0:
            parts.append(f"[cyan]{self._tokens:,}[/cyan] tokens")
        parts.append(self._working_dir)

        self.update(" │ ".join(parts))
