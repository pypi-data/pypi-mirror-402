"""
Sync and Intelligence Tools Module

Provides MCP tools for:
- Checking backend status (pending tasks)
- Reading contracts
- Marking tasks as implemented/completed
"""

import json
from pathlib import Path
from typing import Any, ClassVar

from mcp.types import TextContent

from app.logging_config import get_logger
from app.manager.state_cache import get_state_cache
from app.repositories.project_repository import get_project_repository
from app.tools.base import BaseTool

logger = get_logger(__name__)


class GetBackendStatusTool(BaseTool):
    """
    Tool to get the current backend status and pending tasks.

    Allows filtering tasks by project and status.
    """

    name = "get_backend_status"
    description = (
        "Get information about the backend status, including a list of pending tasks. Can be filtered by project name."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": "Optional name of the project to filter tasks for",
            },
            "status": {
                "type": "string",
                "description": "Status to filter by (default: 'pending')",
                "enum": ["pending"],  # Currently only pending is supported in JSON state
                "default": "pending",
            },
        },
        "required": [],
    }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        project_name = arguments.get("project_name")
        status = arguments.get("status", "pending")

        logger.debug(f"Executing get_backend_status with args: {arguments}")

        # Currently we only support 'pending' status from the JSON cache
        if status != "pending":
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": f"Status '{status}' not supported yet. Only 'pending' is available."}),
                )
            ]

        cache = get_state_cache()
        tasks = cache.get_pending_tasks()

        if project_name:
            repo = get_project_repository()
            project = await repo.get_by_name(project_name)

            if not project:
                return [TextContent(type="text", text=json.dumps({"error": f"Project '{project_name}' not found."}))]

            # Filter tasks that belong to this project path
            # We assume task 'path' is absolute or relative to project?
            # StateCache docs say 'contract_path'

            project_path = Path(project.path)
            filtered_tasks = []

            for task in tasks:
                task_path_str = task.get("path")
                if not task_path_str:
                    continue

                try:
                    task_path = Path(task_path_str)
                    # Check if task path is relative to project path
                    if task_path.is_absolute():
                        if task_path.is_relative_to(project_path):
                            filtered_tasks.append(task)
                    else:
                        # If relative, we assume it's relative to project root?
                        # Or we can't determine. For now, strict check on absolute paths.
                        pass
                except ValueError:
                    continue

            tasks = filtered_tasks

        result = {
            "status": "online",
            "task_count": len(tasks),
            "tasks": tasks,
            "filter": {"project": project_name, "status": status},
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]


class ReadLatestContractTool(BaseTool):
    """
    Tool to read the latest contract file safely.

    Supports filtering by markdown sections.
    """

    name = "read_latest_contract"
    description = "Read the content of a contract file safely. Supports fetching specific sections for Markdown files."
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the contract file",
            },
            "section": {
                "type": "string",
                "description": "Optional section header to extract (Markdown only)",
            },
        },
        "required": ["path"],
    }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        path_str = arguments.get("path")
        section = arguments.get("section")

        if not path_str:
            return [TextContent(type="text", text="Error: 'path' argument is required")]

        from app.services.path_validator import get_path_validator

        validator = get_path_validator()

        try:
            path = await validator.validate_path(path_str)
        except (ValueError, FileNotFoundError, PermissionError) as e:
            return [TextContent(type="text", text=f"Error accessing file: {e}")]

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading file: {e}")]

        if section and path.suffix.lower() == ".md":
            content = self._extract_markdown_section(content, section)
            if not content:
                return [TextContent(type="text", text=f"Section '{section}' not found in {path.name}")]

        return [TextContent(type="text", text=content)]

    def _extract_markdown_section(self, content: str, section: str) -> str | None:
        """
        Extract a specific section from markdown content.

        Looks for headers matching the section name (# Section).
        Returns the content up to the next header of same or higher level.
        """
        import re

        # Normalize section name for regex (escape special chars)
        safe_section = re.escape(section)

        # Match header: # Section, ## Section, etc.
        # Group 1: Header level (#, ##)
        header_pattern = re.compile(f"^(#+)\\s+{safe_section}\\s*$", re.MULTILINE | re.IGNORECASE)

        match = header_pattern.search(content)
        if not match:
            return None

        start_pos = match.end()
        header_level = len(match.group(1))

        # Find end of section: Next header of same or higher level (fewer #)
        # Regex to find next header with length <= header_level
        # e.g. if level is ## (2), stop at # (1) or ## (2)

        lines = content[start_pos:].splitlines(keepends=True)
        section_content = []

        # Regex for potential next header
        next_header_pattern = re.compile(r"^(#+)\s+")

        for line in lines:
            header_match = next_header_pattern.match(line)
            if header_match:
                next_level = len(header_match.group(1))
                if next_level <= header_level:
                    break
            section_content.append(line)

        return "".join(section_content).strip()


