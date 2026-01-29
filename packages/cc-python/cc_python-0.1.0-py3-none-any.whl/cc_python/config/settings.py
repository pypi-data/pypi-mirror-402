"""Settings management for CC Python."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


@dataclass
class Settings:
    """Application settings."""

    # API settings
    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192

    # Thinking mode
    thinking_enabled: bool = False
    thinking_budget: int = 10000

    # Session settings
    session_dir: Path = field(default_factory=lambda: Path.home() / ".cc-python" / "sessions")
    config_dir: Path = field(default_factory=lambda: Path.home() / ".cc-python")

    # Tool settings
    auto_approve_read: bool = False
    auto_approve_write: bool = False
    auto_approve_shell: bool = False

    # Available models
    AVAILABLE_MODELS: list[str] = field(
        default_factory=lambda: [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]
    )

    def __post_init__(self) -> None:
        """Initialize settings after dataclass creation."""
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Load API key from environment if not set
        if not self.api_key:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    @property
    def config_file(self) -> Path:
        """Get the config file path."""
        return self.config_dir / "config.toml"

    @property
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def save(self) -> None:
        """Save settings to config file."""
        config_data = {
            "api": {
                "model": self.model,
                "max_tokens": self.max_tokens,
            },
            "thinking": {
                "enabled": self.thinking_enabled,
                "budget": self.thinking_budget,
            },
            "tools": {
                "auto_approve_read": self.auto_approve_read,
                "auto_approve_write": self.auto_approve_write,
                "auto_approve_shell": self.auto_approve_shell,
            },
        }

        with open(self.config_file, "wb") as f:
            tomli_w.dump(config_data, f)

    def load(self) -> None:
        """Load settings from config file."""
        if not self.config_file.exists():
            return

        with open(self.config_file, "rb") as f:
            config_data = tomllib.load(f)

        # API settings
        api_config = config_data.get("api", {})
        if "model" in api_config:
            self.model = api_config["model"]
        if "max_tokens" in api_config:
            self.max_tokens = api_config["max_tokens"]

        # Thinking settings
        thinking_config = config_data.get("thinking", {})
        if "enabled" in thinking_config:
            self.thinking_enabled = thinking_config["enabled"]
        if "budget" in thinking_config:
            self.thinking_budget = thinking_config["budget"]

        # Tool settings
        tools_config = config_data.get("tools", {})
        if "auto_approve_read" in tools_config:
            self.auto_approve_read = tools_config["auto_approve_read"]
        if "auto_approve_write" in tools_config:
            self.auto_approve_write = tools_config["auto_approve_write"]
        if "auto_approve_shell" in tools_config:
            self.auto_approve_shell = tools_config["auto_approve_shell"]

    def set_model(self, model: str) -> bool:
        """Set the model if valid."""
        if model in self.AVAILABLE_MODELS:
            self.model = model
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "thinking_enabled": self.thinking_enabled,
            "thinking_budget": self.thinking_budget,
            "auto_approve_read": self.auto_approve_read,
            "auto_approve_write": self.auto_approve_write,
            "auto_approve_shell": self.auto_approve_shell,
            "has_api_key": self.has_api_key,
        }


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.load()
    return _settings
