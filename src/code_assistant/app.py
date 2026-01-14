"""Main TUI application for Mini-Claude-Code."""

import asyncio
from pathlib import Path
from typing import AsyncIterator

from agno.agent import (
    RunContentEvent,
    RunOutputEvent,
    ToolCallCompletedEvent,
    ToolCallStartedEvent,
    RunCompletedEvent,
)
from agno.models.base import Model
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Header

from code_assistant.agent.coding_agent import create_coding_agent
from code_assistant.agent.memory import create_agent_md_template
from code_assistant.config.models import create_model, parse_model_string, get_model_display_name
from code_assistant.ui.components import (
    InputPanel,
    OutputPanel,
    StatusBar,
    FileViewer,
    ModelSelectorScreen,
)
from code_assistant.utils.slash_commands import SlashCommandHandler


class MiniClaudeCodeApp(App):
    """Main TUI application for the coding assistant."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #output-container {
        height: 1fr;
    }

    #input-container {
        height: auto;
        max-height: 6;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("ctrl+k", "model_selector", "Model", priority=True),
        Binding("ctrl+o", "open_files", "Files"),
        Binding("f1", "help", "Help"),
    ]

    TITLE = "Mini-Claude-Code"

    def __init__(
        self,
        project_path: str | None = None,
        model: Model | str = "anthropic:claude-sonnet-4-20250514",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.project_path = project_path or str(Path.cwd())

        # Create model instance if string provided
        if isinstance(model, str):
            provider, model_id = parse_model_string(model)
            self.model = create_model(provider, model_id)
        else:
            self.model = model

        self.model_display = get_model_display_name(self.model)
        self.agent = None
        self.session_id = None
        self.total_tokens = 0
        self.slash_handler = SlashCommandHandler()

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="output-container"):
            yield OutputPanel(id="output")

        with Vertical(id="input-container"):
            yield InputPanel(id="input")

        yield StatusBar(id="status")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the agent when the app mounts."""
        self.output = self.query_one("#output", OutputPanel)
        self.input = self.query_one("#input", InputPanel)
        self.status = self.query_one("#status", StatusBar)

        self.status.update_status(model=self.model_display, working_dir=self.project_path)

        self.output.add_system_message(
            "Enter send │ Ctrl+K model │ Ctrl+O files │ F1 help"
        )
        self.output.add_system_message(f"📁 {self.project_path}")

        try:
            self.agent = create_coding_agent(
                project_path=self.project_path,
                model=self.model
            )
            self.output.add_system_message("✓ Agent ready")
        except Exception as e:
            self.output.add_error_message(f"Failed to initialize agent: {e}")

        self.input.focus()

    def on_input_panel_submitted(self, event: InputPanel.Submitted) -> None:
        """Handle submit from input panel."""
        message = event.value
        if not message:
            return

        self.output.add_user_message(message)

        if self.slash_handler.is_slash_command(message):
            self._handle_slash_command(message)
        else:
            asyncio.create_task(self._process_message(message))

    async def _process_message(self, message: str) -> None:
        """Process a user message with the agent using streaming."""
        if not self.agent:
            self.output.add_error_message("Agent not initialized")
            return

        try:
            self.status.update_status(status="thinking")

            # Use async streaming with event handling
            response_stream: AsyncIterator[RunOutputEvent] = self.agent.arun(
                message,
                session_id=self.session_id,
                stream=True,
                stream_events=True,  # Get tool call events too
            )

            has_content = False
            final_response = None

            async for event in response_stream:
                if isinstance(event, RunContentEvent):
                    # Stream content chunks
                    if event.content:
                        if not has_content:
                            self.output.start_streaming()
                            has_content = True
                        self.output.append_to_stream(event.content)

                elif isinstance(event, ToolCallStartedEvent):
                    # Tool call started
                    tool = event.tool
                    if tool:
                        tool_id = tool.tool_call_id or tool.tool_name
                        self.output.add_tool_call_started(
                            tool_id=tool_id,
                            tool_name=tool.tool_name,
                            tool_args=tool.tool_args,
                        )
                        self.status.update_status(status=f"running: {tool.tool_name}")

                elif isinstance(event, ToolCallCompletedEvent):
                    # Tool call completed
                    tool = event.tool
                    if tool:
                        tool_id = tool.tool_call_id or tool.tool_name
                        # Check if tool had an error
                        if tool.error:
                            self.output.mark_tool_call_error(tool_id, str(tool.error))
                        else:
                            result_preview = None
                            if tool.result is not None:
                                result_preview = str(tool.result)
                            self.output.mark_tool_call_completed(tool_id, result_preview)

                elif isinstance(event, RunCompletedEvent):
                    # Run completed - capture final response for metrics
                    final_response = event

            # Finalize streaming content as markdown
            if has_content:
                self.output.finalize_streaming_as_markdown()
            else:
                self.output.add_system_message("Agent provided no response")

            # Extract session_id and update metrics
            if final_response:
                if not self.session_id and hasattr(final_response, 'session_id'):
                    self.session_id = final_response.session_id

                # Update token count from metrics
                if hasattr(final_response, 'metrics') and final_response.metrics:
                    run_tokens = getattr(final_response.metrics, 'total_tokens', 0) or 0
                    self.total_tokens += run_tokens

            self.status.update_status(tokens=self.total_tokens, status="ready")

        except Exception as e:
            self.output.add_error_message(f"Error: {e}")
            self.status.update_status(status="error")

    def _handle_slash_command(self, message: str) -> None:
        """Handle a slash command."""
        result = self.slash_handler.execute(message)

        match result["type"]:
            case "info":
                self.output.add_system_message(result["message"])
            case "error":
                self.output.add_error_message(result["message"])
            case "action":
                self._execute_action(result)

    def _execute_action(self, result: dict) -> None:
        """Execute a slash command action."""
        action = result["action"]

        match action:
            case "clear":
                self.action_clear()
            case "exit":
                self.action_quit()
            case "show_context":
                self.output.add_system_message(
                    f"Session: {self.session_id or 'None'}\n"
                    f"Model: {self.model_display}\n"
                    f"Tokens: {self.total_tokens:,}\n"
                    f"Project: {self.project_path}"
                )
            case "switch_model":
                self._switch_model(result["model"])
            case "switch_model_prompt":
                self.action_model_selector()
            case "init_agent_md":
                msg = create_agent_md_template(self.project_path)
                self.output.add_system_message(msg)
            case "open_files":
                self.action_open_files()
            case "show_help":
                self.action_help()
            case _:
                self.output.add_system_message(f"'{action}' not yet implemented")

    def _switch_model(self, new_model: str) -> None:
        """Switch to a new model by string."""
        try:
            provider, model_id = parse_model_string(new_model)
            self._apply_model(provider, model_id)
        except Exception as e:
            self.output.add_error_message(f"Failed to switch: {e}")

    def _apply_model(self, provider: str, model_id: str) -> None:
        """Apply a new model configuration."""
        self.model = create_model(provider, model_id)
        self.model_display = get_model_display_name(self.model)

        self.output.add_system_message(f"Switched to: {self.model_display}")
        self.status.update_status(model=self.model_display)

        self.agent = create_coding_agent(
            project_path=self.project_path,
            model=self.model
        )

    # === Actions ===

    def action_clear(self) -> None:
        """Clear the output panel."""
        self.output.clear_output()
        self.output.add_system_message("Cleared.")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_help(self) -> None:
        """Show help."""
        self._handle_slash_command("/help")

    def action_model_selector(self) -> None:
        """Open the model selector."""
        def handle_model(result: tuple[str, str] | None) -> None:
            if result:
                provider, model_id = result
                try:
                    self._apply_model(provider, model_id)
                except Exception as e:
                    self.output.add_error_message(f"Failed to switch: {e}")

        self.push_screen(ModelSelectorScreen(self.model_display), handle_model)

    def action_open_files(self) -> None:
        """Open the file viewer."""
        def handle_file(file_path: str | None) -> None:
            if file_path:
                self.output.add_system_message(f"Selected: {file_path}")
            self.input.focus()

        self.push_screen(FileViewer(self.project_path), handle_file)


def run_app(
    project_path: str | None = None,
    model: Model | str = "anthropic:claude-sonnet-4-20250514",
    **model_kwargs,
) -> None:
    """Run the TUI application."""
    if isinstance(model, str) and model_kwargs:
        provider, model_id = parse_model_string(model)
        model = create_model(provider, model_id, **model_kwargs)

    app = MiniClaudeCodeApp(project_path=project_path, model=model)
    app.run()
