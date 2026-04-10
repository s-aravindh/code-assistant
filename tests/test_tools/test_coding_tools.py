"""Tests for the CodingTools toolkit."""

import pytest


class TestReadFile:
    """Tests for the read_file tool."""

    def test_read_file_success(self, coding_tools, temp_project):
        """Test reading an existing file."""
        result = coding_tools.read_file("README.md")
        assert "Test Project" in result
        assert "Error" not in result

    def test_read_file_not_found(self, coding_tools):
        """Test reading a non-existent file."""
        result = coding_tools.read_file("nonexistent.txt")
        assert "Error" in result

    def test_read_file_with_offset_and_limit(self, coding_tools, temp_project):
        """Test reading specific lines using offset and limit."""
        (temp_project / "multiline.txt").write_text(
            "line 1\nline 2\nline 3\nline 4\nline 5\n"
        )
        result = coding_tools.read_file("multiline.txt", offset=1, limit=2)
        assert "line 2" in result
        assert "line 3" in result
        assert "line 1" not in result

    def test_read_file_outside_base_dir_blocked(self, coding_tools):
        """Test that path traversal is blocked."""
        result = coding_tools.read_file("../../etc/passwd")
        assert "Error" in result


class TestWriteFile:
    """Tests for the write_file tool."""

    def test_write_new_file(self, coding_tools, temp_project):
        """Test creating a new file."""
        result = coding_tools.write_file("newfile.txt", "hello world\n")
        assert "Error" not in result
        assert (temp_project / "newfile.txt").read_text() == "hello world\n"

    def test_overwrite_existing_file(self, coding_tools, temp_project):
        """Test overwriting an existing file."""
        result = coding_tools.write_file("README.md", "# New Content\n")
        assert "Error" not in result
        assert "New Content" in (temp_project / "README.md").read_text()

    def test_write_creates_parent_dirs(self, coding_tools, temp_project):
        """Test writing a file in a directory that does not yet exist."""
        result = coding_tools.write_file("subdir/nested/file.txt", "content\n")
        assert "Error" not in result
        assert (temp_project / "subdir" / "nested" / "file.txt").exists()


class TestEditFile:
    """Tests for the edit_file tool."""

    def test_edit_replaces_text(self, coding_tools, temp_project):
        """Test that edit_file replaces matching text."""
        result = coding_tools.edit_file("src/main.py", "print('hello world')", "print('hi!')")
        assert "Error" not in result
        assert "hi!" in (temp_project / "src" / "main.py").read_text()

    def test_edit_file_not_found(self, coding_tools):
        """Test editing a non-existent file."""
        result = coding_tools.edit_file("missing.py", "x", "y")
        assert "Error" in result

    def test_edit_no_match(self, coding_tools):
        """Test edit when old_text doesn't appear in the file."""
        result = coding_tools.edit_file("README.md", "this text does not exist", "replacement")
        assert "Error" in result


class TestRunShell:
    """Tests for the run_shell tool."""

    def test_safe_command_succeeds(self, coding_tools, temp_project):
        """Test that a basic safe command runs successfully."""
        result = coding_tools.run_shell("ls")
        assert "Error" not in result or "src" in result

    def test_command_timeout(self, coding_tools):
        """Test that long-running commands are timed out."""
        result = coding_tools.run_shell("sleep 10", timeout=1)
        assert "timed out" in result.lower() or "Error" in result

