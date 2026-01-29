# CI Formatting Failure - Permanent Fix Strategy

**Date**: 2026-01-19
**Issue**: CI-FAIL-001
**Agent**: Strategist

## Problem Summary

**Gap**: Pre-commit checks only staged files, CI checks all files → formatting issues in untouched files cause CI failures.

**Impact**: ~50% of pushes fail, wasting significant time.

## Solution Options

### Option 1: Pre-commit Check All Files (Recommended)

**Approach**: Add separate pre-commit hook that validates ALL files are formatted.

**Implementation**:
```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.8.6
  hooks:
    - id: ruff
      args: [--fix, --exit-non-zero-on-fix]
    - id: ruff-format  # Auto-fix staged files
    - id: ruff-format-check-all  # NEW: Validate all files
      args: [--check]
      files: ^$
      pass_filenames: false
      always_run: true
```

**Alternative** (if ruff-format-check-all doesn't exist):
```yaml
- repo: local
  hooks:
    - id: ruff-format-check-all
      name: ruff format --check (all files)
      entry: bash -c 'uv run ruff format --check . || (echo "❌ Formatting issues found. Run: uv run ruff format ." && exit 1)'
      language: system
      pass_filenames: false
      always_run: true
```

**Pros**:
- ✅ Catches issues before commit
- ✅ Matches CI behavior exactly
- ✅ No CI failures
- ✅ Minimal code change

**Cons**:
- ⚠️ Slower pre-commit (checks all files)
- ⚠️ Requires formatting entire codebase first

**Risk**: Low
**Effort**: Low
**Production Ready**: Yes

**Recommendation**: **PRIMARY** - Best alignment with CI.

---

### Option 2: CI Check Only Changed Files

**Approach**: Modify CI to only check formatting on changed files.

**Implementation**:
```yaml
- name: Format Check (Ruff) - Changed Files Only
  run: |
    git diff --name-only --diff-filter=ACMRT origin/main...HEAD | grep '\.py$' | xargs uv run ruff format --check || true
    # Or use GitHub's changed-files action
```

**Pros**:
- ✅ Faster CI runs
- ✅ Only checks relevant files

**Cons**:
- ❌ Doesn't catch pre-existing issues
- ❌ Allows technical debt accumulation
- ❌ Different behavior from pre-commit (still gap)

**Risk**: Medium (allows debt)
**Effort**: Low
**Production Ready**: No (hides problems)

**Recommendation**: **NOT RECOMMENDED** - Hides formatting issues.

---

### Option 3: Pre-commit Auto-format All Files

**Approach**: Pre-commit formats ALL files, not just staged.

**Implementation**:
```yaml
- id: ruff-format-all
  name: ruff format (all files)
  entry: bash -c 'uv run ruff format .'
  language: system
  pass_filenames: false
  always_run: true
```

**Pros**:
- ✅ Ensures all files formatted
- ✅ No manual intervention

**Cons**:
- ❌ Modifies unstaged files (dangerous)
- ❌ Can cause unexpected changes
- ❌ Violates pre-commit best practices

**Risk**: High (modifies unstaged files)
**Effort**: Low
**Production Ready**: No

**Recommendation**: **NOT RECOMMENDED** - Too risky.

---

### Option 4: Hybrid - Format Staged + Check All

**Approach**: Format staged files, then validate all files are formatted.

**Implementation**:
```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.8.6
  hooks:
    - id: ruff
      args: [--fix, --exit-non-zero-on-fix]
    - id: ruff-format  # Format staged files
- repo: local
  hooks:
    - id: ruff-format-validate-all
      name: Validate all files formatted
      entry: bash -c 'uv run ruff format --check . || (echo "❌ Unformatted files found. Run: uv run ruff format ." && exit 1)'
      language: system
      pass_filenames: false
      always_run: true
```

**Pros**:
- ✅ Formats staged files automatically
- ✅ Validates entire codebase
- ✅ Clear error message with fix command
- ✅ Matches CI exactly

**Cons**:
- ⚠️ Requires one-time codebase format

**Risk**: Low
**Effort**: Low
**Production Ready**: Yes

**Recommendation**: **PRIMARY** - Best balance.

---

## Recommended Solution

**Primary**: Option 4 - Hybrid Approach

### Implementation Plan

1. **One-time cleanup**:
   ```bash
   uv run ruff format .
   git add -A
   git commit -m "style: format entire codebase"
   ```

2. **Update `.pre-commit-config.yaml`**:
   - Keep existing `ruff-format` (formats staged files)
   - Add `ruff-format-validate-all` hook (validates all files)

3. **Update Developer Workflow**:
   - Add step: "Format entire codebase before major commits"
   - Document in CONTRIBUTING.md

4. **CI Alignment**:
   - Pre-commit and CI now check same scope (all files)
   - No more gaps

### Code Changes

**File**: `.pre-commit-config.yaml`

Add after line 8:
```yaml
  - repo: local
    hooks:
      - id: ruff-format-validate-all
        name: Validate all files are formatted
        entry: bash -c 'uv run ruff format --check . || (echo "❌ Unformatted files detected. Run: uv run ruff format ." && exit 1)'
        language: system
        pass_filenames: false
        always_run: true
```

### Developer Agent Integration

**Enhancement**: Update `developer` agent to:
1. Run `ruff format --check .` before commit
2. Fail if formatting issues found
3. Suggest: `uv run ruff format .`

**File**: `src/sef_agents/rules/development/elite_code_quality.md`

Add:
```markdown
## Pre-Commit Checklist
- [ ] Run `uv run ruff format --check .` (validates entire codebase)
- [ ] Fix any formatting issues before committing
```

## Decision Matrix

| Option | Effort | Risk | Effectiveness | Maintainability | Recommendation |
|--------|--------|------|---------------|-----------------|---------------|
| Option 1 | Low | Low | High | High | ✅ **PRIMARY** |
| Option 2 | Low | Medium | Low | Medium | ❌ Not Recommended |
| Option 3 | Low | High | Medium | Low | ❌ Not Recommended |
| Option 4 | Low | Low | High | High | ✅ **PRIMARY** |

## Expected Outcome

**Before**:
- Pre-commit: Checks staged files only
- CI: Checks all files
- **Result**: Frequent failures

**After**:
- Pre-commit: Formats staged + validates all files
- CI: Checks all files
- **Result**: Zero formatting failures (pre-commit catches everything)

## Next Steps

1. ✅ **Strategy Complete** - Option 4 recommended
2. ⏳ **One-time cleanup** - Format entire codebase
3. ⏳ **Update pre-commit config** - Add validation hook
4. ⏳ **Test** - Verify pre-commit catches formatting issues
5. ⏳ **Document** - Update CONTRIBUTING.md
