#!/usr/bin/env bash
set -euo pipefail

echo "=== Installing dependencies ==="
uv sync --dev

echo "=== Running ruff linter ==="
uv run ruff check .

echo "=== Running ruff formatter check ==="
uv run ruff format --check .

echo "=== Running tests ==="
uv run pytest

echo "=== Building package ==="
uv run python -m build

echo "=== Checking package with twine ==="
uv run twine check dist/*

echo "=== CI passed ==="
