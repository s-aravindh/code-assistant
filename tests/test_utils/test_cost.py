"""Tests for cost calculation utilities."""

import pytest
from code_assistant.utils.cost import (
    get_pricing,
    calculate_cost,
    calculate_session_cost,
    format_cost,
    format_cost_display,
    is_free_model,
    MODEL_PRICING,
)


class TestGetPricing:
    """Tests for get_pricing function."""
    
    def test_get_pricing_anthropic(self):
        """Test getting pricing for Anthropic model."""
        pricing = get_pricing("anthropic:claude-sonnet-4-20250514")
        
        assert "input" in pricing
        assert "output" in pricing
        assert pricing["input"] > 0
        assert pricing["output"] > 0
    
    def test_get_pricing_openai(self):
        """Test getting pricing for OpenAI model."""
        pricing = get_pricing("openai:gpt-4o")
        
        assert pricing["input"] > 0
        assert pricing["output"] > 0
    
    def test_get_pricing_ollama_free(self):
        """Test getting pricing for Ollama (free local model)."""
        pricing = get_pricing("ollama:llama3.2")
        
        assert pricing["input"] == 0
        assert pricing["output"] == 0
    
    def test_get_pricing_unknown_uses_default(self):
        """Test that unknown models use default pricing."""
        pricing = get_pricing("unknown:model")
        
        assert "input" in pricing
        assert "output" in pricing


class TestCalculateCost:
    """Tests for calculate_cost function."""
    
    def test_calculate_cost_basic(self):
        """Test basic cost calculation."""
        cost = calculate_cost(
            "anthropic:claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500,
        )
        
        assert cost > 0
    
    def test_calculate_cost_free_model(self):
        """Test cost calculation for free model."""
        cost = calculate_cost(
            "ollama:llama3.2",
            input_tokens=1000,
            output_tokens=500,
        )
        
        assert cost == 0
    
    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        cost = calculate_cost(
            "openai:gpt-4o",
            input_tokens=0,
            output_tokens=0,
        )
        
        assert cost == 0


class TestCalculateSessionCost:
    """Tests for calculate_session_cost function."""
    
    def test_calculate_session_cost(self):
        """Test session cost estimation from total tokens."""
        cost = calculate_session_cost(
            "anthropic:claude-sonnet-4-20250514",
            total_tokens=1000,
        )
        
        assert cost > 0
    
    def test_calculate_session_cost_custom_ratio(self):
        """Test session cost with custom input ratio."""
        cost_30 = calculate_session_cost(
            "openai:gpt-4o",
            total_tokens=1000,
            input_ratio=0.3,
        )
        
        cost_70 = calculate_session_cost(
            "openai:gpt-4o",
            total_tokens=1000,
            input_ratio=0.7,
        )
        
        # Different ratios should produce different costs
        assert cost_30 != cost_70


class TestFormatCost:
    """Tests for format_cost function."""
    
    def test_format_cost_zero(self):
        """Test formatting zero cost."""
        formatted = format_cost(0)
        assert formatted == "$0.00"
    
    def test_format_cost_small(self):
        """Test formatting small cost."""
        formatted = format_cost(0.0001)
        assert "$" in formatted
        assert "0.0001" in formatted
    
    def test_format_cost_medium(self):
        """Test formatting medium cost."""
        formatted = format_cost(0.15)
        assert "$0.15" in formatted
    
    def test_format_cost_large(self):
        """Test formatting large cost."""
        formatted = format_cost(1.50)
        assert "$1.50" in formatted


class TestFormatCostDisplay:
    """Tests for format_cost_display function."""
    
    def test_format_cost_display_with_breakdown(self):
        """Test display with input/output breakdown."""
        display = format_cost_display(
            "anthropic:claude-sonnet-4-20250514",
            total_tokens=1500,
            input_tokens=1000,
            output_tokens=500,
        )
        
        assert "Input:" in display
        assert "Output:" in display
        assert "Total:" in display
        assert "1,500" in display or "1500" in display
    
    def test_format_cost_display_without_breakdown(self):
        """Test display without input/output breakdown."""
        display = format_cost_display(
            "openai:gpt-4o",
            total_tokens=1000,
        )
        
        assert "Total:" in display
        assert "estimated" in display.lower()


class TestIsFreeModel:
    """Tests for is_free_model function."""
    
    def test_ollama_is_free(self):
        """Test that Ollama models are free."""
        assert is_free_model("ollama:llama3.2") is True
        assert is_free_model("ollama:codellama") is True
    
    def test_anthropic_is_not_free(self):
        """Test that Anthropic models are not free."""
        assert is_free_model("anthropic:claude-sonnet-4-20250514") is False
    
    def test_openai_is_not_free(self):
        """Test that OpenAI models are not free."""
        assert is_free_model("openai:gpt-4o") is False
