.PHONY: help install install-dev setup setup-env venv clean lint format test check-all run run-dev build publish docker-mongo

# Colors
BLUE := \033[1;34m
GREEN := \033[1;32m
YELLOW := \033[1;33m
Red := \033[1;31m
NC := \033[0m

# =============================================================================
# HELP
# =============================================================================

help: ## Show this help message
	@echo "\n$(BLUE)📋 MCP IDE Bridge - Management Console$(NC)\n"
	@grep -E '^[a-zA-Z_-]+:.*?##' Makefile | awk 'BEGIN {FS = ":.*?##"} {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# SETUP & INSTALLATION
# =============================================================================

venv: ## Create virtual environment using uv
	@echo "$(BLUE)🔨 Creating virtual environment...$(NC)"
	@uv venv
	@echo "$(GREEN)✅ Virtual environment created!$(NC)"

setup-env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✅ .env file created from .env.example$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  .env file already exists, skipping...$(NC)"; \
	fi

install: ## Install production dependencies
	@echo "$(BLUE)📦 Installing production dependencies...$(NC)"
	@uv sync
	@echo "$(GREEN)✅ Production dependencies installed!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)📦 Installing development dependencies...$(NC)"
	@uv sync --all-extras
	@echo "$(GREEN)✅ Development dependencies installed!$(NC)"

setup: venv setup-env install-dev ## Full project setup (venv, env, dependencies)
	@echo "$(GREEN)✨ Project setup complete! Ready to code.$(NC)"

# =============================================================================
# DEVELOPMENT STARTUP
# =============================================================================

run: ## Run the MCP server in production mode
	@echo "$(BLUE)🚀 Starting Jtech Bridge MCP...$(NC)"
	@uv run jtech-bridge

run-dev: ## Run server in development mode (Debug + Reload)
	@echo "$(BLUE)🐞 Starting Jtech Bridge MCP (DEV MODE)...$(NC)"
	@LOG_LEVEL=DEBUG uv run jtech-bridge

docker-mongo: ## Start MongoDB Docker container for local development
	@echo "$(BLUE)🐳 Starting MongoDB container...$(NC)"
	@docker run -d --name mcp-mongo -p 27017:27017 --restart unless-stopped mongo:latest 2>/dev/null || docker start mcp-mongo
	@echo "$(GREEN)✅ MongoDB is running on localhost:27017$(NC)"

# =============================================================================
# CODE QUALITY & TESTING
# =============================================================================

lint: ## Run Ruff linter
	@uv run ruff check app tests --fix
	@echo "$(GREEN)✅ Linting complete!$(NC)"

format: ## Run Ruff formatter
	@uv run ruff format app tests
	@echo "$(GREEN)✅ Formatting complete!$(NC)"

typecheck: ## Run mypy type checker
	@uv run mypy app --ignore-missing-imports
	@echo "$(GREEN)✅ Type checking complete!$(NC)"

test: ## Run tests
	@uv run pytest tests -v --tb=short
	@echo "$(GREEN)✅ Tests complete!$(NC)"

check-all: format lint typecheck test ## Run all quality checks
	@echo "$(GREEN)🎉 All checks passed!$(NC)"

# =============================================================================
# BUILD & PUBLISH
# =============================================================================

clean: ## Clean build artifacts and cache
	@rm -rf dist build .pytest_cache .mypy_cache .ruff_cache __pycache__ .coverage htmlcov
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

build: clean ## Build distribution packages (sdist + wheel)
	@echo "$(BLUE)📦 Building distribution packages...$(NC)"
	@uv run python -m build
	@echo "$(GREEN)✅ Build complete! Check dist/ folder.$(NC)"

publish: build ## Publish to PyPI (requires twine)
	@echo "$(BLUE)🚀 Publishing to PyPI...$(NC)"
	@uv run twine upload dist/*
	@echo "$(GREEN)✨ Published successfully!$(NC)"
