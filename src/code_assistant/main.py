"""CLI entry point for Mini-Claude-Code."""

from pathlib import Path

import typer
from rich.console import Console

from code_assistant.app import run_app
from code_assistant.config.models import PROVIDER_DEFAULTS

app = typer.Typer(name="mcc", help="Mini-Claude-Code: TUI coding assistant", add_completion=False)
console = Console()


@app.command()
def main(
    project_path: str | None = typer.Argument(None, help="Project directory"),
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
        help="Custom log directory (defaults to project_path/mcc_logs)"
    ),
    version: bool = typer.Option(False, "--version", "-V", help="Show version"),
):
    """Start the Mini-Claude-Code TUI.

    Examples:
        mcc                                    # Use default (Claude Sonnet)
        mcc --model openai:gpt-4o              # Use GPT-4o
        mcc --provider ollama                  # Use default Ollama model
        mcc -m ollama:llama3.2                 # Use specific Ollama model
        mcc -m openai:gpt-4o -b http://localhost:8080  # Use proxy
    """
    if version:
        console.print("[bold]Mini-Claude-Code[/bold] v0.1.0")
        raise typer.Exit(0)

    proj_path = str(Path(project_path).resolve()) if project_path else str(Path.cwd())

    # If provider specified, use its default model
    if provider:
        provider = provider.lower()
        if provider in PROVIDER_DEFAULTS:
            model = f"{provider}:{PROVIDER_DEFAULTS[provider]}"
        else:
            model = f"{provider}:default"

    # Build model kwargs for custom endpoints
    model_kwargs = {}
    if base_url:
        model_kwargs["base_url"] = base_url
    if api_key:
        model_kwargs["api_key"] = api_key

    try:
        run_app(project_path=proj_path, model=model, log_dir=log_dir, **model_kwargs)
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
