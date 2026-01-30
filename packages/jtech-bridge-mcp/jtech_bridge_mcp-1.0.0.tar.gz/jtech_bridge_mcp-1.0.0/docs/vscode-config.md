# VS Code Configuration Guide

To use the Jtech Bridge MCP in VS Code, you can use any standard MCP extension or an AI assistant extension that supports MCP (like user-created extensions or future integrations).

## Using with "MCP Settings"

Typically, MCP servers are configured in a JSON config file located at:

- **Linux:** `~/.config/Code/User/globalStorage/mcp-settings.json` (or similar depending on the specific extension you are using).
- **MacOS:** `~/Library/Application Support/Code/User/globalStorage/...`

### Configuration JSON

Add the `JtechBridgeMCP` to your MCP servers configuration:

```json
{
  "mcpServers": {
    "JtechBridgeMCP": {
      "command": "/absolute/path/to/project/.venv/bin/uv",
      "args": [
        "run",
        "jtech-bridge"
      ],
      "env": {
        "MONGO_URI": "mongodb://localhost:27017"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Note:** Replace `/absolute/path/to/project/` with the actual path where you installed the bridge.

## Environment Variables

Make sure the `.env` variables required (like `MONGO_URI`) are either loaded by the command automatically (via `python-dotenv` which we use in the app) or passed explicitly in the `env` block above.

Our application loads `.env` located in the current working directory. Since VS Code might run the command from a different CWD, it is safer to:

1. Rely on the `setup.sh` installation which creates a proper environment.
2. Or pass key environment variables in the JSON config as shown above.

## Verification

After configuring:
1. Restart VS Code.
2. Open your MCP-enabled chat assistant.
3. Ask: "List available projects" or "Check backend status".
4. If the tool calls execute, the connection is working.
