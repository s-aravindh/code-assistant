"""Model selector widget with provider and model selection."""

from dataclasses import dataclass
from typing import Dict, List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option


@dataclass
class ModelOption:
    """A model option for selection."""
    model_id: str
    description: str = ""


# Models organized by provider - easy to maintain and expand
PROVIDER_MODELS: Dict[str, List[ModelOption]] = {
    "anthropic": [
        ModelOption("claude-sonnet-4-20250514", "Latest Sonnet - balanced"),
        ModelOption("claude-opus-4-1-20250805", "Most capable"),
        ModelOption("claude-3-5-sonnet-20241022", "Previous Sonnet"),
        ModelOption("claude-3-5-haiku-20241022", "Fast & efficient"),
    ],
    "openai": [
        ModelOption("gpt-4o", "Most capable GPT-4"),
        ModelOption("gpt-4o-mini", "Fast & affordable"),
        ModelOption("gpt-4-turbo", "GPT-4 Turbo"),
        ModelOption("o1", "Reasoning model"),
        ModelOption("o1-mini", "Fast reasoning"),
    ],
    "ollama": [
        ModelOption("llama3.2", "Llama 3.2 (local)"),
        ModelOption("llama3.1", "Llama 3.1 (local)"),
        ModelOption("codellama", "Code Llama (local)"),
        ModelOption("mistral", "Mistral (local)"),
        ModelOption("qwen2.5-coder", "Qwen Coder (local)"),
        ModelOption("deepseek-r1", "DeepSeek R1 (local)"),
    ],
    "openrouter": [
        ModelOption("anthropic/claude-3.5-sonnet", "Claude via OpenRouter"),
        ModelOption("openai/gpt-4o", "GPT-4o via OpenRouter"),
        ModelOption("google/gemini-pro", "Gemini via OpenRouter"),
    ],
    "google": [
        ModelOption("gemini-2.0-flash", "Gemini 2.0 Flash"),
        ModelOption("gemini-1.5-pro", "Gemini 1.5 Pro"),
    ],
    "groq": [
        ModelOption("llama-3.3-70b-versatile", "Llama 3.3 70B (fast)"),
        ModelOption("mixtral-8x7b-32768", "Mixtral 8x7B (fast)"),
    ],
}


class ProviderSelector(ModalScreen):
    """First step: Select a provider."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
    ]

    CSS = """
    ProviderSelector {
        align: center top;
        padding-top: 3;
    }

    ProviderSelector > Vertical {
        width: 60;
        max-height: 20;
        background: $surface;
        border: thick $primary;
    }

    ProviderSelector #header {
        height: 3;
        background: $primary;
        padding: 1;
    }

    ProviderSelector OptionList {
        height: auto;
        max-height: 15;
        border: none;
        background: transparent;
    }

    ProviderSelector OptionList:focus {
        border: none;
    }
    """

    def __init__(self, current_model: str | None = None):
        super().__init__()
        self.current_model = current_model
        self.current_provider = None
        if current_model and ":" in current_model:
            self.current_provider = current_model.split(":")[0]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                "[bold]🤖 Select Provider[/bold] [dim]Enter to select[/dim]",
                id="header"
            )
            yield OptionList(id="provider-list")

    def on_mount(self) -> None:
        """Initialize provider list."""
        option_list = self.query_one("#provider-list", OptionList)
        providers = sorted(PROVIDER_MODELS.keys())

        for provider in providers:
            is_current = provider == self.current_provider
            indicator = "● " if is_current else "  "
            model_count = len(PROVIDER_MODELS[provider])
            label = f"{indicator}[bold]{provider}[/bold] [dim]({model_count} models)[/dim]"
            option_list.add_option(Option(label, id=provider))

        if providers:
            option_list.highlighted = 0

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle provider selection."""
        provider = event.option.id
        if provider:
            # Push model selector for this provider
            self.app.push_screen(
                ModelSelector(provider, self.current_model),
                self._handle_model_selection
            )

    def _handle_model_selection(self, result: tuple[str, str] | None) -> None:
        """Handle model selection from child screen."""
        if result:
            provider, model_id = result
            self.dismiss((provider, model_id))
        else:
            # User cancelled, stay on provider selector
            pass

    def action_close(self) -> None:
        """Close the selector."""
        self.dismiss(None)

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        option_list = self.query_one("#provider-list", OptionList)
        if option_list.highlighted is not None and option_list.highlighted > 0:
            option_list.highlighted -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        option_list = self.query_one("#provider-list", OptionList)
        if option_list.highlighted is not None:
            option_list.highlighted += 1


class ModelSelector(ModalScreen):
    """Second step: Select a model from the chosen provider."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
    ]

    CSS = """
    ModelSelector {
        align: center top;
        padding-top: 3;
    }

    ModelSelector > Vertical {
        width: 70;
        max-height: 20;
        background: $surface;
        border: thick $primary;
    }

    ModelSelector #header {
        height: 3;
        background: $primary;
        padding: 1;
    }

    ModelSelector OptionList {
        height: auto;
        max-height: 15;
        border: none;
        background: transparent;
    }

    ModelSelector OptionList:focus {
        border: none;
    }
    """

    def __init__(self, provider: str, current_model: str | None = None):
        super().__init__()
        self.provider = provider
        self.current_model = current_model
        self.models = PROVIDER_MODELS.get(provider, [])

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                f"[bold]🤖 Select {self.provider} Model[/bold] [dim]Enter to select, Esc to back[/dim]",
                id="header"
            )
            yield OptionList(id="model-list")

    def on_mount(self) -> None:
        """Initialize model list."""
        option_list = self.query_one("#model-list", OptionList)

        for model in self.models:
            full_id = f"{self.provider}:{model.model_id}"
            is_current = self.current_model == full_id
            indicator = "● " if is_current else "  "
            desc = f" - {model.description}" if model.description else ""
            label = f"{indicator}[bold]{model.model_id}[/bold][dim]{desc}[/dim]"
            option_list.add_option(Option(label, id=model.model_id))

        if self.models:
            option_list.highlighted = 0

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle model selection."""
        model_id = event.option.id
        if model_id:
            self.dismiss((self.provider, model_id))

    def action_back(self) -> None:
        """Go back to provider selector."""
        self.dismiss(None)

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        option_list = self.query_one("#model-list", OptionList)
        if option_list.highlighted is not None and option_list.highlighted > 0:
            option_list.highlighted -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        option_list = self.query_one("#model-list", OptionList)
        if option_list.highlighted is not None:
            option_list.highlighted += 1


# Main entry point - alias for ProviderSelector
class ModelSelectorScreen(ProviderSelector):
    """Main model selector entry point - starts with provider selection."""
    pass
