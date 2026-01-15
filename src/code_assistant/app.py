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
from code_assistant.agent.memory import create_agent_md_template, parse_agent_md
from code_assistant.agent.specialized_agents import (
    run_init_agent,
    run_plan_agent,
)
from code_assistant.config.models import create_model, parse_model_string, get_model_display_name
from code_assistant.config.settings import Settings
from code_assistant.storage.conversation import save_conversation, load_conversation
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
from code_assistant.utils.cost import format_cost_display, calculate_session_cost


def safe_stringify(value, max_len: int | None = None) -> str | None:
    """Safely convert a value to string, handling complex objects.
    
    Args:
        value: The value to convert
        max_len: Optional maximum length to truncate to
        
    Returns:
        String representation or None if value is None
    """
    if value is None:
        return None
    
    try:
        if isinstance(value, (dict, list, tuple)):
            result_str = repr(value)
        else:
            result_str = str(value)
    except Exception:
        result_str = "<unable to stringify>"
    
    if max_len and len(result_str) > max_len:
        result_str = result_str[:max_len]
    
    return result_str


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
        self.input_tokens = 0
        self.output_tokens = 0
        self.slash_handler = SlashCommandHandler()
        
        # Context file management
        self.context_files: set[str] = set()
        
        # Conversation messages for save/load
        self.messages: list[dict] = []
        
        # Settings
        self.settings = Settings()
        
        # Initialize logger with rotation settings
        self.logger = create_logger(
            session_id=self.session_id,
            log_dir=log_dir or self.settings.log_file,
            project_path=self.project_path,
            level=self.settings.log_level,
            max_size_mb=self.settings.log_max_size_mb,
            backup_count=self.settings.log_backup_count,
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
                    error_str = safe_stringify(error)
                    self.output.mark_tool_call_error(tool_id, error_str)
                else:
                    result_preview = safe_stringify(getattr(tool, "result", None))
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

    def _validate_agent_md_content(self, content: str) -> bool:
        """Validate that content looks like a valid AGENT.md file.
        
        Args:
            content: The content to validate
            
        Returns:
            True if content appears valid, False otherwise
        """
        if not content:
            return False
        
        # Should start with a markdown heading
        lines = content.strip().split('\n')
        first_line = lines[0].strip()
        
        # Check if it starts with a heading (# or ##)
        if not first_line.startswith('#'):
            return False
        
        # Should have some minimum content (at least a few lines)
        if len(lines) < 3:
            return False
        
        # Should contain at least one section heading
        has_section = any(line.strip().startswith('##') for line in lines[1:])
        
        return has_section

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
            # Session commands
            case "clear":
                self.action_clear()
            case "exit":
                self.action_quit()
            case "compact":
                asyncio.create_task(self._compact_conversation())
            
            # Context commands
            case "show_context":
                context_info = self._get_context_info()
                self.output.add_system_message(context_info)
            case "add_files":
                msg = self._add_context_files(result.get("files", []))
                self.output.add_system_message(msg)
            case "remove_files":
                msg = self._remove_context_files(result.get("files", []))
                self.output.add_system_message(msg)
            
            # Model commands
            case "switch_model":
                self._switch_model(result["model"])
            case "switch_model_prompt":
                self.action_model_selector()
            
            # Conversation persistence
            case "save_conversation":
                msg = self._save_conversation(result.get("filename", "conversation.md"))
                self.output.add_system_message(msg)
            case "load_conversation":
                msg = self._load_conversation(result.get("filename", ""))
                self.output.add_system_message(msg)
            
            # Config and memory
            case "show_config":
                config_info = self._get_config_info()
                self.output.add_system_message(config_info)
            case "show_memory":
                memory_info = self._get_memory_info()
                self.output.add_system_message(memory_info)
            case "show_cost":
                cost_info = format_cost_display(
                    self.model_display,
                    self.total_tokens,
                    self.input_tokens if self.input_tokens > 0 else None,
                    self.output_tokens if self.output_tokens > 0 else None,
                )
                self.output.add_system_message(cost_info)
            
            # AGENT.md commands
            case "init_agent_md":
                # Legacy: simple template creation
                msg = create_agent_md_template(self.project_path)
                self.output.add_system_message(msg)
            case "init_smart":
                # Smart: use agent to analyze project
                asyncio.create_task(self._run_init_agent())
            
            # Git commands
            case "git_review":
                asyncio.create_task(self._run_git_review())
            case "git_commit":
                asyncio.create_task(self._run_git_commit())
            
            # Advanced agents
            case "run_plan_agent":
                asyncio.create_task(self._run_plan_agent(result["requirement"]))
            case "debug_bug":
                asyncio.create_task(self._run_debug_agent(result["description"]))
            case "generate_tests":
                asyncio.create_task(self._run_test_generator())
            
            # File viewer
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

    # === Context and File Management ===

    def _get_context_info(self) -> str:
        """Get current context information."""
        parts = [
            f"**Session**: {self.session_id[:8]}...",
            f"**Model**: {self.model_display}",
            f"**Tokens**: {self.total_tokens:,}",
            f"**Project**: {self.project_path}",
        ]
        
        if self.context_files:
            parts.append(f"**Context Files** ({len(self.context_files)}):")
            for f in sorted(self.context_files)[:10]:
                parts.append(f"  - {f}")
            if len(self.context_files) > 10:
                parts.append(f"  ... and {len(self.context_files) - 10} more")
        else:
            parts.append("**Context Files**: None")
        
        return "\n".join(parts)

    def _add_context_files(self, files: list[str]) -> str:
        """Add files to context.
        
        Args:
            files: List of file paths to add
            
        Returns:
            Status message
        """
        added = []
        errors = []
        
        for file_path in files:
            path = Path(self.project_path) / file_path
            if path.exists() and path.is_file():
                self.context_files.add(file_path)
                added.append(file_path)
            else:
                errors.append(f"{file_path} (not found)")
        
        parts = []
        if added:
            parts.append(f"Added {len(added)} file(s) to context: {', '.join(added)}")
        if errors:
            parts.append(f"Failed to add: {', '.join(errors)}")
        
        return "\n".join(parts) if parts else "No files specified"

    def _remove_context_files(self, files: list[str]) -> str:
        """Remove files from context.
        
        Args:
            files: List of file paths to remove
            
        Returns:
            Status message
        """
        removed = []
        not_found = []
        
        for file_path in files:
            if file_path in self.context_files:
                self.context_files.remove(file_path)
                removed.append(file_path)
            else:
                not_found.append(file_path)
        
        parts = []
        if removed:
            parts.append(f"Removed {len(removed)} file(s) from context: {', '.join(removed)}")
        if not_found:
            parts.append(f"Not in context: {', '.join(not_found)}")
        
        return "\n".join(parts) if parts else "No files specified"

    # === Conversation Persistence ===

    def _save_conversation(self, filename: str) -> str:
        """Save the current conversation to a file.
        
        Args:
            filename: File to save to
            
        Returns:
            Status message
        """
        return save_conversation(
            session_id=self.session_id,
            messages=self.messages,
            filename=filename,
            project_path=self.project_path,
            model_name=self.model_display,
            total_tokens=self.total_tokens,
        )

    def _load_conversation(self, filename: str) -> str:
        """Load a conversation from a file.
        
        Args:
            filename: File to load from
            
        Returns:
            Status message
        """
        if not filename:
            return "Usage: /load <filename>"
        
        session_id, messages, msg = load_conversation(filename)
        
        if session_id:
            self.session_id = session_id
            self.messages = messages
            self.logger.info(f"Loaded conversation from {filename}")
        
        return msg

    # === Config and Memory ===

    def _get_config_info(self) -> str:
        """Get current configuration settings."""
        return (
            f"**Configuration**\n\n"
            f"**Provider**: {self.settings.provider}\n"
            f"**Model**: {self.settings.model}\n"
            f"**Temperature**: {self.settings.temperature}\n"
            f"**Max Tokens**: {self.settings.max_tokens}\n\n"
            f"**Behavior**\n"
            f"- Confirm writes: {self.settings.confirm_before_write}\n"
            f"- Confirm execute: {self.settings.confirm_before_execute}\n"
            f"- Auto-approve reads: {self.settings.auto_approve_reads}\n\n"
            f"**Logging**: {self.settings.log_level}"
        )

    def _get_memory_info(self) -> str:
        """Get agent memory information."""
        if not self.agent:
            return "Agent not initialized"
        
        # Try to access agent's memory
        memory_info = ["**Agent Memory**\n"]
        
        # Check for user memories
        if hasattr(self.agent, 'memory') and self.agent.memory:
            memories = self.agent.memory
            if hasattr(memories, 'get_memories'):
                user_memories = memories.get_memories()
                if user_memories:
                    memory_info.append(f"**User Memories** ({len(user_memories)}):")
                    for mem in user_memories[:5]:
                        memory_info.append(f"  - {mem[:100]}...")
                    if len(user_memories) > 5:
                        memory_info.append(f"  ... and {len(user_memories) - 5} more")
                else:
                    memory_info.append("No user memories stored")
            else:
                memory_info.append("Memory system active (details not accessible)")
        else:
            memory_info.append("Memory system: Enabled (using Agno default)")
        
        memory_info.append(f"\n**History Runs**: {getattr(self.agent, 'num_history_runs', 'N/A')}")
        
        return "\n".join(memory_info)

    # === Conversation Compaction ===

    async def _compact_conversation(self) -> None:
        """Summarize and compact the conversation history."""
        if not self.agent:
            self.output.add_error_message("Agent not initialized")
            return
        
        self.output.add_system_message("Compacting conversation history...")
        self.status.update_status(status="compacting")
        
        try:
            # Use the agent to summarize
            prompt = """Please provide a brief summary of our conversation so far. 
Include:
1. Main topics discussed
2. Key decisions made
3. Files modified or created
4. Important context to remember

Keep it concise but comprehensive."""

            has_content = False
            async for event in self.agent.arun(
                prompt,
                session_id=self.session_id,
                stream=True,
                stream_events=True,
            ):
                if isinstance(event, RunContentEvent) and event.content:
                    if not has_content:
                        self.output.start_streaming()
                        has_content = True
                    self.output.append_to_stream(event.content)
            
            if has_content:
                self.output.finalize_streaming_as_markdown()
            
            self.output.add_system_message("Conversation compacted. Old history summarized.")
            self.status.update_status(status="ready")
            
        except Exception as e:
            self.logger.exception(f"Compact error: {e}")
            self.output.add_error_message(f"Failed to compact: {e}")
            self.status.update_status(status="error")

    # === Git Commands ===

    async def _run_git_review(self) -> None:
        """Review current git changes."""
        if not self.agent:
            self.output.add_error_message("Agent not initialized")
            return
        
        self.output.add_system_message("Reviewing git changes...")
        
        prompt = """Review the current git changes:

1. First, run `git status` to see the current state
2. Run `git diff` to see unstaged changes
3. Run `git diff --cached` to see staged changes
4. Provide a summary of what has changed

Be concise and highlight important changes."""

        await self._process_message(prompt)

    async def _run_git_commit(self) -> None:
        """Generate commit message and create commit."""
        if not self.agent:
            self.output.add_error_message("Agent not initialized")
            return
        
        self.output.add_system_message("Generating commit...")
        
        prompt = """Help me create a git commit:

1. First, run `git status` and `git diff --cached` to see what's staged
2. If nothing is staged, run `git diff` to see unstaged changes
3. Analyze the changes and suggest a commit message following conventional commits format
4. Ask for confirmation before running `git commit`

The commit message should be clear and describe WHY the changes were made."""

        await self._process_message(prompt)

    # === Specialized Agent Runners ===

    async def _run_init_agent(self) -> None:
        """Run the init agent to analyze project and create AGENT.md."""
        from pathlib import Path
        
        agent_md_path = Path(self.project_path) / "AGENT.md"
        if agent_md_path.exists():
            self.output.add_system_message("AGENT.md already exists. Analyzing to update...")
        
        self.output.add_system_message("🔍 Analyzing project structure...")
        self.status.update_status(status="analyzing project")
        
        try:
            has_content = False
            content_buffer = ""
            
            async for event in run_init_agent(
                self.project_path,
                self.model,
                session_id=f"{self.session_id}-init",
            ):
                if isinstance(event, RunContentEvent) and event.content:
                    if not has_content:
                        self.output.start_streaming()
                        has_content = True
                    self.output.append_to_stream(event.content)
                    content_buffer += event.content
                elif isinstance(event, ToolCallStartedEvent):
                    tool = event.tool
                    if tool:
                        self.output.add_tool_call_started(
                            tool_id=tool.tool_call_id or tool.tool_name,
                            tool_name=tool.tool_name,
                            tool_args=tool.tool_args or {},
                        )
                        has_content = False  # Reset for new content after tool
                elif isinstance(event, ToolCallCompletedEvent):
                    tool = event.tool
                    if tool:
                        self.output.mark_tool_call_completed(
                            tool_id=tool.tool_call_id or tool.tool_name,
                            result=safe_stringify(getattr(tool, "result", None), max_len=200),
                        )
            
            if has_content:
                self.output.finalize_streaming_as_markdown()
            
            # Try to extract and save AGENT.md content
            if content_buffer:
                content_stripped = content_buffer.strip()
                
                # Validate content looks like markdown (should start with a heading)
                if not content_stripped:
                    self.output.add_error_message("Generated content is empty")
                elif not self._validate_agent_md_content(content_stripped):
                    self.output.add_error_message(
                        "Generated content doesn't appear to be valid AGENT.md format. "
                        "Expected markdown starting with a heading (#)."
                    )
                else:
                    # Content is valid, write it
                    agent_md_path.write_text(content_stripped, encoding='utf-8')
                    self.output.add_system_message(f"✅ Created/Updated AGENT.md at {agent_md_path}")
                    
                    # Reload agent with new context
                    project_context = parse_agent_md(self.project_path)
                    if project_context:
                        self.agent = create_coding_agent(
                            project_path=self.project_path,
                            model=self.model,
                            project_context=project_context,
                        )
                        self.output.add_system_message("✅ Agent reloaded with project context")
            
            self.status.update_status(status="ready")
            
        except Exception as e:
            self.logger.exception(f"Init agent error: {e}")
            self.output.add_error_message(f"Init agent failed: {e}")
            self.status.update_status(status="error")

    async def _run_plan_agent(self, requirement: str) -> None:
        """Run the planning agent for a requirement."""
        self.output.add_system_message(f"📋 Creating implementation plan for: {requirement[:50]}...")
        self.status.update_status(status="planning")
        
        try:
            has_content = False
            
            async for event in run_plan_agent(
                self.project_path,
                self.model,
                requirement,
                session_id=f"{self.session_id}-plan",
            ):
                if isinstance(event, RunContentEvent) and event.content:
                    if not has_content:
                        self.output.start_streaming()
                        has_content = True
                    self.output.append_to_stream(event.content)
                elif isinstance(event, ToolCallStartedEvent):
                    tool = event.tool
                    if tool:
                        self.output.add_tool_call_started(
                            tool_id=tool.tool_call_id or tool.tool_name,
                            tool_name=tool.tool_name,
                            tool_args=tool.tool_args or {},
                        )
                        has_content = False
                elif isinstance(event, ToolCallCompletedEvent):
                    tool = event.tool
                    if tool:
                        self.output.mark_tool_call_completed(
                            tool_id=tool.tool_call_id or tool.tool_name,
                            result=safe_stringify(getattr(tool, "result", None), max_len=200),
                        )
            
            if has_content:
                self.output.finalize_streaming_as_markdown()
            
            self.status.update_status(status="ready")
            
        except Exception as e:
            self.logger.exception(f"Plan agent error: {e}")
            self.output.add_error_message(f"Plan agent failed: {e}")
            self.status.update_status(status="error")

    async def _run_debug_agent(self, description: str) -> None:
        """Run the main agent in debug mode for a bug."""
        if not self.agent:
            self.output.add_error_message("Agent not initialized")
            return
        
        self.output.add_system_message(f"🐛 Starting debug session for: {description[:50]}...")
        
        debug_prompt = f"""I need help debugging an issue:

**Bug Description:**
{description}

Please:
1. Analyze the codebase to understand the relevant code
2. Identify potential causes of this bug
3. Suggest fixes with code changes
4. If possible, help me test the fix

Start by searching for relevant code and understanding the context."""

        # Use the main agent with the debug prompt
        await self._process_message(debug_prompt)

    async def _run_test_generator(self) -> None:
        """Generate tests for recent changes."""
        if not self.agent:
            self.output.add_error_message("Agent not initialized")
            return
        
        self.output.add_system_message("🧪 Generating tests for recent changes...")
        
        test_prompt = """Analyze the codebase and generate tests:

1. First, run `git diff HEAD~1` to see recent changes
2. Identify what code was modified or added
3. Generate appropriate unit tests for the changes
4. Follow the existing test patterns in the project

Focus on:
- Testing the new/modified functionality
- Edge cases
- Error handling

Generate the test code and explain what each test covers."""

        await self._process_message(test_prompt)

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
