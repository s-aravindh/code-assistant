"""File operations toolkit with HITL confirmation for writes."""

import fnmatch
from pathlib import Path

from agno.tools.toolkit import Toolkit
from agno.utils.log import logger

WRITE_OPERATIONS = ["write_file", "edit_file", "delete_file", "create_file"]

# Default protected paths that should not be modified
DEFAULT_PROTECTED_PATHS = [
    "~/.ssh/*",
    "~/.gnupg/*",
    "/etc/*",
    "*.pem",
    "*.key",
    ".env",
    ".env.*",
]


class FileToolkit(Toolkit):
    """Toolkit for file operations (read, write, edit)."""

    def __init__(
        self,
        working_directory: str = ".",
        protected_paths: list[str] | None = None,
        **kwargs
    ):
        self.working_directory = Path(working_directory).resolve()
        self.protected_paths = protected_paths or DEFAULT_PROTECTED_PATHS

        super().__init__(
            name="file_tools",
            tools=[self.read_file, self.write_file, self.edit_file, self.delete_file, self.create_file],
            requires_confirmation_tools=WRITE_OPERATIONS,
            **kwargs
        )
    
    def _resolve_path(self, file_path: str, check_traversal: bool = True) -> Path:
        """Resolve a file path relative to working directory with traversal protection.
        
        Args:
            file_path: The path to resolve
            check_traversal: Whether to check for directory traversal attacks
            
        Returns:
            Resolved absolute Path
            
        Raises:
            ValueError: If path is outside working directory (traversal attempt)
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.working_directory / path
        resolved = path.resolve()
        
        # Security: ensure path is within working directory
        if check_traversal:
            try:
                resolved.relative_to(self.working_directory)
            except ValueError:
                raise ValueError(f"Access denied: {file_path} is outside the working directory")
        
        return resolved
    
    def _is_protected_path(self, file_path: str) -> bool:
        """Check if a path matches any protected path pattern.
        
        Args:
            file_path: The path to check
            
        Returns:
            True if the path is protected, False otherwise
        """
        # Expand ~ in file_path for comparison
        expanded_path = str(Path(file_path).expanduser())
        
        for pattern in self.protected_paths:
            # Expand ~ in pattern
            expanded_pattern = str(Path(pattern).expanduser())
            
            # Check if path matches the pattern
            if fnmatch.fnmatch(expanded_path, expanded_pattern):
                return True
            if fnmatch.fnmatch(file_path, pattern):
                return True
            # Also check just the filename for patterns like "*.pem"
            if fnmatch.fnmatch(Path(file_path).name, pattern):
                return True
        
        return False

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

        except ValueError as e:
            # Path traversal attempt
            logger.warning(f"Path traversal blocked: {file_path}")
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {e}"
    
    def create_file(
        self,
        file_path: str,
        content: str = "",
        create_directories: bool = True
    ) -> str:
        """Create a new file. Fails if file already exists. Requires user confirmation (HITL).
        
        Args:
            file_path: Path to the file to create (relative to working directory)
            content: Optional initial content for the file (default: empty string)
            create_directories: Whether to create parent directories if they don't exist (default: True)
        
        Returns:
            Success or error message
        """
        try:
            # Check protected paths before resolving
            if self._is_protected_path(file_path):
                return f"Error: Cannot create protected file: {file_path}"
            
            path = self._resolve_path(file_path)

            if path.exists():
                return f"Error: File already exists: {file_path}"

            if create_directories:
                path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding='utf-8')
            return f"Successfully created {file_path}"

        except ValueError as e:
            logger.warning(f"Path traversal blocked: {file_path}")
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Error creating file {file_path}: {e}")
            return f"Error creating file: {e}"
    
    def write_file(
        self,
        file_path: str,
        content: str,
        create_directories: bool = True
    ) -> str:
        """Write content to a file. Overwrites if file exists. Requires user confirmation (HITL).
        
        Args:
            file_path: Path to the file to write (relative to working directory)
            content: The content to write to the file (required)
            create_directories: Whether to create parent directories if they don't exist (default: True)
        
        Returns:
            Success or error message
        """
        try:
            # Check protected paths before resolving
            if self._is_protected_path(file_path):
                return f"Error: Cannot write to protected file: {file_path}"
            
            path = self._resolve_path(file_path)

            if create_directories:
                path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding='utf-8')
            return f"Successfully wrote to {file_path}"

        except ValueError as e:
            logger.warning(f"Path traversal blocked: {file_path}")
            return f"Error: {e}"
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
            occurrence: Which occurrence to replace (-1 for all, 1+ for specific, 1-indexed)
        """
        try:
            # Check protected paths before resolving
            if self._is_protected_path(file_path):
                return f"Error: Cannot edit protected file: {file_path}"
            
            path = self._resolve_path(file_path)

            if not path.exists():
                return f"Error: File not found: {file_path}"

            content = path.read_text(encoding='utf-8')

            if search not in content:
                return f"Error: Search text not found in {file_path}"

            if occurrence == -1:
                # Replace all occurrences
                new_content = content.replace(search, replace)
                count = content.count(search)
            else:
                # Replace specific occurrence (1-indexed)
                # Find the nth occurrence by iterating
                total_occurrences = content.count(search)
                if occurrence < 1:
                    return f"Error: Occurrence must be -1 (all) or >= 1, got {occurrence}"
                if occurrence > total_occurrences:
                    return f"Error: Only {total_occurrences} occurrence(s) found, requested #{occurrence}"
                
                # Find the start index of the nth occurrence
                idx = -1
                for i in range(occurrence):
                    idx = content.find(search, idx + 1)
                    if idx == -1:
                        return f"Error: Only {i} occurrence(s) found"
                
                # Replace at the found position
                new_content = content[:idx] + replace + content[idx + len(search):]
                count = 1

            path.write_text(new_content, encoding='utf-8')
            return f"Successfully replaced {count} occurrence(s) in {file_path}"

        except ValueError as e:
            logger.warning(f"Path traversal blocked: {file_path}")
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Error editing file {file_path}: {e}")
            return f"Error editing file: {e}"
    
    def delete_file(self, file_path: str) -> str:
        """Delete a file. Requires user confirmation (HITL).
        
        Args:
            file_path: Path to the file to delete (relative to working directory)
        
        Returns:
            Success or error message
        """
        try:
            # Check protected paths before resolving
            if self._is_protected_path(file_path):
                return f"Error: Cannot delete protected file: {file_path}"
            
            path = self._resolve_path(file_path)

            if not path.exists():
                return f"Error: File not found: {file_path}"
            if not path.is_file():
                return f"Error: Not a file: {file_path}"

            path.unlink()
            return f"Successfully deleted {file_path}"

        except ValueError as e:
            logger.warning(f"Path traversal blocked: {file_path}")
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return f"Error deleting file: {e}"
