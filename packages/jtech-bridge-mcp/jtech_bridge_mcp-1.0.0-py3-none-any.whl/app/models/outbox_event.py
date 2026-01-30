"""
Outbox Event Model

Pydantic models for the Transactional Outbox Pattern.
"""

from collections.abc import Generator
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(str):
    """Custom type for MongoDB ObjectId handling in Pydantic."""

    @classmethod
    def __get_validators__(cls) -> Generator[Any, None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, *_args: Any) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v}")


class EventStatus(str, Enum):
    """Status of an outbox event."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutboxEventCreate(BaseModel):
    """Schema for creating a new outbox event."""

    event_type: str = Field(..., description="Type of the event (e.g., 'file_changed')")
    payload: dict[str, Any] = Field(..., description="Event data payload")
    priority: int = Field(default=0, description="Processing priority (higher first)")


class OutboxEvent(BaseModel):
    """
    Full outbox event model stored in database.
    """

    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    event_type: str
    payload: dict[str, Any]
    status: EventStatus = EventStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = None
    retry_count: int = 0
    error_message: str | None = None
    priority: int = 0

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
        },
    }

    def to_document(self) -> dict[str, Any]:
        """Convert to MongoDB document."""
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "processed_at": self.processed_at,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "priority": self.priority,
        }
