.PHONY: help setup test lint format build clean examples

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies
	uv sync

setup-dev: ## Install with dev dependencies
	uv sync --all-extras

test: ## Run all tests
	uv run pytest

test-verbose: ## Run tests with verbose output
	uv run pytest -v

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src/scp_sdk --cov-report=term-missing --cov-report=html

lint: ## Run linter (ruff)
	uv run ruff check .

lint-fix: ## Fix linting issues automatically
	uv run ruff check --fix .

format: ## Format code with ruff
	uv run ruff format .

format-check: ## Check code formatting without changes
	uv run ruff format --check .

typecheck: ## Run type checker (mypy)
	uv run mypy src/scp_sdk

check: lint format-check typecheck ## Run all code quality checks

build: ## Build package
	uv build

examples: ## Run all examples
	@echo "Running basic usage example..."
	uv run python examples/basic_usage.py
	@echo "\nRunning integration example..."
	uv run python examples/custom_integration.py

clean: ## Clean build artifacts and caches
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .ruff_cache/ .mypy_cache/
	rm -rf htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

clean-venv: ## Remove virtual environment
	rm -rf .venv/

clean-all: clean clean-venv ## Full cleanup including venv
