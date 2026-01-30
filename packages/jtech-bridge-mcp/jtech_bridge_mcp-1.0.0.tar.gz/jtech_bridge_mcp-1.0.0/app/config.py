"""
Application Configuration Module

Centralized configuration using Pydantic Settings for type-safe
environment variable handling with validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Follows the Single Responsibility Principle (SRP) - manages only configuration.
    Uses Pydantic for automatic validation and type coercion.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================================
    # MongoDB Configuration
    # =========================================================================
    mongo_uri: str = Field(
        default="mongodb://127.0.0.1:27017",
        description="MongoDB connection URI (localhost only for security)",
    )
    mongo_database: str = Field(
        default="mcp_bridge",
        description="MongoDB database name",
    )

    # =========================================================================
    # Logging Configuration
    # =========================================================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level for the application",
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Logging format pattern",
    )

    # =========================================================================
    # State Management
    # =========================================================================
    state_file_path: Path = Field(
        default=Path("./data/sync_state.json"),
        description="Path to the local state cache file",
    )

    # =========================================================================
    # Watchdog Configuration
    # =========================================================================
    watchdog_debounce_ms: int = Field(
        default=500,
        ge=100,
        le=5000,
        description="Debounce time in milliseconds for file change events",
    )

    # =========================================================================
    # Notification Configuration
    # =========================================================================
    notify_enabled: bool = Field(
        default=True,
        description="Enable OS notifications via notify-send",
    )
    notify_icon_path: Path = Field(
        default=Path("/usr/share/icons/hicolor/48x48/apps/mcp-bridge.png"),
        description="Path to the notification icon",
    )

    # =========================================================================
    # Validators
    # =========================================================================
    @field_validator("mongo_uri")
    @classmethod
    def validate_localhost_only(cls, v: str) -> str:
        """Ensure MongoDB is only accessible locally for security."""
        allowed_hosts = ["127.0.0.1", "localhost"]
        if not any(host in v for host in allowed_hosts):
            raise ValueError("MongoDB must be configured for localhost only (127.0.0.1 or localhost)")
        return v

    @field_validator("state_file_path", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        """Convert string paths to Path objects."""
        return Path(v) if isinstance(v, str) else v

    # =========================================================================
    # Computed Properties
    # =========================================================================
    @property
    def state_directory(self) -> Path:
        """Get the directory containing the state file."""
        return self.state_file_path.parent

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.state_directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached application settings (Singleton pattern via lru_cache).

    Returns:
        Settings: The application settings instance.
    """
    return Settings()
