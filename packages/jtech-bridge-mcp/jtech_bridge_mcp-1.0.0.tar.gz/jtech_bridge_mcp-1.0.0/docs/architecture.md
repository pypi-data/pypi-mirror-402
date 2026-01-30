# Architecture Document: Jtech Bridge MCP (Antigravity ↔ IDEs)

## 1. Introdução

Este documento detalha a infraestrutura técnica do **Jtech Bridge MCP**, projetado para sincronização de contexto local entre IDEs (Cursor, Windsurf, VS Code, etc.) e o desenvolvimento Backend (Produtor de Contexto), utilizando o protocolo MCP. O objetivo é garantir uma ponte de dados resiliente, segura e performática.

### 1.1 Starter Template

* **Decisão:** **N/A - Greenfield project**.
* **Racional:** O servidor será construído como uma ferramenta de sistema leve, utilizando o SDK oficial da Anthropic para evitar overhead desnecessário de frameworks pesados.

### 1.2 Change Log

| Data | Versão | Descrição | Autor |
| --- | --- | --- | --- |
| 2026-01-20 | 1.0 | Definição de Stack (Python/uv/Mongo) e Outbox Pattern | The Matrix |

## 2. High Level Architecture

* **Estilo Arquitetural:** Servidor de Protocolo via STDIO para integração local direta com IDEs.
* **Padrão de Persistência:** **Outbox Pattern** utilizando MongoDB Change Streams para garantir que notificações não sejam perdidas.
* **Mecanismo de Monitoramento:** **Observer (Watchdog)** para detecção em tempo real de mudanças em contratos (ex: `openapi.json`).

## 3. Tech Stack Definitiva

| Categoria | Tecnologia | Versão | Propósito | Racional |
| --- | --- | --- | --- | --- |
| **Linguagem** | Python | 3.12+ | Runtime principal | Performance superior e Type Hints modernos |
| **Package Manager** | **uv** | Latest | Gestão de ambiente | Velocidade extrema e reprodutibilidade sem `pip` |
| **Banco de Dados** | MongoDB | 6.0+ | Estado e Outbox | Suporte a Transações e Change Streams nativos |
| **Async Driver** | `motor` | Latest | Driver MongoDB | Integração não-bloqueante com o loop do `asyncio` |
| **Monitoramento** | `watchdog` | 4.0+ | Eventos de FS | Baixa latência na detecção de mudanças de arquivos |
| **Atomicidade** | `fasteners` | Latest | File Locking | Proteção do cache `sync_state.json` contra concorrência |

## 4. Data Models (MongoDB)

* **Coleção `projects**`: Mapeia os caminhos absolutos e os papéis (Producer/Consumer) de cada repositório.
* **Coleção `sync_state**`: Mantém o status atual das tarefas e o hash de versão dos contratos.
* **Coleção `outbox**`: Fila atômica de eventos para propagação de mudanças para as IDEs e notificações OS.

## 5. Source Tree (Layout uv)

```plaintext
jtech-bridge-mcp/
├── app/
│   ├── server.py           # Entrada Principal (MCP Core)
│   ├── models/             # Schemas Pydantic
│   ├── services/
│   │   ├── db_service.py   # Lógica de Outbox e Motor
│   │   ├── watchdog.py     # Monitoramento de Filesystem
│   │   └── notifier.py     # Integração notify-send
│   └── manager/
│       └── state_cache.py  # Gestão do sync_state.json
├── tests/                  # Testes de integração e atomicidade
├── pyproject.toml          # Definições uv
└── setup.sh                # Instalador automatizado

```

## 6. Segurança e Guardrails

* **Path Allow-listing**: O servidor apenas lerá/escreverá em diretórios explicitamente registrados no MongoDB.
* **Prevenção de Traversal**: Uso rigoroso de `pathlib.Path.resolve()` para validar limites de acesso.
* **Isolamento**: MongoDB configurado estritamente para `127.0.0.1`.

## 7. Infraestrutura e SO (Ubuntu)

* **Instalador (`setup.sh`)**: Script idempotente para configurar `uv`, dependências, coleções do MongoDB e permissões.
* **Persistência de Serviço**: Configuração via **Systemd** (`jtech-bridge-mcp.service`) para execução em background e reinício automático.
* **Notificações**: Chamadas diretas ao binário do sistema `/usr/bin/notify-send`.

---

**Documento elaborado pelo Arquiteto Jtech (The Matrix)**.

---
