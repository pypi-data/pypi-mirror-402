# Cursor Configuration Guide

Cursor supports the Model Context Protocol (MCP) natively. Follow these steps to configure the Jtech Bridge MCP.

## Prerequisites

1. Ensure the bridge is installed and running (or installable via the command line).
2. You need the full path to the `uv` executable or the python interpreter in your virtual environment.

## 1. Project-Specific Configuration (`.cursor/mcp.json`)

If you want to configure this for a specific project, create a file at `.cursor/mcp.json` (or add to your existing workspace configuration if supported).

*Note: As of early 2025, Cursor configuration for MCP is typically done in the global settings "Features" > "MCP" section, but you can also define it via command arguments.*

## 2. Global Configuration

1. Open Cursor.
2. Go to **Settings** (Cmd/Ctrl + ,).
3. Navigate to **Features** -> **MCP**.
4. Click **Add New Server**.

### Configuration Values

*   **Name:** `JtechBridgeMCP`
*   **Type:** `command` (stdio)
*   **Command:** `/absolute/path/to/your/project/.venv/bin/uv`
*   **Arguments:**
    *   `run`
    *   `jtech-bridge`

**Example:**
If your project is at `/home/user/code/mcp-ide-bridge`:

- **Command:** `/home/user/code/mcp-ide-bridge/.venv/bin/uv`
- **Args:** `run jtech-bridge`

## 3. Usage in Cursor

Once configured, you can use the bridge in Composer (Cmd+I) or Chat (Cmd+L).

- **Check Status:** "Get backend status" -> Calls `get_backend_status`
- **Register Project:** "Register this project as a producer" -> Calls `register_project`
- **Read Contract:** "Read the latest API contract" -> Calls `read_latest_contract`

## 4. Best Practices with Cursor Rules

Create a `.cursorrules` file in your consumer project (Frontend) to instruct the AI on how to use the bridge:

```markdown
# MCP Bridge Integration

You have access to the `JtechBridgeMCP` MCP server.
Use it to synchronize with the backend development.

1. Always check for pending tasks at the start of a session:
   - Call `get_backend_status(status='pending')`

2. When implementing a feature:
   - Read the contract using `read_latest_contract(path=...)`.
   - If the contract is large, request specific sections using the `section` parameter.

3. After finishing implementation:
   - Call `mark_as_implemented(task_id=...)` to notify the backend team.
```
