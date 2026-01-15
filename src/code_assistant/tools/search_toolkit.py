"""Search toolkit for finding files and code patterns."""

import subprocess
from pathlib import Path

from agno.tools.toolkit import Toolkit
from agno.utils.log import logger


class SearchToolkit(Toolkit):
    """Toolkit for searching files and code patterns."""

    def __init__(self, working_directory: str = ".", **kwargs):
        self.working_directory = Path(working_directory).resolve()

        super().__init__(
            name="search_tools",
            tools=[self.grep_search, self.find_files],
            **kwargs
        )
    
    def grep_search(
        self,
        pattern: str,
        path: str = ".",
        include: str | None = None,
        exclude: str | None = None,
        case_sensitive: bool = True,
        max_results: int = 100
    ) -> str:
        """Search for a pattern in files using ripgrep (falls back to grep).
        
        Args:
            pattern: The search pattern (required)
            path: Directory to search in (default: ".")
            include: File glob pattern to include (e.g., "*.py")
            exclude: File glob pattern to exclude
            case_sensitive: Whether search is case sensitive (default: True)
            max_results: Maximum number of results to return (default: 100)
        
        Returns:
            Search results or error message
        """
        search_path = self.working_directory / path

        if not search_path.exists():
            return f"Error: Path not found: {path}"

        try:
            return self._search_with_ripgrep(pattern, search_path, include, exclude, case_sensitive, max_results)
        except (FileNotFoundError, subprocess.CalledProcessError):
            return self._search_with_grep(pattern, search_path, include, exclude, case_sensitive, max_results)
        except subprocess.TimeoutExpired:
            return "Error: Search timed out"
        except Exception as e:
            logger.error(f"Error in grep search: {e}")
            return f"Error: {e}"

    def _search_with_ripgrep(
        self,
        pattern: str,
        search_path: Path,
        include: str | None,
        exclude: str | None,
        case_sensitive: bool,
        max_results: int
    ) -> str:
        """Execute search using ripgrep."""
        cmd = ["rg", "--color=never", "--line-number"]

        if not case_sensitive:
            cmd.append("--ignore-case")
        if include:
            cmd.extend(["--glob", include])
        if exclude:
            cmd.extend(["--glob", f"!{exclude}"])

        cmd.extend(["--max-count", str(max_results), pattern, str(search_path)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            return result.stdout or "No matches found"
        if result.returncode == 1:
            return "No matches found"
        raise subprocess.CalledProcessError(result.returncode, cmd)

    def _search_with_grep(
        self,
        pattern: str,
        search_path: Path,
        include: str | None,
        exclude: str | None,
        case_sensitive: bool,
        max_results: int
    ) -> str:
        """Execute search using grep as fallback."""
        cmd = ["grep", "-rn"]

        if not case_sensitive:
            cmd.append("-i")
        if include:
            cmd.extend(["--include", include])
        if exclude:
            cmd.extend(["--exclude", exclude])

        cmd.extend([pattern, str(search_path)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return '\n'.join(lines[:max_results])
        if result.returncode == 1:
            return "No matches found"
        return f"Error: {result.stderr}"
    
    def find_files(
        self,
        pattern: str,
        path: str = ".",
        max_results: int = 100
    ) -> str:
        """Find files by name pattern (supports wildcards).
        
        Args:
            pattern: File name pattern with wildcards (e.g., "*.py") (required)
            path: Directory to search in (default: ".")
            max_results: Maximum number of results to return (default: 100)
        
        Returns:
            List of matching files or error message
        """
        search_path = self.working_directory / path

        if not search_path.exists():
            return f"Error: Path not found: {path}"

        try:
            cmd = ["find", str(search_path), "-name", pattern, "-type", "f"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return f"Error: {result.stderr}"

            files = [line for line in result.stdout.strip().split('\n') if line][:max_results]

            if not files:
                return "No files found"

            return '\n'.join(self._make_relative(f) for f in files)

        except subprocess.TimeoutExpired:
            return "Error: Search timed out"
        except Exception as e:
            logger.error(f"Error finding files: {e}")
            return f"Error: {e}"

    def _make_relative(self, file_path: str) -> str:
        """Convert absolute path to relative path if possible."""
        try:
            return str(Path(file_path).relative_to(self.working_directory))
        except ValueError:
            return file_path
