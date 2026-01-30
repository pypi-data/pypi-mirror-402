# Plano de Implementação: Jtech Bridge MCP

## 📋 Resumo Executivo

Este documento detalha o plano de implementação completo para o **Jtech Bridge MCP**, um servidor MCP local que atua como ponte de sincronização em tempo real entre IDEs (Cursor, Windsurf, VS Code) e o desenvolvimento Backend/Frontend, utilizando o protocolo MCP.

**Escopo:** Servidor MCP em Python com persistência MongoDB, Outbox Pattern, e Watchdog para monitoramento de arquivos.

---

## 🎯 Objetivos do MVP

| # | Objetivo | Critério de Sucesso |
|---|---|---|
| 1 | Sincronização em tempo real | Notificação automática em < 2s após mudança de contrato |
| 2 | Eliminação de cópia manual | Zero arquivos duplicados entre repos |
| 3 | Independência de IDE | Suporte a qualquer IDE compatível com MCP via STDIO |
| 4 | Segurança e Integridade | Allow-listing de paths + transações atômicas |

---

## 🏗️ Épicos e User Stories

### Epic 1: Foundation (Base do Projeto)

| Story | Título | Descrição | Prioridade |
|-------|--------|-----------|------------|
| 1.1 | Scaffolding do Projeto | Setup inicial com `uv`, estrutura de diretórios e dependências | 🔴 Alta |
| 1.2 | Servidor MCP Base | Implementação do protocolo MCP via STDIO usando SDK Anthropic | 🔴 Alta |
| 1.3 | Conexão MongoDB | Integração com `motor` (async driver) e configuração de coleções | 🔴 Alta |
| 1.4 | Gerenciamento de Estado | sync_state.json com file locking via `fasteners` | 🔴 Alta |

### Epic 2: Role & Monitoring (Papéis e Monitoramento)

| Story | Título | Descrição | Prioridade |
|-------|--------|-----------|------------|
| 2.1 | Registro de Projetos | CRUD de projetos na coleção `projects` com papel (Producer/Consumer) | 🔴 Alta |
| 2.2 | Watchdog de Arquivos | Monitoramento de `openapi.json` e diretórios de contratos | 🔴 Alta |
| 2.3 | Outbox Pattern | Fila de eventos atômica para propagação de mudanças | 🟡 Média |

### Epic 3: Intelligence Tools (Ferramentas MCP)

| Story | Título | Descrição | Prioridade |
|-------|--------|-----------|------------|
| 3.1 | `get_backend_status` | Retorna tarefas recentes do produtor e pendências | 🔴 Alta |
| 3.2 | `read_latest_contract` | Leitura granular de contratos (JSON/Markdown) | 🔴 Alta |
| 3.3 | `mark_as_implemented` | Atualização de status de sincronização bi-direcional | 🔴 Alta |
| 3.4 | `register_task_completion` | Registro de conclusão de tarefas pelo produtor | 🟡 Média |

### Epic 4: Integration & Guardrails (Integração e Segurança)

| Story | Título | Descrição | Prioridade |
|-------|--------|-----------|------------|
| 4.1 | Path Validation | Allow-listing e prevenção de Path Traversal | 🔴 Alta |
| 4.2 | Notificações OS | Integração com `notify-send` (Ubuntu/Linux) | 🟡 Média |
| 4.3 | Systemd Service | Configuração para execução em background | 🟡 Média |
| 4.4 | Setup Automatizado | Script `setup.sh` idempotente | 🟡 Média |

---

## 📦 Dependências Técnicas

```toml
# pyproject.toml (uv)
[project]
name = "jtech-bridge-mcp"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.0.0",
    "motor>=3.3.0",
    "watchdog>=4.0.0",
    "fasteners>=0.19",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",
]
```

---

## 🗃️ Modelos de Dados (MongoDB)

### Coleção: `projects`
```json
{
  "_id": ObjectId,
  "name": "omniagent-backend",
  "path": "/home/user/projects/omniagent",
  "role": "producer",  // producer | consumer
  "watch_patterns": ["**/openapi.json", "**/docs/*.md"],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### Coleção: `sync_state`
```json
{
  "_id": ObjectId,
  "task_id": "feat-login-001",
  "description": "API de Autenticação JWT",
  "producer_project_id": ObjectId,
  "contract_path": "/home/user/projects/backend/docs/auth.md",
  "contract_hash": "sha256:abc123...",
  "status": "pending",  // pending | implemented | outdated
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### Coleção: `outbox`
```json
{
  "_id": ObjectId,
  "event_type": "contract_updated",
  "payload": { ... },
  "status": "pending",  // pending | processed | failed
  "retry_count": 0,
  "created_at": ISODate,
  "processed_at": ISODate
}
```

---

## 🔐 Requisitos de Segurança

| Requisito | Implementação | Status |
|-----------|---------------|--------|
| Path Allow-listing | Lista de diretórios autorizados no MongoDB | ⬜ TODO |
| Path Traversal Prevention | `pathlib.Path.resolve()` + validação de prefixo | ⬜ TODO |
| Isolamento MongoDB | Bind exclusivo em `127.0.0.1` | ⬜ TODO |
| File Locking | `fasteners.InterProcessLock` | ⬜ TODO |

---

## 📊 Diagrama de Fluxo

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Backend IDE   │     │   MCP Server    │     │  Frontend IDE   │
│   (Producer)    │     │ (Local Bridge)  │     │   (Consumer)    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  1. register_task()   │                       │
         │──────────────────────>│                       │
         │                       │                       │
         │       [Watchdog]      │                       │
         │  2. File Change Event │                       │
         │<- - - - - - - - - - - │                       │
         │                       │                       │
         │                       │  3. notify-send       │
         │                       │─────────────────────> │
         │                       │                       │
         │                       │  4. get_backend_status│
         │                       │<──────────────────────│
         │                       │                       │
         │                       │  5. read_contract     │
         │                       │<──────────────────────│
         │                       │                       │
         │                       │  6. mark_implemented  │
         │                       │<──────────────────────│
         │                       │                       │
```

---

## ⏱️ Estimativa de Esforço

| Épico | Stories | Estimativa | Complexidade |
|-------|---------|------------|--------------|
| Epic 1: Foundation | 4 | 3-4 dias | Alta |
| Epic 2: Role & Monitoring | 3 | 2-3 dias | Média |
| Epic 3: Intelligence Tools | 4 | 3-4 dias | Alta |
| Epic 4: Integration | 4 | 2-3 dias | Média |
| **Total** | **15** | **10-14 dias** | - |

---

## ✅ Critérios de Aceite Globais

- [ ] O servidor MCP inicia via STDIO e responde a ferramentas
- [ ] Projetos são registrados com papel (Producer/Consumer)
- [ ] Mudanças em `openapi.json` disparam eventos no Outbox
- [ ] Ferramentas `get_backend_status`, `read_latest_contract`, `mark_as_implemented` funcionais
- [ ] Notificações `notify-send` são disparadas em tempo real
- [ ] Path Traversal é prevenido em todas as operações de leitura
- [ ] O serviço roda em background via Systemd e reinicia automaticamente

---

**Documento gerado em:** 2026-01-20
**Versão:** 1.0
