"""CLI entry point for myassistant."""

from pathlib import Path

import typer
from rich.console import Console

from myassistant.app import run_app
from myassistant.config.models import PROVIDER_DEFAULTS

app = typer.Typer(
    name="myassistant",
    help="myassistant: TUI coding assistant",
    add_completion=False,
    invoke_without_command=True,
)
console = Console()


def _resolve_model(model: str, provider: str | None, base_url: str | None, api_key: str | None) -> tuple[str, dict]:
    """Resolve the model string and collect extra model kwargs.

    Args:
        model (str): Default model string.
        provider (str | None): Provider shortcut override.
        base_url (str | None): Custom API base URL.
        api_key (str | None): API key override.

    Returns:
        tuple[str, dict]: Resolved model string and kwargs dict.
    """
    if provider:
        provider = provider.lower()
        model = f"{provider}:{PROVIDER_DEFAULTS.get(provider, 'default')}"

    model_kwargs: dict = {}
    if base_url:
        model_kwargs["base_url"] = base_url
    if api_key:
        model_kwargs["api_key"] = api_key

    return model, model_kwargs


@app.callback()
def main(
    ctx: typer.Context,
    project_path: str | None = typer.Option(None, "--project", "-P", help="Project directory (defaults to cwd)"),
    model: str = typer.Option(
        "anthropic:claude-sonnet-4-20250514",
        "--model", "-m",
        help="Model string (provider:model_id) e.g. anthropic:claude-sonnet-4-20250514, openai:gpt-4o, ollama:llama3.2"
    ),
    provider: str | None = typer.Option(
        None, "--provider", "-p",
        help=f"Use default model for provider ({', '.join(PROVIDER_DEFAULTS.keys())})"
    ),
    base_url: str | None = typer.Option(
        None, "--base-url", "-b",
        help="Custom API base URL (for proxy or self-hosted)"
    ),
    api_key: str | None = typer.Option(
        None, "--api-key", "-k",
        help="API key (overrides environment variable)"
    ),
    log_dir: str | None = typer.Option(
        None, "--log-dir", "-l",
        help="Custom log directory (defaults to project_path/myassistant_logs)"
    ),
    version: bool = typer.Option(False, "--version", "-V", help="Show version"),
):
    """Start the myassistant TUI.

    Examples:
        myassistant                                    # Use default (Claude Sonnet)
        myassistant --model openai:gpt-4o              # Use GPT-4o
        myassistant --provider ollama                  # Use default Ollama model
        myassistant -m ollama:llama3.2                 # Use specific Ollama model
        myassistant -m openai:gpt-4o -b http://localhost:8080  # Use proxy
    """
    if version:
        console.print("[bold]myassistant[/bold] v0.1.0")
        raise typer.Exit(0)

    # If a subcommand was invoked (e.g. `analyze`), don't start the TUI
    if ctx.invoked_subcommand is not None:
        return

    proj_path = str(Path(project_path).resolve()) if project_path else str(Path.cwd())
    model, model_kwargs = _resolve_model(model, provider, base_url, api_key)

    try:
        run_app(project_path=proj_path, model=model, log_dir=log_dir, **model_kwargs)
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def analyze(
    project_path: str | None = typer.Argument(None, help="Project directory to analyze (defaults to cwd)"),
    model: str = typer.Option(
        "anthropic:claude-sonnet-4-20250514",
        "--model", "-m",
        help="Model string (provider:model_id)"
    ),
    provider: str | None = typer.Option(
        None, "--provider", "-p",
        help=f"Use default model for provider ({', '.join(PROVIDER_DEFAULTS.keys())})"
    ),
    base_url: str | None = typer.Option(None, "--base-url", "-b", help="Custom API base URL"),
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key override"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing context/ files"),
):
    """Analyze the repo and generate context/ config files.

    Explores the repository structure, conventions, and stack, then writes:

    \b
      context/project_context.md  — project description and structure
      context/memory.md            — key facts the agent should always know
      context/system_prompt.md     — tailored system prompt for this project
      context/commands.json        — safe/destructive command classification
      context/agent_settings.json  — agent behaviour settings

    Examples:
        myassistant analyze
        myassistant analyze /path/to/project --force
        myassistant analyze --model openai:gpt-4o
    """
    import asyncio
    from myassistant.agent.repo_analyzer import create_repo_analyzer_agent

    proj_path = str(Path(project_path).resolve()) if project_path else str(Path.cwd())
    model, model_kwargs = _resolve_model(model, provider, base_url, api_key)

    console.print(f"[bold]Analyzing[/bold] {proj_path} ...")

    agent = create_repo_analyzer_agent(
        project_path=proj_path,
        model=model,
        force=force,
        **model_kwargs,
    )

    try:
        asyncio.run(agent.aprint_response("Analyze this repository and generate the context/ files.", stream=True))
    except KeyboardInterrupt:
        console.print("\n[dim]Analysis cancelled.[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
