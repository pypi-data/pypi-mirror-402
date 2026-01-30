"""
Tests for Project Models

Unit tests for Pydantic models in app/models/project.py.
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.project import (
    ProjectBase,
    ProjectCreate,
    ProjectInDB,
    ProjectRead,
    ProjectRole,
    ProjectUpdate,
)


class TestProjectRole:
    """Tests for ProjectRole enum."""

    def test_producer_value(self):
        """Test producer role value."""
        assert ProjectRole.PRODUCER.value == "producer"

    def test_consumer_value(self):
        """Test consumer role value."""
        assert ProjectRole.CONSUMER.value == "consumer"

    def test_from_string(self):
        """Test creating role from string."""
        assert ProjectRole("producer") == ProjectRole.PRODUCER
        assert ProjectRole("consumer") == ProjectRole.CONSUMER


class TestProjectBase:
    """Tests for ProjectBase model."""

    def test_valid_project(self, tmp_path: Path):
        """Test creating valid project base."""
        project = ProjectBase(
            name="test-project",
            path=str(tmp_path),
            role=ProjectRole.PRODUCER,
        )
        assert project.name == "test-project"
        assert project.path == str(tmp_path)
        assert project.role == ProjectRole.PRODUCER

    def test_default_watch_patterns(self, tmp_path: Path):
        """Test default watch patterns."""
        project = ProjectBase(
            name="test",
            path=str(tmp_path),
            role=ProjectRole.CONSUMER,
        )
        assert "**/openapi.json" in project.watch_patterns
        assert "**/docs/*.md" in project.watch_patterns

    def test_relative_path_fails(self):
        """Test that relative paths are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectBase(
                name="test",
                path="relative/path",
                role=ProjectRole.PRODUCER,
            )
        assert "absolute" in str(exc_info.value).lower()

    def test_empty_name_fails(self, tmp_path: Path):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError):
            ProjectBase(
                name="",
                path=str(tmp_path),
                role=ProjectRole.PRODUCER,
            )


class TestProjectCreate:
    """Tests for ProjectCreate model."""

    def test_valid_create(self, tmp_path: Path):
        """Test creating valid project."""
        project = ProjectCreate(
            name="test-project",
            path=str(tmp_path),
            role=ProjectRole.PRODUCER,
        )
        assert project.name == "test-project"

    def test_nonexistent_path_fails(self):
        """Test that non-existent paths are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                name="test",
                path="/nonexistent/path/that/does/not/exist",
                role=ProjectRole.PRODUCER,
            )
        assert "does not exist" in str(exc_info.value).lower()

    def test_file_path_fails(self, tmp_path: Path):
        """Test that file paths (not directories) are rejected."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                name="test",
                path=str(test_file),
                role=ProjectRole.PRODUCER,
            )
        assert "directory" in str(exc_info.value).lower()


class TestProjectUpdate:
    """Tests for ProjectUpdate model."""

    def test_partial_update(self):
        """Test partial update with only name."""
        update = ProjectUpdate(name="new-name")
        assert update.name == "new-name"
        assert update.role is None
        assert update.watch_patterns is None

    def test_empty_update(self):
        """Test empty update is valid."""
        update = ProjectUpdate()
        assert update.name is None
        assert update.role is None
        assert update.watch_patterns is None


class TestProjectRead:
    """Tests for ProjectRead model."""

    def test_from_dict(self, tmp_path: Path):
        """Test creating from dictionary (simulating DB response)."""
        now = datetime.utcnow()
        data = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "test-project",
            "path": str(tmp_path),
            "role": ProjectRole.PRODUCER,
            "watch_patterns": ["*.json"],
            "created_at": now,
            "updated_at": now,
        }

        project = ProjectRead(**data)
        assert project.id == "507f1f77bcf86cd799439011"
        assert project.name == "test-project"


class TestProjectInDB:
    """Tests for ProjectInDB model."""

    def test_to_document(self, tmp_path: Path):
        """Test converting to MongoDB document."""
        project = ProjectInDB(
            name="test",
            path=str(tmp_path),
            role=ProjectRole.PRODUCER,
            watch_patterns=["*.json"],
        )

        doc = project.to_document()
        assert doc["name"] == "test"
        assert doc["path"] == str(tmp_path)
        assert doc["role"] == "producer"
        assert "created_at" in doc
        assert "updated_at" in doc

    def test_from_document(self, tmp_path: Path):
        """Test creating from MongoDB document."""
        now = datetime.utcnow()
        doc = {
            "name": "test",
            "path": str(tmp_path),
            "role": "consumer",
            "watch_patterns": ["*.md"],
            "created_at": now,
            "updated_at": now,
        }

        project = ProjectInDB.from_document(doc)
        assert project.name == "test"
        assert project.role == ProjectRole.CONSUMER
