"""Repo analyzer agent — explores a codebase and generates context/ config files."""

from pathlib import Path

from agno.agent import Agent
from agno.models.base import Model

from myassistant.config.models import create_model, parse_model_string
from myassistant.tools import CodingTool

# Repo-level prompts live alongside this file's context folder
_ANALYZER_CONTEXT_DIR = Path(__file__).parent.parent.parent.parent / "context" / "repo_analyzer"


def _load_analyzer_prompt(project_path: Path) -> str:
    """Load the analyzer system prompt, with project-level override support.

    Looks for the prompt in:
      1. <project>/context/repo_analyzer/system_prompt.md
      2. <repo>/context/repo_analyzer/system_prompt.md  (default)

    Args:
        project_path (Path): The user's project directory.

    Returns:
        str: The system prompt text.
    """
    project_override = project_path / "context" / "repo_analyzer" / "system_prompt.md"
    if project_override.exists():
        return project_override.read_text(encoding="utf-8").strip()

    default = _ANALYZER_CONTEXT_DIR / "system_prompt.md"
    if default.exists():
        return default.read_text(encoding="utf-8").strip()

    return "You are a repo analyzer. Explore the repo and write context/ config files."


def _load_output_template(project_path: Path) -> str:
    """Load the output template, with project-level override support.

    Args:
        project_path (Path): The user's project directory.

    Returns:
        str: The template markdown text, or empty string if not found.
    """
    project_override = project_path / "context" / "repo_analyzer" / "output_template.md"
    if project_override.exists():
        return project_override.read_text(encoding="utf-8").strip()

    default = _ANALYZER_CONTEXT_DIR / "output_template.md"
    if default.exists():
        return default.read_text(encoding="utf-8").strip()

    return ""


def create_repo_analyzer_agent(
    project_path: str | None = None,
    model: Model | str = "anthropic:claude-sonnet-4-20250514",
    force: bool = False,
    **model_kwargs,
) -> Agent:
    """Create the repo analyzer agent.

    The agent explores the repo structure and writes context/ config files:
      - context/project_context.md
      - context/memory.md
      - context/system_prompt.md
      - context/commands.json
      - context/agent_settings.json

    Args:
        project_path (str | None): Project directory to analyze (defaults to cwd).
        model (Model | str): Model instance or "provider:model_id" string.
        force (bool): If True, overwrite existing context files.
        **model_kwargs: Extra model kwargs (api_key, base_url, etc.).

    Returns:
        Configured Agno Agent ready to run.
    """
    if project_path is None:
        project_path = str(Path.cwd())

    proj = Path(project_path)

    if isinstance(model, str):
        provider, model_id = parse_model_string(model)
        model = create_model(provider, model_id, **model_kwargs)

    system_prompt = _load_analyzer_prompt(proj)
    template = _load_output_template(proj)

    # Embed the output template and force flag into the task instruction
    force_note = (
        "You MAY overwrite existing files in context/ because --force was set."
        if force
        else "Do NOT overwrite files that already exist in context/."
    )

    task_instruction = f"""
{force_note}

Your working directory is: {project_path}

## Output templates

Use the following templates exactly when producing context/ files:

{template}

Begin your analysis now. When done, confirm which files you wrote.
""".strip()

    # CodingTool without a ContextLoader — we cannot load real context yet
    # (that's what the analyzer is about to create). Use repo-level defaults only.
    from myassistant.config.context_loader import ContextLoader

    # Load from the repo defaults so the tool has safe/destructive rules
    default_loader = ContextLoader(project_path)

    return Agent(
        name="repo_analyzer",
        model=model,
        instructions=system_prompt,
        tools=[CodingTool(base_dir=project_path, context_loader=default_loader)],
        markdown=True,
        description="Analyzes a repository and generates context/ configuration files.",
        additional_context=task_instruction,
    )
