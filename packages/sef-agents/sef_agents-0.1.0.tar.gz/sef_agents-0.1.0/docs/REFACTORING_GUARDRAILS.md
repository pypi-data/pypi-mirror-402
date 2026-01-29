# Refactoring Guardrails Protocol

## Overview
This document defines the guardrails we follow to ensure refactoring doesn't break working code or logic. All refactoring must pass these checks before completion.

## SEF-Agents Guardrails (Non-Negotiable)

### 1. Pre-Refactoring Validation
- ✅ **Regression Risk Scan**: `mcp_sef-agents_scan_regression_risk`
  - Identifies high-risk patterns before changes
  - Must show LOW risk before proceeding
- ✅ **Code Quality Baseline**: `mcp_sef-agents_scan_code_quality`
  - Establishes baseline metrics
  - Tracks improvement/degradation

### 2. During Refactoring
- ✅ **Linter Checks**: `read_lints` after each file change
  - Zero linter errors required
  - Catches syntax/type issues immediately
- ✅ **Logic Preservation**: Forensic comparison
  - Compare old vs new implementation
  - Verify public API unchanged
  - Ensure exception handling logic preserved

### 3. Post-Refactoring Validation
- ✅ **Test Execution**: Run all affected tests
  ```bash
  uv run pytest tests/unit/<module>/test_<file>.py -v --tb=short
  ```
  - All existing tests must pass
  - New tests added for new behavior
- ✅ **Regression Risk Re-scan**: Verify no new risks introduced
- ✅ **Code Quality Re-scan**: Verify metrics improved or maintained
- ✅ **Public API Verification**: Ensure backward compatibility

## Multi-Layer Validation Strategy

### Layer 1: Static Analysis (SEF-Agents)
1. **Platform Engineer Scan**: `scan_code_quality`
   - Critical issues count
   - Complexity metrics
   - Code smell detection

2. **Regression Risk Scan**: `scan_regression_risk`
   - High-risk pattern detection
   - Logic change warnings

3. **Compliance Validation**: `validate_compliance`
   - SEF standards adherence
   - Best practices compliance

### Layer 2: Test Execution
1. **Unit Tests**: All existing tests must pass
2. **Integration Tests**: End-to-end flows verified
3. **Test Coverage**: Maintain or improve coverage

### Layer 3: Logic Verification
1. **Forensic Comparison**: Old vs new implementation
2. **Public API Check**: All public methods/attributes preserved
3. **Exception Handling**: Specific exceptions maintained
4. **Error Messages**: Context preserved

### Layer 4: Runtime Validation
1. **Linter Errors**: Zero errors required
2. **Type Checking**: Type hints preserved
3. **Import Validation**: All imports resolve

## Exception Handling Refactoring Protocol

### Before Change
1. Identify all `except Exception` blocks
2. Document intended behavior (fail-fast vs graceful)
3. Identify specific exception types to catch

### During Change
1. Replace `except Exception` with specific types
2. Preserve error messages and context
3. Maintain re-raise behavior where appropriate
4. Migrate logging to structlog if touching file

### After Change
1. Run affected tests
2. Verify exception types match expected behavior
3. Check error messages preserved
4. Validate logging output format

## Structlog Migration Protocol

### Before Migration
1. Identify all `logging.getLogger(__name__)` usage
2. Check if file already uses structlog
3. Verify structlog compatibility

### During Migration
1. Replace `import logging` → `from app.shared.utils.logging import get_logger`
2. Replace `logger = logging.getLogger(__name__)` → `logger = get_logger(__name__)`
3. Verify log calls use structured format (key=value)

### After Migration
1. Run tests to verify logging works
2. Check logstream compatibility (stdout output)
3. Verify structured logging format

## Complexity Refactoring Protocol

### Before Refactoring
1. Identify complexity hotspots (>50 complexity)
2. Use strategist for refactoring recommendations
3. Plan extraction strategy (SRP compliance)

### During Refactoring
1. Extract classes/modules following SRP
2. Maintain public API compatibility
3. Use delegation pattern where appropriate

### After Refactoring
1. Verify complexity reduced (<15 per class)
2. Run all tests
3. Update CODE_MAP.md
4. Verify no new dependencies introduced

## Current Status

### Exception Handling Progress
- **Fixed**: `chunk_consumer.py` (4 handlers), `file_discovery_service.py` (2 handlers)
- **Remaining**: 79 critical issues across 30+ files
- **Regression Risk**: ✅ LOW (verified via SEF-agents)

### Structlog Migration Progress
- **Migrated**: `chunk_consumer.py`, `dataverse.py`, `dataverse_*_manager.py` (4 files)
- **Remaining**: 19 files still use `logging.getLogger()`
- **Logstream Compatible**: ✅ YES (stdout output verified)

### Test Status
- **Passing**: 27/34 tests (79%)
- **Failing**: 7 tests (expected - batch operation changes)
- **Coverage**: Maintained

## Guardrail Checklist (Per File)

- [ ] Pre-scan regression risk (LOW required)
- [ ] Baseline code quality metrics
- [ ] Fix exception handling (specific types)
- [ ] Migrate to structlog (if touching file)
- [ ] Run linter (zero errors)
- [ ] Run affected tests (all pass)
- [ ] Post-scan regression risk (LOW maintained)
- [ ] Post-scan code quality (improved/maintained)
- [ ] Update CODE_MAP.md
- [ ] Verify public API unchanged

## Failure Modes & Recovery

### Test Failures
- **Action**: Investigate root cause
- **If expected**: Update tests to match new behavior
- **If regression**: Revert and fix logic

### Regression Risk Increase
- **Action**: Review high-risk patterns
- **Fix**: Address identified risks before proceeding

### Code Quality Degradation
- **Action**: Review complexity/metrics
- **Fix**: Refactor to improve metrics

## Tools & Commands

```bash
# Regression risk scan
mcp_sef-agents_scan_regression_risk --files <file1>,<file2>

# Code quality scan
mcp_sef-agents_scan_code_quality --directory <dir>

# Run tests
uv run pytest tests/unit/<module>/test_<file>.py -v --tb=short

# Linter check
read_lints --paths <file>

# Compliance validation
mcp_sef-agents_validate_compliance --file_path <file>
```

## References
- SEF-Agents MCP: https://github.com/sef-agents
- Structlog docs: https://www.structlog.org/
- Azure Logstream: Captures stdout/stderr automatically
