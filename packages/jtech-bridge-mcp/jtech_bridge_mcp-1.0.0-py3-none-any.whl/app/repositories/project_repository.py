"""
Project Repository Module

Implements Repository Pattern for project persistence.
Provides CRUD operations for the projects collection.
"""

from datetime import datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.logging_config import get_logger
from app.models.project import (
    ProjectCreate,
    ProjectRead,
    ProjectRole,
    ProjectUpdate,
)
from app.services.db_service import get_database

logger = get_logger(__name__)


class ProjectRepository:
    """
    Repository for project persistence operations.

    Implements the Repository Pattern to abstract database operations.
    Follows Single Responsibility Principle - handles only project data access.

    Example:
        repo = ProjectRepository()
        project = await repo.create(ProjectCreate(
            name="my-backend",
            path="/home/user/projects/backend",
            role=ProjectRole.PRODUCER
        ))
    """

    def __init__(self) -> None:
        """Initialize repository with database connection."""
        self._db = get_database()

    @property
    def _collection(self) -> AsyncIOMotorCollection:  # type: ignore[type-arg]
        """Get the projects collection."""
        return self._db.projects

    async def create(self, project: ProjectCreate) -> ProjectRead:
        """
        Create a new project.

        Args:
            project: Project creation data.

        Returns:
            ProjectRead: The created project with database fields.

        Raises:
            ValueError: If a project with the same path already exists.
        """
        # Check for existing project with same path
        existing = await self._collection.find_one({"path": project.path})
        if existing:
            raise ValueError(f"Project with path '{project.path}' already exists")

        now = datetime.utcnow()
        document = {
            "name": project.name,
            "path": project.path,
            "role": project.role.value,
            "watch_patterns": project.watch_patterns,
            "created_at": now,
            "updated_at": now,
        }

        result = await self._collection.insert_one(document)
        inserted_id = str(result.inserted_id)

        logger.info(f"Project created: {project.name} ({project.role.value})")
        return ProjectRead(
            _id=inserted_id,
            name=project.name,
            path=project.path,
            role=project.role,
            watch_patterns=project.watch_patterns,
            created_at=now,
            updated_at=now,
        )

    async def get_by_id(self, project_id: str) -> ProjectRead | None:
        """
        Get a project by its ID.

        Args:
            project_id: The MongoDB document ID.

        Returns:
            ProjectRead if found, None otherwise.
        """
        if not ObjectId.is_valid(project_id):
            return None

        doc = await self._collection.find_one({"_id": ObjectId(project_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
            return ProjectRead(**doc)
        return None

    async def get_by_path(self, path: str) -> ProjectRead | None:
        """
        Get a project by its file path.

        Args:
            path: The project directory path.

        Returns:
            ProjectRead if found, None otherwise.
        """
        doc = await self._collection.find_one({"path": path})
        if doc:
            doc["_id"] = str(doc["_id"])
            return ProjectRead(**doc)
        return None

    async def get_all(self) -> list[ProjectRead]:
        """
        Get all registered projects.

        Returns:
            List of all projects.
        """
        projects = []
        async for doc in self._collection.find().sort("name", 1):
            doc["_id"] = str(doc["_id"])
            projects.append(ProjectRead(**doc))
        return projects

    async def get_by_role(self, role: ProjectRole) -> list[ProjectRead]:
        """
        Get all projects with a specific role.

        Args:
            role: The project role to filter by.

        Returns:
            List of projects with the specified role.
        """
        projects = []
        async for doc in self._collection.find({"role": role.value}).sort("name", 1):
            doc["_id"] = str(doc["_id"])
            projects.append(ProjectRead(**doc))
        return projects

    async def update(self, project_id: str, update_data: ProjectUpdate) -> ProjectRead | None:
        """
        Update an existing project.

        Args:
            project_id: The MongoDB document ID.
            update_data: Fields to update.

        Returns:
            Updated ProjectRead if found, None otherwise.
        """
        if not ObjectId.is_valid(project_id):
            return None

        # Build update document with only provided fields
        update_fields: dict[str, Any] = {}
        if update_data.name is not None:
            update_fields["name"] = update_data.name
        if update_data.role is not None:
            update_fields["role"] = update_data.role.value
        if update_data.watch_patterns is not None:
            update_fields["watch_patterns"] = update_data.watch_patterns

        if not update_fields:
            # No fields to update, just return current project
            return await self.get_by_id(project_id)

        update_fields["updated_at"] = datetime.utcnow()

        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(project_id)},
            {"$set": update_fields},
            return_document=True,
        )

        if result:
            result["_id"] = str(result["_id"])
            logger.info(f"Project updated: {result['name']}")
            return ProjectRead(**result)
        return None

    async def delete(self, project_id: str) -> bool:
        """
        Delete a project by its ID.

        Args:
            project_id: The MongoDB document ID.

        Returns:
            True if deleted, False if not found.
        """
        if not ObjectId.is_valid(project_id):
            return False

        result = await self._collection.delete_one({"_id": ObjectId(project_id)})
        if result.deleted_count > 0:
            logger.info(f"Project deleted: {project_id}")
            return True
        return False

    async def delete_by_path(self, path: str) -> bool:
        """
        Delete a project by its path.

        Args:
            path: The project directory path.

        Returns:
            True if deleted, False if not found.
        """
        result = await self._collection.delete_one({"path": path})
        if result.deleted_count > 0:
            logger.info(f"Project deleted by path: {path}")
            return True
        return False

    async def count(self) -> int:
        """
        Get the total number of registered projects.

        Returns:
            Number of projects.
        """
        count: int = await self._collection.count_documents({})
        return count

    async def get_paths(self, role: ProjectRole | None = None) -> list[str]:
        """
        Get all registered project paths.

        Args:
            role: Optional role filter.

        Returns:
            List of project paths.
        """
        query = {"role": role.value} if role else {}
        paths = []
        async for doc in self._collection.find(query, {"path": 1}):
            paths.append(doc["path"])
        return paths


def get_project_repository() -> ProjectRepository:
    """
    Factory function for ProjectRepository.

    Returns:
        ProjectRepository instance.
    """
    return ProjectRepository()
