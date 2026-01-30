"""
Project Tools Module

MCP tools for project management operations.
Implements register_project, list_projects, and related operations.
"""

import json
from typing import Any

from mcp.types import TextContent
from pydantic import ValidationError

from app.logging_config import get_logger
from app.models.project import ProjectCreate, ProjectRole
from app.repositories.project_repository import get_project_repository
from app.tools.base import BaseTool

logger = get_logger(__name__)


class RegisterProjectTool(BaseTool):
    """
    Tool for registering a new project.

    Registers a project path with a specified role (producer/consumer)
    for file monitoring and synchronization.
    """

    @property
    def name(self) -> str:
        return "register_project"

    @property
    def description(self) -> str:
        return (
            "Register a project with the MCP Bridge for synchronization. "
            "The project path must exist and be an absolute path."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Human-readable project name (e.g., 'my-backend')",
                },
                "path": {
                    "type": "string",
                    "description": "Absolute path to the project directory",
                },
                "role": {
                    "type": "string",
                    "enum": ["producer", "consumer"],
                    "description": "Project role: 'producer' creates APIs, 'consumer' uses them",
                },
                "watch_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Glob patterns for files to watch (optional)",
                },
            },
            "required": ["name", "path", "role"],
        }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute project registration."""
        try:
            # Create project model with validation
            project_data = ProjectCreate(
                name=arguments["name"],
                path=arguments["path"],
                role=ProjectRole(arguments["role"]),
                watch_patterns=arguments.get("watch_patterns", ["**/openapi.json", "**/docs/*.md"]),
            )

            # Register in database
            repo = get_project_repository()
            project = await repo.create(project_data)

            result = {
                "success": True,
                "message": f"Project '{project.name}' registered successfully",
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "path": project.path,
                    "role": project.role.value,
                    "watch_patterns": project.watch_patterns,
                },
            }

            logger.info(f"Project registered via tool: {project.name}")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except ValidationError as e:
            error_msg = str(e)
            logger.warning(f"Project registration validation failed: {error_msg}")
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": "Validation error",
                            "details": error_msg,
                        },
                        indent=2,
                    ),
                )
            ]
        except ValueError as e:
            logger.warning(f"Project registration failed: {e}")
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                        },
                        indent=2,
                    ),
                )
            ]
        except Exception as e:
            logger.error(f"Unexpected error registering project: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": "Internal error",
                            "details": str(e),
                        },
                        indent=2,
                    ),
                )
            ]


class ListProjectsTool(BaseTool):
    """
    Tool for listing all registered projects.

    Returns all projects with optional filtering by role.
    """

    @property
    def name(self) -> str:
        return "list_projects"

    @property
    def description(self) -> str:
        return "List all registered projects. Optionally filter by role (producer/consumer)."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "enum": ["producer", "consumer"],
                    "description": "Filter by project role (optional)",
                },
            },
            "required": [],
        }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute project listing."""
        try:
            repo = get_project_repository()
            role = arguments.get("role")

            if role:
                projects = await repo.get_by_role(ProjectRole(role))
            else:
                projects = await repo.get_all()

            result = {
                "success": True,
                "count": len(projects),
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "path": p.path,
                        "role": p.role.value,
                        "watch_patterns": p.watch_patterns,
                        "created_at": p.created_at.isoformat(),
                    }
                    for p in projects
                ],
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error listing projects: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                        },
                        indent=2,
                    ),
                )
            ]


class GetProjectTool(BaseTool):
    """
    Tool for getting a specific project by ID or path.
    """

    @property
    def name(self) -> str:
        return "get_project"

    @property
    def description(self) -> str:
        return "Get a specific project by its ID or path."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Project MongoDB ID",
                },
                "path": {
                    "type": "string",
                    "description": "Project directory path",
                },
            },
            "required": [],
        }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute project retrieval."""
        try:
            repo = get_project_repository()
            project = None

            if "id" in arguments:
                project = await repo.get_by_id(arguments["id"])
            elif "path" in arguments:
                project = await repo.get_by_path(arguments["path"])
            else:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": False,
                                "error": "Either 'id' or 'path' is required",
                            },
                            indent=2,
                        ),
                    )
                ]

            if project:
                result = {
                    "success": True,
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "path": project.path,
                        "role": project.role.value,
                        "watch_patterns": project.watch_patterns,
                        "created_at": project.created_at.isoformat(),
                        "updated_at": project.updated_at.isoformat(),
                    },
                }
            else:
                result = {
                    "success": False,
                    "error": "Project not found",
                }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error getting project: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                        },
                        indent=2,
                    ),
                )
            ]


class UnregisterProjectTool(BaseTool):
    """
    Tool for unregistering (deleting) a project.
    """

    @property
    def name(self) -> str:
        return "unregister_project"

    @property
    def description(self) -> str:
        return "Unregister (delete) a project from the MCP Bridge."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Project MongoDB ID",
                },
                "path": {
                    "type": "string",
                    "description": "Project directory path (alternative to ID)",
                },
            },
            "required": [],
        }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute project deletion."""
        try:
            repo = get_project_repository()
            deleted = False

            if "id" in arguments:
                deleted = await repo.delete(arguments["id"])
            elif "path" in arguments:
                deleted = await repo.delete_by_path(arguments["path"])
            else:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": False,
                                "error": "Either 'id' or 'path' is required",
                            },
                            indent=2,
                        ),
                    )
                ]

            if deleted:
                result = {
                    "success": True,
                    "message": "Project unregistered successfully",
                }
            else:
                result = {
                    "success": False,
                    "error": "Project not found",
                }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error unregistering project: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                        },
                        indent=2,
                    ),
                )
            ]


class ProjectTools:
    """
    Factory for project-related tools.

    Provides a convenient way to get all project tools.
    """

    @staticmethod
    def get_all() -> list[BaseTool]:
        """Get all project tools."""
        return [
            RegisterProjectTool(),
            ListProjectsTool(),
            GetProjectTool(),
            UnregisterProjectTool(),
        ]
