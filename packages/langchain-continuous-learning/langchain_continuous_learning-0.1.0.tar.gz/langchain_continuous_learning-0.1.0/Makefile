.PHONY: all format lint lint_package lint_tests test tests test_watch integration_tests clean help

# Default target
all: format lint test

# Format code with ruff
format:
	uv run --group lint ruff format .
	uv run --group lint ruff check --fix .

# Lint code with ruff
lint:
	uv run --group lint ruff check .
	uv run --group lint ruff format --check .

# Lint package code (excluding tests)
lint_package:
	uv run --group lint ruff check ace examples
	uv run --group lint ruff format --check ace examples

# Lint tests only
lint_tests:
	uv run --group lint ruff check tests
	uv run --group lint ruff format --check tests

# Run unit tests
test tests:
	uv run --group test pytest tests/unit_tests -v

# Run tests in watch mode
test_watch:
	uv run --group test pytest-watch tests/unit_tests

# Run integration tests
integration_tests:
	uv run --group test --group test_integration pytest tests/integration_tests -v

# Type checking
typecheck:
	uv run --group typing mypy ace

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Build package
build:
	uv build

# Help
help:
	@echo "Available targets:"
	@echo "  format           - Format code with ruff"
	@echo "  lint             - Lint code with ruff"
	@echo "  lint_package     - Lint package code (excluding tests)"
	@echo "  lint_tests       - Lint tests only"
	@echo "  test / tests     - Run unit tests"
	@echo "  test_watch       - Run tests in watch mode"
	@echo "  integration_tests - Run integration tests"
	@echo "  typecheck        - Run mypy type checking"
	@echo "  clean            - Remove build artifacts"
	@echo "  build            - Build package"
