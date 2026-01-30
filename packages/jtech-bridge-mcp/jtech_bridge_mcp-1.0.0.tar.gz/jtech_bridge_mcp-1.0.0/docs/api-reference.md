# API Reference: MCP Tools

This document describes the tools available in the Jtech Bridge MCP.

## Project Management

### `register_project`
Register a new project for monitoring.

**Arguments:**
- `name` (string, required): Unique name of the project to identify it in the bridge.
- `path` (string, required): Absolute file system path to the project root.
- `role` (string, required): Role of the project (`producer` or `consumer`).
- `watch_patterns` (array[string], optional): List of glob patterns to watch for file changes (e.g., `["openapi.json", "docs/*.md"]`).

**Returns:**
- JSON with the registered project details.

### `list_projects`
List all registered projects.

**Arguments:**
- None.

**Returns:**
- JSON list of all projects and their status.

### `unregister_project`
Remove a project from monitoring.

**Arguments:**
- `name` (string, required): Name of the project to remove.

**Returns:**
- Success message.

---

## Intelligence & Sync

### `get_backend_status`
Checking pending tasks and backend status.

**Arguments:**
- `project_name` (string, optional): Filter tasks by producer project name.
- `status` (string, optional): Filter by task status (default: `pending`).

**Returns:**
- JSON with task count and list of tasks.

### `read_latest_contract`
Read the content of a contract file safely.

**Arguments:**
- `path` (string, required): Absolute path to the contract file.
- `section` (string, optional): Specific Markdown section header to extract (e.g., `Authentication`).

**Returns:**
- The content of the file or section.

### `mark_as_implemented`
Mark a pending task as implemented (Consumer action).

**Arguments:**
- `task_id` (string, required): ID of the task to mark as done.

**Returns:**
- Success message and confirmation of Outbox event generation.

### `register_task_completion`
Register that a backend task is completed (Producer action).

**Arguments:**
- `task_id` (string, required): Unique ID for the task.
- `description` (string, required): Description of the implementation.
- `contract_path` (string, required): Path to the updated contract file.

**Returns:**
- Success message indicating the task is now pending for consumers.
