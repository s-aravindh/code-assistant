"""Tests for diff utilities."""

import pytest
from code_assistant.utils.diff import (
    generate_diff,
    format_diff_rich,
    format_file_change,
    format_new_file,
    format_delete_file,
)


class TestGenerateDiff:
    """Tests for generate_diff function."""
    
    def test_generate_diff_basic(self):
        """Test generating a basic diff."""
        original = "line 1\nline 2\nline 3\n"
        modified = "line 1\nmodified line 2\nline 3\n"
        
        diff = generate_diff(original, modified, "test.txt")
        
        assert "a/test.txt" in diff
        assert "b/test.txt" in diff
        assert "-line 2" in diff
        assert "+modified line 2" in diff
    
    def test_generate_diff_no_changes(self):
        """Test diff with no changes."""
        content = "line 1\nline 2\n"
        
        diff = generate_diff(content, content, "test.txt")
        
        # No changes should produce empty or minimal diff
        assert diff == "" or "@@" not in diff
    
    def test_generate_diff_addition(self):
        """Test diff with additions."""
        original = "line 1\nline 2\n"
        modified = "line 1\nline 2\nnew line\n"
        
        diff = generate_diff(original, modified, "test.txt")
        
        assert "+new line" in diff
    
    def test_generate_diff_deletion(self):
        """Test diff with deletions."""
        original = "line 1\nline 2\nline 3\n"
        modified = "line 1\nline 3\n"
        
        diff = generate_diff(original, modified, "test.txt")
        
        assert "-line 2" in diff


class TestFormatDiffRich:
    """Tests for format_diff_rich function."""
    
    def test_format_adds_colors(self):
        """Test that formatting adds color markup."""
        original = "line 1\nline 2\n"
        modified = "line 1\nmodified\n"
        
        diff = generate_diff(original, modified, "test.txt")
        formatted = format_diff_rich(diff)
        
        # Should contain rich color markup
        assert "[" in formatted and "]" in formatted
    
    def test_format_empty_diff(self):
        """Test formatting empty diff."""
        formatted = format_diff_rich("")
        
        assert "No changes" in formatted


class TestFormatFileChange:
    """Tests for format_file_change function."""
    
    def test_format_file_change(self):
        """Test formatting a file change."""
        original = "line 1\n"
        modified = "line 1\nline 2\n"
        
        formatted = format_file_change("test.txt", original, modified)
        
        assert "test.txt" in formatted
        assert "+" in formatted


class TestFormatNewFile:
    """Tests for format_new_file function."""
    
    def test_format_new_file(self):
        """Test formatting a new file."""
        content = "line 1\nline 2\nline 3\n"
        
        formatted = format_new_file("new.txt", content)
        
        assert "new.txt" in formatted
        assert "new file" in formatted
        assert "+line 1" in formatted or "line 1" in formatted
    
    def test_format_new_file_truncates_long(self):
        """Test that long files are truncated."""
        lines = [f"line {i}" for i in range(20)]
        content = "\n".join(lines)
        
        formatted = format_new_file("long.txt", content)
        
        assert "more lines" in formatted


class TestFormatDeleteFile:
    """Tests for format_delete_file function."""
    
    def test_format_delete_file(self):
        """Test formatting a file deletion."""
        formatted = format_delete_file("deleted.txt")
        
        assert "deleted.txt" in formatted
        assert "deleted" in formatted.lower()
