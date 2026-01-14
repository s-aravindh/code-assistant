"""Output panel component for displaying agent responses."""

from textual.containers import VerticalScroll
from textual.widgets import Markdown, Static


def escape_markup(text: str) -> str:
    """Escape Rich markup characters to prevent parsing errors.
    
    Brackets [ ] are doubled to escape them in Rich markup.
    """
    return text.replace("[", "[[").replace("]", "]]")


class StreamingMessage(Static):
    """A message widget that can be updated for streaming content."""

    DEFAULT_CSS = """
    StreamingMessage {
        background: $panel;
        padding: 1;
        margin: 1 0;
        border-left: thick $primary;
    }
    """

    def __init__(self, initial_content: str = "", **kwargs) -> None:
        super().__init__(initial_content, **kwargs)
        self._content_parts: list[str] = []
        if initial_content:
            self._content_parts.append(initial_content)

    def append_content(self, content: str) -> None:
        """Append content to the streaming message."""
        self._content_parts.append(content)
        self.update("".join(self._content_parts))

    def get_full_content(self) -> str:
        """Get the full accumulated content."""
        return "".join(self._content_parts)


class ToolCallWidget(Static):
    """Widget for displaying tool call status."""

    DEFAULT_CSS = """
    ToolCallWidget {
        background: $surface;
        padding: 0 1;
        margin: 0 0;
        border-left: thick $accent;
        color: $text-muted;
    }

    ToolCallWidget.running {
        border-left: thick $warning;
    }

    ToolCallWidget.completed {
        border-left: thick $success;
    }

    ToolCallWidget.error {
        border-left: thick $error;
    }
    """

    def __init__(self, tool_name: str, tool_args: dict | None = None, **kwargs) -> None:
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        # Format args for display (truncate long values)
        args_display = self._format_args(self.tool_args)
        super().__init__(f"[dim]⚙ {tool_name}[/dim] {args_display}", **kwargs)
        self.add_class("running")

    def _format_args(self, args: dict, max_len: int = 60) -> str:
        """Format tool arguments for display."""
        if not args:
            return ""
        parts = []
        for k, v in args.items():
            v_str = str(v)
            if len(v_str) > max_len:
                v_str = v_str[:max_len] + "..."
            # Escape markup characters in argument values
            v_str = escape_markup(v_str)
            parts.append(f"{k}={v_str}")
        return "[dim](" + ", ".join(parts) + ")[/dim]"

    def mark_completed(self, result: str | None = None) -> None:
        """Mark the tool call as completed."""
        self.remove_class("running")
        self.add_class("completed")
        result_preview = ""
        if result:
            result_str = str(result)[:100]
            if len(str(result)) > 100:
                result_str += "..."
            # Escape markup characters in result to prevent parsing errors
            result_str = escape_markup(result_str)
            result_preview = f" → [dim]{result_str}[/dim]"
        self.update(f"[dim]✓ {self.tool_name}[/dim]{result_preview}")

    def mark_error(self, error: str | None = None) -> None:
        """Mark the tool call as failed."""
        self.remove_class("running")
        self.add_class("error")
        # Escape markup characters in error message
        error_escaped = escape_markup(str(error)) if error else ""
        error_msg = f" → [red]{error_escaped}[/red]" if error else ""
        self.update(f"[dim]✗ {self.tool_name}[/dim]{error_msg}")


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

    OutputPanel .tool-group {
        margin: 0;
        padding: 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_streaming_message: StreamingMessage | None = None
        self._tool_widgets: dict[str, ToolCallWidget] = {}

    def _add_message(self, widget: Static | Markdown) -> None:
        """Mount a message widget and scroll to it."""
        self.mount(widget)
        self.scroll_end(animate=False)

    def add_user_message(self, message: str) -> None:
        """Add a user message to the output."""
        self._finalize_streaming()
        # Escape markup in user message to prevent parsing errors
        safe_message = escape_markup(message)
        self._add_message(Static(f"[bold]You:[/bold] {safe_message}", classes="user-message"))

    def add_agent_message(self, message: str) -> None:
        """Add an agent message (supports markdown)."""
        self._finalize_streaming()
        self._add_message(Markdown(message, classes="agent-message"))

    def add_system_message(self, message: str) -> None:
        """Add a system message."""
        self._finalize_streaming()
        # Escape markup in system message to prevent parsing errors
        safe_message = escape_markup(message)
        self._add_message(Static(f"[italic]{safe_message}[/italic]", classes="system-message"))

    def add_error_message(self, message: str) -> None:
        """Add an error message."""
        self._finalize_streaming()
        # Escape markup in error message to prevent parsing errors
        safe_message = escape_markup(message)
        self._add_message(Static(f"[bold red]Error:[/bold red] {safe_message}", classes="error-message"))

    # === Streaming support ===

    def start_streaming(self) -> StreamingMessage:
        """Start a new streaming message and return it for updates."""
        self._finalize_streaming()
        self._current_streaming_message = StreamingMessage()
        self.mount(self._current_streaming_message)
        self.scroll_end(animate=False)
        return self._current_streaming_message

    def append_to_stream(self, content: str) -> None:
        """Append content to the current streaming message."""
        if self._current_streaming_message is None:
            self._current_streaming_message = self.start_streaming()
        self._current_streaming_message.append_content(content)
        self.scroll_end(animate=False)

    def finalize_streaming_as_markdown(self) -> None:
        """Convert the current streaming message to proper markdown."""
        if self._current_streaming_message is not None:
            full_content = self._current_streaming_message.get_full_content()
            self._current_streaming_message.remove()
            self._current_streaming_message = None
            if full_content.strip():
                self._add_message(Markdown(full_content, classes="agent-message"))

    def _finalize_streaming(self) -> None:
        """Finalize any ongoing streaming message."""
        if self._current_streaming_message is not None:
            self.finalize_streaming_as_markdown()

    # === Tool call support ===

    def add_tool_call_started(self, tool_id: str, tool_name: str, tool_args: dict | None = None) -> None:
        """Add a tool call started indicator."""
        # Finalize any streaming content BEFORE the tool call widget
        # This ensures proper ordering: content -> tool -> more content
        self._finalize_streaming()
        
        widget = ToolCallWidget(tool_name, tool_args)
        self._tool_widgets[tool_id] = widget
        self.mount(widget)
        self.scroll_end(animate=False)

    def mark_tool_call_completed(self, tool_id: str, result: str | None = None) -> None:
        """Mark a tool call as completed."""
        if tool_id in self._tool_widgets:
            self._tool_widgets[tool_id].mark_completed(result)
            del self._tool_widgets[tool_id]

    def mark_tool_call_error(self, tool_id: str, error: str | None = None) -> None:
        """Mark a tool call as failed."""
        if tool_id in self._tool_widgets:
            self._tool_widgets[tool_id].mark_error(error)
            del self._tool_widgets[tool_id]

    def clear_output(self) -> None:
        """Clear all messages from the output panel."""
        self._finalize_streaming()
        self._tool_widgets.clear()
        self.remove_children()
