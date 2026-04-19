"""CLI entry point for myassistant."""

from pathlib import Path

import typer
from rich.console import Console

from myassistant.app import run_app
from myassistant.config.context_loader import ContextLoader
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
    model: str | None = typer.Option(
        None,
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

    # Load agent_settings for model fallbacks (CLI args take priority)
    agent_settings = ContextLoader(proj_path).agent_settings
    resolved_base_url = base_url or agent_settings.get("base_url") or None
    resolved_api_key = api_key or agent_settings.get("api_key") or None

    # Resolve model string: CLI --provider/--model > agent_settings > hardcoded default
    if not provider and model is None:
        as_provider = agent_settings.get("provider", "anthropic")
        as_model_id = agent_settings.get("model_id") or PROVIDER_DEFAULTS.get(as_provider, "default")
        model = f"{as_provider}:{as_model_id}"

    model, model_kwargs = _resolve_model(model or "", provider, resolved_base_url, resolved_api_key)

    try:
        run_app(project_path=proj_path, model=model, log_dir=log_dir, **model_kwargs)
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
