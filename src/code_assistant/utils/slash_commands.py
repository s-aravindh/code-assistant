"""Slash command parsing and handling."""

from typing import Any

# Type aliases for clarity
CommandResult = dict[str, Any]
CommandArgs = list[str]

HELP_TEXT = """
**Available Commands:**

**Session:**
- `/help` - Show this help message
- `/clear` - Clear conversation history
- `/compact` - Summarize conversation to save tokens
- `/exit`, `/quit` - Exit the application

**Info:**
- `/context` - Show current session info (model, tokens)
- `/config` - Show current configuration
- `/memory` - Show agent memory entries
- `/cost` - Show token usage and estimated cost

**Model:**
- `/model <name>` - Switch to a different model

**Git:**
- `/init` - Analyze project and create AGENT.md
- `/review` - Review current git changes
- `/commit` - Generate commit message and commit

**Advanced:**
- `/plan <requirement>` - Create implementation plan
- `/bug <description>` - Start debugging workflow
- `/test` - Generate tests for recent changes
"""


def _action(name: str, **kwargs: Any) -> CommandResult:
    """Create an action result."""
    return {"type": "action", "action": name, **kwargs}


def _error(message: str) -> CommandResult:
    """Create an error result."""
    return {"type": "error", "message": message}


def _info(message: str) -> CommandResult:
    """Create an info result."""
    return {"type": "info", "message": message}


class SlashCommandHandler:
    """Handler for slash commands in the chat."""

    def __init__(self):
        self._commands = {
            "/help": self._help,
            "/clear": lambda _: _action("clear"),
            "/compact": lambda _: _action("compact"),
            "/context": lambda _: _action("show_context"),
            "/config": lambda _: _action("show_config"),
            "/memory": lambda _: _action("show_memory"),
            "/cost": lambda _: _action("show_cost"),
            "/exit": lambda _: _action("exit"),
            "/quit": lambda _: _action("exit"),
            "/init": lambda _: _action("init_smart"),
            "/review": lambda _: _action("git_review"),
            "/commit": lambda _: _action("git_commit"),
            "/model": self._model,
            "/plan": self._plan,
            "/bug": self._bug,
            "/test": lambda _: _action("generate_tests"),
        }

    def is_slash_command(self, message: str) -> bool:
        """Check if a message is a slash command."""
        return message.strip().startswith("/")

    def parse_command(self, message: str) -> tuple[str, CommandArgs]:
        """Parse a slash command into command and arguments."""
        parts = message.strip().split()
        command = parts[0] if parts else ""
        args = parts[1:]
        return command, args

    def execute(self, message: str) -> CommandResult:
        """Execute a slash command."""
        command, args = self.parse_command(message)

        if command not in self._commands:
            return _error(f"Unknown command: {command}. Type /help for available commands.")

        return self._commands[command](args)

    def _help(self, args: CommandArgs) -> CommandResult:
        return _info(HELP_TEXT)

    def _model(self, args: CommandArgs) -> CommandResult:
        if not args:
            return _error("Usage: /model <model_name>")
        return _action("switch_model", model=" ".join(args))

    def _plan(self, args: CommandArgs) -> CommandResult:
        if not args:
            return _error("Usage: /plan <requirement description>")
        requirement = " ".join(args)
        return _action("run_plan_agent", requirement=requirement)

    def _bug(self, args: CommandArgs) -> CommandResult:
        if not args:
            return _error("Usage: /bug <bug description or error message>")
        description = " ".join(args)
        return _action("debug_bug", description=description)
