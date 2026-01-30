# PRD: Local MCP Bridge (Antigravity ↔ IDEs)

## 1. Goals (Objetivos)

* **Sincronização em Tempo Real**: Notificar automaticamente a IDE de Frontend (Consumidora) sobre conclusões no Backend (Produtor).
* **Eliminação de Cópia Manual**: Reduzir a zero a necessidade de duplicar arquivos de contrato entre repositórios.
* **Independência de IDE**: Suporte universal via protocolo MCP (Cursor, VS Code, Windsurf, etc.).
* **Segurança e Integridade**: Garantir acesso restrito via allow-listing e persistência atômica de estado.

## 2. Requirements (Requisitos)

### 2.1 Funcionais (FR)

* **FR1**: Registro de tarefas concluídas pelo papel de "Produtor".
* **FR2**: Monitoramento automático (Watchdog) de arquivos como `openapi.json`.
* **FR3**: Ferramenta `get_backend_status` para consulta de progresso.
* **FR4**: Ferramenta `read_latest_contract` com suporte a leitura granular (seções Markdown).
* **FR5**: Ferramenta `mark_as_implemented` para sincronização bi-direcional.

### 2.2 Não-Funcionais (NFR)

* **NFR1**: Segurança de caminhos (Allow-listing) para evitar acesso a arquivos sensíveis do SO.
* **NFR2**: Atomicidade de escrita no `sync_state.json` (File Locking).
* **NFR3**: Notificações nativas via `notify-send` (Ubuntu/Linux).

## 3. User Interface & Technical Assumptions

* **Interface**: Comunicação via **STDIO** para IAs e **Toasts nativos** para o desenvolvedor humano.
* **Plataforma**: Foco inicial em ambientes **Linux/Ubuntu**.
* **Arquitetura**: Processo de background leve, rodando como servidor MCP isolado.

## 4. Epic & Story List

### Epic 1: Foundation

* **Story 1.1**: Scaffolding do projeto e implementação básica do protocolo MCP.
* **Story 1.2**: Gerenciamento de estado atômico em JSON com locking.

### Epic 2: Role & Monitoring

* **Story 2.1**: Mapeamento de repositórios por Papel (Producer/Consumer).
* **Story 2.2**: Implementação do Watchdog de sistema de arquivos.

### Epic 3: Intelligence Tools

* **Story 3.1**: Implementação da ferramenta de status global.
* **Story 3.2**: Leitor granular de contratos com parser de Markdown.

### Epic 4: Integration & Guardrails

* **Story 4.1**: Segurança de Path Validation (Allow-listing).
* **Story 4.2**: Integração com notificações do sistema operacional.

---

## 5. Checklist de Validação (PM)

* [x] O escopo resolve o problema de "vazio de informação"? **Sim.**
* [x] Os requisitos são testáveis por um agente de QA? **Sim.**
* [x] A solução é agnóstica em relação à IDE? **Sim, via protocolo MCP.**
* [x] Riscos de segurança (Path Traversal) foram mitigados? **Sim, via NFR1 e Story 4.1.**
* [x] A concorrência multi-IDE foi tratada? **Sim, via NFR2 e Story 1.2.**
