# PRD: Local MCP Bridge (Antigravity ↔ Cursor)

## 1. Visão Geral

Um servidor MCP (Model Context Protocol) local que monitora o progresso do desenvolvimento no Backend (Antigravity) e fornece ao Frontend (Cursor) o status atualizado, documentação e tarefas pendentes de implementação.

## 2. O Problema

O desenvolvedor perde tempo e contexto ao copiar manualmente arquivos `.md` ou `openapi.json` do backend para o frontend, e o Cursor (frontend) não tem consciência imediata de quando uma nova API foi finalizada no Antigravity (backend).

## 3. Arquitetura Proposta

O MCP Server funcionará como um **Estado de Sincronização**.

* **Backend (Antigravity):** Notifica o MCP quando uma tarefa termina.
* **MCP Server:** Armazena o estado e lê os arquivos de documentação diretamente.
* **Frontend (Cursor):** Consulta o MCP para saber "o que há de novo".

---

## 4. Requisitos Funcionais

### RF01: Registro de Conclusão (Trigger)

O servidor deve expor uma ferramenta ou endpoint onde o Antigravity possa registrar: *"Terminei o endpoint X"*.

* **Payload:** `{ "task": "create_user", "docs_path": "...", "status": "ready" }`

### RF02: Monitoramento de Arquivos (Watchdog)

O MCP deve vigiar automaticamente arquivos específicos (ex: `openapi.json`) e marcar o status do frontend como "Outdated" (Desatualizado) sempre que o arquivo mudar.

### RF03: Ferramentas para o Cursor (Tools)

O MCP deve expor as seguintes ferramentas para a IA do Cursor:

1. `get_backend_status()`: Retorna o que foi feito recentemente no backend e o que ainda não foi implementado no frontend.
2. `read_latest_contract()`: Lê o `openapi.json` ou `.md` diretamente da pasta do backend sem precisar copiar.
3. `mark_as_implemented()`: Atualiza o status para que o desenvolvedor saiba que aquela tarefa foi concluída em ambos os lados.

---

## 5. Especificações Técnicas (MVP)

* **Linguagem:** Python (usando a biblioteca `mcp`) ou Node.js.
* **Persistência:** Um arquivo JSON simples (`sync_state.json`) para manter o histórico entre reinicializações.
* **Interface:** Standard Input/Output (STDIO) para comunicação com o Cursor.

### Estrutura do `sync_state.json`:

```json
{
  "last_updated": "2026-01-20T15:00:00Z",
  "pending_tasks": [
    {
      "id": "feat-login-001",
      "description": "API de Autenticação JWT",
      "contract_type": "swagger",
      "path": "/home/angelo/projects/backend/docs/auth.md"
    }
  ]
}

```

---

## 6. Plano de Implementação (Passo a Passo para sua IA)

### Passo 1: O Servidor

Peça à sua IA: *"Crie um MCP Server em Python usando a biblioteca 'mcp'. Ele deve ter uma ferramenta chamada 'check_backend_sync' que lê um arquivo JSON e me diz quais APIs foram criadas no backend mas ainda não existem no frontend."*

### Passo 2: O Trigger do Backend

No Antigravity, você pode criar um script simples ou comando que:

1. Atualiza o `sync_state.json`.
2. Salva o `openapi.json`.

### Passo 3: O Listener do Frontend

No Cursor, configure o `.cursorrules` para que, ao iniciar qualquer chat, ele execute:

> "Sempre verifique `check_backend_sync` via MCP. Se houver algo pendente, me avise e peça permissão para ler o contrato e implementar."

---

## 7. Critérios de Aceite

* O Antigravity termina um código -> o `sync_state.json` é atualizado.
* O Cursor, ao ser questionado "O que tenho para hoje?", lista exatamente a nova API do backend.
* O Cursor consegue ler o conteúdo do arquivo de documentação do backend sem que o arquivo exista na pasta do frontend.

---

**Dica Pro:** Como você usa **Ubuntu**, você pode fazer o MCP Server disparar um `notify-send` toda vez que o estado mudar. Assim, mesmo com o Cursor minimizado, você recebe um pop-up: *"Antigravity finalizou a API. Cursor pronto para implementar!"*

Deseja que eu escreva o código inicial desse servidor MCP em Python para você começar?
