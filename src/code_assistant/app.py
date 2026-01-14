"""Main TUI application for Mini-Claude-Code."""

import asyncio
import uuid
from pathlib import Path
from typing import AsyncIterator, Optional

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
from code_assistant.config.settings import Settings
from code_assistant.ui.components import (
    InputPanel,
    OutputPanel,
    StatusBar,
    FileViewer,
    ModelSelectorScreen,
    ApprovalDialog,
)
from code_assistant.utils.logger import create_logger
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
        Binding("ctrl+q", "quit", "Quit", priority=True),
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
        log_dir: str | Path | None = None,
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
        self.session_id = str(uuid.uuid4())
        self.total_tokens = 0
        self.slash_handler = SlashCommandHandler()
        
        # Initialize logger
        settings = Settings()
        self.logger = create_logger(
            session_id=self.session_id,
            log_dir=log_dir or settings.log_file,
            project_path=self.project_path,
            level=settings.log_level,
        )
        self.logger.info(f"App started: model={self.model_display}, path={self.project_path}")

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
            "Enter send │ Ctrl+Q quit │ Ctrl+K model │ Ctrl+O files │ F1 help"
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
        """Process a user message with the agent using streaming.
        
        Uses Agno's HITL pattern:
        1. Stream events from agent.arun()
        2. If run_event.is_paused, handle tool confirmations
        3. Use acontinue_run(run_response=run_event) to resume
        4. Loop while is_paused to handle multiple confirmation rounds
        """
        if not self.agent:
            self.output.add_error_message("Agent not initialized")
            self.logger.error("Agent not initialized")
            return

        try:
            self.status.update_status(status="thinking")
            self.logger.info(f"User: {message[:100]}...")

            has_content = False
            final_response = None
            
            # Initial run with streaming
            run_result = await self._stream_run(
                self.agent.arun(
                    message,
                    session_id=self.session_id,
                    stream=True,
                    stream_events=True,
                ),
                has_content,
            )
            has_content = run_result["has_content"]
            final_response = run_result.get("final_response")
            run_event = run_result.get("run_event")
            
            # HITL loop: handle pauses and continue until complete
            while run_event and hasattr(run_event, 'is_paused') and run_event.is_paused:
                self.logger.info("Run paused - waiting for tool confirmations")
                
                # For streaming HITL, tools requiring confirmation are in run_event.tools
                tools_to_confirm = getattr(run_event, 'tools', None) or []
                
                for tool in tools_to_confirm:
                    tool_name = getattr(tool, 'tool_name', 'unknown')
                    tool_args = getattr(tool, 'tool_args', {}) or {}
                    
                    # Check if this tool requires confirmation
                    if getattr(tool, 'confirmation_required', False) or getattr(tool, 'requires_confirmation', False):
                        self.logger.info(f"Tool awaiting confirmation: {tool_name}")
                        
                        # Show approval dialog
                        approved = await self._show_approval_dialog(
                            tool_name=tool_name,
                            tool_args=tool_args,
                        )
                        
                        if approved:
                            tool.confirmed = True
                            self.logger.info(f"Tool confirmed: {tool_name}")
                        else:
                            tool.confirmed = False
                            self.logger.info(f"Tool rejected: {tool_name}")
                            self.output.add_system_message(f"Tool call rejected: {tool_name}")
                
                # Continue the run after handling confirmations
                run_id = getattr(run_event, 'run_id', None)
                self.logger.info(f"Continuing run: {run_id}")
                self.status.update_status(status="continuing")
                
                # Continue using run_id and updated_tools pattern for streaming
                continue_result = await self._stream_run(
                    self.agent.acontinue_run(
                        run_id=run_id,
                        updated_tools=tools_to_confirm,
                        stream=True,
                        stream_events=True,
                        session_id=self.session_id,
                    ),
                    has_content,
                )
                has_content = continue_result["has_content"]
                final_response = continue_result.get("final_response") or final_response
                run_event = continue_result.get("run_event")

            # Finalize streaming content as markdown
            if has_content:
                self.output.finalize_streaming_as_markdown()
            else:
                self.output.add_system_message("Agent provided no response")

            # Extract session_id and update metrics
            if final_response:
                if hasattr(final_response, 'session_id') and final_response.session_id:
                    self.session_id = final_response.session_id

                # Update token count from metrics
                if hasattr(final_response, 'metrics') and final_response.metrics:
                    run_tokens = getattr(final_response.metrics, 'total_tokens', 0) or 0
                    self.total_tokens += run_tokens
                    self.logger.info(f"Response: {run_tokens} tokens")

            self.status.update_status(tokens=self.total_tokens, status="ready")

        except Exception as e:
            self.logger.exception(f"Error: {e}")
            self.output.add_error_message(f"Error: {e}")
            self.status.update_status(status="error")

    async def _stream_run(
        self,
        response_stream: AsyncIterator[RunOutputEvent],
        has_content: bool,
    ) -> dict:
        """Stream events from an agent run and return the final state.
        
        Args:
            response_stream: Async iterator of run events
            has_content: Whether content has been streamed already
            
        Returns:
            dict with keys:
              - has_content: bool
              - final_response: RunCompletedEvent or None
              - run_event: Last event (may have is_paused=True)
        """
        final_response = None
        run_event = None
        
        async for event in response_stream:
            run_event = event
            
            # Check if this is a paused event - stop processing and return
            if hasattr(event, 'is_paused') and event.is_paused:
                self.logger.debug("Received paused event, returning for HITL handling")
                break
            
            # Handle regular events
            has_content = await self._handle_event(event, has_content)
            
            if isinstance(event, RunCompletedEvent):
                final_response = event
        
        return {
            "has_content": has_content,
            "final_response": final_response,
            "run_event": run_event,
        }

    async def _handle_event(self, event: RunOutputEvent, has_content: bool) -> bool:
        """Handle a single event and return updated has_content status.
        
        Maintains proper event ordering:
        - Content before tool calls is finalized when tool starts
        - Content after tool calls gets a new streaming container
        """
        if isinstance(event, RunContentEvent):
            # Stream content chunks
            if event.content:
                if not has_content:
                    self.output.start_streaming()
                    has_content = True
                self.output.append_to_stream(event.content)
                self.logger.debug(f"Chunk: {len(event.content)} chars")

        elif isinstance(event, ToolCallStartedEvent):
            # Tool call started
            tool = event.tool
            if tool:
                tool_id = tool.tool_call_id or tool.tool_name
                tool_name = tool.tool_name
                tool_args = tool.tool_args or {}
                
                self.logger.info(f"Tool started: {tool_name}")
                # add_tool_call_started will finalize any current streaming content
                # This ensures content appears BEFORE the tool widget
                self.output.add_tool_call_started(
                    tool_id=tool_id,
                    tool_name=tool_name,
                    tool_args=tool_args,
                )
                self.status.update_status(status=f"running: {tool_name}")
                # Reset has_content so content AFTER tool call gets a new container
                has_content = False

        elif isinstance(event, ToolCallCompletedEvent):
            # Tool call completed
            tool = event.tool
            if tool:
                tool_id = tool.tool_call_id or tool.tool_name
                tool_name = tool.tool_name
                
                # Agno's ToolExecution may or may not expose an error field depending on backend.
                error = getattr(tool, "error", None)
                if error:
                    self.logger.error(f"Tool error: {tool_name} - {error}")
                    self.output.mark_tool_call_error(tool_id, str(error))
                else:
                    result_preview = None
                    if getattr(tool, "result", None) is not None:
                        result_preview = str(tool.result)
                    self.logger.info(f"Tool done: {tool_name}")
                    self.output.mark_tool_call_completed(tool_id, result_preview)

        return has_content

    async def _show_approval_dialog(self, tool_name: str, tool_args: dict) -> bool:
        """Show approval dialog and return True if approved."""
        # Create a message describing the operation
        operation_desc = self._get_operation_description(tool_name, tool_args)
        
        dialog = ApprovalDialog(
            title=f"Approve {tool_name}?",
            message=operation_desc,
            tool_name=tool_name,
            tool_args=tool_args,
        )
        
        # Use Future to wait for dialog result
        future = asyncio.Future()
        
        def handle_result(result: str | None) -> None:
            if not future.done():
                future.set_result(result == "approved")
        
        self.push_screen(dialog, handle_result)
        result = await future
        return result

    def _get_operation_description(self, tool_name: str, tool_args: dict) -> str:
        """Get a human-readable description of the operation."""
        if tool_name == "write_file":
            file_path = tool_args.get("file_path", "unknown")
            content_len = len(str(tool_args.get("content", "")))
            return f"Write {content_len} characters to {file_path}"
        elif tool_name == "edit_file":
            file_path = tool_args.get("file_path", "unknown")
            return f"Edit file {file_path}"
        elif tool_name == "delete_file":
            file_path = tool_args.get("file_path", "unknown")
            return f"Delete file {file_path}"
        elif tool_name == "run_command":
            command = tool_args.get("command", "unknown")
            return f"Execute command: {command}"
        elif tool_name == "git_commit":
            message = tool_args.get("message", "unknown")
            return f"Create git commit: {message}"
        else:
            return f"Execute {tool_name} with provided arguments"

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
    log_dir: str | Path | None = None,
    **model_kwargs,
) -> None:
    """Run the TUI application.
    
    Args:
        project_path: Path to the project directory
        model: Model string or Model instance
        log_dir: Custom log directory (defaults to project_path/mcc_logs)
        **model_kwargs: Additional model parameters
    """
    if isinstance(model, str) and model_kwargs:
        provider, model_id = parse_model_string(model)
        model = create_model(provider, model_id, **model_kwargs)

    app = MiniClaudeCodeApp(project_path=project_path, model=model, log_dir=log_dir)
    app.run()
