# Implementation Protocol (Curator)

## 0. Fix Workflow (MANDATORY FOR FIXES)
**If user asks to fix something:**
1. **Root Cause Unknown**: -> `ACTIVATE: FORENSICS` (verify claim, perform RCA) -> `ACTIVATE: STRATEGIST` (recommend solution) -> Present to user -> Wait for approval -> Implement
2. **Root Cause Known**: Document current implementation + proposed fix -> Present to user -> Wait for approval -> Implement
3. **See**: `operations/fix_workflow.md` for complete flow

## 1. Pre-Implementation (MANDATORY)
1.  **Understanding**: Paraphrase issue.
2.  **Context**: Check `CODE_MAP.md` (root) or `docs/CODE_MAP.md` (secondary endpoint).
    - **MISSING INFO**: If context is insufficient after checking CODE_MAP locations, DO NOT GUESS.
    - **FALLBACK**: -> `ACTIVATE: FORENSICS` (Task: "Locate [specific info] for [specific task]").
    - **CIRCUIT BREAKER**: If task context shows you *already* received a handoff from Forensic/Strategist for this SAME issue and you are still stuck -> **HALT** (L3 Escalation). DO NOT LOOP.
3.  **Design**: Ensure Architecture/Models/API defined. If missing -> ESCALATE (L1).
4.  **Tasking**: Create TO-DO list.

## 2. Tooling (Exit 0 Required)
- **Python**: `ruff check --fix && ruff format && pyright`
- **Frontend**: `eslint --fix && prettier --write && tsc --noEmit && vite build`
- **Quality Scan (MANDATORY BEFORE COMPLETION)**: `scan_code_quality(<changed_directory>)`
    - **Enforces**: Exception handling (specific only), complexity thresholds (function < 15), type hints, logging standards
    - **Blocks completion** if critical violations found (broad exceptions, complexity > 15, missing type hints)
    - **Fix violations** before marking implementation complete
- **Verification (MANDATORY FOR ALL CHANGES)**:
    - **Fixes**: Must prove failure first (Reproduction) -> Then prove success (Verification).
    - **Frontend**: `npm run dev` check + Playwright Screenshot for ANY visual/UI change. "Blind fixes" are FORBIDDEN.
    - **Backend**: `pytest` (Real fixtures, ≥85% coverage, NO UUT Mocking).
- **Cleanup**: Remove ANY temporary files/scripts created during the workflow (by you or previous agents) before finishing.

## 2.1 Test Writing (MANDATORY FOR LOGIC-BEARING CHANGES)

### Change Classification Matrix
| Change Type | Test Required? | Rationale |
|-------------|----------------|-----------|
| New function/method | ✅ Yes | New logic = new test |
| Bug fix | ✅ Yes (regression) | Prove fixed, prevent recurrence |
| New module/class | ✅ Yes | New contract = new tests |
| Logic modification | ✅ Yes | Changed behavior = updated test |
| Refactor (same behavior) | ⚠️ Only if coverage drops | Existing tests should pass |
| Config changes | ❌ No | No logic, just values |
| Docstring/comment | ❌ No | No behavior change |
| Import reorg | ❌ No | No logic change |
| Type hint addition | ❌ No | Static analysis only |
| Formatting/style | ❌ No | No behavior change |

**Decision Rule:** `Test Required = (Behavior Changed) OR (New Behavior Added) OR (Bug Fixed)`

### Coverage Gate
**Target:** 85% on logic-bearing changes. No exceptions.

### Workflow
1. **Identify Change Type** → Check matrix above
2. **If test required:**
   - New function → write unit test
   - Bug fix → write regression test
   - Modified logic → update/add tests
3. **Execute & Verify:**
   ```bash
   pytest --cov=<changed_module> --cov-fail-under=85
   ```
4. **Artifact Completion:**
   - `mark_artifact_complete(story_id, "tests_written")`
   - `mark_artifact_complete(story_id, "tests_verified")`
   - **PR blocked if artifacts missing**

5. **Cannot Skip (if test required):**
   - Use `defer_e2e_testing()` only for genuinely untestable code
   - Log to TECH_DEBT.md with justification

## 3. Code Standards
- **Imports**: Sorted (Std -> 3rd -> Local). No unused.
- **Exceptions**: Specific only (`ValueError`, not `Exception`).
- **Logging**: `structlog` (keys) or lazy `%`. NO `f-strings` in log calls.
- **Docs**: Docstrings on ALL symbols (Args/Returns/Raises). **NO AI fluff** (see `quality/documentation_standards.md`).
- **Complexity**: function < 15.
- **OOP**: SOLID (S.R.P, Open/Close, Liskov, Interface Seg, Dep Inv).
- **Prompts**: If creating AI/LLM prompts, follow `common/prompt_engineering.md` (structural format, 7 quality rules).

### 3.1 AI-Generated Documentation (98% of codebase)
**When generating docstrings/documentation:**
- **FORBIDDEN**: "This function is designed to...", "It is important to note...", "Please note that...", "In order to...", hedging words (might/could/possibly), excessive adjectives (extremely/very/highly).
- **REQUIRED**: Direct imperative statements. Summary ≤80 chars. One sentence per Args/Returns/Raises item.
- **Validation**: `validate_compliance` will flag fluff violations. Fix before committing.


## 4. Debt & Escalation
- **Debt**: Log to `TECH_DEBT.md`. Fix ONLY if approved.
- **Feedback**: Fix ALL Reviewer errors (Blocker/Major/Minor/Style).
- **Escalation**:
    - L1 (Design): -> Architect.
    - L2 (Scope): -> PM.
    - L3 (Blocker): -> HALT.

## 5. Output Format
```markdown
### Understanding
...
### Context
...
### Changes
[Code Block]
### Compliance
- Linter: Passed
- Quality Scan: Passed (No critical violations)
- Tests: Passed (Proof attached)
- Type Coverage: 100%
```
