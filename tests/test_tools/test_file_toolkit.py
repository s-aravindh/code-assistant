"""Tests for FileToolkit."""

import pytest
from pathlib import Path


class TestReadFile:
    """Tests for the read_file method."""
    
    def test_read_file_success(self, file_toolkit, temp_project):
        """Test reading an existing file."""
        result = file_toolkit.read_file("README.md")
        assert "Test Project" in result
        assert "Error" not in result
    
    def test_read_file_not_found(self, file_toolkit):
        """Test reading a non-existent file."""
        result = file_toolkit.read_file("nonexistent.txt")
        assert "Error: File not found" in result
    
    def test_read_file_with_line_range(self, file_toolkit, temp_project):
        """Test reading specific lines from a file."""
        # Create a multi-line file
        (temp_project / "multiline.txt").write_text(
            "line 1\n"
            "line 2\n"
            "line 3\n"
            "line 4\n"
            "line 5\n"
        )
        
        # Read lines 2-4
        result = file_toolkit.read_file("multiline.txt", line_start=2, line_end=4)
        assert "line 2" in result
        assert "line 3" in result
        assert "line 4" in result
        assert "line 1" not in result
        assert "line 5" not in result
    
    def test_read_file_not_a_file(self, file_toolkit, temp_project):
        """Test reading a directory (not a file)."""
        result = file_toolkit.read_file("src")
        assert "Error: Not a file" in result


class TestWriteFile:
    """Tests for the write_file method."""
    
    def test_write_file_new(self, file_toolkit, temp_project):
        """Test writing a new file."""
        result = file_toolkit.write_file("new_file.txt", "Hello, World!")
        assert "Successfully wrote" in result
        assert (temp_project / "new_file.txt").read_text() == "Hello, World!"
    
    def test_write_file_overwrite(self, file_toolkit, temp_project):
        """Test overwriting an existing file."""
        result = file_toolkit.write_file("README.md", "New content")
        assert "Successfully wrote" in result
        assert (temp_project / "README.md").read_text() == "New content"
    
    def test_write_file_creates_directories(self, file_toolkit, temp_project):
        """Test that write_file creates parent directories."""
        result = file_toolkit.write_file("new_dir/nested/file.txt", "Content")
        assert "Successfully wrote" in result
        assert (temp_project / "new_dir" / "nested" / "file.txt").exists()
    
    def test_write_file_protected_path(self, file_toolkit):
        """Test that protected paths cannot be written."""
        result = file_toolkit.write_file(".env", "SECRET=value")
        assert "Error: Cannot write to protected file" in result


class TestCreateFile:
    """Tests for the create_file method."""
    
    def test_create_file_success(self, file_toolkit, temp_project):
        """Test creating a new file."""
        result = file_toolkit.create_file("new.txt", "Content")
        assert "Successfully created" in result
        assert (temp_project / "new.txt").read_text() == "Content"
    
    def test_create_file_already_exists(self, file_toolkit):
        """Test that create_file fails if file exists."""
        result = file_toolkit.create_file("README.md", "Content")
        assert "Error: File already exists" in result


