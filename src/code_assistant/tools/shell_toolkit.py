"""Shell command execution toolkit with HITL confirmation."""

import subprocess
from pathlib import Path

from agno.tools.toolkit import Toolkit
from agno.utils.log import logger


class ShellToolkit(Toolkit):
    """Toolkit for executing shell commands."""

    def __init__(self, working_directory: str = ".", **kwargs):
        self.working_directory = Path(working_directory).resolve()

        super().__init__(
            name="shell_tools",
            tools=[self.run_command],
            requires_confirmation_tools=["run_command"],
            **kwargs
        )

    def run_command(
        self,
        command: str,
        timeout: int = 300,
        capture_output: bool = True
    ) -> str:
        """Execute a shell command. Requires user confirmation (HITL).
        
        Args:
            command: The shell command to execute (required)
            timeout: Maximum execution time in seconds (default: 300)
            capture_output: Whether to capture stdout/stderr (default: True)
        
        Returns:
            Command output or error message
        """
        try:
            logger.info(f"Running shell command: {command}")

            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.working_directory),
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )

            status = "Command executed successfully" if result.returncode == 0 else f"Command exited with code {result.returncode}"
            parts = [status]

            if capture_output:
                if result.stdout:
                    parts.append(f"\nStdout:\n{result.stdout}")
                if result.stderr:
                    parts.append(f"\nStderr:\n{result.stderr}")

            return "".join(parts)

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds")
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return f"Error executing command: {e}"
