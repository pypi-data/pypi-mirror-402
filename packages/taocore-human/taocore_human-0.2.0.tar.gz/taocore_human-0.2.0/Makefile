.PHONY: help install install-dev install-all setup test test-cov lint format typecheck clean build publish

# Use uv for package management
UV := uv
PYTHON := uv run python
PYTEST := uv run pytest
RUFF := uv run ruff
MYPY := uv run mypy

help:
	@echo "taocore-human - Development Commands (using uv)"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install package (basic)"
	@echo "  make install-dev   Install with dev dependencies"
	@echo "  make install-all   Install with all optional dependencies"
	@echo "  make setup         Full dev setup (sync + install dev)"
	@echo "  make sync          Sync dependencies from lockfile"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run tests"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make test-verbose  Run tests with verbose output"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          Run linter (ruff)"
	@echo "  make format        Format code (ruff)"
	@echo "  make typecheck     Run type checker (mypy)"
	@echo "  make check         Run all checks (lint + typecheck + test)"
	@echo ""
	@echo "Build & Publish:"
	@echo "  make build         Build package"
	@echo "  make publish       Publish to PyPI"
	@echo "  make publish-test  Publish to TestPyPI"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         Remove build artifacts"
	@echo "  make clean-all     Remove all generated files"

# Setup targets
sync:
	$(UV) sync

install:
	$(UV) pip install -e .

install-dev:
	$(UV) pip install -e ".[dev]"

install-image:
	$(UV) pip install -e ".[image]"

install-video:
	$(UV) pip install -e ".[video]"

install-ml:
	$(UV) pip install -e ".[ml]"

install-all:
	$(UV) pip install -e ".[dev,video,ml]"

setup:
	$(UV) sync --all-extras
	@echo "Development environment ready!"

# Testing targets
test:
	$(PYTEST) tests/ -v

test-cov:
	$(PYTEST) tests/ -v --cov=src/taocore_human --cov-report=term-missing --cov-report=html

test-verbose:
	$(PYTEST) tests/ -vv -s

test-fast:
	$(PYTEST) tests/ -v -x --ff

# Code quality targets
lint:
	$(RUFF) check src/ tests/

lint-fix:
	$(RUFF) check src/ tests/ --fix

format:
	$(RUFF) format src/ tests/

format-check:
	$(RUFF) format src/ tests/ --check

typecheck:
	$(MYPY) src/taocore_human

check: lint typecheck test
	@echo "All checks passed!"

# Build targets
build: clean
	$(UV) build

publish: build
	$(UV) publish

publish-test: build
	$(UV) publish --index testpypi

# Clean targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .tox/
	rm -rf .venv/
