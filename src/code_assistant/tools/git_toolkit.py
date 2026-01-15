"""Git operations toolkit."""

import subprocess
from pathlib import Path

from agno.tools.toolkit import Toolkit
from agno.utils.log import logger


class GitToolkit(Toolkit):
    """Toolkit for Git operations."""

    def __init__(self, working_directory: str = ".", **kwargs):
        self.working_directory = Path(working_directory).resolve()

        super().__init__(
            name="git_tools",
            tools=[self.git_status, self.git_diff, self.git_log, self.git_commit],
            requires_confirmation_tools=["git_commit"],
            **kwargs
        )

    def _run_git_command(self, args: list[str], timeout: int = 30) -> tuple[bool, str]:
        """Run a git command and return (success, output)."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=str(self.working_directory),
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return True, result.stdout
            return False, result.stderr or result.stdout

        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"Error running git command: {e}")
            return False, str(e)
    
    def git_status(self) -> str:
        """Get git status.
        
        Returns:
            Git status output or error message
        """
        success, output = self._run_git_command(["status", "--short"])

        if not success:
            return f"Error: {output}"
        return output.strip() or "Working tree clean"

    def git_diff(self, staged: bool = False, file: str | None = None) -> str:
        """Show git diff.
        
        Args:
            staged: Whether to show staged changes (default: False)
            file: Optional specific file to show diff for
        
        Returns:
            Git diff output or error message
        """
        args = ["diff"]
        if staged:
            args.append("--cached")
        if file:
            args.append(file)

        success, output = self._run_git_command(args)

        if not success:
            return f"Error: {output}"
        if not output.strip():
            return "No staged changes" if staged else "No changes"
        return output

    def git_log(self, count: int = 10, file: str | None = None) -> str:
        """Show git commit history.
        
        Args:
            count: Number of commits to show (default: 10)
            file: Optional specific file to show history for
        
        Returns:
            Git log output or error message
        """
        args = ["log", f"-{count}", "--pretty=format:%h - %an, %ar : %s"]

        if file:
            args.extend(["--", file])

        success, output = self._run_git_command(args)

        if not success:
            return f"Error: {output}"
        return output.strip() or "No commits found"

    def git_commit(
        self,
        message: str,
        files: list[str] | None = None,
        add_all: bool = False
    ) -> str:
        """Create a git commit. Requires user confirmation (HITL).
        
        Args:
            message: Commit message (required)
            files: Optional list of specific files to commit
            add_all: Whether to stage all changes before committing (default: False)
        
        Returns:
            Success or error message
        """
        try:
            if add_all:
                success, output = self._run_git_command(["add", "-A"])
                if not success:
                    return f"Error staging files: {output}"
            elif files:
                for file in files:
                    success, output = self._run_git_command(["add", file])
                    if not success:
                        return f"Error staging {file}: {output}"

            success, output = self._run_git_command(["commit", "-m", message])

            if not success:
                return f"Error creating commit: {output}"
            return f"Successfully created commit: {output}"

        except Exception as e:
            logger.error(f"Error in git_commit: {e}")
            return f"Error: {e}"
