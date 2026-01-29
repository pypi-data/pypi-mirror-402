# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov --cov-report=html

# Run linter
lint:
    uv run ruff check src tests

# Fix linting issues
fix:
    uv run ruff check --fix src tests

# Format code
format:
    uv run ruff format src tests

# Type check
typecheck:
    uv run mypy src

# Run all checks (like FastMCP's build)
build:
    uv sync
    just lint
    just typecheck
    just test

# Run server locally
run:
    uv run python -m scalene_mcp.server

# Clean build artifacts
clean:
    rm -rf dist build *.egg-info .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache

# Install dependencies
install:
    uv sync

# Show help
help:
    @just --list
