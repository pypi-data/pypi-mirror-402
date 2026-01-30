"""
Outbox Repository Module

Implements Repository Pattern for the outbox collection.
Handles event persistence and retrieval for the worker.
"""

from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.logging_config import get_logger
from app.models.outbox_event import EventStatus, OutboxEvent, OutboxEventCreate
from app.services.db_service import get_database

logger = get_logger(__name__)


class OutboxRepository:
    """
    Repository for outbox event operations.
    """

    def __init__(self) -> None:
        """Initialize repository."""
        self._db = get_database()

    @property
    def _collection(self) -> AsyncIOMotorCollection:  # type: ignore[type-arg]
        """Get the outbox collection."""
        return self._db.outbox

    @property
    def _dlq_collection(self) -> AsyncIOMotorCollection:  # type: ignore[type-arg]
        """Get the dead-letter queue collection."""
        return self._db.outbox_dlq

    async def create(self, event_data: OutboxEventCreate) -> OutboxEvent:
        """
        Create a new outbox event.

        Args:
            event_data: Event creation data.

        Returns:
            Created OutboxEvent.
        """
        event = OutboxEvent(
            event_type=event_data.event_type,
            payload=event_data.payload,
            priority=event_data.priority,
        )

        document = event.to_document()
        result = await self._collection.insert_one(document)
        event.id = str(result.inserted_id)

        logger.debug(f"Outbox event created: {event.id} ({event.event_type})")
        return event

    async def get_pending_events(self, limit: int = 10) -> list[OutboxEvent]:
        """
        Get pending events ordered by priority and creation time.

        Args:
            limit: Maximum number of events to return.

        Returns:
            List of pending events.
        """
        events = []
        cursor = (
            self._collection.find({"status": EventStatus.PENDING.value})
            .sort([("priority", -1), ("created_at", 1)])
            .limit(limit)
        )

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            events.append(OutboxEvent(**doc))

        return events

    async def mark_as_processing(self, event_id: str) -> bool:
        """
        Mark an event as being processed.
        Uses optimistic locking (PENDING -> PROCESSING).

        Args:
            event_id: Event ID.

        Returns:
            True if status was updated, False if event not in PENDING state.
        """
        result = await self._collection.update_one(
            {"_id": ObjectId(event_id), "status": EventStatus.PENDING.value},
            {"$set": {"status": EventStatus.PROCESSING.value, "updated_at": datetime.now(UTC)}},
        )
        return result.modified_count > 0

    async def mark_as_completed(self, event_id: str) -> bool:
        """
        Mark an event as completed.

        Args:
            event_id: Event ID.

        Returns:
            True if updated.
        """
        result = await self._collection.update_one(
            {"_id": ObjectId(event_id)},
            {
                "$set": {
                    "status": EventStatus.COMPLETED.value,
                    "processed_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            },
        )
        return result.modified_count > 0

    async def mark_as_failed(self, event_id: str, error: str, max_retries: int = 3) -> bool:
        """
        Mark an event as failed. Increments retry count.
        If max retries reached, moves to DLQ.

        Args:
            event_id: Event ID.
            error: Error message.
            max_retries: Maximum number of retries before DLQ.

        Returns:
            True if updated.
        """
        now = datetime.now(UTC)
        event_doc = await self._collection.find_one({"_id": ObjectId(event_id)})

        if not event_doc:
            return False

        retry_count = event_doc.get("retry_count", 0) + 1

        if retry_count >= max_retries:
            # Move to DLQ
            event_doc["status"] = EventStatus.FAILED.value
            event_doc["error_message"] = error
            event_doc["retry_count"] = retry_count
            event_doc["updated_at"] = now
            event_doc["failed_at"] = now

            # Insert into DLQ
            await self._dlq_collection.insert_one(event_doc)
            # Remove from outbox
            await self._collection.delete_one({"_id": ObjectId(event_id)})

            logger.warning(f"Event moved to DLQ: {event_id} (retries exceeded)")
            return True
        else:
            # Retry later (set back to PENDING)
            # Note: A real implementation might use exponential backoff for the "next_retry" time
            result = await self._collection.update_one(
                {"_id": ObjectId(event_id)},
                {
                    "$set": {
                        "status": EventStatus.PENDING.value,
                        "retry_count": retry_count,
                        "error_message": error,
                        "updated_at": now,
                    }
                },
            )
            logger.info(f"Event failed (retry {retry_count}/{max_retries}): {event_id}")
            return result.modified_count > 0


def get_outbox_repository() -> OutboxRepository:
    """Get OutboxRepository instance."""
    return OutboxRepository()
