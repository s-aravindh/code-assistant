"""Application settings."""

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
    
    # LLM Settings (used in /config display)
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
    
    # Behavior Settings (used in /config display)
    auto_approve_reads: bool = Field(
        default=True,
        description="Auto-approve file read operations"
    )
    confirm_before_write: bool = Field(
        default=True,
        description="Confirm before writing files"
    )
    confirm_before_execute: bool = Field(
        default=True,
        description="Confirm before executing commands"
    )
    
    # Logging
    log_level: str = Field(
        default="info",
        description="Logging level"
    )
    log_file: str | None = Field(
        default=None,
        description="Log file path"
    )
    log_max_size_mb: int = Field(
        default=10,
        ge=1,
        description="Maximum log file size in MB before rotation"
    )
    log_backup_count: int = Field(
        default=5,
        ge=0,
        description="Number of backup log files to keep"
    )