class MarkAsImplementedTool(BaseTool):
    """
    Tool to mark a task as implemented.

    This creates a persistent event and updates the local state.
    """

    name = "mark_as_implemented"
    description = (
        "Mark a specific task as implemented. "
        "This notifies the backend (outbox event) and updates the local sync user status."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "The unique identifier of the task",
            },
        },
        "required": ["task_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        task_id = arguments.get("task_id")

        if not task_id:
            return [TextContent(type="text", text="Error: 'task_id' argument is required")]

        # 1. Update local StateCache
        cache = get_state_cache()
        successful = cache.remove_pending_task(task_id)

        if not successful:
            # We don't fail hard, as it might just not be in the pending list anymore
            logger.warning(f"Task {task_id} not found in pending tasks during implementation mark.")

        # 2. Create Outbox Event
        try:
            from datetime import UTC, datetime

            from app.models.outbox_event import OutboxEventCreate
            from app.repositories.outbox_repository import get_outbox_repository

            repo = get_outbox_repository()

            payload = {"task_id": task_id, "timestamp": datetime.now(UTC).isoformat(), "status": "implemented"}

            await repo.create(
                OutboxEventCreate(
                    event_type="task_implemented",
                    payload=payload,
                    priority=20,  # Higher priority than file changes
                )
            )

            msg = f"Task {task_id} marked as implemented."
            if not successful:
                msg += " (Warning: Task was not found in pending list)"

            return [TextContent(type="text", text=json.dumps({"status": "success", "message": msg}))]

        except Exception as e:
            logger.error(f"Failed to create outbox event for task {task_id}: {e}")
            return [TextContent(type="text", text=f"Error processing task implementation: {e}")]


class RegisterTaskCompletionTool(BaseTool):
    """
    Tool for the Producer (Backend) to register that a task/contract is ready.

    This adds the task to the pending list for Consumers (Frontend) and triggers
    notifications.
    """

    name = "register_task_completion"
    description = (
        "Register that a backend task is completed and a contract is ready. "
        "This adds the task to the pending list for consumers."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "Unique identifier for the task",
            },
            "description": {
                "type": "string",
                "description": "Human-readable description of what was implemented",
            },
            "contract_path": {
                "type": "string",
                "description": "Absolute path to the relevant contract (openapi.json or markdown)",
            },
        },
        "required": ["task_id", "description", "contract_path"],
    }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        task_id = arguments.get("task_id")
        description = arguments.get("description")
        contract_path = arguments.get("contract_path")

        if not all([task_id, description, contract_path]):
            return [TextContent(type="text", text="Error: Missing required arguments")]

        # Validate path
        from app.services.path_validator import get_path_validator

        validator = get_path_validator()
        try:
            await validator.validate_path(contract_path)
        except Exception as e:
            return [TextContent(type="text", text=f"Invalid contract path: {e}")]

        # 1. Update local StateCache (Add to pending)
        cache = get_state_cache()

        # Determine contract type
        path_obj = Path(contract_path)
        contract_type = "openapi" if path_obj.suffix == ".json" else "markdown"

        cache.add_pending_task(
            task_id=task_id, description=description, contract_path=contract_path, contract_type=contract_type
        )

        # 2. Create Outbox Event
        try:
            from datetime import UTC, datetime

            from app.models.outbox_event import OutboxEventCreate
            from app.repositories.outbox_repository import get_outbox_repository

            repo = get_outbox_repository()

            payload = {
                "task_id": task_id,
                "description": description,
                "contract_path": contract_path,
                "timestamp": datetime.now(UTC).isoformat(),
                "status": "pending_consumer",
            }

            await repo.create(
                OutboxEventCreate(
                    event_type="backend_task_completed",
                    payload=payload,
                    priority=15,
                )
            )

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "success",
                            "message": f"Task {task_id} registered and marked as pending for consumers.",
                        }
                    ),
                )
            ]

        except Exception as e:
            logger.error(f"Failed to create outbox event for task {task_id}: {e}")
            return [TextContent(type="text", text=f"Error registering task: {e}")]


class SyncTools:
    """Registry Helper for Sync Tools."""

    @staticmethod
    def get_all() -> list[BaseTool]:
        """Get all sync tools."""
        return [
            GetBackendStatusTool(),
            ReadLatestContractTool(),
            MarkAsImplementedTool(),
            RegisterTaskCompletionTool(),
            WaitForNewTaskTool(),
        ]


class WaitForNewTaskTool(BaseTool):
    """
    Tool to block and wait for a new task to appear.

    This enables 'Active' monitoring by the Agent without busy-waiting loops in the LLM context.
    The tool performs long-polling on the state cache.
    """

    name = "wait_for_new_task"
    description = (
        "Waits (long-polling) for a new pending task to become available. "
        "Use this to actively listen for work from the backend. "
        "Returns immediately if tasks are already pending."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "timeout_seconds": {
                "type": "integer",
                "description": "Maximum time to wait in seconds (default: 60)",
                "default": 60,
            },
            "project_name": {
                "type": "string",
                "description": "Optional project name to filter tasks",
            },
        },
        "required": [],
    }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        import asyncio

        from app.manager.state_cache import get_state_cache
        from app.repositories.project_repository import get_project_repository

        timeout = arguments.get("timeout_seconds", 60)
        project_name = arguments.get("project_name")

        logger.info(f"Waiting for new task... (timeout={timeout}s)")

        # Resolve project path if filtering
        project_path = None
        if project_name:
            repo = get_project_repository()
            project = await repo.get_by_name(project_name)
            if project:
                project_path = Path(project.path)

        async def check_tasks() -> list[dict[str, Any]]:
            cache = get_state_cache()
            tasks = cache.get_pending_tasks()

            if not project_path:
                return tasks

            # Filter
            filtered = []
            for t in tasks:
                t_path = t.get("path")
                if t_path and Path(t_path).is_absolute() and Path(t_path).is_relative_to(project_path):
                    filtered.append(t)
            return filtered

        # Polling loop
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            tasks = await check_tasks()
            if tasks:
                return [
                    TextContent(
                        type="text", text=json.dumps({"status": "new_task_available", "tasks": tasks}, indent=2)
                    )
                ]

            # Wait before next poll
            await asyncio.sleep(2.0)

        return [
            TextContent(
                type="text",
                text=json.dumps({"status": "timeout", "message": "No new tasks appeared within the timeout period."}),
            )
        ]
