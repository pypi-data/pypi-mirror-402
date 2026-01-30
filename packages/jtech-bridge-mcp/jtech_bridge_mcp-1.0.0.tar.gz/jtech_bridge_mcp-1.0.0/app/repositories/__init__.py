"""
Repositories Package

Data access layer implementing the Repository Pattern.
Provides abstraction over database operations for domain entities.
"""

from app.repositories.outbox_repository import OutboxRepository, get_outbox_repository
from app.repositories.project_repository import ProjectRepository, get_project_repository

__all__ = [
    "OutboxRepository",
    "ProjectRepository",
    "get_outbox_repository",
    "get_project_repository",
]
