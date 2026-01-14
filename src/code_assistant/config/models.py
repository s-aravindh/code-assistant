"""Model factory for creating Agno model instances."""

from typing import Any, TYPE_CHECKING

from agno.models.base import Model

if TYPE_CHECKING:
    pass  # Type hints only

# Default model IDs per provider
PROVIDER_DEFAULTS = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
    "ollama": "llama3.2",
    "openrouter": "anthropic/claude-3.5-sonnet",
    "litellm": "gpt-4o",
}


def create_model(
    provider: str,
    model_id: str | None = None,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    **kwargs: Any,
) -> Model:
    """Create an Agno model instance.

    Args:
        provider: Provider name (anthropic, openai, ollama, openrouter, litellm)
        model_id: Model ID (uses provider default if not specified)
        api_key: Optional API key override
        base_url: Optional base URL for proxy/custom endpoints
        **kwargs: Additional model parameters (temperature, max_tokens, etc.)

    Returns:
        Configured Agno Model instance
    """
    provider = provider.lower()
    model_id = model_id or PROVIDER_DEFAULTS.get(provider, "")

    # Build common kwargs
    model_kwargs: dict[str, Any] = {"id": model_id, **kwargs}
    if api_key:
        model_kwargs["api_key"] = api_key

    match provider:
        case "anthropic":
            from agno.models.anthropic import Claude
            return Claude(**model_kwargs)

        case "openai":
            from agno.models.openai import OpenAIChat
            if base_url:
                model_kwargs["base_url"] = base_url
            return OpenAIChat(**model_kwargs)

        case "ollama":
            from agno.models.ollama import Ollama
            if base_url:
                model_kwargs["host"] = base_url
            return Ollama(**model_kwargs)

        case "openrouter":
            from agno.models.openrouter import OpenRouter
            if base_url:
                model_kwargs["base_url"] = base_url
            return OpenRouter(**model_kwargs)

        case "litellm":
            from agno.models.litellm import LiteLLM
            if base_url:
                model_kwargs["base_url"] = base_url
            return LiteLLM(**model_kwargs)

        case _:
            # Fallback to LiteLLM for unknown providers
            from agno.models.litellm import LiteLLM
            model_kwargs["id"] = f"{provider}/{model_id}" if model_id else provider
            if base_url:
                model_kwargs["base_url"] = base_url
            return LiteLLM(**model_kwargs)


def parse_model_string(model_string: str) -> tuple[str, str]:
    """Parse a model string into provider and model_id.

    Args:
        model_string: String like "anthropic:claude-sonnet-4-20250514" or just "claude-sonnet-4-20250514"

    Returns:
        Tuple of (provider, model_id)
    """
    if ":" in model_string:
        provider, model_id = model_string.split(":", 1)
        return provider.lower(), model_id

    # Infer provider from model name
    model_lower = model_string.lower()
    if "claude" in model_lower:
        return "anthropic", model_string
    if "gpt" in model_lower or "o1" in model_lower:
        return "openai", model_string
    if "llama" in model_lower or "mistral" in model_lower or "qwen" in model_lower:
        return "ollama", model_string

    # Default to anthropic
    return "anthropic", model_string


def get_model_display_name(model: Model) -> str:
    """Get a display-friendly name for a model."""
    provider = getattr(model, "provider", "unknown")
    model_id = getattr(model, "id", "unknown")
    return f"{provider}:{model_id}"
