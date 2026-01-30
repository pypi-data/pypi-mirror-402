"""
Tests for State Cache Manager

Tests atomic operations and file locking functionality.
"""

import threading
import time
from pathlib import Path


class TestStateCache:
    """Test suite for StateCache class."""

    def test_read_empty_state(self, mock_state_cache, temp_state_file: Path):  # noqa: ARG002
        """Test reading state from a new/empty file."""
        state = mock_state_cache.read_state()

        assert "version" in state
        assert "last_updated" in state
        assert "pending_tasks" in state
        assert isinstance(state["pending_tasks"], list)

    def test_write_and_read_state(self, mock_state_cache):
        """Test writing and reading state."""
        test_data = {
            "version": "1.0",
            "custom_field": "test_value",
            "pending_tasks": [],
        }

        mock_state_cache.write_state(test_data)
        result = mock_state_cache.read_state()

        assert result["custom_field"] == "test_value"
        assert "last_updated" in result

    def test_update_state(self, mock_state_cache):
        """Test atomic state update."""
        mock_state_cache.write_state({"version": "1.0", "pending_tasks": []})

        updated = mock_state_cache.update_state({"new_field": "new_value"})

        assert updated["new_field"] == "new_value"
        assert "last_updated" in updated

    def test_add_pending_task(self, mock_state_cache):
        """Test adding a pending task."""
        task = mock_state_cache.add_pending_task(
            task_id="test-001",
            description="Test Task",
            contract_path="/path/to/contract.md",
            contract_type="markdown",
        )

        assert task["id"] == "test-001"
        assert task["description"] == "Test Task"

        tasks = mock_state_cache.get_pending_tasks()
        assert len(tasks) == 1
        assert tasks[0]["id"] == "test-001"

    def test_remove_pending_task(self, mock_state_cache):
        """Test removing a pending task."""
        mock_state_cache.add_pending_task(
            task_id="test-002",
            description="Task to Remove",
            contract_path="/path/to/file.md",
        )

        result = mock_state_cache.remove_pending_task("test-002")

        assert result is True
        assert len(mock_state_cache.get_pending_tasks()) == 0

    def test_remove_nonexistent_task(self, mock_state_cache):
        """Test removing a task that doesn't exist."""
        result = mock_state_cache.remove_pending_task("nonexistent")
        assert result is False

    def test_duplicate_task_update(self, mock_state_cache):
        """Test that adding a duplicate task updates it."""
        mock_state_cache.add_pending_task(
            task_id="test-003",
            description="Original",
            contract_path="/original.md",
        )

        mock_state_cache.add_pending_task(
            task_id="test-003",
            description="Updated",
            contract_path="/updated.md",
        )

        tasks = mock_state_cache.get_pending_tasks()
        assert len(tasks) == 1
        assert tasks[0]["description"] == "Updated"

    def test_clear_state(self, mock_state_cache):
        """Test clearing all state."""
        mock_state_cache.add_pending_task(
            task_id="test-004",
            description="Task",
            contract_path="/file.md",
        )

        mock_state_cache.clear()

        tasks = mock_state_cache.get_pending_tasks()
        assert len(tasks) == 0

    def test_concurrent_writes(self, mock_state_cache):
        """Test that concurrent writes are handled safely."""
        errors = []

        def writer(thread_id: int):
            try:
                for i in range(10):
                    mock_state_cache.add_pending_task(
                        task_id=f"thread-{thread_id}-task-{i}",
                        description=f"Task from thread {thread_id}",
                        contract_path=f"/path/{thread_id}/{i}.md",
                    )
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent writes: {errors}"

        # Verify state is valid JSON
        state = mock_state_cache.read_state()
        assert isinstance(state, dict)
        assert "pending_tasks" in state
