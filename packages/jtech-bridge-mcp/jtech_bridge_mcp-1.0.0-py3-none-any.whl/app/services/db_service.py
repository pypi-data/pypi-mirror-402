"""
MongoDB Database Service Module

Provides async database connection and operations using Motor driver.
Implements Singleton pattern for connection reuse and manages collections.
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """
    Async MongoDB database service using Motor driver.

    Implements Singleton pattern to ensure a single database connection
    is reused across the application. Follows the Single Responsibility
    Principle - handles only database connection and collection management.

    Attributes:
        COLLECTION_PROJECTS: Name of the projects collection.
        COLLECTION_SYNC_STATE: Name of the sync state collection.
        COLLECTION_OUTBOX: Name of the outbox collection.
    """

    COLLECTION_PROJECTS = "projects"
    COLLECTION_SYNC_STATE = "sync_state"
    COLLECTION_OUTBOX = "outbox"
    COLLECTION_OUTBOX_DLQ = "outbox_dlq"

    _instance: Optional["DatabaseService"] = None
    _client: AsyncIOMotorClient | None = None  # type: ignore[type-arg]
    _database: AsyncIOMotorDatabase | None = None  # type: ignore[type-arg]

    def __new__(cls) -> "DatabaseService":
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the database service (only once due to Singleton)."""
        if DatabaseService._client is not None:
            return

        settings = get_settings()
        DatabaseService._client = AsyncIOMotorClient(settings.mongo_uri)
        DatabaseService._database = DatabaseService._client[settings.mongo_database]
        logger.info(f"Database service initialized: {settings.mongo_database}")

    @property
    def client(self) -> AsyncIOMotorClient:  # type: ignore[type-arg]
        """Get the MongoDB client instance."""
        if self._client is None:
            raise RuntimeError("Database not initialized")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:  # type: ignore[type-arg]
        """Get the MongoDB database instance."""
        if self._database is None:
            raise RuntimeError("Database not initialized")
        return self._database

    # =========================================================================
    # Collection Accessors
    # =========================================================================
    @property
    def projects(self) -> AsyncIOMotorCollection:  # type: ignore[type-arg]
        """Get the projects collection."""
        return self.database[self.COLLECTION_PROJECTS]

    @property
    def sync_state(self) -> AsyncIOMotorCollection:  # type: ignore[type-arg]
        """Get the sync state collection."""
        return self.database[self.COLLECTION_SYNC_STATE]

    @property
    def outbox(self) -> AsyncIOMotorCollection:  # type: ignore[type-arg]
        """Get the outbox collection."""
        return self.database[self.COLLECTION_OUTBOX]

    @property
    def outbox_dlq(self) -> AsyncIOMotorCollection:  # type: ignore[type-arg]
        """Get the outbox dead-letter queue collection."""
        return self.database[self.COLLECTION_OUTBOX_DLQ]

    # =========================================================================
    # Health Check
    # =========================================================================
    async def health_check(self) -> bool:
        """
        Check if the database connection is healthy.

        Returns:
            bool: True if connection is healthy, False otherwise.
        """
        try:
            await self.client.admin.command("ping")
            logger.debug("Database health check: OK")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    # =========================================================================
    # Collection Initialization
    # =========================================================================
    async def initialize_collections(self) -> None:
        """
        Initialize collections with indexes and validation rules.

        Creates necessary indexes for optimal query performance
        and data integrity.
        """
        logger.info("Initializing database collections and indexes...")

        # Projects collection indexes
        await self._create_projects_indexes()

        # Sync state collection indexes
        await self._create_sync_state_indexes()

        # Outbox collection indexes
        await self._create_outbox_indexes()

        logger.info("Database collections initialized successfully")

    async def _create_projects_indexes(self) -> None:
        """Create indexes for the projects collection."""
        await self.projects.create_index("path", unique=True)
        await self.projects.create_index("role")
        await self.projects.create_index("name")
        logger.debug("Projects collection indexes created")

    async def _create_sync_state_indexes(self) -> None:
        """Create indexes for the sync_state collection."""
        await self.sync_state.create_index("task_id", unique=True)
        await self.sync_state.create_index("status")
        await self.sync_state.create_index("producer_project_id")
        await self.sync_state.create_index([("status", 1), ("created_at", -1)])
        logger.debug("Sync state collection indexes created")

    async def _create_outbox_indexes(self) -> None:
        """Create indexes for the outbox collection."""
        await self.outbox.create_index("status")
        await self.outbox.create_index([("status", 1), ("created_at", 1)])
        await self.outbox.create_index("event_type")

        # DLQ indexes
        await self.outbox_dlq.create_index("original_id")
        await self.outbox_dlq.create_index("failed_at")
        logger.debug("Outbox collection indexes created")

    # =========================================================================
    # Lifecycle Management
    # =========================================================================
    async def close(self) -> None:
        """Close the database connection gracefully."""
        if self._client is not None:
            self._client.close()
            DatabaseService._client = None
            DatabaseService._database = None
            DatabaseService._instance = None
            logger.info("Database connection closed")


def get_database() -> DatabaseService:
    """
    Get the database service instance.

    Returns:
        DatabaseService: The singleton database service instance.
    """
    return DatabaseService()
