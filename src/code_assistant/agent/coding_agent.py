"""Main coding agent implementation using Agno."""

from pathlib import Path

from agno.agent import Agent
from agno.models.base import Model

from code_assistant.storage.database import create_database
from code_assistant.tools import FileToolkit, GitToolkit, SearchToolkit, ShellToolkit
from code_assistant.agent.memory import parse_agent_md
from code_assistant.agent.system_prompt import build_system_prompt
from code_assistant.config.models import create_model, parse_model_string


def create_coding_agent(
    project_path: str | None = None,
    model: Model | str = "anthropic:claude-sonnet-4-20250514",
    db_path: str | None = None,
    project_context: str | None = None,
    **model_kwargs,
) -> Agent:
    """Create the main coding assistant agent.

    Args:
        project_path: Path to the project directory (defaults to current directory)
        model: Agno Model instance or model string like "provider:model_id"
        db_path: Optional custom database path
        project_context: Optional project context from AGENT.md
        **model_kwargs: Additional model parameters (api_key, base_url, temperature, etc.)

    Returns:
        Configured Agno Agent
    """
    if project_path is None:
        project_path = str(Path.cwd())

    # Create or use provided model
    if isinstance(model, str):
        provider, model_id = parse_model_string(model)
        model = create_model(provider, model_id, **model_kwargs)

    # Create database
    db = create_database(db_path)

    # Parse AGENT.md if it exists and no context provided
    if project_context is None:
        project_context = parse_agent_md(project_path)

    # Build system prompt with optional project context
    system_prompt = build_system_prompt(project_context)

    # Create agent with tools
    agent = Agent(
        name="coding-assistant",
        model=model,
        instructions=system_prompt,
        tools=[
            FileToolkit(working_directory=project_path),
            ShellToolkit(working_directory=project_path),
            SearchToolkit(working_directory=project_path),
            GitToolkit(working_directory=project_path),
        ],
        db=db,
        enable_user_memories=True,
        markdown=True,
    )

    return agent
