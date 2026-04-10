"""Tests for ContextLoader."""

import json
import pytest
from pathlib import Path
from myassistant.config.context_loader import ContextLoader


@pytest.fixture
def project_with_context(tmp_path):
    """A temp project directory with a context/ folder."""
    ctx = tmp_path / "context"
    ctx.mkdir()
    return tmp_path, ctx


class TestContextLoaderFallback:
    """ContextLoader falls back to repo defaults when project has no context/."""

    def test_system_prompt_loaded_from_repo_defaults(self, tmp_path):
        """System prompt falls back to repo context/system_prompt.md."""
        loader = ContextLoader(str(tmp_path))
        assert loader.system_prompt  # non-empty
        assert "coding assistant" in loader.system_prompt.lower()

    def test_destructive_patterns_loaded(self, tmp_path):
        """Destructive patterns load from repo defaults."""
        loader = ContextLoader(str(tmp_path))
        assert loader.is_destructive("rm -rf /tmp")
        assert not loader.is_destructive("ls -la")

    def test_safe_patterns_loaded(self, tmp_path):
        """Safe patterns load from repo defaults."""
        loader = ContextLoader(str(tmp_path))
        assert loader.is_safe("ls -la")
        assert loader.is_safe("pytest tests/")

    def test_agent_settings_have_defaults(self, tmp_path):
        """Agent settings return expected defaults."""
        loader = ContextLoader(str(tmp_path))
        settings = loader.agent_settings
        assert settings["num_history_runs"] == 15
        assert settings["markdown"] is True


class TestContextLoaderProjectOverride:
    """Project-level context/ files override repo defaults."""

    def test_system_prompt_overridden_by_project(self, project_with_context):
        """Project system_prompt.md overrides repo default."""
        tmp_path, ctx = project_with_context
        (ctx / "system_prompt.md").write_text("My custom system prompt.")
        loader = ContextLoader(str(tmp_path))
        assert loader.system_prompt == "My custom system prompt."

    def test_commands_overridden_by_project(self, project_with_context):
        """Project commands.json overrides repo default."""
        tmp_path, ctx = project_with_context
        (ctx / "commands.json").write_text(json.dumps({
            "destructive": ["drop"],
            "safe": ["select"],
            "ignored_paths": [],
        }))
        loader = ContextLoader(str(tmp_path))
        assert loader.is_destructive("DROP TABLE users")
        assert not loader.is_destructive("rm -rf /tmp")  # Not in this override

    def test_agent_settings_overridden(self, project_with_context):
        """Project agent_settings.json overrides defaults."""
        tmp_path, ctx = project_with_context
        (ctx / "agent_settings.json").write_text(json.dumps({
            "num_history_runs": 5,
            "markdown": False,
        }))
        loader = ContextLoader(str(tmp_path))
        assert loader.agent_settings["num_history_runs"] == 5
        assert loader.agent_settings["markdown"] is False


class TestProjectContext:
    """Tests for get_project_context merging."""

    def test_no_context_returns_none(self, tmp_path):
        """No context/ file and no AGENT.md returns None."""
        loader = ContextLoader(str(tmp_path))
        result = loader.get_project_context()
        assert result is None

    def test_agent_md_only(self, tmp_path):
        """Only AGENT.md content is returned as project context."""
        (tmp_path / "AGENT.md").write_text("# My Project")
        loader = ContextLoader(str(tmp_path))
        result = loader.get_project_context()
        assert result == "# My Project"

    def test_project_context_md_only(self, project_with_context):
        """Only project_context.md is returned."""
        tmp_path, ctx = project_with_context
        (ctx / "project_context.md").write_text("Context from file.")
        loader = ContextLoader(str(tmp_path))
        result = loader.get_project_context()
        assert result == "Context from file."

    def test_both_merged(self, project_with_context):
        """Both project_context.md and AGENT.md are merged with separator."""
        tmp_path, ctx = project_with_context
        (ctx / "project_context.md").write_text("From context file.")
        (tmp_path / "AGENT.md").write_text("From AGENT.md.")
        loader = ContextLoader(str(tmp_path))
        result = loader.get_project_context()
        assert "From context file." in result
        assert "From AGENT.md." in result
        assert "---" in result  # separator
