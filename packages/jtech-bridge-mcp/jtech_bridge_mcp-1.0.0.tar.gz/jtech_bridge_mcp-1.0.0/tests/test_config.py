"""
Tests for Configuration Module

Tests Pydantic settings validation and loading.
"""

from pathlib import Path

import pytest


class TestSettings:
    """Test suite for Settings class."""

    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        from app.config import Settings

        settings = Settings()

        assert settings.mongo_uri == "mongodb://127.0.0.1:27017"
        assert settings.mongo_database == "mcp_bridge"
        assert settings.log_level == "INFO"
        assert settings.watchdog_debounce_ms == 500

    def test_localhost_only_validation(self):
        """Test that non-localhost MongoDB URIs are rejected."""
        from app.config import Settings

        with pytest.raises(ValueError, match="localhost only"):
            Settings(mongo_uri="mongodb://remote-server:27017")

    def test_valid_localhost_variations(self):
        """Test that localhost variations are accepted."""
        from app.config import Settings

        # 127.0.0.1
        settings1 = Settings(mongo_uri="mongodb://127.0.0.1:27017")
        assert "127.0.0.1" in settings1.mongo_uri

        # localhost
        settings2 = Settings(mongo_uri="mongodb://localhost:27017")
        assert "localhost" in settings2.mongo_uri

    def test_state_directory_property(self, tmp_path: Path):
        """Test state_directory computed property."""
        from app.config import Settings

        state_file = tmp_path / "nested" / "state.json"
        settings = Settings(state_file_path=state_file)

        assert settings.state_directory == tmp_path / "nested"

    def test_ensure_directories(self, tmp_path: Path):
        """Test that ensure_directories creates the state directory."""
        from app.config import Settings

        state_file = tmp_path / "new_dir" / "state.json"
        settings = Settings(state_file_path=state_file)

        settings.ensure_directories()

        assert (tmp_path / "new_dir").exists()

    def test_log_level_validation(self):
        """Test that invalid log levels are rejected."""
        from app.config import Settings

        with pytest.raises(ValueError):
            Settings(log_level="INVALID")

    def test_watchdog_debounce_bounds(self):
        """Test watchdog debounce value boundaries."""
        from app.config import Settings

        # Too low
        with pytest.raises(ValueError):
            Settings(watchdog_debounce_ms=50)

        # Too high
        with pytest.raises(ValueError):
            Settings(watchdog_debounce_ms=10000)

        # Valid
        settings = Settings(watchdog_debounce_ms=1000)
        assert settings.watchdog_debounce_ms == 1000


class TestGetSettings:
    """Test suite for get_settings function."""

    def test_singleton_behavior(self):
        """Test that get_settings returns the same instance."""
        from app.config import get_settings

        # Clear the cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2
