"""
Watchdog Service Module

File system monitoring service using the watchdog library.
Monitors registered project directories for contract file changes.
"""

import hashlib
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class FileChangeEvent:
    """
    Represents a file change event.

    Immutable data class for file change information.
    """

    __slots__ = ("event_type", "file_hash", "path", "project_path", "timestamp")

    def __init__(
        self,
        path: Path,
        event_type: str,
        project_path: Path,
        file_hash: str | None = None,
    ) -> None:
        self.path = path
        self.event_type = event_type
        self.timestamp = datetime.now(UTC)
        self.file_hash = file_hash
        self.project_path = project_path

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": str(self.path),
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "file_hash": self.file_hash,
            "project_path": str(self.project_path),
        }


class DebouncedEventHandler(FileSystemEventHandler):
    """
    File system event handler with debouncing.

    Prevents multiple rapid events from triggering duplicate callbacks.
    Uses file hash to detect actual content changes.
    """

    def __init__(
        self,
        callback: Callable[[FileChangeEvent], None],
        patterns: list[str],
        project_path: Path,
        debounce_ms: int = 500,
    ) -> None:
        """
        Initialize the debounced event handler.

        Args:
            callback: Function to call when file changes.
            patterns: Glob patterns to match (e.g., ['*.json', '*.md']).
            project_path: Root path of the project being watched.
            debounce_ms: Debounce time in milliseconds.
        """
        super().__init__()
        self._callback = callback
        self._patterns = patterns
        self._project_path = project_path
        self._debounce_seconds = debounce_ms / 1000.0
        self._pending_events: dict[str, threading.Timer] = {}
        self._file_hashes: dict[str, str] = {}
        self._lock = threading.Lock()

        logger.debug(
            f"DebouncedEventHandler initialized for {project_path} with patterns {patterns}, debounce={debounce_ms}ms"
        )

    def _matches_pattern(self, path: Path) -> bool:
        """Check if path matches any of the configured patterns."""
        import fnmatch

        for pattern in self._patterns:
            # Support both simple patterns (*.json) and glob patterns (**/docs/*.md)
            if "**" in pattern:
                # For glob patterns, match against relative path
                try:
                    rel_path = path.relative_to(self._project_path)
                    rel_str = str(rel_path)
                    # Also check just the filename for patterns like **/openapi.json
                    if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(path.name, pattern.split("/")[-1]):
                        return True
                except ValueError:
                    # Path not relative to project
                    pass
            elif fnmatch.fnmatch(path.name, pattern):
                return True
        return False

    def _calculate_hash(self, path: Path) -> str | None:
        """Calculate SHA256 hash of file contents."""
        try:
            if not path.exists() or not path.is_file():
                return None
            with path.open("rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not calculate hash for {path}: {e}")
            return None

    def _has_content_changed(self, path: Path) -> bool:
        """Check if file content has actually changed."""
        current_hash = self._calculate_hash(path)
        if current_hash is None:
            return True  # File deleted or inaccessible

        path_str = str(path)
        with self._lock:
            previous_hash = self._file_hashes.get(path_str)
            if previous_hash == current_hash:
                logger.debug(f"File {path} unchanged (same hash)")
                return False
            self._file_hashes[path_str] = current_hash
            return True

    def _process_event(self, path: Path, event_type: str) -> None:
        """Process a debounced file event."""
        path_str = str(path)

        with self._lock:
            # Remove from pending events
            if path_str in self._pending_events:
                del self._pending_events[path_str]

        # For modified events, check if content actually changed
        if event_type == "modified" and not self._has_content_changed(path):
            return

        # Calculate hash for the event
        file_hash = self._calculate_hash(path)

        # Create event and invoke callback
        event = FileChangeEvent(
            path=path,
            event_type=event_type,
            project_path=self._project_path,
            file_hash=file_hash,
        )

        logger.info(f"File {event_type}: {path}")
        try:
            self._callback(event)
        except Exception as e:
            logger.error(f"Error in file change callback: {e}", exc_info=True)

    def _schedule_event(self, path: Path, event_type: str) -> None:
        """Schedule a debounced event."""
        path_str = str(path)

        with self._lock:
            # Cancel any pending timer for this file
            if path_str in self._pending_events:
                self._pending_events[path_str].cancel()

            # Schedule new timer
            timer = threading.Timer(
                self._debounce_seconds,
                self._process_event,
                args=(path, event_type),
            )
            timer.daemon = True
            self._pending_events[path_str] = timer
            timer.start()

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation event."""
        if event.is_directory:
            return
        path = Path(str(event.src_path))
        if self._matches_pattern(path):
            self._schedule_event(path, "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event."""
        if event.is_directory:
            return
        path = Path(str(event.src_path))
        if self._matches_pattern(path):
            self._schedule_event(path, "modified")

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion event."""
        if event.is_directory:
            return
        path = Path(str(event.src_path))
        if self._matches_pattern(path):
            # Clear hash cache for deleted files
            with self._lock:
                self._file_hashes.pop(str(path), None)
            self._schedule_event(path, "deleted")

    def cancel_all_pending(self) -> None:
        """Cancel all pending debounced events."""
        with self._lock:
            for timer in self._pending_events.values():
                timer.cancel()
            self._pending_events.clear()


class WatchdogService:
    """
    File system monitoring service.

    Manages watchdog observers for registered project directories.
    Implements the Singleton pattern for global access.

    Follows Single Responsibility Principle - handles only file monitoring.
    """

    _instance: "WatchdogService | None" = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> "WatchdogService":
        """Singleton pattern implementation."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        """Initialize the watchdog service."""
        if self._initialized:
            return

        self._settings = get_settings()
        self._observer: Any = None  # Observer type not well-typed
        self._handlers: dict[str, DebouncedEventHandler] = {}
        self._callbacks: list[Callable[[FileChangeEvent], None]] = []
        self._running = False
        self._initialized = True

        logger.info("WatchdogService initialized")

    def add_callback(self, callback: Callable[[FileChangeEvent], None]) -> None:
        """
        Add a callback for file change events.

        Args:
            callback: Function to call when files change.
        """
        self._callbacks.append(callback)
        callback_name = getattr(callback, "__name__", repr(callback))
        logger.debug(f"Added file change callback: {callback_name}")

    def remove_callback(self, callback: Callable[[FileChangeEvent], None]) -> None:
        """
        Remove a file change callback.

        Args:
            callback: The callback to remove.
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            callback_name = getattr(callback, "__name__", repr(callback))
            logger.debug(f"Removed file change callback: {callback_name}")

    def _dispatch_event(self, event: FileChangeEvent) -> None:
        """Dispatch event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                callback_name = getattr(callback, "__name__", repr(callback))
                logger.error(f"Error in callback {callback_name}: {e}", exc_info=True)

    def watch_project(self, project_path: Path, patterns: list[str]) -> bool:
        """
        Start watching a project directory.

        Args:
            project_path: Path to the project directory.
            patterns: Glob patterns for files to watch.

        Returns:
            True if watching started successfully.
        """
        path_str = str(project_path)

        if path_str in self._handlers:
            logger.warning(f"Already watching: {project_path}")
            return False

        if not project_path.exists():
            logger.error(f"Project path does not exist: {project_path}")
            return False

        # Create handler for this project
        handler = DebouncedEventHandler(
            callback=self._dispatch_event,
            patterns=patterns,
            project_path=project_path,
            debounce_ms=self._settings.watchdog_debounce_ms,
        )

        # Ensure observer is running
        if self._observer is None:
            self._observer = Observer()
            self._observer.start()
            self._running = True
            logger.info("Watchdog observer started")

        # Schedule watch
        try:
            self._observer.schedule(handler, path_str, recursive=True)
            self._handlers[path_str] = handler
            logger.info(f"Started watching project: {project_path} with patterns {patterns}")
            return True
        except Exception as e:
            logger.error(f"Failed to watch project {project_path}: {e}")
            return False

    def unwatch_project(self, project_path: Path) -> bool:
        """
        Stop watching a project directory.

        Args:
            project_path: Path to the project directory.

        Returns:
            True if unwatching was successful.
        """
        path_str = str(project_path)

        if path_str not in self._handlers:
            logger.warning(f"Not watching: {project_path}")
            return False

        handler = self._handlers.pop(path_str)
        handler.cancel_all_pending()

        if self._observer is not None:
            self._observer.unschedule_all()  # Unschedule all and reschedule remaining
            for remaining_path, remaining_handler in self._handlers.items():
                self._observer.schedule(remaining_handler, remaining_path, recursive=True)

        logger.info(f"Stopped watching project: {project_path}")
        return True

    def is_watching(self, project_path: Path) -> bool:
        """Check if a project is being watched."""
        return str(project_path) in self._handlers

    @property
    def watched_projects(self) -> list[str]:
        """Get list of watched project paths."""
        return list(self._handlers.keys())

    def start(self) -> None:
        """Start the watchdog service."""
        if self._running:
            return

        if self._observer is None:
            self._observer = Observer()

        self._observer.start()
        self._running = True
        logger.info("WatchdogService started")

    def stop(self) -> None:
        """Stop the watchdog service gracefully."""
        if not self._running:
            return

        # Cancel all pending events
        for handler in self._handlers.values():
            handler.cancel_all_pending()

        # Stop observer
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None

        self._handlers.clear()
        self._running = False
        logger.info("WatchdogService stopped")

    @property
    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._running


def get_watchdog_service() -> WatchdogService:
    """
    Get the watchdog service singleton.

    Returns:
        WatchdogService instance.
    """
    return WatchdogService()
