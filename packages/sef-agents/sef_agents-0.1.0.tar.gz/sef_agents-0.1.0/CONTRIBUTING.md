# Contributing to SEF Agents

Thank you for contributing to SEF Agents. This document outlines development setup, coding standards, and PR guidelines.

---

## Development Setup

### Prerequisites

- Python 3.13+
- `uv` package manager ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))

### Initial Setup

```bash
git clone https://github.com/Mishtert/sef-agents.git
cd sef-agents
uv sync
```

### Running Locally

```bash
# Run MCP server
uv run sef-agents

# Run tests
uv run pytest

# Run linter
uvx ruff check .
uvx ruff format .
```

---

## Code Standards

### Curator Protocol

SEF Agents follows the **Curator Protocol** for documentation:

- **Code comments**: Explain *why*, not *what*. No code-echoing.
- **Docstrings**: Google style for Python. Mandatory for non-trivial functions.
- **Module headers**: Purpose (1 sentence) + Usage example (≤3 lines).

See `src/sef_agents/rules/quality/documentation_standards.md` for full standards.

### Python Standards

- **Style**: PEP 8, enforced via `ruff`
- **Type hints**: Required for all function signatures
- **Exceptions**: Specific exceptions only (`ValueError`, not `Exception`)
- **Logging**: Use `structlog` (keys), never `f-strings` in log calls
- **Imports**: Sorted (Std → 3rd → Local), no unused imports

### Testing

- **Coverage**: ≥85% for new code
- **Fixtures**: Real fixtures, no UUT mocking
- **Execution**: Real test execution (no mocked test runners)

---

## Pull Request Process

### Before Submitting

1. **Sync**: `git pull origin main`
2. **Test**: `uv run pytest`
3. **Lint**: `uvx ruff check . && uvx ruff format .`
4. **Verify**: All tests pass, no linter errors

### PR Template

```markdown
## Description
[What this PR does]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments/documentation updated
- [ ] No new warnings generated
```

### Review Criteria

PRs must pass:

- ✅ All tests pass
- ✅ Linter passes (`ruff check`)
- ✅ Code follows Curator Protocol
- ✅ Type hints present
- ✅ No security issues (run `uv run python -m sef_agents.security_scan`)

---

## Architecture Decision Records (ADR)

For significant architectural changes, create an ADR:

1. Copy `docs/templates/ADR.md`
2. Fill in context, decision, consequences
3. Submit with PR

---

## Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Follow the Curator Protocol (laconic, context-focused)

---

## Questions?

Open an issue or contact maintainers via GitHub Discussions.
