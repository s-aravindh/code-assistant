"""Context loader — resolves .md and .json config files from context/ folders.

Resolution order (first match wins):
  1. <project_path>/context/   — per-project overrides
  2. <repo_root>/context/      — myassistant's shipped defaults

This allows users to drop a context/ folder in their project and override
any default without touching the myassistant source.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from functools import cached_property


# Directory where myassistant's default context files live
_REPO_CONTEXT_DIR = Path(__file__).parent.parent.parent.parent / "context"


class ContextLoader:
    """Loads and caches config from context/ .md and .json files.

    Args:
        project_path (str | Path): The user's working project directory.
    """

    def __init__(self, project_path: str | Path) -> None:
        self._project_dir = Path(project_path)
        self._project_context_dir = self._project_dir / "context"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve(self, filename: str) -> Path | None:
        """Find the first existing context file in the lookup chain."""
        for base in (self._project_context_dir, _REPO_CONTEXT_DIR):
            candidate = base / filename
            if candidate.exists():
                return candidate
        return None

    def _read_md(self, filename: str, default: str = "") -> str:
        """Read a Markdown file, falling back to default."""
        path = self._resolve(filename)
        if path is None:
            return default
        return path.read_text(encoding="utf-8").strip()

    def _read_json(self, filename: str, default: dict) -> dict:
        """Read a JSON file, falling back to default."""
        path = self._resolve(filename)
        if path is None:
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return default

    # ------------------------------------------------------------------
    # Prompt / context accessors
    # ------------------------------------------------------------------

    @cached_property
    def system_prompt(self) -> str:
        """Base system prompt loaded from context/system_prompt.md."""
        return self._read_md("system_prompt.md")

    def get_project_context(self) -> str | None:
        """Return merged project context from context/project_context.md and AGENT.md.

        Reads project-level context/project_context.md and also the legacy
        AGENT.md from the project root, merging both if present.

        Returns:
            str | None: Merged context string, or None if nothing found.
        """
        context_md = self._read_md("project_context.md")

        # Legacy AGENT.md support — read from project root if it exists
        agent_md = ""
        agent_md_path = self._project_dir / "AGENT.md"
        if agent_md_path.exists():
            try:
                agent_md = agent_md_path.read_text(encoding="utf-8").strip()
            except OSError:
                pass

        parts = [p for p in (context_md, agent_md) if p and p.strip()]
        return "\n\n---\n\n".join(parts) if parts else None

    def get_memory(self) -> str | None:
        """Return persistent memory notes from context/memory.md.

        Only reads from the project-level context/ folder — memory is always
        per-project and cannot be defaulted from the repo.

        Returns:
            str | None: Memory content, or None if file is absent.
        """
        memory_path = self._project_context_dir / "memory.md"
        if not memory_path.exists():
            return None
        try:
            content = memory_path.read_text(encoding="utf-8").strip()
            return content if content else None
        except OSError:
            return None

    # ------------------------------------------------------------------
    # Commands config
    # ------------------------------------------------------------------

    @cached_property
    def _commands(self) -> dict:
        return self._read_json("commands.json", default={"destructive": [], "safe": [], "ignored_paths": []})

    @staticmethod
    def _build_pattern(entries: list[str]) -> re.Pattern:
        """Compile a list of plain-string entries into a single regex.

        Single-word entries (no spaces) get word boundaries so they don't
        match as substrings of other words (e.g. "rm" won't match "firm").
        Phrase entries (containing spaces) are matched as literal substrings.

        Args:
            entries (list[str]): Plain command words or phrases.

        Returns:
            re.Pattern: Compiled case-insensitive pattern. Never matches if empty.
        """
        if not entries:
            return re.compile(r"(?!)")  # never-match

        parts = []
        for entry in entries:
            escaped = re.escape(entry)
            if " " in entry:
                parts.append(escaped)       # phrase: literal substring
            else:
                parts.append(rf"\b{escaped}\b")  # word: boundary-protected
        return re.compile("|".join(parts), re.IGNORECASE)

    @cached_property
    def destructive_pattern(self) -> re.Pattern:
        """Compiled regex from context/commands.json destructive list."""
        return self._build_pattern(self._commands.get("destructive", []))

    @cached_property
    def safe_pattern(self) -> re.Pattern:
        """Compiled regex from context/commands.json safe list."""
        return self._build_pattern(self._commands.get("safe", []))

    @cached_property
    def ignored_paths(self) -> list[str]:
        """Glob patterns of paths the file tool should not access."""
        return self._commands.get("ignored_paths", [])

    def is_destructive(self, command: str) -> bool:
        """Return True if the command matches any destructive pattern.

        Args:
            command (str): Shell command string.

        Returns:
            bool: True if destructive.
        """
        return bool(self.destructive_pattern.search(command))

    def is_safe(self, command: str) -> bool:
        """Return True if the command matches any known-safe pattern.

        Args:
            command (str): Shell command string.

        Returns:
            bool: True if explicitly safe.
        """
        return bool(self.safe_pattern.search(command))

    # ------------------------------------------------------------------
    # Agent settings
    # ------------------------------------------------------------------

    @cached_property
    def agent_settings(self) -> dict:
        """Structured agent settings from context/agent_settings.json."""
        return self._read_json(
            "agent_settings.json",
            default={
                "provider": "anthropic",
                "model_id": "claude-sonnet-4-20250514",
                "base_url": None,
                "api_key": None,
                "num_history_runs": 15,
                "add_history_to_context": True,
                "read_chat_history": True,
                "read_tool_call_history": True,
                "markdown": True,
                "temperature": 0.7,
                "max_tokens": 4096,
                "confirmation_tools": ["run_shell"],
                "unknown_command_behavior": "auto_approve",
            },
        )

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    def get_skills(self):
        """Load agno Skills from context/skills/ folders.

        Loads from repo defaults first, then project-level (project overrides
        repo defaults when skill names collide). Returns None if no skills
        directories exist or no valid skills are found.

        Returns:
            Skills | None: Configured agno Skills instance, or None.
        """
        try:
            from agno.skills import Skills
            from agno.skills.loaders.local import LocalSkills
        except ImportError:
            return None

        loaders = []

        # Repo-level skills (loaded first, project overrides)
        repo_skills = _REPO_CONTEXT_DIR / "skills"
        if repo_skills.is_dir():
            loaders.append(LocalSkills(str(repo_skills), validate=True))

        # Project-level skills (loaded last, highest priority)
        project_skills = self._project_context_dir / "skills"
        if project_skills.is_dir():
            loaders.append(LocalSkills(str(project_skills), validate=True))

        if not loaders:
            return None

        try:
            skills = Skills(loaders=loaders)
            if not skills.get_all_skills():
                return None
            return skills
        except Exception:
            return None
