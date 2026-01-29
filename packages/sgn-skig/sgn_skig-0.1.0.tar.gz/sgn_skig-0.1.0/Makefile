.PHONY: help all install test lint format clean

all: format lint test

help:
	@echo "Available targets:"
	@echo "  all        Run format, lint, and test (in order)"
	@echo "  install    Install package in development mode"
	@echo "  test       Run tests with coverage"
	@echo "  lint       Run ruff linter"
	@echo "  format     Format code with ruff"
	@echo "  clean      Remove build artifacts"

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
