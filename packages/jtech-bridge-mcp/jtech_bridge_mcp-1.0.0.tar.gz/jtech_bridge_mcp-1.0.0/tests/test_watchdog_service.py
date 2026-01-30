"""
Tests for Watchdog Service

Tests file monitoring, debouncing, and hash-based change detection.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.services.watchdog_service import (
    DebouncedEventHandler,
    FileChangeEvent,
    WatchdogService,
)


class TestFileChangeEvent:
    """Test suite for FileChangeEvent class."""

    def test_create_event(self, tmp_path: Path) -> None:
        """Test creating a file change event."""
        test_file = tmp_path / "test.json"
        event = FileChangeEvent(
            path=test_file,
            event_type="modified",
            project_path=tmp_path,
            file_hash="abc123",
        )

        assert event.path == test_file
        assert event.event_type == "modified"
        assert event.project_path == tmp_path
        assert event.file_hash == "abc123"
        assert event.timestamp is not None

    def test_event_to_dict(self, tmp_path: Path) -> None:
        """Test converting event to dictionary."""
        test_file = tmp_path / "test.json"
        event = FileChangeEvent(
            path=test_file,
            event_type="created",
            project_path=tmp_path,
        )

        result = event.to_dict()

        assert result["path"] == str(test_file)
        assert result["event_type"] == "created"
        assert result["project_path"] == str(tmp_path)
        assert "timestamp" in result


class TestDebouncedEventHandler:
    """Test suite for DebouncedEventHandler class."""

    def test_matches_simple_pattern(self, tmp_path: Path) -> None:
        """Test matching simple glob patterns."""
        callback = MagicMock()
        handler = DebouncedEventHandler(
            callback=callback,
            patterns=["*.json", "*.md"],
            project_path=tmp_path,
            debounce_ms=100,
        )

        assert handler._matches_pattern(tmp_path / "test.json")
        assert handler._matches_pattern(tmp_path / "README.md")
        assert not handler._matches_pattern(tmp_path / "test.py")
        assert not handler._matches_pattern(tmp_path / "test.txt")

    def test_matches_glob_pattern(self, tmp_path: Path) -> None:
        """Test matching complex glob patterns."""
        callback = MagicMock()
        handler = DebouncedEventHandler(
            callback=callback,
            patterns=["**/docs/*.md", "**/openapi.json"],
            project_path=tmp_path,
            debounce_ms=100,
        )

        # Create nested structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        assert handler._matches_pattern(docs_dir / "api.md")
        assert handler._matches_pattern(tmp_path / "api" / "openapi.json")

    def test_calculate_hash(self, tmp_path: Path) -> None:
        """Test SHA256 hash calculation."""
        callback = MagicMock()
        handler = DebouncedEventHandler(
            callback=callback,
            patterns=["*.json"],
            project_path=tmp_path,
            debounce_ms=100,
        )

        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}')

        hash1 = handler._calculate_hash(test_file)
        assert hash1 is not None
        assert len(hash1) == 64  # SHA256 hex length

        # Same content should have same hash
        hash2 = handler._calculate_hash(test_file)
        assert hash1 == hash2

        # Different content should have different hash
        test_file.write_text('{"key": "different"}')
        hash3 = handler._calculate_hash(test_file)
        assert hash3 != hash1

    def test_hash_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Test hash calculation for nonexistent file."""
        callback = MagicMock()
        handler = DebouncedEventHandler(
            callback=callback,
            patterns=["*.json"],
            project_path=tmp_path,
            debounce_ms=100,
        )

        result = handler._calculate_hash(tmp_path / "nonexistent.json")
        assert result is None

    def test_debounce_prevents_rapid_events(self, tmp_path: Path) -> None:
        """Test that debouncing prevents rapid event processing."""
        callback = MagicMock()
        handler = DebouncedEventHandler(
            callback=callback,
            patterns=["*.json"],
            project_path=tmp_path,
            debounce_ms=200,
        )

        test_file = tmp_path / "test.json"
        test_file.write_text('{"v": 1}')

        # Schedule multiple events rapidly
        handler._schedule_event(test_file, "modified")
        handler._schedule_event(test_file, "modified")
        handler._schedule_event(test_file, "modified")

        # Wait for debounce
        time.sleep(0.4)

        # Should only have processed once
        assert callback.call_count == 1

    def test_cancel_all_pending(self, tmp_path: Path) -> None:
        """Test canceling all pending events."""
        callback = MagicMock()
        handler = DebouncedEventHandler(
            callback=callback,
            patterns=["*.json"],
            project_path=tmp_path,
            debounce_ms=500,
        )

        test_file = tmp_path / "test.json"
        test_file.write_text('{"v": 1}')

        # Schedule event
        handler._schedule_event(test_file, "modified")

        # Cancel before debounce completes
        handler.cancel_all_pending()

        # Wait past debounce time
        time.sleep(0.6)

        # Should not have processed
        assert callback.call_count == 0


