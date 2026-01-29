# CI Formatting Failure RCA

**Date**: 2026-01-19
**Issue**: CI-FAIL-001
**Agent**: Forensic Engineer

## Problem Statement

**Symptom**: GitHub Actions "Elite Quality Pipeline" fails on `ruff format --check .` with:
```
Would reformat: tests/test_prompts.py
1 file would be reformatted, 88 files already formatted
Error: Process completed with exit code 1.
```

**Frequency**: "Every other push fails" - consistent pattern across multiple commits.

**Impact**:
- Wasted CI/CD time
- Failed builds block deployment
- Developer frustration

## Root Cause Analysis

### Investigation Findings

1. **Pre-commit Configuration** (`.pre-commit-config.yaml`):
   ```yaml
   - id: ruff-format
   ```
   - **Behavior**: Auto-fixes formatting issues
   - **Scope**: Only runs on **staged files**
   - **Failure Mode**: Does NOT fail if files need formatting (only auto-fixes)

2. **CI Configuration** (`.github/workflows/ci.yml`):
   ```yaml
   - name: Format Check (Ruff)
     run: uv run ruff format --check .
   ```
   - **Behavior**: Checks ALL files in repository
   - **Scope**: Entire codebase (not just changed files)
   - **Failure Mode**: Fails if ANY file needs formatting

3. **Commit Analysis** (`cae1f3e`):
   ```
   Modified files:
   - src/sef_agents/auth.py
   - tests/test_auth_routing.py
   - sef-reports/*.md (4 files)

   NOT modified:
   - tests/test_prompts.py ❌
   ```

4. **File Status**:
   - `tests/test_prompts.py` has formatting issues (confirmed)
   - File was NOT modified in recent commits
   - File was NOT staged → pre-commit didn't check it
   - CI checks ALL files → catches the issue

### Root Cause

**Gap Between Pre-commit and CI**:

| Aspect | Pre-commit | CI |
|--------|-----------|-----|
| **Scope** | Staged files only | All files |
| **Mode** | Auto-fix (no failure) | Check-only (fails) |
| **Behavior** | Fixes issues silently | Fails if issues exist |

**The Problem**:
1. Pre-commit `ruff-format` only checks **staged files**
2. Files not modified/staged skip pre-commit checks
3. CI checks **all files** in repository
4. Unstaged files with formatting issues slip through pre-commit
5. CI catches them → build fails

### Why This Happens Frequently

**Pattern Observed**:
- Developer modifies files A, B, C
- Files D, E have pre-existing formatting issues
- Pre-commit checks A, B, C → passes
- Commit succeeds
- CI checks A, B, C, D, E → fails on D or E
- **Every push fails** because different untouched files have issues

### Point of Failure

**Location**: `.pre-commit-config.yaml` line 7
```yaml
- id: ruff-format
```

**Issue**:
- No `--check` flag → auto-fixes but doesn't fail
- No `files: .` → only checks staged files
- No validation that ALL files are formatted

## Impact Analysis

**Time Wasted**:
- Each failed CI run: ~2-5 minutes
- Frequency: ~50% of pushes (every other push)
- Developer time: 5-10 minutes per failure (investigation + fix + re-push)
- **Total waste**: Significant cumulative time loss

**Failed Commits** (from screenshot):
- `cae1f3e` - Remove API key requirement
- `2d9156b` - FastMCP Cloud HTTP transport
- `ac09bce` - fastmcp.json transport update
- `6078660` - Python requirement fix
- `f20f0e4` - Python version mismatch fix

**Pattern**: All failed on formatting checks, not code issues.

## Why Code Quality Agent Wasn't Triggered

**SEF Agent Responsibility**: `developer` agent (Phase 4) is responsible for code quality.

**Why Not Triggered**:
1. **Workflow Context**: Story AUTH-REMOVE-001 focused on auth logic, not formatting
2. **File Scope**: Only modified `auth.py` and `test_auth_routing.py`
3. **Pre-commit Passed**: Developer saw pre-commit pass → assumed quality OK
4. **Agent Limitation**: Developer agent doesn't scan entire codebase by default
5. **Missing Step**: No explicit "format all files" check in workflow

**Gap**: Developer agent should enforce "format entire codebase" before commit, not just changed files.

## Recommendations

See `sef-reports/strategy/ci_formatting_fix_strategy_2026-01-19.md` for permanent fix recommendations.
