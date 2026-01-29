"""Configuration management using Pydantic Settings"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cosmux configuration settings"""

    model_config = SettingsConfigDict(
        env_prefix="COSMUX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key",
        alias="ANTHROPIC_API_KEY",
    )

    # Server
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=3333, description="Server port")

    # Database
    db_path: str = Field(default=".cosmux/cosmux.db", description="SQLite database path")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Model
    model: str = Field(
        default="claude-opus-4-5-20251101",
        description="Claude model to use",
    )
    max_tokens: int = Field(default=64000, description="Max tokens per response (Opus 4.5 max: 64k)")

    # Workspace (set dynamically)
    workspace: Optional[Path] = Field(default=None, description="Workspace directory")

    def get_db_path(self, workspace: Path) -> Path:
        """Get absolute database path relative to workspace"""
        db_path = Path(self.db_path)
        if db_path.is_absolute():
            return db_path
        return workspace / db_path


# Global settings instance
settings = Settings()