class TestWatchdogService:
    """Test suite for WatchdogService class."""

    @pytest.fixture
    def watchdog_service(self) -> WatchdogService:
        """Create a fresh watchdog service for each test."""
        # Reset singleton for testing
        WatchdogService._instance = None
        service = WatchdogService()
        yield service
        service.stop()
        WatchdogService._instance = None

    def test_singleton_pattern(self) -> None:
        """Test that WatchdogService is a singleton."""
        WatchdogService._instance = None
        service1 = WatchdogService()
        service2 = WatchdogService()
        assert service1 is service2
        service1.stop()
        WatchdogService._instance = None

    def test_add_and_remove_callback(self, watchdog_service: WatchdogService) -> None:
        """Test adding and removing callbacks."""
        callback = MagicMock()

        watchdog_service.add_callback(callback)
        assert callback in watchdog_service._callbacks

        watchdog_service.remove_callback(callback)
        assert callback not in watchdog_service._callbacks

    def test_watch_project(self, watchdog_service: WatchdogService, tmp_path: Path) -> None:
        """Test watching a project directory."""
        result = watchdog_service.watch_project(
            project_path=tmp_path,
            patterns=["*.json"],
        )

        assert result is True
        assert watchdog_service.is_watching(tmp_path)
        assert str(tmp_path) in watchdog_service.watched_projects

    def test_watch_nonexistent_project(self, watchdog_service: WatchdogService) -> None:
        """Test watching a nonexistent directory."""
        result = watchdog_service.watch_project(
            project_path=Path("/nonexistent/path"),
            patterns=["*.json"],
        )

        assert result is False

    def test_watch_project_twice(self, watchdog_service: WatchdogService, tmp_path: Path) -> None:
        """Test that watching the same project twice fails."""
        watchdog_service.watch_project(tmp_path, ["*.json"])

        result = watchdog_service.watch_project(tmp_path, ["*.md"])

        assert result is False

    def test_unwatch_project(self, watchdog_service: WatchdogService, tmp_path: Path) -> None:
        """Test unwatching a project."""
        watchdog_service.watch_project(tmp_path, ["*.json"])

        result = watchdog_service.unwatch_project(tmp_path)

        assert result is True
        assert not watchdog_service.is_watching(tmp_path)

    def test_unwatch_nonwatched_project(self, watchdog_service: WatchdogService, tmp_path: Path) -> None:
        """Test unwatching a project that isn't being watched."""
        result = watchdog_service.unwatch_project(tmp_path)

        assert result is False

    def test_start_stop(self, watchdog_service: WatchdogService) -> None:
        """Test starting and stopping the service."""
        watchdog_service.start()
        assert watchdog_service.is_running

        watchdog_service.stop()
        assert not watchdog_service.is_running

    def test_dispatch_event_to_callbacks(self, watchdog_service: WatchdogService, tmp_path: Path) -> None:
        """Test that events are dispatched to all callbacks."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        watchdog_service.add_callback(callback1)
        watchdog_service.add_callback(callback2)

        event = FileChangeEvent(
            path=tmp_path / "test.json",
            event_type="modified",
            project_path=tmp_path,
        )

        watchdog_service._dispatch_event(event)

        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)

    def test_callback_error_handling(self, watchdog_service: WatchdogService, tmp_path: Path) -> None:
        """Test that callback errors don't affect other callbacks."""
        callback1 = MagicMock(side_effect=Exception("Test error"))
        callback2 = MagicMock()

        watchdog_service.add_callback(callback1)
        watchdog_service.add_callback(callback2)

        event = FileChangeEvent(
            path=tmp_path / "test.json",
            event_type="modified",
            project_path=tmp_path,
        )

        # Should not raise
        watchdog_service._dispatch_event(event)

        # Second callback should still be called
        callback2.assert_called_once_with(event)
