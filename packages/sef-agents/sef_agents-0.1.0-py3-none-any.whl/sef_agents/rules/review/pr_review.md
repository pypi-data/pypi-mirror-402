# PR Review Protocol

## 1. Compliance (MANDATORY)
- Types: 100% on changes.
- Logs: `structlog` + keywords. No `print()`.
- Errors: Specific exceptions only.
- Tests: Real execution, ≥85% coverage on changes. No unit-under-test mocking.
- Dead Code: remove unused imports/files (`scan_dead_code`).
- Tools: All `@mcp.tool()` must have docstrings.
- Documentation: Google style docstrings (full sentences). Curator protocol for comments (no code-echoing).

## 2. Debt Management
- Log all debt to `docs/TECH_DEBT.md`.
- Block if: New debt introduced without approval.
- Pass if: Pre-existing debt remains (but must be logged).

## 3. Review Verdicts (REQUEST CHANGES if any error)
- Style/Trivial: Fix directly or delegate to Developer.
- Compliance/Logic: Delegate to Developer (fix ALL errors).
- Security/Critical: 🛑 HALT -> User.

## 4. Report Structure
| Section | Content |
|---------|---------|
| Summary | 1 paragraph assessment. |
| Positives | Key wins. |
| Blockers | Critical defects. |
| Issues | Major/Minor (ALL must be fixed). |
| Verdict | APPROVE (0 errors) | REQUEST CHANGES (≥1 error). |

## 5. Escalation
- L1 (Style/Nits) -> Developer.
- L2 (Logic/Compliance) -> Developer + Architect.
- L3 (Security/Critical) -> HALT.
