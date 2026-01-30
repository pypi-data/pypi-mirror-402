# Jtech Bridge MCP

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🌉 A Model Context Protocol (MCP) server for synchronizing development context between Backend (Producer) and Frontend (Consumer) IDEs.

## 🎯 Overview

Jtech Bridge MCP eliminates the "information gap" between development roles by providing real-time synchronization of API contracts, documentation, and task status across different IDEs (Cursor, VS Code, Windsurf, etc.).

### Key Features

- **Real-time Sync**: Automatic file change detection via Watchdog
- **IDE Agnostic**: Works with any MCP-compatible IDE
- **Atomic Operations**: File locking for multi-IDE scenarios
- **Native Notifications**: Ubuntu/Linux `notify-send` integration
- **Role-based**: Distinguishes between Producer and Consumer projects

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- MongoDB 6.0+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/angelovicentefilho/mcp-ide-bridge.git
cd mcp-ide-bridge

# Run the automated setup script
# This will install uv, sync dependencies, and setup the systemd service
./setup.sh
```

Alternatively, for manual installation:

```bash
uv sync
cp .env.example .env
uv run jtech-bridge
```

### IDE Configuration

Detailed guides are available in the `docs/` folder:

- [Cursor Configuration](docs/cursor-config.md)
- [VS Code Configuration](docs/vscode-config.md)

## 🛠️ Available Tools

See [API Reference](docs/api-reference.md) for full details.

| Tool | Description |
|------|-------------|
| `register_project` | Register a project (Producer/Consumer) for monitoring |
| `list_projects` | List all registered projects |
| `get_backend_status` | Check for pending tasks from the backend |
| `read_latest_contract` | Read contract files (Markdown/JSON) safely |
| `mark_as_implemented` | Mark a task as done (Consumer) |
| `register_task_completion` | Register a completed task (Producer) |
| `wait_for_new_task` | Block and wait for new tasks (Consumer/Active Mode) |

## 🤖 Workflow Automático (Escuta Ativa)

O Jtech Bridge permite um fluxo de trabalho onde o Agente Frontend (Consumidor) monitora ativamente o Backend (Produtor) e começa a implementar funcionalidades automaticamente assim que elas são disponibilizadas, sem intervenção humana manual.

### 1. Configurar o Consumidor (Frontend)
No Cursor (projeto Frontend), cole este prompt para iniciar o **Modo de Escuta Ativa**:

```markdown
Eu quero que você entre no "Modo de Escuta Ativa".
Sua tarefa é monitorar continuamente o backend e implementar o que for solicitado.

Execute este loop:
1. Chame a tool `wait_for_new_task(timeout_seconds=300)`.
2. Essa tool vai ficar esperando. Se ela retornar uma tarefa:
   a. Leia o contrato da tarefa.
   b. Implemente o código necessário no frontend.
   c. Marque a tarefa como concluída com `mark_as_implemented`.
   d. Volte para o passo 1 imediatamente.
3. Se ela der timeout (retornar "timeout"), volte para o passo 1 imediatamente.

Não pare até que eu mande. Fique nesse loop infinito de trabalho.
```

### 2. Disparar Tarefas no Produtor (Backend)
No Antigravity ou outra IDE (projeto Backend), use este prompt para criar e delegar uma nova feature:

```markdown
Vamos criar uma nova funcionalidade no sistema.
1. Crie um arquivo de especificação chamado "docs/nova-feature.md".
2. Nele, descreva a API ou funcionalidade desejada.
3. Após criar o arquivo, use a tool "register_task_completion" para notificar o frontend:
   - task_id: "feature-xyz-001"
   - description: "Descrição da feature para o frontend implementar"
   - contract_path: (caminho absoluto do arquivo criado)
```

Assim que a etapa 3 for executada pelo Backend, o Frontend detectará a tarefa e iniciará a implementação automaticamente.

## 📁 Project Structure

```
jtech-bridge-mcp/
├── app/
│   ├── __init__.py          # Package metadata
│   ├── config.py             # Pydantic Settings
│   ├── logging_config.py     # Structured logging
│   ├── server.py             # MCP Server entry point
│   ├── models/               # Pydantic schemas
│   ├── services/
│   │   └── db_service.py     # MongoDB async service
│   └── manager/
│       └── state_cache.py    # Local state with file locking
├── tests/                     # Test suite
├── docs/                      # Documentation
├── pyproject.toml            # Project configuration
└── .env.example              # Environment template
```

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://127.0.0.1:27017` | MongoDB connection URI |
| `MONGO_DATABASE` | `mcp_bridge` | Database name |
| `LOG_LEVEL` | `INFO` | Logging level |
| `STATE_FILE_PATH` | `./data/sync_state.json` | Local state file path |
| `WATCHDOG_DEBOUNCE_MS` | `500` | File change debounce time |
| `NOTIFY_ENABLED` | `true` | Enable OS notifications |

## 🧪 Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Lint code
uv run ruff check .

# Type check
uv run mypy app/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ by Jtech**
