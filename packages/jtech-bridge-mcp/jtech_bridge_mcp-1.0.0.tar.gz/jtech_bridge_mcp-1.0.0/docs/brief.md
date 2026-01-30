# Project Brief: Local MCP Bridge (Antigravity ↔ IDEs)

## 1. Executive Summary

* **Conceito**: Um servidor MCP (Model Context Protocol) local que atua como uma ponte de sincronização em tempo real entre papéis de desenvolvimento.
* **Objetivo**: Eliminar o "vazio de informação" entre o Produtor de Contexto (Backend) e o Consumidor de Contexto (Frontend), automatizando a notificação de APIs concluídas e o compartilhamento de contratos técnicos.
* **Valor**: Proporcionar uma experiência de desenvolvimento Fullstack fluida e agnóstica em relação à IDE utilizada.

## 2. Problem Statement

* **Pain Points**: Atualmente, o desenvolvedor precisa copiar manualmente arquivos `.md` ou `openapi.json` entre repositórios.
* **Impacto**: Perda de tempo em tarefas manuais, risco de implementar funcionalidades baseadas em contratos desatualizados e falta de consciência imediata da IDE de frontend sobre o progresso do backend.
* **Lacuna**: As IAs das IDEs (Cursor, Windsurf, VS Code) operam "no escuro" em relação às mudanças realizadas em outros repositórios locais.

## 3. Proposed Solution

* **Abordagem**: Implementar um **MCP Server Local** que funcione como o "Cérebro de Sincronização".
* **Diferencial**: O servidor é agnóstico à IDE e focado em **Papéis** (Backend como fonte primária e Frontend como consumidor).
* **Visão**: Qualquer IDE compatível com MCP poderá consultar o servidor para saber "o que há de novo" e ler documentos diretamente da fonte.

## 4. Target Users

* **Desenvolvedores Jtech-Method**: Que utilizam o ciclo SM → Dev → QA em múltiplos repositórios.
* **Power Users de IDEs com IA**: Que desejam sincronização automática de contexto entre Cursor, VS Code, Windsurf e outros.

## 5. Goals & Success Metrics

* **Goal 1**: Independência total de IDE (suporte universal via protocolo MCP).
* **Goal 2**: Redução a zero da necessidade de duplicar arquivos de documentação entre pastas.
* **Métrica de Sucesso**: O status de uma API finalizada no papel de "Backend" ser refletido instantaneamente em qualquer IDE aberta no papel de "Frontend".

## 6. MVP Scope

* **Registro de Trigger**: Endpoint ou ferramenta para o papel de "Produtor" registrar a conclusão de tarefas.
* **Watchdog de Arquivos**: Monitoramento automático de mudanças no `openapi.json` ou diretórios de contratos.
* **Ferramentas MCP Core**:
* `get_backend_status()`: Retorna o que foi produzido recentemente.
* `read_latest_contract()`: Lê arquivos diretamente da pasta da fonte primária.
* `mark_as_implemented()`: Atualiza o status global de sincronização.



## 7. Technical Considerations

* **Protocolo**: MCP (Model Context Protocol) via Standard Input/Output (STDIO).
* **Persistência**: Arquivo JSON simples (`sync_state.json`) para manter o estado entre sessões.
* **OS Integration**: Suporte a notificações nativas `notify-send` no Ubuntu/Linux.
* **Lógica de Papéis**: O sistema diferencia projetos por papel (Produtor vs. Consumidor) e não por nome de IDE.

## 8. Constraints & Assumptions

* **Acesso ao Filesystem**: O servidor MCP deve ter permissão de leitura nos caminhos absolutos de ambos os projetos.
* **Execução Local**: Servidor e IDEs devem rodar no mesmo ambiente local para garantir baixa latência e acesso a arquivos.

## 9. Risks & Open Questions

* **Concorrência**: Gerenciamento de múltiplas IDEs tentando atualizar o `mark_as_implemented()` simultaneamente.
* **Segurança**: Garantir que a ferramenta `read_latest_contract()` respeite limites de diretórios (prevenção de Path Traversal).

---

**Documento elaborado pelo Analista Jtech (Bob Esponja)**.
