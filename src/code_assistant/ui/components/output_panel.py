"""Output panel component for displaying agent responses."""

from textual.containers import VerticalScroll
from textual.widgets import Markdown, Static


class OutputPanel(VerticalScroll):
    """Scrollable output panel for displaying conversation."""

    DEFAULT_CSS = """
    OutputPanel {
        border: solid $primary;
        padding: 1;
    }

    OutputPanel .user-message {
        background: $boost;
        padding: 1;
        margin: 1 0;
        border-left: thick $success;
    }

    OutputPanel .agent-message {
        background: $panel;
        padding: 1;
        margin: 1 0;
        border-left: thick $primary;
    }

    OutputPanel .system-message {
        color: $text-muted;
        padding: 1;
        margin: 1 0;
        border-left: thick $warning;
    }

    OutputPanel .error-message {
        background: $error 20%;
        padding: 1;
        margin: 1 0;
        border-left: thick $error;
    }
    """

    def _add_message(self, widget: Static | Markdown) -> None:
        """Mount a message widget and scroll to it."""
        self.mount(widget)
        self.scroll_end(animate=False)

    def add_user_message(self, message: str) -> None:
        """Add a user message to the output."""
        self._add_message(Static(f"[bold]You:[/bold] {message}", classes="user-message"))

    def add_agent_message(self, message: str) -> None:
        """Add an agent message (supports markdown)."""
        self._add_message(Markdown(message, classes="agent-message"))

    def add_system_message(self, message: str) -> None:
        """Add a system message."""
        self._add_message(Static(f"[italic]{message}[/italic]", classes="system-message"))

    def add_error_message(self, message: str) -> None:
        """Add an error message."""
        self._add_message(Static(f"[bold red]Error:[/bold red] {message}", classes="error-message"))

    def clear_output(self) -> None:
        """Clear all messages from the output panel."""
        self.remove_children()
