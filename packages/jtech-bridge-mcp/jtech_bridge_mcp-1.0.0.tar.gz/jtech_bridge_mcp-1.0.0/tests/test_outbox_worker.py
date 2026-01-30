from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.outbox_event import EventStatus, OutboxEvent
from app.services.outbox_worker import OutboxWorker


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_pending_events = AsyncMock(return_value=[])
    repo.mark_as_processing = AsyncMock()
    repo.mark_as_completed = AsyncMock()
    repo.mark_as_failed = AsyncMock()
    return repo


@pytest.fixture
def outbox_worker(mock_repo):
    with patch("app.repositories.outbox_repository.get_outbox_repository", return_value=mock_repo):
        worker = OutboxWorker()
        yield worker


@pytest.mark.asyncio
async def test_register_handler(outbox_worker):
    async def handler(e):
        pass

    outbox_worker.register_handler("test_event", handler)
    assert "test_event" in outbox_worker._processors
    assert outbox_worker._processors["test_event"] == handler


@pytest.mark.asyncio
async def test_process_batch_success(outbox_worker, mock_repo):
    # Setup event
    event = OutboxEvent(
        id="test_id",
        event_type="test_event",
        payload={},
        status=EventStatus.PENDING,
        priority=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        retry_count=0,
    )

    # Setup repo returns
    mock_repo.get_pending_events.return_value = [event]
    mock_repo.mark_as_processing.return_value = event  # Successful lock

    # Setup handler
    handler_mock = AsyncMock()
    outbox_worker.register_handler("test_event", handler_mock)

    # Run process batch
    await outbox_worker._process_batch()

    # Verify calls
    mock_repo.get_pending_events.assert_called()
    mock_repo.mark_as_processing.assert_called_with("test_id")
    handler_mock.assert_called_with(event)
    mock_repo.mark_as_completed.assert_called_with("test_id")


@pytest.mark.asyncio
async def test_process_batch_no_handler(outbox_worker, mock_repo):
    event = OutboxEvent(
        id="test_id",
        event_type="unknown_event",
        payload={},
        status=EventStatus.PENDING,
        priority=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        retry_count=0,
    )

    mock_repo.get_pending_events.return_value = [event]
    mock_repo.mark_as_processing.return_value = event

    await outbox_worker._process_batch()

    # Should fail because no handler
    mock_repo.mark_as_failed.assert_called_with("test_id", "No handler registered")


@pytest.mark.asyncio
async def test_process_batch_handler_error(outbox_worker, mock_repo):
    event = OutboxEvent(
        id="test_id",
        event_type="test_event",
        payload={},
        status=EventStatus.PENDING,
        priority=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        retry_count=0,
    )

    mock_repo.get_pending_events.return_value = [event]
    mock_repo.mark_as_processing.return_value = event

    # Handler raises exception
    async def failing_handler(_):
        raise ValueError("Handler failed")

    outbox_worker.register_handler("test_event", failing_handler)

    await outbox_worker._process_batch()

    mock_repo.mark_as_failed.assert_called_with("test_id", "ValueError: Handler failed")


@pytest.mark.asyncio
async def test_worker_lifecycle(outbox_worker):
    # Just test start/stop flags
    # We won't actually wait for the loop because it's infinite
    # We can mock asyncio.create_task to avoid running the real loop

    with patch("asyncio.create_task") as mock_create_task:
        # Make the task awaitable (AsyncMock)
        mock_task = AsyncMock()
        mock_create_task.return_value = mock_task

        await outbox_worker.start()
        assert outbox_worker._running is True
        mock_create_task.assert_called()

        await outbox_worker.stop()
        assert outbox_worker._running is False
        # Should have awaited the task
        mock_task.assert_awaited()
