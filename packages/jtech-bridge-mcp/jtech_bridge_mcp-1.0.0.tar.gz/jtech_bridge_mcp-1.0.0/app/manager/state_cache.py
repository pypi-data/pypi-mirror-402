"""
State Cache Manager Module

Manages the local sync_state.json file with atomic operations
and file locking to prevent race conditions in multi-IDE scenarios.
"""

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

import fasteners

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class StateCache:
    """
    Local state cache manager with atomic file operations.

    Provides thread-safe and process-safe access to the local
    sync_state.json file using file locking via fasteners.

    Follows the Single Responsibility Principle - handles only
    local file state management with locking.
    """

    _instance: Optional["StateCache"] = None
    _class_lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> "StateCache":
        """Singleton pattern implementation with thread-safety."""
        with cls._class_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        """Initialize the state cache manager."""
        if self._initialized:
            return

        settings = get_settings()
        self._file_path: Path = settings.state_file_path
        self._lock_path: Path = self._file_path.with_suffix(".lock")

        # Thread lock for intra-process synchronization
        self._thread_lock: threading.RLock = threading.RLock()

        # Inter-process lock for cross-process synchronization
        self._process_lock: fasteners.InterProcessLock = fasteners.InterProcessLock(str(self._lock_path))

        # Ensure directories exist
        settings.ensure_directories()

        # Initialize file if it doesn't exist
        self._ensure_file_exists()

        self._initialized = True
        logger.info(f"State cache initialized: {self._file_path}")

    def _ensure_file_exists(self) -> None:
        """Create the state file with default content if it doesn't exist."""
        if not self._file_path.exists():
            default_state = {
                "version": "1.0",
                "last_updated": datetime.now(UTC).isoformat(),
                "pending_tasks": [],
            }
            self._write_raw(default_state)
            logger.info(f"Created new state file: {self._file_path}")

    def _write_raw(self, data: dict[str, Any]) -> None:
        """Write data to file without locking (internal use only)."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        with self._file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    # =========================================================================
    # Public API - Atomic Operations
    # =========================================================================
    def read_state(self) -> dict[str, Any]:
        """
        Read the current state from the cache file atomically.

        Returns:
            dict: The current state data.

        Raises:
            RuntimeError: If the lock cannot be acquired.
        """
        with self._thread_lock:
            try:
                with self._file_path.open(encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
                logger.debug("State read successfully")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in state file: {e}")
                # Return default state on corruption
                return {
                    "version": "1.0",
                    "last_updated": datetime.now(UTC).isoformat(),
                    "pending_tasks": [],
                }
            except FileNotFoundError:
                logger.warning("State file not found, returning default")
                return {
                    "version": "1.0",
                    "last_updated": datetime.now(UTC).isoformat(),
                    "pending_tasks": [],
                }

    def write_state(self, data: dict[str, Any]) -> None:
        """
        Write state to the cache file atomically.

        Args:
            data: The state data to write.

        Raises:
            RuntimeError: If the lock cannot be acquired.
        """
        with self._thread_lock:
            # Update timestamp
            data["last_updated"] = datetime.now(UTC).isoformat()
            self._write_raw(data)
            logger.debug("State written successfully")

    def update_state(self, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Atomically read, update, and write state.

        This is the preferred method for modifying state as it
        performs the read-modify-write cycle under a single lock.

        Args:
            updates: Dictionary of updates to apply.

        Returns:
            dict: The updated state data.
        """
        with self._thread_lock:
            # Read current state
            try:
                with self._file_path.open(encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                data = {
                    "version": "1.0",
                    "pending_tasks": [],
                }

            # Apply updates
            data.update(updates)
            data["last_updated"] = datetime.now(UTC).isoformat()

            # Write back
            self._write_raw(data)
            logger.debug("State updated successfully")
            return data

    # =========================================================================
    # Task Management
    # =========================================================================
    def add_pending_task(
        self,
        task_id: str,
        description: str,
        contract_path: str,
        contract_type: str = "markdown",
    ) -> dict[str, Any]:
        """
        Add a new pending task to the state.

        Args:
            task_id: Unique identifier for the task.
            description: Human-readable task description.
            contract_path: Path to the contract file.
            contract_type: Type of contract (markdown, swagger, etc.).

        Returns:
            dict: The new task entry.
        """
        with self._thread_lock:
            data = self._read_unlocked()

            # Check for duplicates
            existing_ids = {t["id"] for t in data.get("pending_tasks", [])}
            if task_id in existing_ids:
                logger.warning(f"Task {task_id} already exists, updating...")
                data["pending_tasks"] = [t for t in data["pending_tasks"] if t["id"] != task_id]

            # Create new task entry
            task = {
                "id": task_id,
                "description": description,
                "contract_type": contract_type,
                "path": contract_path,
                "created_at": datetime.now(UTC).isoformat(),
            }

            data.setdefault("pending_tasks", []).append(task)
            data["last_updated"] = datetime.now(UTC).isoformat()

            self._write_raw(data)
            logger.info(f"Added pending task: {task_id}")
            return task

    def remove_pending_task(self, task_id: str) -> bool:
        """
        Remove a task from the pending list.

        Args:
            task_id: The ID of the task to remove.

        Returns:
            bool: True if task was removed, False if not found.
        """
        with self._thread_lock:
            data = self._read_unlocked()
            original_count = len(data.get("pending_tasks", []))

            data["pending_tasks"] = [t for t in data.get("pending_tasks", []) if t["id"] != task_id]

            if len(data["pending_tasks"]) < original_count:
                data["last_updated"] = datetime.now(UTC).isoformat()
                self._write_raw(data)
                logger.info(f"Removed pending task: {task_id}")
                return True

            logger.warning(f"Task not found: {task_id}")
            return False

    def get_pending_tasks(self) -> list[dict[str, Any]]:
        """
        Get all pending tasks.

        Returns:
            list: List of pending task entries.
        """
        data = self.read_state()
        tasks: list[dict[str, Any]] = data.get("pending_tasks", [])
        return tasks

    def _read_unlocked(self) -> dict[str, Any]:
        """Read state without acquiring lock (must be called within lock context)."""
        try:
            with self._file_path.open(encoding="utf-8") as f:
                result: dict[str, Any] = json.load(f)
                return result
        except (json.JSONDecodeError, FileNotFoundError):
            return {"version": "1.0", "pending_tasks": []}

    # =========================================================================
    # Utility Methods
    # =========================================================================
    def clear(self) -> None:
        """Clear all state data."""
        with self._thread_lock:
            default_state = {
                "version": "1.0",
                "last_updated": datetime.now(UTC).isoformat(),
                "pending_tasks": [],
            }
            self._write_raw(default_state)
            logger.info("State cache cleared")

    @property
    def file_path(self) -> Path:
        """Get the path to the state file."""
        return self._file_path


def get_state_cache() -> StateCache:
    """
    Get the state cache instance.

    Returns:
        StateCache: The singleton state cache instance.
    """
    return StateCache()
