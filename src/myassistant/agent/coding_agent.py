"""Main coding agent implementation using Agno."""

from pathlib import Path

from agno.agent import Agent
from agno.models.base import Model

from myassistant.config.context_loader import ContextLoader
from myassistant.storage.database import create_database
from myassistant.tools import CodingTool
from myassistant.config.models import create_model, parse_model_string


def _build_system_prompt(context_loader: ContextLoader) -> str:
    """Assemble the full system prompt from context files.

    Combines:
      - context/system_prompt.md  (base persona + guidelines)
      - context/project_context.md + AGENT.md  (project info)
      - context/memory.md  (persistent notes)

    Args:
        context_loader (ContextLoader): Loaded context configuration.

    Returns:
        str: Complete system prompt.
    """
    parts = [context_loader.system_prompt]

    project_ctx = context_loader.get_project_context()
    if project_ctx:
        parts.append(f"## Project Context\n\n{project_ctx}")

    memory = context_loader.get_memory()
    if memory:
        parts.append(f"## Persistent Notes\n\n{memory}")

    return "\n\n".join(parts)


def create_coding_agent(
    project_path: str | None = None,
    model: Model | str = "anthropic:claude-sonnet-4-20250514",
    db_path: str | None = None,
    context_loader: ContextLoader | None = None,
    **model_kwargs,
) -> Agent:
    """Create the main coding assistant agent.

    Args:
        project_path: Path to the project directory (defaults to current directory).
        model: Agno Model instance or model string like "provider:model_id".
        db_path: Optional custom database path.
        context_loader: Pre-built ContextLoader. Created from project_path if not provided.
        **model_kwargs: Additional model parameters (api_key, base_url, temperature, etc.).

    Returns:
        Configured Agno Agent.
    """
    if project_path is None:
        project_path = str(Path.cwd())

    if isinstance(model, str):
        provider, model_id = parse_model_string(model)
        model = create_model(provider, model_id, **model_kwargs)

    if context_loader is None:
        context_loader = ContextLoader(project_path)

    db = create_database(db_path)
    system_prompt = _build_system_prompt(context_loader)

    # Load configurable agent settings from context/agent_settings.json
    settings = context_loader.agent_settings

    agent = Agent(
        name="myassistant",
        model=model,
        instructions=system_prompt,
        tools=[CodingTool(base_dir=project_path, context_loader=context_loader)],
        skills=context_loader.get_skills(),
        db=db,
        enable_user_memories=True,
        markdown=settings.get("markdown", True),
        num_history_runs=settings.get("num_history_runs", 15),
        add_history_to_context=settings.get("add_history_to_context", True),
        read_chat_history=settings.get("read_chat_history", True),
        read_tool_call_history=settings.get("read_tool_call_history", True),
    )

    return agent


