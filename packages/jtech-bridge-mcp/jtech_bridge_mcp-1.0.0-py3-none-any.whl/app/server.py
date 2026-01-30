"""
MCP Server Entry Point

Main server implementation using the Model Context Protocol (MCP).
Provides STDIO-based communication with IDEs for context synchronization.
"""

import asyncio
import signal
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
import sys
import argparse

from app import __version__
from app.config import get_settings
from app.logging_config import get_logger
from app.manager.state_cache import get_state_cache
from app.models.outbox_event import OutboxEvent, OutboxEventCreate
from app.repositories.outbox_repository import get_outbox_repository
from app.repositories.project_repository import get_project_repository
from app.services.db_service import get_database
from app.services.notification_service import get_notification_service
from app.services.outbox_worker import get_outbox_worker
from app.services.watchdog_service import FileChangeEvent, get_watchdog_service
from app.tools.base import ToolRegistry
from app.tools.project_tools import ProjectTools
from app.tools.sync_tools import SyncTools

logger = get_logger(__name__)


class MCPBridgeServer:
    """
    MCP Bridge Server implementation.

    Provides the main server functionality for IDE synchronization
    using the Model Context Protocol. Implements lifecycle management
    and tool registration.

    Follows Single Responsibility Principle - manages only MCP server operations.
    Uses ToolRegistry for dynamic tool management (Open/Closed Principle).
    """

    def __init__(self) -> None:
        """Initialize the MCP Bridge server."""
        self._server = Server("jtech-bridge-mcp")
        self._settings = get_settings()
        self._db = get_database()
        self._state_cache = get_state_cache()
        self._project_repository = get_project_repository()
        self._outbox_repository = get_outbox_repository()
        self._watchdog_service = get_watchdog_service()
        self._outbox_worker = get_outbox_worker()
        self._notification_service = get_notification_service()

        self._shutdown_event = asyncio.Event()
        self._tool_registry = ToolRegistry()
        self._loop: asyncio.AbstractEventLoop | None = None

        # Register all tools
        self._setup_tools()
        self._register_mcp_handlers()

        logger.info(f"MCP Bridge Server v{__version__} initialized")

    def _setup_tools(self) -> None:
        """Setup all tools in the registry."""
        # Register project management tools
        self._tool_registry.register_all(ProjectTools.get_all())

        # Register sync tools
        self._tool_registry.register_all(SyncTools.get_all())

        logger.debug(f"Registered tools: {self._tool_registry.tool_names}")

    def _register_mcp_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self._server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            # Core tools (built-in)
            core_tools = [
                Tool(
                    name="ping",
                    description="Health check - returns pong if server is running",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                Tool(
                    name="get_server_info",
                    description="Get information about the MCP Bridge server",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                Tool(
                    name="get_pending_tasks",
                    description="Get list of pending tasks from the sync state",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
            ]

            # Add registered tools from registry
            registered_tools = self._tool_registry.list_tools()

            return core_tools + registered_tools

        @self._server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            logger.debug(f"Tool called: {name} with args: {arguments}")

            # Check core tools first
            if name == "ping":
                return await self._handle_ping()
            elif name == "get_server_info":
                return await self._handle_get_server_info()
            elif name == "get_pending_tasks":
                return await self._handle_get_pending_tasks()

            # Try registered tools
            tool = self._tool_registry.get(name)
            if tool:
                return await tool.execute(arguments)

            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        logger.debug("MCP handlers registered")

    # =========================================================================
    # Core Tool Handlers
    # =========================================================================
    async def _handle_ping(self) -> list[TextContent]:
        """Handle ping tool - simple health check."""
        return [TextContent(type="text", text="pong")]

    async def _handle_get_server_info(self) -> list[TextContent]:
        """Handle get_server_info tool."""
        import json

        db_healthy = await self._db.health_check()

        info = {
            "name": "Local MCP Bridge",
            "version": __version__,
            "database": {
                "healthy": db_healthy,
                "database_name": self._settings.mongo_database,
            },
            "state_file": str(self._state_cache.file_path),
            "registered_tools": self._tool_registry.tool_names,
        }

        return [TextContent(type="text", text=json.dumps(info, indent=2))]

    async def _handle_get_pending_tasks(self) -> list[TextContent]:
        """Handle get_pending_tasks tool."""
        import json

        tasks = self._state_cache.get_pending_tasks()

        result = {
            "count": len(tasks),
            "tasks": tasks,
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # =========================================================================
    # Event Handlers
    # =========================================================================
    def _handle_file_change(self, event: FileChangeEvent) -> None:
        """
        Handle file change event from watchdog (runs in thread).

        Bridges the synchronous watchdog callback to the asynchronous
        OutboxRepository by scheduling a coroutine on the main event loop.
        """
        logger.debug(f"Detected change: {event.path} ({event.event_type})")

        async def _create_outbox_event() -> None:
            try:
                await self._outbox_repository.create(
                    OutboxEventCreate(
                        event_type="file_change",
                        payload=event.to_dict(),
                        priority=10,
                    )
                )
            except Exception as e:
                logger.error(f"Failed to create outbox event for file change: {e}")

        # Schedule execution in the main event loop
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(_create_outbox_event(), self._loop)

    async def _process_file_change_event(self, event: OutboxEvent) -> None:
        """
        Process file change event from outbox.

        This is where we would implement logic to notify the IDE or
        perform other actions in response to a file change.
        """
        logger.info(f"Processing file change event {event.id}: {event.payload}")

        path = event.payload.get("path", "unknown")
        event_type = event.payload.get("event_type", "change")

        await self._notification_service.send_notification(
            title="File Changed", message=f"{event_type}: {path}", urgency="low"
        )

    async def _process_task_completed_event(self, event: OutboxEvent) -> None:
        """Process backend task completion event."""
        logger.info(f"Processing task completion: {event.payload}")

        task_id = event.payload.get("task_id")
        description = event.payload.get("description")

        await self._notification_service.send_notification(
            title="Backend Task Completed", message=f"Task {task_id} is ready.\n\n{description}", urgency="normal"
        )

    # =========================================================================
    # Lifecycle Management
    # =========================================================================
    @asynccontextmanager
    async def _lifespan(self) -> AsyncIterator[None]:
        """Manage server lifecycle - startup and shutdown."""
        logger.info("Starting MCP Bridge Server...")

        try:
            # Initialize database collections
            await self._db.initialize_collections()

            # Verify database connection
            if not await self._db.health_check():
                logger.warning("Database health check failed, continuing without DB")

            # Store reference to the running loop for thread-safe bridging
            self._loop = asyncio.get_running_loop()

            # Initialize Watchdog
            logger.info("Initializing Watchdog Service...")
            self._watchdog_service.add_callback(self._handle_file_change)
            self._watchdog_service.start()

            # Restore watched projects
            try:
                projects = await self._project_repository.get_all()
                for project in projects:
                    try:
                        self._watchdog_service.watch_project(Path(project.path), project.watch_patterns)
                        logger.info(f"Restored watch for project: {project.name}")
                    except Exception as e:
                        logger.error(f"Failed to restore watch for {project.name}: {e}")
            except Exception as e:
                logger.error(f"Failed to restore projects watches: {e}")

            # Initialize Outbox Worker
            logger.info("Initializing Outbox Worker...")
            self._outbox_worker.register_handler("file_change", self._process_file_change_event)
            self._outbox_worker.register_handler("backend_task_completed", self._process_task_completed_event)
            await self._outbox_worker.start()

            logger.info("MCP Bridge Server started successfully")
            yield

        finally:
            # Cleanup
            logger.info("Shutting down MCP Bridge Server...")

            # Stop background services
            await self._outbox_worker.stop()
            self._watchdog_service.stop()
            self._watchdog_service.remove_callback(self._handle_file_change)

            await self._db.close()
            logger.info("MCP Bridge Server shutdown complete")

    async def run(self) -> None:
        """Run the MCP server using STDIO transport."""
        async with self._lifespan():
            # Setup signal handlers for graceful shutdown
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, lambda: self._shutdown_event.set())

            # Run the STDIO server
            async with stdio_server() as (read_stream, write_stream):
                logger.info("STDIO transport ready")
                await self._server.run(
                    read_stream,
                    write_stream,
                    self._server.create_initialization_options(),
                )

    def request_shutdown(self) -> None:
        """Request graceful server shutdown."""
        logger.info("Shutdown requested")
        self._shutdown_event.set()


def main() -> None:
    """Main entry point for the MCP Bridge server."""
    # Check for install command before anything else
    if "--install-service" in sys.argv:
        try:
            from app.installer import install_service
            install_service()
            return
        except ImportError as e:
            print(f"Error importing installer: {e}")
            sys.exit(1)

    logger.info("=" * 60)
    logger.info(f"Local MCP Bridge v{__version__}")
    logger.info("=" * 60)

    server = MCPBridgeServer()

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
