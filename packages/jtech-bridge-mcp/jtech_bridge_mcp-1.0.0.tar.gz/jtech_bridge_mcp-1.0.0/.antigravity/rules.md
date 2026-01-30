# Agent Execution Rules
- Antes de qualquer `git commit`, o agente deve obrigatoriamente executar `make check-all`.
- Se `make check-all` falhar, o agente está proibido de realizar o commit até que os erros sejam resolvidos.
