"""Token cost calculation utilities."""

from typing import TypedDict


class PricingTier(TypedDict):
    """Pricing information for a model."""
    input: float  # Cost per 1K input tokens
    output: float  # Cost per 1K output tokens


# Pricing per 1K tokens (as of early 2025)
# Prices may vary - update as needed
MODEL_PRICING: dict[str, PricingTier] = {
    # Anthropic
    "anthropic:claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "anthropic:claude-opus-4-1-20250805": {"input": 0.015, "output": 0.075},
    "anthropic:claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "anthropic:claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005},
    
    # OpenAI
    "openai:gpt-4o": {"input": 0.005, "output": 0.015},
    "openai:gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "openai:gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "openai:o1": {"input": 0.015, "output": 0.06},
    "openai:o1-mini": {"input": 0.003, "output": 0.012},
    
    # Ollama (local, free)
    "ollama:llama3.2": {"input": 0.0, "output": 0.0},
    "ollama:llama3.1": {"input": 0.0, "output": 0.0},
    "ollama:codellama": {"input": 0.0, "output": 0.0},
    "ollama:mistral": {"input": 0.0, "output": 0.0},
    "ollama:qwen2.5-coder": {"input": 0.0, "output": 0.0},
    "ollama:deepseek-r1": {"input": 0.0, "output": 0.0},
    
    # OpenRouter (approximate, varies)
    "openrouter:anthropic/claude-sonnet-4.5": {"input": 0.003, "output": 0.015},
    "openrouter:anthropic/claude-haiku-4.5": {"input": 0.001, "output": 0.005},
    "openrouter:anthropic/claude-opus-4.5": {"input": 0.015, "output": 0.075},
    
    # Google
    "google:gemini-2.0-flash": {"input": 0.00035, "output": 0.0015},
    "google:gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    
    # Groq (fast inference, competitive pricing)
    "groq:llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
    "groq:mixtral-8x7b-32768": {"input": 0.00024, "output": 0.00024},
}

# Default pricing for unknown models
DEFAULT_PRICING: PricingTier = {"input": 0.01, "output": 0.03}


def get_pricing(model: str) -> PricingTier:
    """Get pricing for a model.
    
    Args:
        model: Model string (e.g., "anthropic:claude-sonnet-4-20250514")
        
    Returns:
        Pricing tier dict with 'input' and 'output' costs per 1K tokens
    """
    return MODEL_PRICING.get(model, DEFAULT_PRICING)


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Calculate the cost of a request.
    
    Args:
        model: Model string
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    pricing = get_pricing(model)
    
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    
    return input_cost + output_cost


def calculate_session_cost(
    model: str,
    total_tokens: int,
    input_ratio: float = 0.3,
) -> float:
    """Estimate session cost from total tokens.
    
    When we only have total tokens, we estimate the split between
    input and output tokens.
    
    Args:
        model: Model string
        total_tokens: Total tokens used
        input_ratio: Estimated ratio of input to total (default 30%)
        
    Returns:
        Estimated cost in USD
    """
    input_tokens = int(total_tokens * input_ratio)
    output_tokens = total_tokens - input_tokens
    
    return calculate_cost(model, input_tokens, output_tokens)


def format_cost(cost: float) -> str:
    """Format a cost value for display.
    
    Args:
        cost: Cost in USD
        
    Returns:
        Formatted string (e.g., "$0.0023" or "$1.45")
    """
    if cost == 0:
        return "$0.00"
    elif cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def format_cost_display(
    model: str,
    total_tokens: int,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> str:
    """Format a complete cost display.
    
    Args:
        model: Model string
        total_tokens: Total tokens used
        input_tokens: Optional specific input token count
        output_tokens: Optional specific output token count
        
    Returns:
        Formatted display string
    """
    pricing = get_pricing(model)
    
    if input_tokens is not None and output_tokens is not None:
        cost = calculate_cost(model, input_tokens, output_tokens)
        return (
            f"**Token Usage**\n"
            f"- Input: {input_tokens:,} tokens\n"
            f"- Output: {output_tokens:,} tokens\n"
            f"- Total: {total_tokens:,} tokens\n\n"
            f"**Cost** (estimated)\n"
            f"- Input: {format_cost((input_tokens / 1000) * pricing['input'])}\n"
            f"- Output: {format_cost((output_tokens / 1000) * pricing['output'])}\n"
            f"- **Total: {format_cost(cost)}**"
        )
    else:
        cost = calculate_session_cost(model, total_tokens)
        return (
            f"**Token Usage**\n"
            f"- Total: {total_tokens:,} tokens\n\n"
            f"**Cost** (estimated)\n"
            f"- **Total: {format_cost(cost)}**\n\n"
            f"*Note: Cost is estimated based on typical input/output ratio*"
        )


def is_free_model(model: str) -> bool:
    """Check if a model is free (local).
    
    Args:
        model: Model string
        
    Returns:
        True if the model is free to use
    """
    pricing = get_pricing(model)
    return pricing["input"] == 0 and pricing["output"] == 0
