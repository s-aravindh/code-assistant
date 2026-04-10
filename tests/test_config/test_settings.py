"""Tests for settings."""

import pytest
from myassistant.config.settings import Settings


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
        monkeypatch.setenv("MA_PROVIDER", "openai")
        monkeypatch.setenv("MA_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("MA_TEMPERATURE", "0.5")
        
        settings = Settings()
        
        assert settings.provider == "openai"
        assert settings.model == "openai:gpt-4o"
        assert settings.temperature == 0.5
    
    def test_log_rotation_settings(self):
        """Test log rotation settings have proper defaults."""
        settings = Settings()
        
        assert settings.log_max_size_mb == 10
        assert settings.log_backup_count == 5
    
    def test_log_level_setting(self):
        """Test log level setting has a default."""
        settings = Settings()
        assert settings.log_level == "info"
