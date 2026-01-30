.PHONY: help install dev test coverage lint format typecheck clean

help:  ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install the package
	uv sync

dev:  ## Install development dependencies
	uv sync --group dev
	pre-commit install

test:  ## Run tests
	tox

coverage:  ## Run tests with coverage report
	tox -e coverage

lint:  ## Run linting
	ruff check src tests

format:  ## Format code
	ruff check --fix src tests
	ruff format src tests

typecheck:  ## Run type checking
	tox -e mypy

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