class TestEditFile:
    """Tests for the edit_file method."""
    
    def test_edit_file_all_occurrences(self, file_toolkit, temp_project):
        """Test replacing all occurrences."""
        (temp_project / "test.txt").write_text("foo bar foo baz foo")
        
        result = file_toolkit.edit_file("test.txt", "foo", "qux", occurrence=-1)
        assert "Successfully replaced 3 occurrence(s)" in result
        assert (temp_project / "test.txt").read_text() == "qux bar qux baz qux"
    
    def test_edit_file_single_occurrence(self, file_toolkit, temp_project):
        """Test replacing a specific occurrence (regression test for bug fix)."""
        (temp_project / "test.txt").write_text("foo bar foo baz foo")
        
        # Replace the 2nd occurrence
        result = file_toolkit.edit_file("test.txt", "foo", "qux", occurrence=2)
        assert "Successfully replaced 1 occurrence(s)" in result
        assert (temp_project / "test.txt").read_text() == "foo bar qux baz foo"
    
    def test_edit_file_first_occurrence(self, file_toolkit, temp_project):
        """Test replacing the first occurrence."""
        (temp_project / "test.txt").write_text("foo bar foo baz foo")
        
        result = file_toolkit.edit_file("test.txt", "foo", "qux", occurrence=1)
        assert "Successfully replaced 1 occurrence(s)" in result
        assert (temp_project / "test.txt").read_text() == "qux bar foo baz foo"
    
    def test_edit_file_third_occurrence(self, file_toolkit, temp_project):
        """Test replacing the third occurrence."""
        (temp_project / "test.txt").write_text("foo bar foo baz foo")
        
        result = file_toolkit.edit_file("test.txt", "foo", "qux", occurrence=3)
        assert "Successfully replaced 1 occurrence(s)" in result
        assert (temp_project / "test.txt").read_text() == "foo bar foo baz qux"
    
    def test_edit_file_not_found(self, file_toolkit):
        """Test editing a non-existent file."""
        result = file_toolkit.edit_file("nonexistent.txt", "foo", "bar")
        assert "Error: File not found" in result
    
    def test_edit_file_search_not_found(self, file_toolkit, temp_project):
        """Test editing when search text doesn't exist."""
        result = file_toolkit.edit_file("README.md", "nonexistent text", "replacement")
        assert "Error: Search text not found" in result
    
    def test_edit_file_occurrence_too_high(self, file_toolkit, temp_project):
        """Test editing when occurrence number is too high."""
        (temp_project / "test.txt").write_text("foo bar foo")
        
        result = file_toolkit.edit_file("test.txt", "foo", "qux", occurrence=5)
        assert "Error: Only 2 occurrence(s) found" in result
    
    def test_edit_file_invalid_occurrence(self, file_toolkit, temp_project):
        """Test editing with invalid occurrence value."""
        (temp_project / "test.txt").write_text("foo bar foo")
        
        result = file_toolkit.edit_file("test.txt", "foo", "qux", occurrence=0)
        assert "Error: Occurrence must be -1 (all) or >= 1" in result


class TestDeleteFile:
    """Tests for the delete_file method."""
    
    def test_delete_file_success(self, file_toolkit, temp_project):
        """Test deleting an existing file."""
        (temp_project / "to_delete.txt").write_text("Delete me")
        
        result = file_toolkit.delete_file("to_delete.txt")
        assert "Successfully deleted" in result
        assert not (temp_project / "to_delete.txt").exists()
    
    def test_delete_file_not_found(self, file_toolkit):
        """Test deleting a non-existent file."""
        result = file_toolkit.delete_file("nonexistent.txt")
        assert "Error: File not found" in result
    
    def test_delete_file_is_directory(self, file_toolkit):
        """Test deleting a directory (should fail)."""
        result = file_toolkit.delete_file("src")
        assert "Error: Not a file" in result


class TestPathTraversal:
    """Tests for path traversal protection."""
    
    def test_path_traversal_blocked_read(self, file_toolkit):
        """Test that reading outside working directory is blocked."""
        result = file_toolkit.read_file("../../../etc/passwd")
        assert "Error: Access denied" in result
    
    def test_path_traversal_blocked_write(self, file_toolkit):
        """Test that writing outside working directory is blocked."""
        result = file_toolkit.write_file("../outside.txt", "content")
        assert "Error: Access denied" in result
    
    def test_path_traversal_blocked_delete(self, file_toolkit):
        """Test that deleting outside working directory is blocked."""
        result = file_toolkit.delete_file("../../important.txt")
        assert "Error: Access denied" in result


class TestProtectedPaths:
    """Tests for protected path protection."""
    
    def test_protected_env_file(self, file_toolkit):
        """Test that .env files are protected."""
        result = file_toolkit.write_file(".env", "SECRET=value")
        assert "Error: Cannot write to protected file" in result
    
    def test_protected_pem_file(self, file_toolkit):
        """Test that .pem files are protected."""
        result = file_toolkit.write_file("key.pem", "private key content")
        assert "Error: Cannot write to protected file" in result
    
    def test_protected_key_file(self, file_toolkit):
        """Test that .key files are protected."""
        result = file_toolkit.create_file("secret.key", "key content")
        assert "Error: Cannot create protected file" in result
