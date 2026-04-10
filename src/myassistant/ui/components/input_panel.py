"""Input panel component for user messages."""

from textual import events
from textual.message import Message
from textual.widgets import TextArea


class InputPanel(TextArea):
    """Simple multiline input panel.
    
    - Enter: Submit message
    - Shift+Enter: Newline
    """

    DEFAULT_CSS = """
    InputPanel {
        height: auto;
        min-height: 3;
        max-height: 10;
        border: solid $primary;
    }

    InputPanel:focus {
        border: solid $accent;
    }
    """

    class Submitted(Message):
        """Posted when user submits input."""
        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(
            show_line_numbers=False,
            soft_wrap=True,
            **kwargs
        )
        self.placeholder = "Type message... (Enter send, Shift+Enter newline)"

    async def _on_key(self, event: events.Key) -> None:
        """Handle key events."""
        # Shift+Enter: insert newline (key name includes modifier)
        if event.key == "shift+enter":
            self.insert("\n")
            event.stop()
            return
        
        # Plain Enter: submit
        if event.key == "enter":
            self._do_submit()
            event.stop()
            return
        
        # All other keys: default TextArea behavior
        await super()._on_key(event)

    def _do_submit(self) -> None:
        """Submit the message."""
        value = self.text.strip()
        if not value:
            return
        self.clear()
        self.post_message(self.Submitted(value))
