"""Memory management including AGENT.md parsing."""

from pathlib import Path

AGENT_MD_TEMPLATE = """\
# Project: {project_name}

## Overview
Brief description of the project.

## Tech Stack
- List your technologies here
- Programming languages
- Frameworks and libraries

## Conventions
- Coding style guidelines
- Naming conventions
- Best practices for this project

## Architecture
Describe the project structure:
- `/src` - Source code
- `/tests` - Test files
- `/docs` - Documentation

## Common Commands
- `make dev` - Start development server
- `make test` - Run tests
- `make lint` - Run linters

## Notes
- Important decisions
- Known issues
- Future plans
"""


def parse_agent_md(project_path: str) -> str | None:
    """Parse AGENT.md file from project root."""
    agent_md_path = Path(project_path) / "AGENT.md"

    if not agent_md_path.exists():
        return None

    try:
        return agent_md_path.read_text(encoding='utf-8')
    except Exception:
        return None


def create_agent_md_template(project_path: str) -> str:
    """Create a template AGENT.md file in the project."""
    project_dir = Path(project_path)
    agent_md_path = project_dir / "AGENT.md"

    if agent_md_path.exists():
        return "AGENT.md already exists in this project"

    try:
        content = AGENT_MD_TEMPLATE.format(project_name=project_dir.name)
        agent_md_path.write_text(content, encoding='utf-8')
        return f"Successfully created AGENT.md in {project_path}"
    except Exception as e:
        return f"Error creating AGENT.md: {e}"
