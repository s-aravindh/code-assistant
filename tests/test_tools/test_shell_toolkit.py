"""Tests for ShellToolkit."""

import pytest


class TestRunCommand:
    """Tests for the run_command method."""
    
    def test_run_command_success(self, shell_toolkit):
        """Test running a successful command."""
        result = shell_toolkit.run_command("echo 'hello world'")
        assert "Command executed successfully" in result
        assert "hello world" in result
    
    def test_run_command_with_exit_code(self, shell_toolkit):
        """Test running a command that fails."""
        result = shell_toolkit.run_command("exit 1")
        assert "Command exited with code 1" in result
    
    def test_run_command_with_stderr(self, shell_toolkit):
        """Test running a command that outputs to stderr."""
        result = shell_toolkit.run_command("echo 'error' >&2")
        assert "Stderr:" in result or "error" in result
    
    def test_run_command_in_working_directory(self, shell_toolkit, temp_project):
        """Test that commands run in the correct directory."""
        result = shell_toolkit.run_command("pwd")
        assert str(temp_project) in result
    
    def test_run_command_list_files(self, shell_toolkit, temp_project):
        """Test listing files in the project."""
        result = shell_toolkit.run_command("ls -la")
        assert "README.md" in result
        assert "src" in result
    
    def test_run_command_timeout(self, shell_toolkit):
        """Test command timeout."""
        # Use a very short timeout
        result = shell_toolkit.run_command("sleep 10", timeout=1)
        assert "Error: Command timed out" in result
