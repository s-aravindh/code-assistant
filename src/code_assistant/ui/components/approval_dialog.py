"""Approval dialog for HITL tool confirmations."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
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
            
            with Vertical(classes="dialog-content"):
                # Text.assemble: (text, style) tuples - plain text won't be parsed as markup
                yield Static(Text.assemble(("Tool: ", "bold"), (self.tool_name, "")))
                yield Static(Text.assemble(("Operation: ", "bold"), (self.message, "")))
                yield Static("")
                
                # Show tool arguments
                if self.tool_args:
                    yield Static(Text("Arguments:", style="bold"))
                    for key, value in self.tool_args.items():
                        val_str = safe_str(value, max_len=200)
                        yield Static(Text(f"  {safe_str(key)}: {val_str}"))
            
            with Horizontal(classes="button-row"):
                yield Button("Yes", variant="success", id="yes")
                yield Button("No", variant="error", id="no")
                yield Button("Edit", variant="default", id="edit")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "yes":
            self.result = "approved"
        elif button_id == "no":
            self.result = "rejected"
        elif button_id == "edit":
            self.result = "edit"
        
        self.dismiss(self.result)
