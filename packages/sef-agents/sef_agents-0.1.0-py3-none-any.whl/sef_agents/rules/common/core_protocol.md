# Elite Code Quality Protocol v5 (Structural)
**Zero fake tests · Real execution guaranteed · Python + React/TypeScript/Vite 2025**

## 1. Pre-Implementation Checklist
- [ ] **IF** task size > 30 LOC -> **THEN** Paraphrase task and reference `CODE_MAP.md`.
- [ ] **IF** task involves new files -> **THEN** Update `CODE_MAP.md`.
- [ ] **IF** legacy code is touched -> **THEN** Check for technical debt markers.

## 2. Mandatory Tooling (Exit 0)
- [ ] **Python**: `ruff check --fix && ruff format && pyright`
- [ ] **Frontend**: `eslint --fix && prettier --write && tsc --noEmit && vite build`

## 3. Language Rules
### [PYTHON_RULES]
- [ ] **Types**: 100% hints on all function signatures.
- [ ] **Imports**: Standardlib → 3rd-party → Local. Sort alphabetical.
- [ ] **Errors**: Derive from `AppError`. Specific exceptions only.
- [ ] **Logs**: Use `structlog`. **FORBIDDEN**: `print()`, `logging.info`.
- [ ] **Docs**: Google style docstrings for all public symbols. **NO AI fluff** (see `quality/documentation_standards.md`). `validate_compliance` flags violations.

### [TYPESCRIPT_RULES]
- [ ] **Types**: **FORBIDDEN**: `any`. Use explicit `interface` or `type`.
- [ ] **Validation**: `Zod` schema required for all external inputs.
- [ ] **State**: `TanStack Query` for all server-side state.
- [ ] **Structure**: Use Boundary+Suspense; Absolute imports `@/`.

## 4. Universal Standards
- [ ] **Complexity**: Cyclomatic ≤ 15/func. Cognitive ≤ 15/func.
- [ ] **Handoff**: **IF** state changes (replan/escalate) -> **THEN** `log_escalation`.

## 5. Real Execution Testing
- [ ] **Integrity**: **FORBIDDEN**: Mocking the unit under test (UUT) or any internal functions/methods.
- [ ] **Mocking Policy**: Only external third-party APIs may be mocked (with documented justification and TECH_DEBT entry).
- [ ] **Coverage**: ≥85% on changed files.
- [ ] **Proof**: Paste actual shell execution output in the "Compliance" section.

## 6. Absolute Forbidden
- [ ] Linter/type errors.
- [ ] `any` in TS. Bare `except:` in Python.
- [ ] Missing real tests.
- [ ] Prop drilling >2 levels.
- [ ] Direct API calls in UI components.
- [ ] `print()` in production code.
