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
    
    # Create sample directory structure
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / "docs").mkdir()
    
    # Create sample files
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
def file_toolkit(temp_project):
    """Create a FileToolkit instance for testing."""
    from code_assistant.tools.file_toolkit import FileToolkit
    return FileToolkit(working_directory=str(temp_project))


@pytest.fixture
def search_toolkit(temp_project):
    """Create a SearchToolkit instance for testing."""
    from code_assistant.tools.search_toolkit import SearchToolkit
    return SearchToolkit(working_directory=str(temp_project))


@pytest.fixture
def git_toolkit(temp_project):
    """Create a GitToolkit instance for testing.
    
    Initializes a git repo in the temp project.
    """
    import subprocess
    from code_assistant.tools.git_toolkit import GitToolkit
    
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=str(temp_project),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(temp_project),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(temp_project),
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=str(temp_project),
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(temp_project),
        capture_output=True,
    )
    
    return GitToolkit(working_directory=str(temp_project))


@pytest.fixture
def shell_toolkit(temp_project):
    """Create a ShellToolkit instance for testing."""
    from code_assistant.tools.shell_toolkit import ShellToolkit
    return ShellToolkit(working_directory=str(temp_project))


@pytest.fixture
def slash_handler():
    """Create a SlashCommandHandler instance for testing."""
    from code_assistant.utils.slash_commands import SlashCommandHandler
    return SlashCommandHandler()
