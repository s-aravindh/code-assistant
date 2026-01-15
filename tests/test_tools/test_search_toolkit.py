"""Tests for SearchToolkit."""

import pytest


class TestGrepSearch:
    """Tests for the grep_search method."""
    
    def test_grep_search_finds_pattern(self, search_toolkit):
        """Test finding a pattern in files."""
        result = search_toolkit.grep_search("hello world")
        assert "main.py" in result or "hello" in result
    
    def test_grep_search_with_include(self, search_toolkit):
        """Test searching with file type filter."""
        result = search_toolkit.grep_search("def", include="*.py")
        assert "test_main.py" in result or "utils.py" in result
    
    def test_grep_search_case_insensitive(self, search_toolkit, temp_project):
        """Test case-insensitive search."""
        (temp_project / "case.txt").write_text("Hello HELLO hello")
        
        result = search_toolkit.grep_search("hello", path="case.txt", case_sensitive=False)
        # Should find all variants
        assert "case.txt" in result or "hello" in result.lower()
    
    def test_grep_search_no_matches(self, search_toolkit):
        """Test search with no matches."""
        result = search_toolkit.grep_search("xyznonexistent123")
        assert "No matches found" in result
    
    def test_grep_search_path_not_found(self, search_toolkit):
        """Test search in non-existent path."""
        result = search_toolkit.grep_search("pattern", path="nonexistent_dir")
        assert "Error: Path not found" in result


class TestFindFiles:
    """Tests for the find_files method."""
    
    def test_find_files_by_pattern(self, search_toolkit):
        """Test finding files by pattern."""
        result = search_toolkit.find_files("*.py")
        assert "main.py" in result
        assert "utils.py" in result
    
    def test_find_files_markdown(self, search_toolkit):
        """Test finding markdown files."""
        result = search_toolkit.find_files("*.md")
        assert "README.md" in result
    
    def test_find_files_no_matches(self, search_toolkit):
        """Test finding files with no matches."""
        result = search_toolkit.find_files("*.nonexistent")
        assert "No files found" in result
    
    def test_find_files_path_not_found(self, search_toolkit):
        """Test finding files in non-existent path."""
        result = search_toolkit.find_files("*.py", path="nonexistent_dir")
        assert "Error: Path not found" in result
