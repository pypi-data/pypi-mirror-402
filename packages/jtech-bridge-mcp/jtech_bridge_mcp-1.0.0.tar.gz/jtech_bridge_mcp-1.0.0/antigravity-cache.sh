#!/bin/bash

# 1. Encerra todos os processos do Antigravity
echo "Fechando o Antigravity IDE..."
pkill -f antigravity

# 2. Define os caminhos de cache específicos do Antigravity no Linux
# O Antigravity geralmente usa ~/.config/Antigravity ou ~/.antigravity
CONFIG_PATH="$HOME/.config/Antigravity"
DATA_PATH="$HOME/.antigravity"

echo "Limpando caches do Antigravity..."

# Limpeza da pasta de configuração (Caches de interface e Service Worker)
if [ -d "$CONFIG_PATH" ]; then
    rm -rf "$CONFIG_PATH/Cache"
    rm -rf "$CONFIG_PATH/CachedData"
    rm -rf "$CONFIG_PATH/Code Cache"
    rm -rf "$CONFIG_PATH/Service Worker"
    rm -rf "$CONFIG_PATH/GPUCache"
    echo "Caches de sistema removidos em $CONFIG_PATH."
fi

# Limpeza da pasta de dados de usuário (Caches de extensões/plugins)
if [ -d "$DATA_PATH" ]; then
    rm -rf "$DATA_PATH/extensions"
    rm -rf "$DATA_PATH/workspaceStorage"
    echo "Caches de plugins removidos em $DATA_PATH."
fi

echo "Limpeza concluída. Reinicie o Antigravity."
