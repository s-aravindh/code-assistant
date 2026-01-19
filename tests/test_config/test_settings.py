"""Tests for settings."""

import pytest
from code_assistant.config.settings import Settings


class TestSettings:
    """Tests for Settings class."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        
        assert settings.provider == "anthropic"
        assert "claude" in settings.model
        assert settings.temperature == 0.7
        assert settings.max_tokens == 4096
    
    def test_settings_from_env(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("MCC_PROVIDER", "openai")
        monkeypatch.setenv("MCC_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("MCC_TEMPERATURE", "0.5")
        
        settings = Settings()
        
        assert settings.provider == "openai"
        assert settings.model == "openai:gpt-4o"
        assert settings.temperature == 0.5
    
    def test_log_rotation_settings(self):
        """Test log rotation settings have proper defaults."""
        settings = Settings()
        
        assert settings.log_max_size_mb == 10
        assert settings.log_backup_count == 5
    
    def test_behavior_settings(self):
        """Test behavior settings have defaults."""
        settings = Settings()
        
        assert settings.confirm_before_write is True
        assert settings.confirm_before_execute is True
        assert settings.auto_approve_reads is True
