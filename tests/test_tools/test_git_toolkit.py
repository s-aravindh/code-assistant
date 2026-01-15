"""Tests for GitToolkit."""

import pytest


class TestGitStatus:
    """Tests for the git_status method."""
    
    def test_git_status_clean(self, git_toolkit):
        """Test git status on clean repo."""
        result = git_toolkit.git_status()
        assert "Working tree clean" in result
    
    def test_git_status_with_changes(self, git_toolkit, temp_project):
        """Test git status with uncommitted changes."""
        # Make a change
        (temp_project / "README.md").write_text("Modified content")
        
        result = git_toolkit.git_status()
        assert "README.md" in result


class TestGitDiff:
    """Tests for the git_diff method."""
    
    def test_git_diff_no_changes(self, git_toolkit):
        """Test git diff with no changes."""
        result = git_toolkit.git_diff()
        assert "No changes" in result
    
    def test_git_diff_with_changes(self, git_toolkit, temp_project):
        """Test git diff with uncommitted changes."""
        # Make a change
        (temp_project / "README.md").write_text("Modified content")
        
        result = git_toolkit.git_diff()
        assert "Modified content" in result or "README.md" in result
    
    def test_git_diff_staged(self, git_toolkit, temp_project):
        """Test git diff for staged changes."""
        import subprocess
        
        # Make and stage a change
        (temp_project / "README.md").write_text("Staged content")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=str(temp_project),
            capture_output=True,
        )
        
        result = git_toolkit.git_diff(staged=True)
        assert "Staged content" in result or "README.md" in result


class TestGitLog:
    """Tests for the git_log method."""
    
    def test_git_log_shows_commits(self, git_toolkit):
        """Test git log shows commit history."""
        result = git_toolkit.git_log()
        assert "Initial commit" in result
    
    def test_git_log_with_count(self, git_toolkit):
        """Test git log with limited count."""
        result = git_toolkit.git_log(count=1)
        assert "Initial commit" in result


class TestGitCommit:
    """Tests for the git_commit method."""
    
    def test_git_commit_success(self, git_toolkit, temp_project):
        """Test creating a commit."""
        # Make a change
        (temp_project / "new_file.txt").write_text("New content")
        
        result = git_toolkit.git_commit(
            message="Add new file",
            files=["new_file.txt"],
        )
        assert "Successfully created commit" in result
    
    def test_git_commit_add_all(self, git_toolkit, temp_project):
        """Test committing with add_all."""
        # Make a change
        (temp_project / "another_file.txt").write_text("Another content")
        
        result = git_toolkit.git_commit(
            message="Add another file",
            add_all=True,
        )
        assert "Successfully created commit" in result
    
    def test_git_commit_no_changes(self, git_toolkit):
        """Test commit with no changes."""
        result = git_toolkit.git_commit(message="Empty commit")
        assert "Error" in result or "nothing to commit" in result.lower()
