from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.models.outbox_event import EventStatus, OutboxEventCreate
from app.repositories.outbox_repository import OutboxRepository


@pytest.fixture
def mock_collection():
    collection = MagicMock()
    # Setup async methods
    collection.insert_one = AsyncMock()
    collection.find_one = AsyncMock()
    collection.find_one_and_update = AsyncMock()
    collection.update_one = AsyncMock()
    collection.delete_one = AsyncMock()

    # Setup cursor for find
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=[])
    cursor.sort = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)

    # Setup async iteration default (empty)
    cursor.__aiter__.return_value = cursor
    cursor.__anext__.side_effect = StopAsyncIteration

    collection.find = MagicMock(return_value=cursor)

    return collection


@pytest_asyncio.fixture
async def outbox_repository(mock_collection, mock_db):
    # Retrieve the database mock from the mock_db fixture
    db = mock_db

    # Set properties to return mock_collection
    db.outbox = mock_collection
    # Also set default get_collection just in case (though not used via property)
    db.get_collection.return_value = mock_collection

    repo = OutboxRepository()
    # Force injection of mock db
    repo._db = db
    return repo


@pytest.mark.asyncio
async def test_create_event(outbox_repository, mock_collection):
    event_create = OutboxEventCreate(event_type="test_event", payload={"key": "value"}, priority=1)

    mock_collection.insert_one.return_value.inserted_id = "507f1f77bcf86cd799439011"

    event = await outbox_repository.create(event_create)

    assert event.event_type == "test_event"
    assert event.payload == {"key": "value"}
    assert event.status == EventStatus.PENDING
    mock_collection.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_pending_events(outbox_repository, mock_collection):
    # Setup mock data return
    mock_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "event_type": "test_event",
        "payload": {},
        "status": "PENDING",
        "priority": 10,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "retry_count": 0,
    }

    # Configure cursor for iteration
    cursor = mock_collection.find.return_value
    cursor.__anext__.side_effect = [mock_doc, StopAsyncIteration]

    events = await outbox_repository.get_pending_events(limit=5)

    assert len(events) == 1
    assert events[0].id == "507f1f77bcf86cd799439011"
    # Verify query
    mock_collection.find.assert_called()
    call_args = mock_collection.find.call_args
    assert call_args[0][0]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_mark_as_processing(outbox_repository, mock_collection):
    mock_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "event_type": "test_event",
        "payload": {},
        "status": "PROCESSING",
        "priority": 10,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "retry_count": 0,
    }
    mock_collection.find_one_and_update.return_value = mock_doc

    result = await outbox_repository.mark_as_processing("507f1f77bcf86cd799439011")

    assert result is not None
    assert result.status == EventStatus.PROCESSING
    mock_collection.find_one_and_update.assert_called()


@pytest.mark.asyncio
async def test_mark_as_completed(outbox_repository, mock_collection):
    mock_collection.update_one.return_value.modified_count = 1

    success = await outbox_repository.mark_as_completed("507f1f77bcf86cd799439011")

    assert success is True
    mock_collection.update_one.assert_called()
    call_args = mock_collection.update_one.call_args
    assert call_args[1]["update"]["$set"]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_mark_as_failed_retry(outbox_repository, mock_collection):
    # Mock event that should retry
    mock_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "event_type": "test_event",
        "payload": {},
        "status": "PENDING",  # reverting to pending
        "retry_count": 1,
        "error_message": "error",
    }

    # First find_one returns the current state
    mock_collection.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439011",
        "retry_count": 0,
        "status": "PROCESSING",
    }

    # Update sets it back to pending
    mock_collection.find_one_and_update.return_value = mock_doc

    success = await outbox_repository.mark_as_failed("507f1f77bcf86cd799439011", "error")

    assert success is True
    # Should have updated retry count + status PENDING
    mock_collection.find_one_and_update.assert_called()
    update_arg = mock_collection.find_one_and_update.call_args[1]["update"]
    assert update_arg["$inc"]["retry_count"] == 1
    assert update_arg["$set"]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_mark_as_failed_dlq(outbox_repository, mock_collection):
    # Mock event that exceeded retries
    current_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "retry_count": 5,  # Limit is 5
        "status": "PROCESSING",
        "event_type": "test",
        "payload": {},
        "priority": 1,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    mock_collection.find_one.return_value = current_doc

    # For DLQ, we assume outbox_dlq collection is also mocked
    # Mock get_collection("outbox_dlq")
    dlq_collection = MagicMock()
    dlq_collection.insert_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()

    # Configure db mock properties to return our collections
    outbox_repository._db.outbox_dlq = dlq_collection
    outbox_repository._db.outbox = mock_collection

    success = await outbox_repository.mark_as_failed("507f1f77bcf86cd799439011", "error")

    assert success is True
    dlq_collection.insert_one.assert_called()
    mock_collection.delete_one.assert_called()
