"""Tests for ContextLoader command classification (is_destructive / is_safe)."""

import pytest
from myassistant.config.context_loader import ContextLoader


@pytest.fixture
def loader(tmp_path):
    """ContextLoader pointing to a temp project (falls back to repo defaults)."""
    return ContextLoader(str(tmp_path))


class TestIsDestructiveCommand:
    """Tests for the shell command classification helper."""

    def test_safe_commands(self, loader):
        """Safe read-only commands should not be classified as destructive."""
        safe = [
            "ls",
            "ls -la",
            "cat README.md",
            "grep -r 'hello' src/",
            "find . -name '*.py'",
            "git status",
            "git log --oneline",
            "git diff",
            "git show HEAD",
            "python --version",
            "pytest tests/",
            "echo hello",
            "pwd",
            "which python",
            "ps aux",
        ]
        for cmd in safe:
            assert not loader.is_destructive(cmd), f"Expected safe: {cmd!r}"

    def test_destructive_commands(self, loader):
        """Destructive commands should be correctly identified."""
        destructive = [
            "rm -rf dist/",
            "rm file.txt",
            "sudo apt-get install curl",
            "chmod 777 /tmp",
            "chown user:group file",
            "git push origin main",
            "git reset --hard HEAD~1",
            "git clean -fd",
            "git rebase main",
            "git commit -m 'fix'",
            "pip install requests",
            "npm install",
            "uv add httpx",
            "uv remove httpx",
            "echo hello > output.txt",
            "echo data >> log.txt",
        ]
        for cmd in destructive:
            assert loader.is_destructive(cmd), f"Expected destructive: {cmd!r}"
