"""File operations toolkit with HITL confirmation for writes."""

from pathlib import Path

from agno.tools.toolkit import Toolkit
from agno.utils.log import logger

WRITE_OPERATIONS = ["write_file", "edit_file", "delete_file"]


class FileToolkit(Toolkit):
    """Toolkit for file operations (read, write, edit)."""

    def __init__(self, working_directory: str = ".", **kwargs):
        self.working_directory = Path(working_directory).resolve()

        super().__init__(
            name="file_tools",
            tools=[self.read_file, self.write_file, self.edit_file, self.delete_file],
            requires_confirmation_tools=WRITE_OPERATIONS,
            **kwargs
        )
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a file path relative to working directory."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.working_directory / path
        return path.resolve()

    def read_file(
        self,
        file_path: str,
        line_start: int | None = None,
        line_end: int | None = None
    ) -> str:
        """Read contents of a file.

        Args:
            file_path: Path to the file to read
            line_start: Optional starting line number (1-indexed)
            line_end: Optional ending line number (1-indexed, inclusive)
        """
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return f"Error: File not found: {file_path}"
            if not path.is_file():
                return f"Error: Not a file: {file_path}"

            content = path.read_text(encoding='utf-8')

            if line_start is not None or line_end is not None:
                lines = content.splitlines(keepends=True)
                start = (line_start - 1) if line_start else 0
                end = line_end if line_end else len(lines)
                content = ''.join(lines[start:end])

            return content

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {e}"
    
    def write_file(
        self,
        file_path: str,
        content: str,
        create_directories: bool = True
    ) -> str:
        """Write content to a file. Requires user confirmation (HITL)."""
        try:
            path = self._resolve_path(file_path)

            if create_directories:
                path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding='utf-8')
            return f"Successfully wrote to {file_path}"

        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return f"Error writing file: {e}"
    
    def edit_file(
        self,
        file_path: str,
        search: str,
        replace: str,
        occurrence: int = -1
    ) -> str:
        """Edit a file by replacing text. Requires user confirmation (HITL).

        Args:
            file_path: Path to the file to edit
            search: Text to search for
            replace: Text to replace with
            occurrence: Which occurrence to replace (-1 for all, 1+ for specific)
        """
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return f"Error: File not found: {file_path}"

            content = path.read_text(encoding='utf-8')

            if search not in content:
                return f"Error: Search text not found in {file_path}"

            if occurrence == -1:
                new_content = content.replace(search, replace)
                count = content.count(search)
            else:
                parts = content.split(search)
                if occurrence > len(parts) - 1:
                    return f"Error: Only {len(parts) - 1} occurrences found"
                new_content = search.join(parts[:occurrence]) + replace + search.join(parts[occurrence + 1:])
                count = 1

            path.write_text(new_content, encoding='utf-8')
            return f"Successfully replaced {count} occurrence(s) in {file_path}"

        except Exception as e:
            logger.error(f"Error editing file {file_path}: {e}")
            return f"Error editing file: {e}"
    
    def delete_file(self, file_path: str) -> str:
        """Delete a file. Requires user confirmation (HITL)."""
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return f"Error: File not found: {file_path}"
            if not path.is_file():
                return f"Error: Not a file: {file_path}"

            path.unlink()
            return f"Successfully deleted {file_path}"

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return f"Error deleting file: {e}"
