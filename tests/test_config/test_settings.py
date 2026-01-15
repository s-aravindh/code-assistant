"""Tests for settings."""

import pytest
import tempfile
from pathlib import Path
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
    
    def test_security_settings(self):
        """Test security settings have defaults."""
        settings = Settings()
        
        assert len(settings.command_blocklist) > 0
        assert len(settings.protected_paths) > 0
        assert "~/.ssh" in settings.protected_paths
    
    def test_behavior_settings(self):
        """Test behavior settings have defaults."""
        settings = Settings()
        
        assert settings.confirm_before_write is True
        assert settings.confirm_before_execute is True
        assert settings.auto_approve_reads is True


class TestSettingsYaml:
    """Tests for YAML configuration."""
    
    def test_save_and_load_yaml(self, temp_dir):
        """Test saving and loading settings to YAML."""
        config_path = temp_dir / "config.yaml"
        
        # Create and save settings
        settings = Settings(provider="openai", temperature=0.8)
        settings.save_to_yaml(config_path)
        
        # Load and verify
        loaded = Settings.load_from_yaml(config_path)
        assert loaded.provider == "openai"
        assert loaded.temperature == 0.8
    
    def test_load_nonexistent_yaml(self, temp_dir):
        """Test loading from non-existent file returns defaults."""
        config_path = temp_dir / "nonexistent.yaml"
        
        settings = Settings.load_from_yaml(config_path)
        
        # Should return default settings
        assert settings.provider == "anthropic"
    
    def test_get_config_path_global(self):
        """Test getting global config path."""
        config_path = Settings.get_config_path()
        
        assert ".config" in str(config_path) or "mcc" in str(config_path)
    
    def test_get_config_path_project(self, temp_dir):
        """Test getting project-level config path."""
        # Create project config
        project_config = temp_dir / ".mcc" / "config.yaml"
        project_config.parent.mkdir(parents=True)
        project_config.write_text("provider: ollama\n")
        
        config_path = Settings.get_config_path(project_path=temp_dir)
        
        assert str(temp_dir) in str(config_path)
