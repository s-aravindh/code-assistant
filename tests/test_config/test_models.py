"""Tests for model configuration."""

import pytest
from code_assistant.config.models import (
    parse_model_string,
    create_model,
    get_model_display_name,
    PROVIDER_DEFAULTS,
)


class TestParseModelString:
    """Tests for parse_model_string function."""
    
    def test_parse_with_provider(self):
        """Test parsing a model string with explicit provider."""
        provider, model_id = parse_model_string("anthropic:claude-sonnet-4-20250514")
        assert provider == "anthropic"
        assert model_id == "claude-sonnet-4-20250514"
    
    def test_parse_with_provider_openai(self):
        """Test parsing an OpenAI model string."""
        provider, model_id = parse_model_string("openai:gpt-4o")
        assert provider == "openai"
        assert model_id == "gpt-4o"
    
    def test_parse_infers_anthropic(self):
        """Test that Claude models infer anthropic provider."""
        provider, model_id = parse_model_string("claude-sonnet-4-20250514")
        assert provider == "anthropic"
        assert model_id == "claude-sonnet-4-20250514"
    
    def test_parse_infers_openai(self):
        """Test that GPT models infer openai provider."""
        provider, model_id = parse_model_string("gpt-4o")
        assert provider == "openai"
        assert model_id == "gpt-4o"
    
    def test_parse_infers_ollama(self):
        """Test that Llama models infer ollama provider."""
        provider, model_id = parse_model_string("llama3.2")
        assert provider == "ollama"
        assert model_id == "llama3.2"
    
    def test_parse_unknown_defaults_to_anthropic(self):
        """Test that unknown models default to anthropic."""
        provider, model_id = parse_model_string("some-unknown-model")
        assert provider == "anthropic"
        assert model_id == "some-unknown-model"
    
    def test_parse_preserves_case(self):
        """Test that model IDs preserve case."""
        provider, model_id = parse_model_string("OPENAI:GPT-4o")
        assert provider == "openai"  # Provider is lowercased
        assert model_id == "GPT-4o"  # Model ID preserves case


class TestCreateModel:
    """Tests for create_model function."""
    
    def test_create_anthropic_model(self):
        """Test creating an Anthropic model."""
        model = create_model("anthropic", "claude-sonnet-4-20250514")
        assert model is not None
        assert hasattr(model, "id")
    
    def test_create_openai_model(self):
        """Test creating an OpenAI model."""
        model = create_model("openai", "gpt-4o")
        assert model is not None
    
    def test_create_ollama_model(self):
        """Test creating an Ollama model."""
        model = create_model("ollama", "llama3.2")
        assert model is not None
    
    def test_create_model_with_api_key(self):
        """Test creating a model with custom API key."""
        model = create_model("anthropic", "claude-sonnet-4-20250514", api_key="test-key")
        assert model is not None
    
    def test_create_model_unknown_provider(self):
        """Test creating a model with unknown provider falls back to LiteLLM."""
        model = create_model("unknown-provider", "some-model")
        assert model is not None


class TestProviderDefaults:
    """Tests for provider defaults."""
    
    def test_anthropic_default(self):
        """Test anthropic has a default model."""
        assert "anthropic" in PROVIDER_DEFAULTS
        assert "claude" in PROVIDER_DEFAULTS["anthropic"]
    
    def test_openai_default(self):
        """Test openai has a default model."""
        assert "openai" in PROVIDER_DEFAULTS
        assert "gpt" in PROVIDER_DEFAULTS["openai"]
    
    def test_ollama_default(self):
        """Test ollama has a default model."""
        assert "ollama" in PROVIDER_DEFAULTS
