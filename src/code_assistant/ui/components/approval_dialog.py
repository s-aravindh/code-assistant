"""Approval dialog for HITL tool confirmations."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from rich.text import Text


def safe_str(value, max_len: int | None = None) -> str:
    """Safely convert any value to string."""
    if value is None:
        return ""
    try:
        s = repr(value) if isinstance(value, (dict, list, tuple)) else str(value)
        return s[:max_len] + "..." if max_len and len(s) > max_len else s
    except Exception:
        return "<error>"


class ApprovalDialog(ModalScreen):
    """Modal dialog for approving/rejecting tool operations."""
    
    BINDINGS = [
        Binding("y", "approve", "Yes"),
        Binding("n", "reject", "No"),
        Binding("escape", "reject", "Cancel"),
    ]
    
    DEFAULT_CSS = """
    ApprovalDialog {
        align: center middle;
    }
    
    ApprovalDialog > Container {
        width: 80;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    ApprovalDialog .dialog-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $primary;
        padding: 1;
    }
    
    ApprovalDialog .dialog-content {
        width: 100%;
        height: auto;
        max-height: 20;
        background: $panel;
        border: solid $accent;
        padding: 1;
        margin: 1 0;
    }
    
    ApprovalDialog .button-row {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding: 1 0;
    }
    
    ApprovalDialog Button {
        margin: 0 1;
    }
    
    ApprovalDialog .hint {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        padding: 0 0 1 0;
    }
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        tool_name: str,
        tool_args: dict,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title_text = title
        self.message = message
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.result = None
    
    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Container():
            yield Label(self.title_text, classes="dialog-title")
            
            with VerticalScroll(classes="dialog-content"):
                yield Static(Text.assemble(("Tool: ", "bold"), (self.tool_name, "")))
                yield Static(Text.assemble(("Operation: ", "bold"), (self.message, "")))
                yield Static("")
                
                # Show tool arguments
                if self.tool_args:
                    yield Static(Text("Arguments:", style="bold"))
                    for key, value in self.tool_args.items():
                        val_str = safe_str(value, max_len=200)
                        yield Static(Text(f"  {safe_str(key)}: {val_str}"))
            
            yield Static("[dim]Press Y to approve, N to reject[/dim]", classes="hint")
            
            with Horizontal(classes="button-row"):
                yield Button("Yes (Y)", variant="success", id="yes")
                yield Button("No (N)", variant="error", id="no")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "yes":
            self.action_approve()
        elif event.button.id == "no":
            self.action_reject()
    
    def action_approve(self) -> None:
        """Approve the action."""
        self.result = "approved"
        self.dismiss(self.result)
    
    def action_reject(self) -> None:
        """Reject the action."""
        self.result = "rejected"
        self.dismiss(self.result)
