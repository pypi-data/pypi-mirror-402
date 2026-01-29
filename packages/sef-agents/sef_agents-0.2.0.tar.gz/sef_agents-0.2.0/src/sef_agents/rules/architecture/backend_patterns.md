---
description: Whenever there is a need to scan code for quality. Follow these rules
alwaysApply: false
---
# Backend Quality Fragments

## 1. Validation & Security
- **Inputs**: Validate all user/API/CLI data. Check types/ranges.
- **Injection**: Parameterize SQL. Use safe shell commands. Sanitize paths.
- **Secrets**: No hardcoded credentials. Use env vars.
- **Serial**: Avoid insecure `pickle`. Use safe `yaml.safe_load`.

## 2. Errors & Resources
- **Exceptions**: Specific catches only. No broad `except:`.
- **Resources**: Mandate `with` context managers. Close sockets/files.
- **Logging**: Use structured lazy logging. No sensitive data.
- **Disclosure**: Mask stack traces in production.

## 3. Performance
- **Complexity**: O(n²) alert. Choose optimal data structures.
- **I/O**: Use `async` for non-blocking operations. Batch queries.
- **Memory**: Clean large object references. Check for leaks.
- **Cache**: Memoize expensive calculations.

## 4. maintainability
- **Structure**: Focused functions. Cohesive modules.
- **Idioms**: PEP 8. Use Pythonic patterns (list comps, generators).
- **Types**: Mandate type hints and Google-style docstrings.
- **DRY**: Abstract repeated blocks.

## 5. Deployment & Testing
- **Deps**: Pin versions in `pyproject.toml`. Check vulnerabilities.
- **Env**: Isolate dev/prod logic.
- **Tests**: Verify critical paths. Stress edge cases. Assert specific outcomes.

## 6. Concurrency
- **Safety**: Protect shared state. Use appropriate locking.
- **Async**: Correct `await` placement. No blocking in event loop.

## 7. Report Output
- **Directory**: `scancheck/backend`
- **Scores**: CRITICAL(0-3), HIGH(4-6), MEDIUM(7-8), LOW(9-10).
- **Summary**: Overall score (0-100). Top 5 criticals. PASS/FAIL.
