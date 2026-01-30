"""
Tests for Project Repository

Unit tests for project CRUD operations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.models.project import ProjectCreate, ProjectRole, ProjectUpdate
from app.repositories.project_repository import ProjectRepository


@pytest.fixture
def mock_collection():
    """Create a mock MongoDB collection."""
    collection = AsyncMock()
    return collection


@pytest.fixture
def repository(mock_collection):
    """Create repository with mocked collection."""
    with patch("app.repositories.project_repository.get_database") as mock_db:
        mock_db_instance = MagicMock()
        mock_db_instance.projects = mock_collection
        mock_db.return_value = mock_db_instance
        repo = ProjectRepository()
        repo._db = mock_db_instance
        yield repo


class TestProjectRepositoryCreate:
    """Tests for project creation."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, repository, mock_collection, tmp_path):
        """Test successful project creation."""
        # Setup
        mock_collection.find_one.return_value = None  # No existing project
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))

        project_data = ProjectCreate(
            name="test-project",
            path=str(tmp_path),
            role=ProjectRole.PRODUCER,
        )

        # Execute
        result = await repository.create(project_data)

        # Verify
        assert result.name == "test-project"
        assert result.id == "507f1f77bcf86cd799439011"
        mock_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_path_fails(self, repository, mock_collection, tmp_path):
        """Test that duplicate paths are rejected."""
        # Setup - existing project found
        mock_collection.find_one.return_value = {"path": str(tmp_path)}

        project_data = ProjectCreate(
            name="test-project",
            path=str(tmp_path),
            role=ProjectRole.PRODUCER,
        )

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            await repository.create(project_data)
        assert "already exists" in str(exc_info.value)


class TestProjectRepositoryRead:
    """Tests for project retrieval."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_collection, tmp_path):
        """Test getting project by ID."""
        now = datetime.utcnow()
        mock_collection.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "name": "test",
            "path": str(tmp_path),
            "role": "producer",
            "watch_patterns": [],
            "created_at": now,
            "updated_at": now,
        }

        result = await repository.get_by_id("507f1f77bcf86cd799439011")

        assert result is not None
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_collection):
        """Test getting non-existent project."""
        mock_collection.find_one.return_value = None

        result = await repository.get_by_id("507f1f77bcf86cd799439011")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_invalid_id(self, repository):
        """Test getting project with invalid ID."""
        result = await repository.get_by_id("invalid-id")
        assert result is None


class TestProjectRepositoryUpdate:
    """Tests for project updates."""

    @pytest.mark.asyncio
    async def test_update_project(self, repository, mock_collection, tmp_path):
        """Test updating a project."""
        now = datetime.utcnow()
        mock_collection.find_one_and_update.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "name": "updated-name",
            "path": str(tmp_path),
            "role": "producer",
            "watch_patterns": [],
            "created_at": now,
            "updated_at": now,
        }

        update_data = ProjectUpdate(name="updated-name")
        result = await repository.update("507f1f77bcf86cd799439011", update_data)

        assert result is not None
        assert result.name == "updated-name"


class TestProjectRepositoryDelete:
    """Tests for project deletion."""

    @pytest.mark.asyncio
    async def test_delete_project_success(self, repository, mock_collection):
        """Test successful project deletion."""
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        result = await repository.delete("507f1f77bcf86cd799439011")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, repository, mock_collection):
        """Test deleting non-existent project."""
        mock_collection.delete_one.return_value = MagicMock(deleted_count=0)

        result = await repository.delete("507f1f77bcf86cd799439011")

        assert result is False
