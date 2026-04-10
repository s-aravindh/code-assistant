"""Custom coding toolkit — file operations and shell execution in one class.

Four core tools: read_file, write_file, edit_file, run_shell.
grep / find / ls are intentionally omitted — the agent uses run_shell for those
(e.g. `grep -rn pattern src/`, `ls -la`, `find . -name '*.py'`).

This toolkit replaces agno's built-in CodingTools so we can customise every
aspect: path filtering, ignored paths, docstrings, and confirmation behaviour.
Extend this class or add new methods to add project-specific tools.
"""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path
from typing import Optional

from agno.tools import Toolkit

from myassistant.config.context_loader import ContextLoader


class CodingTool(Toolkit):
    """File operations + shell execution for the coding assistant.

    All paths are resolved relative to base_dir. File access to ignored paths
    (from context/commands.json) is blocked. Shell commands require HITL
    confirmation; the app layer auto-approves safe commands and shows a dialog
    for destructive ones.

    Args:
        base_dir (str | Path): Working directory — all relative paths resolve here.
        context_loader (ContextLoader): Loaded context config (ignored paths, etc.).
        shell_timeout (int): Default timeout in seconds for shell commands.
        max_read_bytes (int): Maximum bytes returned by read_file.
    """

    def __init__(
        self,
        base_dir: str | Path,
        context_loader: ContextLoader,
        shell_timeout: int = 120,
        max_read_bytes: int = 50_000,
    ) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.context_loader = context_loader
        self.shell_timeout = shell_timeout
        self.max_read_bytes = max_read_bytes

        super().__init__(
            name="coding_tool",
            tools=[
                self.read_file,
                self.write_file,
                self.edit_file,
                self.run_shell,
            ],
            requires_confirmation_tools=context_loader.agent_settings.get(
                "confirmation_tools", ["run_shell"]
            ),
            add_instructions=True,
        )

    # ------------------------------------------------------------------
    # Internal path helpers
    # ------------------------------------------------------------------

    def _resolve_path(self, path: str) -> Path:
        """Resolve a relative or absolute path under base_dir."""
        resolved = (self.base_dir / path).resolve()
        if not str(resolved).startswith(str(self.base_dir)):
            raise PermissionError(f"Path '{path}' is outside the base directory.")
        return resolved

    def _is_ignored(self, path: Path) -> bool:
        """Return True if the path matches any ignored_paths glob pattern."""
        rel = str(path.relative_to(self.base_dir))
        return any(fnmatch.fnmatch(rel, pat) for pat in self.context_loader.ignored_paths)

    # ------------------------------------------------------------------
    # File tools
    # ------------------------------------------------------------------

    def read_file(self, path: str, offset: int = 0, limit: Optional[int] = None) -> str:
        """Read the contents of a file with optional line range.

        Always read a file before editing it to understand its current contents.
        Use offset and limit to paginate large files. Line numbers are shown for reference.

        :param path: Path to the file (relative to project root).
        :param offset: Zero-based line number to start reading from (default: 0).
        :param limit: Maximum number of lines to return. Reads entire file if not set.
        :return: File contents with line numbers, or an error message.
        """
        try:
            resolved = self._resolve_path(path)
        except PermissionError as e:
            return f"Error: {e}"

        if not resolved.exists():
            return f"Error: File not found: {path}"
        if not resolved.is_file():
            return f"Error: Not a file: {path}"
        if self._is_ignored(resolved):
            return f"Error: Path '{path}' is in the ignored list."

        try:
            raw = resolved.read_bytes()
            if len(raw) > self.max_read_bytes:
                raw = raw[: self.max_read_bytes]
                truncated = True
            else:
                truncated = False

            text = raw.decode("utf-8", errors="replace")
            lines = text.splitlines()
            subset = lines[offset : offset + limit] if limit is not None else lines[offset:]
            numbered = "\n".join(f"{offset + i + 1:4}: {line}" for i, line in enumerate(subset))

            footer = ""
            if truncated:
                footer = f"\n[File truncated at {self.max_read_bytes} bytes]"
            return numbered + footer

        except OSError as e:
            return f"Error reading file: {e}"

    def write_file(self, path: str, content: str) -> str:
        """Create a new file or overwrite an existing one.

        Use this for creating new files. For modifying existing files, prefer edit_file.
        Parent directories are created automatically.

        :param path: Destination path (relative to project root).
        :param content: Full content to write.
        :return: Success message or an error message.
        """
        try:
            resolved = self._resolve_path(path)
        except PermissionError as e:
            return f"Error: {e}"

        if self._is_ignored(resolved):
            return f"Error: Path '{path}' is in the ignored list."

        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            return f"Wrote {len(content)} characters to {path}"
        except OSError as e:
            return f"Error writing file: {e}"

    def edit_file(self, path: str, old_text: str, new_text: str) -> str:
        """Make a precise find-and-replace edit inside a file.

        The old_text must match exactly one location, including all whitespace and indentation.
        Include enough surrounding context to guarantee a unique match.
        Always read the file first to confirm the exact text.

        :param path: Path to the file (relative to project root).
        :param old_text: The exact text to replace.
        :param new_text: The replacement text.
        :return: Success message or an error message.
        """
        try:
            resolved = self._resolve_path(path)
        except PermissionError as e:
            return f"Error: {e}"

        if not resolved.exists():
            return f"Error: File not found: {path}"
        if self._is_ignored(resolved):
            return f"Error: Path '{path}' is in the ignored list."

        try:
            original = resolved.read_text(encoding="utf-8")
        except OSError as e:
            return f"Error reading file: {e}"

        count = original.count(old_text)
        if count == 0:
            return "Error: old_text not found in file. Check whitespace and indentation."
        if count > 1:
            return f"Error: old_text matched {count} locations. Provide more context to make it unique."

        updated = original.replace(old_text, new_text, 1)
        try:
            resolved.write_text(updated, encoding="utf-8")
        except OSError as e:
            return f"Error writing file: {e}"

        lines_changed = new_text.count("\n") - old_text.count("\n")
        return f"Edit applied to {path} ({lines_changed:+d} lines)"

    # ------------------------------------------------------------------
    # Shell tool
    # ------------------------------------------------------------------

    def run_shell(self, command: str, timeout: Optional[int] = None) -> str:
        """Execute a shell command in the project directory.

        Use for running tests, git, package managers, file search (grep/find/ls), and more.
        Commands run from the project root. Output is truncated if too long.
        Destructive commands require user confirmation (handled by the app layer).

        Examples:
          - List files:    ls -la src/
          - Search code:   grep -rn "def create" src/
          - Find files:    find . -name "*.py" -type f
          - Run tests:     pytest tests/ -v
          - Git status:    git status

        :param command: Shell command string to execute.
        :param timeout: Override the default timeout in seconds.
        :return: Combined stdout + stderr, or an error message.
        """
        effective_timeout = timeout if timeout is not None else self.shell_timeout
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=str(self.base_dir),
            )
            output = result.stdout
            if result.stderr:
                output += ("\n" if output else "") + result.stderr

            # Truncate very long output
            max_chars = 20_000
            if len(output) > max_chars:
                output = output[:max_chars] + f"\n[Output truncated at {max_chars} characters]"

            return output or "(no output)"

        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {effective_timeout} seconds"
        except Exception as e:
            return f"Error running command: {e}"

