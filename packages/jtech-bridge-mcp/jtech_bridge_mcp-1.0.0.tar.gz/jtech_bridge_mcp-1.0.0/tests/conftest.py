"""
Pytest Configuration and Fixtures

Provides shared fixtures and configuration for the test suite.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio


# ============================================================================
# Event Loop Configuration
# ============================================================================
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Settings Fixtures
# ============================================================================
@pytest.fixture
def temp_state_file(tmp_path: Path) -> Path:
    """Create a temporary state file for testing."""
    state_file = tmp_path / "data" / "sync_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    return state_file


@pytest.fixture
def mock_settings(temp_state_file: Path):
    """Create mock settings for testing."""
    with patch("app.config.get_settings") as mock:
        settings = MagicMock()
        settings.mongo_uri = "mongodb://127.0.0.1:27017"
        settings.mongo_database = "mcp_bridge_test"
        settings.log_level = "DEBUG"
        settings.log_format = "%(message)s"
        settings.state_file_path = temp_state_file
        settings.state_directory = temp_state_file.parent
        settings.watchdog_debounce_ms = 100
        settings.notify_enabled = False
        settings.ensure_directories = MagicMock()
        mock.return_value = settings
        yield settings


# ============================================================================
# Database Fixtures
# ============================================================================
@pytest_asyncio.fixture
async def mock_db() -> AsyncGenerator[MagicMock, None]:
    """Create a mock database service."""
    with patch("app.services.db_service.DatabaseService") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.health_check = MagicMock(return_value=True)
        mock_instance.initialize_collections = MagicMock()
        mock_instance.close = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


# ============================================================================
# State Cache Fixtures
# ============================================================================
@pytest.fixture
def mock_state_cache(temp_state_file: Path, mock_settings):  # noqa: ARG001
    """Create a state cache with temporary file."""
    from app.manager.state_cache import StateCache

    # Reset singleton completely
    StateCache._instance = None

    # Create new instance with proper initialization flag reset
    cache = StateCache.__new__(StateCache)
    cache._initialized = False
    StateCache._instance = cache
    cache.__init__()

    # Ensure clean state for each test
    cache.clear()

    yield cache

    # Cleanup - reset singleton for next test
    StateCache._instance = None
