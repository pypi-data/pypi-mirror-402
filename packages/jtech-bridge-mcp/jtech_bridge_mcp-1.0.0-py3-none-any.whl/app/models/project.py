"""
Project Model Module

Pydantic models for project registration and management.
Supports Producer/Consumer roles for IDE synchronization.
"""

from collections.abc import Generator
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, model_validator


class ProjectRole(str, Enum):
    """
    Project role enumeration.

    Defines the synchronization role of a project:
    - PRODUCER: Creates contracts/APIs that others consume
    - CONSUMER: Uses contracts/APIs from producers
    """

    PRODUCER = "producer"
    CONSUMER = "consumer"


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


class ProjectBase(BaseModel):
    """
    Base project model with common fields.

    Used as a foundation for create/read schemas following
    the Single Responsibility Principle.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Human-readable project name")
    path: str = Field(..., description="Absolute path to the project directory")
    role: ProjectRole = Field(..., description="Project role: producer or consumer")
    watch_patterns: list[str] = Field(
        default=["**/openapi.json", "**/docs/*.md"], description="Glob patterns for files to watch"
    )

    @field_validator("path")
    @classmethod
    def validate_path_absolute(cls, v: str) -> str:
        """Validate that path is absolute."""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError(f"Path must be absolute: {v}")
        return v


class ProjectCreate(ProjectBase):
    """
    Schema for creating a new project.

    Includes validation for path existence.
    """

    @model_validator(mode="after")
    def validate_path_exists(self) -> "ProjectCreate":
        """Validate that the project path exists."""
        path = Path(self.path)
        if not path.exists():
            raise ValueError(f"Project path does not exist: {self.path}")
        if not path.is_dir():
            raise ValueError(f"Project path is not a directory: {self.path}")
        return self


class ProjectUpdate(BaseModel):
    """
    Schema for updating an existing project.

    All fields are optional to support partial updates.
    """

    name: str | None = Field(None, min_length=1, max_length=100, description="Human-readable project name")
    role: ProjectRole | None = Field(None, description="Project role: producer or consumer")
    watch_patterns: list[str] | None = Field(None, description="Glob patterns for files to watch")


class ProjectRead(ProjectBase):
    """
    Schema for reading a project from database.

    Includes database-generated fields like _id and timestamps.
    """

    id: str = Field(..., alias="_id", description="MongoDB document ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
        },
    }


class ProjectInDB(ProjectBase):
    """
    Internal model for database operations.

    Represents the full document structure stored in MongoDB.
    """

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_document(self) -> dict[str, Any]:
        """Convert to MongoDB document format."""
        return {
            "name": self.name,
            "path": self.path,
            "role": self.role.value,
            "watch_patterns": self.watch_patterns,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_document(cls, doc: dict[str, Any]) -> "ProjectInDB":
        """Create instance from MongoDB document."""
        return cls(
            name=doc["name"],
            path=doc["path"],
            role=ProjectRole(doc["role"]),
            watch_patterns=doc.get("watch_patterns", []),
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at", datetime.utcnow()),
        )
