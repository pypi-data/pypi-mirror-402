#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Jtech Bridge MCP Setup...${NC}"

# 1. Check/Install uv
if ! command -v uv &> /dev/null; then
    echo -e "${BLUE}📦 Instaling uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
else
    echo -e "${GREEN}✅ uv is already installed.${NC}"
fi

# 2. Setup Project
echo -e "${BLUE}🛠️  Setting up project environment...${NC}"
uv sync --all-extras
echo -e "${GREEN}✅ Environment created and dependencies installed.${NC}"

# 3. Check MongoDB
if ! command -v mongod &> /dev/null; then
    echo -e "${RED}⚠️  MongoDB not found! Please install MongoDB first.${NC}"
    echo "This script assumes a local MongoDB instance for development."
else
    echo -e "${GREEN}✅ MongoDB found.${NC}"
    # Ideally we'd check if it's running: systemctl is-active mongod
fi

# 4. Setup Systemd Service
# 4. Setup Systemd Service
SERVICE_NAME="jtech-bridge-mcp.service"
SERVICE_PATH="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_PATH"

echo -e "${BLUE}⚙️  Configuring Systemd service...${NC}"

# Replace placeholders in service file if needed, or just copy
# Since we used %h and %u, we might not need substitution for user paths
cp deployment/jtech-bridge-mcp.service "$SERVICE_PATH/$SERVICE_NAME"

# Reload systemd
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"

echo -e "${GREEN}✅ Service installed to $SERVICE_PATH/$SERVICE_NAME${NC}"
echo -e "${BLUE}ℹ️  To start the service run: systemctl --user start $SERVICE_NAME${NC}"
echo -e "${BLUE}ℹ️  Check status with: systemctl --user status $SERVICE_NAME${NC}"

echo -e "${GREEN}✨ Setup complete!${NC}"
