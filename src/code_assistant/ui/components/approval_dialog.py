"""Approval dialog for HITL tool confirmations."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


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
        """Initialize the approval dialog.
        
        Args:
            title: Dialog title
            message: Description of the operation
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool
            **kwargs: Additional arguments for ModalScreen
        """
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
                yield Static(f"[bold]Tool:[/bold] {self.tool_name}")
                yield Static(f"[bold]Operation:[/bold] {self.message}")
                yield Static("")
                
                # Show tool arguments
                if self.tool_args:
                    yield Static("[bold]Arguments:[/bold]")
                    for key, value in self.tool_args.items():
                        # Truncate long values
                        val_str = str(value)
                        if len(val_str) > 200:
                            val_str = val_str[:200] + "..."
                        yield Static(f"  {key}: {val_str}")
            
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
