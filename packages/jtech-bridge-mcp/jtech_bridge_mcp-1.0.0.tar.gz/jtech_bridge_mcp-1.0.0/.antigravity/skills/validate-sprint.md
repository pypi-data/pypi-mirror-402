---
name: sprint-validator
description: Valida o código usando Makefile antes de finalizar sprints ou épicos.
---

# Sprint Validator Skill

## Context
Este projeto usa um Makefile para garantir a qualidade do código (mypy, ruff e hooks de pre-commit).

## Instructions
Sempre que eu pedir para "finalizar o sprint", "concluir o épico" ou "fazer o commit final":
1. Você **DEVE** executar o comando `make check-all` no terminal.
2. Analise a saída do comando:
   - **Se o comando falhar (exit code != 0):** Não prossiga com o commit ou conclusão. Leia os erros do mypy/ruff e me pergunte se deseja que você os corrija automaticamente.
   - **Se o comando passar:** Prossiga com as etapas finais (ex: gerar mensagem de commit ou atualizar status do épico).

## Requirements
- Certifique-se de que o ambiente virtual está ativo antes de rodar o `make`.
