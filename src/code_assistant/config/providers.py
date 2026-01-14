"""LLM provider configuration."""

PROVIDERS = {
    "anthropic": "anthropic:claude-sonnet-4-20250514",
    "openai": "openai:gpt-4o",
    "ollama": "ollama:llama3.2",
}


def get_model_string(provider: str) -> str:
    """Get the default model string for a provider."""
    provider = provider.lower()
    if provider not in PROVIDERS:
        return f"{provider}:default"
    return PROVIDERS[provider]
