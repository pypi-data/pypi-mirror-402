# Version Number Logic

## Semantic Versioning (SemVer)

Format: `MAJOR.MINOR.PATCH` (e.g., `0.2.0`)

## Version Bump Rules

### Patch (0.1.0 → 0.1.1)
**When:** Bug fixes only
- Fixes incorrect behavior
- Security patches
- Performance improvements (no API changes)
- Documentation fixes
- Test improvements

**Example:**
- Fix: INVEST scorer incorrectly counts dependencies
- Fix: Gherkin parser fails on edge case

### Minor (0.1.0 → 0.2.0)
**When:** New features, backward compatible
- New functionality added
- New tools/models added
- New agent capabilities
- Enhanced existing features (non-breaking)
- New templates or examples

**Example:**
- Feature: Add INVEST scoring tool
- Feature: Add Epic/Feature hierarchy
- Feature: Add JSON output format

### Major (0.1.0 → 1.0.0)
**When:** Breaking changes
- API changes (function signatures, return types)
- Removed functionality
- Changed default behavior
- Incompatible data format changes
- Agent protocol changes

**Example:**
- Breaking: Remove markdown output (only JSON)
- Breaking: Change MCP tool signatures
- Breaking: Remove deprecated agent

## Pre-1.0.0 Versions

**Current:** `0.x.x` (pre-1.0.0)

**Meaning:**
- API may change between minor versions
- Not considered "stable" for production
- Breaking changes allowed in minor bumps (but should be avoided)

**Post-1.0.0:**
- Minor bumps MUST be backward compatible
- Breaking changes ONLY in major bumps

## Decision Process

1. **Identify change type:**
   - Bug fix → Patch
   - New feature (backward compatible) → Minor
   - Breaking change → Major

2. **Check backward compatibility:**
   - Existing code still works? → Minor
   - Requires code changes? → Major

3. **Update `pyproject.toml`:**
   ```toml
   version = "0.2.0"
   ```

4. **Create git tag:**
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

## Current Version: 0.2.0

**Reason:** Added 5 new features (INVEST, Gherkin, JSON, Hierarchy, Version) - all backward compatible.

---

*See [PUBLISH.md](../PUBLISH.md) for publishing workflow.*
