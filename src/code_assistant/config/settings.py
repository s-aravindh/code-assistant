"""Application settings."""

from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_prefix="MCC_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # LLM Settings
    provider: str = Field(
        default="anthropic",
        description="Default LLM provider"
    )
    model: str = Field(
        default="anthropic:claude-sonnet-4-20250514",
        description="Default model string"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Model temperature"
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        description="Maximum tokens for response"
    )
    
    # TUI Settings
    theme: str = Field(
        default="dark",
        description="TUI theme (dark/light)"
    )
    show_token_count: bool = Field(
        default=True,
        description="Show token count in status bar"
    )
    show_cost: bool = Field(
        default=True,
        description="Show estimated cost"
    )
    auto_scroll: bool = Field(
        default=True,
        description="Auto-scroll output panel"
    )
    vim_mode: bool = Field(
        default=False,
        description="Enable vim keybindings"
    )
    
    # Behavior Settings
    auto_approve_reads: bool = Field(
        default=True,
        description="Auto-approve file read operations"
    )
    auto_approve_safe_commands: bool = Field(
        default=False,
        description="Auto-approve safe shell commands"
    )
    confirm_before_write: bool = Field(
        default=True,
        description="Confirm before writing files"
    )
    confirm_before_execute: bool = Field(
        default=True,
        description="Confirm before executing commands"
    )
    max_file_size_kb: int = Field(
        default=1024,
        ge=1,
        description="Maximum file size to read (KB)"
    )
    max_context_files: int = Field(
        default=20,
        ge=1,
        description="Maximum files to keep in context"
    )
    
    # Memory Settings
    enable_global_memory: bool = Field(
        default=True,
        description="Enable global user memories"
    )
    enable_project_memory: bool = Field(
        default=True,
        description="Enable project-specific memory"
    )
    auto_compact_threshold: int = Field(
        default=80000,
        ge=1000,
        description="Token threshold for auto-compaction"
    )
    
    # Security Settings
    command_allowlist: List[str] = Field(
        default_factory=lambda: [
            "npm test",
            "npm run lint",
            "pytest",
            "make test",
            "cargo test",
        ],
        description="Commands that can auto-execute"
    )
    command_blocklist: List[str] = Field(
        default_factory=lambda: [
            "rm -rf /",
            "sudo rm",
        ],
        description="Commands that are always blocked"
    )
    protected_paths: List[str] = Field(
        default_factory=lambda: [
            "~/.ssh",
            "~/.gnupg",
            "/etc",
            ".env",
            "*.pem",
            "*.key",
        ],
        description="Paths that cannot be modified"
    )
    
    # Logging
    log_level: str = Field(
        default="info",
        description="Logging level"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path"
    )
    
    # Database
    db_path: Optional[str] = Field(
        default=None,
        description="Custom database path"
    )
    
    @classmethod
    def get_config_path(cls, project_path: Optional[Path] = None) -> Path:
        """Get the config file path.
        
        Args:
            project_path: Optional project directory
            
        Returns:
            Path to config file
        """
        if project_path:
            # Check for project-level config
            project_config = project_path / ".mcc" / "config.yaml"
            if project_config.exists():
                return project_config
        
        # Fall back to global config
        return Path.home() / ".config" / "mcc" / "config.yaml"
    
    @classmethod
    def load_from_yaml(cls, config_path: Path) -> "Settings":
        """Load settings from a YAML file.
        
        Args:
            config_path: Path to YAML config file
            
        Returns:
            Settings instance
        """
        if not config_path.exists():
            return cls()
        
        try:
            import yaml
            
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                return cls()
            
            return cls(**config_data)
        except Exception:
            # Fall back to defaults if config is invalid
            return cls()
    
    def save_to_yaml(self, config_path: Path) -> None:
        """Save settings to a YAML file.
        
        Args:
            config_path: Path to save config file
        """
        import yaml
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and save
        config_dict = self.model_dump()
        
        with open(config_path, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)
