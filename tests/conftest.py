"""Shared test fixtures."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_project(temp_dir):
    """Create a temporary project directory with sample files."""
    project = temp_dir / "test_project"
    project.mkdir()

    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / "docs").mkdir()

    (project / "README.md").write_text("# Test Project\n\nA test project.")
    (project / "src" / "main.py").write_text("print('hello world')\n")
    (project / "src" / "utils.py").write_text(
        "def helper():\n"
        "    return 'helped'\n\n"
        "def another_helper():\n"
        "    return 'also helped'\n"
    )
    (project / "tests" / "test_main.py").write_text(
        "def test_example():\n"
        "    assert True\n"
    )

    yield project


@pytest.fixture
def coding_tools(temp_project):
    """Create a CodingTool instance for testing."""
    from myassistant.tools import CodingTool
    from myassistant.config.context_loader import ContextLoader
    loader = ContextLoader(str(temp_project))
    return CodingTool(base_dir=str(temp_project), context_loader=loader)


@pytest.fixture
def slash_handler():
    """Create a SlashCommandHandler instance for testing."""
    from myassistant.utils.slash_commands import SlashCommandHandler
    return SlashCommandHandler()
