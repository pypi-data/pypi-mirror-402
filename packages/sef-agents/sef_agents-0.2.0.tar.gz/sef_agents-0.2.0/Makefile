.PHONY: lint format test build clean ci install secrets

# Install dependencies
install:
	uv sync

# Lint and format
lint:
	uv run ruff check --fix .
	uv run ruff format .

# Format only (no lint fixes)
format:
	uv run ruff format .

# Run tests
test:
	uv run pytest -q

# Run tests with coverage
test-cov:
	uv run pytest --cov=src/sef_agents --cov-report=term-missing

# Secret scanning
secrets:  # pragma: allowlist secret
	uv run detect-secrets scan --baseline .secrets.baseline

# Security audit
audit:
	uv run python -m sef_agents.security_scan

# Build package
build:
	uv build

# Full CI pipeline (run before commit)
ci: lint test
	@echo "✅ CI checks passed"

# Full CI with security audit (stricter)
ci-full: lint test audit
	@echo "✅ Full CI checks passed"

# Clean build artifacts
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	rm -rf dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Pre-commit setup
setup-hooks:
	uv run pre-commit install --hook-type pre-commit
	@echo "✅ Pre-commit hooks installed"
