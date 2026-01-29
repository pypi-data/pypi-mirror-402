# Defect Prevention Strategy

## Concept
Quality is not a phase; it is an attribute of the code at the moment of creation.

## Mechanisms
1.  **Strong Typing**: Python type hints and TypeScript interfaces are non-negotiable.
2.  **Linter/Formatter Strictness**: Ruff/ESLint must pass before commit.
3.  **Pre-Commit Hooks**: Local validation prevents bad pushes.
4.  **Acceptance Criteria as Contract**: Code is not written until AC is approved.

## Quality Gates
-   The MCP `validate_compliance` tool serves as the primary automated gate.
-   Agents must refuse to generate "quick fixes" that violate these standards.
