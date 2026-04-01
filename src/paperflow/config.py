"""Configuration management for paperflow."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class OllamaConfig(BaseModel):
    """Ollama translation configuration."""

    host: str = "http://localhost:11434"
    model: str = "qwen2"
    timeout: int = 60


class Settings(BaseSettings):
    """Application settings."""

    # Data storage
    data_dir: Path = Path.home() / ".paperflow"
    db_path: Optional[Path] = None

    # Translation
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2"
    translate_enabled: bool = True

    # Fetching
    fetch_days: int = 7
    request_timeout: int = 30
    request_delay: float = 1.0  # seconds between requests

    @property
    def database_path(self) -> Path:
        """Get the database path."""
        if self.db_path:
            return self.db_path
        return self.data_dir / "papers.db"

    def ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    model_config = {
        "env_prefix": "PAPERFLOW_",
        "env_file": ".env",
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def save_settings(settings: Settings) -> None:
    """Save settings to config file."""
    config_path = settings.data_dir / "config.yaml"
    settings.ensure_data_dir()

    config_data = {
        "ollama_host": settings.ollama_host,
        "ollama_model": settings.ollama_model,
        "translate_enabled": settings.translate_enabled,
        "fetch_days": settings.fetch_days,
    }

    with open(config_path, "w") as f:
        yaml.dump(config_data, f)


def load_settings() -> Settings:
    """Load settings from config file or create defaults."""
    global _settings
    settings = get_settings()
    config_path = settings.data_dir / "config.yaml"

    if config_path.exists():
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
            if config_data:
                for key, value in config_data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)

    _settings = settings
    return settings
