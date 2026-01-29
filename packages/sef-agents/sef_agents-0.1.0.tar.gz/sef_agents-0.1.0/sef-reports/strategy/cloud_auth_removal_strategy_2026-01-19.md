# Cloud Authentication Removal Strategy

**Date**: 2026-01-19
**Issue**: AUTH-REMOVE-001
**Agent**: Strategist

## Problem Statement

**Requirement**: Remove API key authentication for cloud version to match local behavior (Open Mode by default).

**Current State**:
- Local: No auth by default (Open Mode)
- Cloud: Requires `SEF_API_KEYS` env var → forces authentication
- **Goal**: Cloud should match local (no auth required)

## Solution Options

### Option 1: Remove Cloud Auth Requirement (Recommended)

**Approach**: Modify `load_api_keys()` to treat empty `SEF_API_KEYS` as Open Mode.

**Implementation**:
```python
# In auth.py:load_api_keys()
env_keys = os.environ.get(ENV_VAR_NAME)
if env_keys and env_keys.strip():  # ← Check for non-empty
    keys = {k.strip() for k in env_keys.split(",") if k.strip()}
    if keys:  # ← Only return if keys found
        return keys
# Falls through to Open Mode
```

**Pros**:
- ✅ Cloud matches local behavior
- ✅ Minimal code change
- ✅ Backward compatible (empty env var = Open Mode)
- ✅ FastMCP Cloud entry point unchanged (`fastmcp.json`)

**Cons**:
- ⚠️ Cloud deployments become publicly accessible (security consideration)
- ⚠️ No access control for cloud version

**Risk**: Low
**Effort**: Low
**Production Ready**: Yes (if security acceptable)

**Recommendation**: **PRIMARY** - Simplest solution, aligns with requirement.

---

### Option 2: Environment-Based Toggle

**Approach**: Add `SEF_DISABLE_AUTH=true` flag to explicitly disable auth.

**Implementation**:
```python
# In auth.py:load_api_keys()
if os.environ.get("SEF_DISABLE_AUTH", "").lower() in ("true", "1", "yes"):
    return set()  # Open Mode

# Existing logic...
```

**Pros**:
- ✅ Explicit control via env var
- ✅ Maintains security option (can still enable auth)
- ✅ Clear intent in deployment config

**Cons**:
- ⚠️ Additional complexity
- ⚠️ Requires FastMCP Cloud env var configuration

**Risk**: Low
**Effort**: Low-Medium
**Production Ready**: Yes

**Recommendation**: **ALTERNATIVE** - If explicit opt-out preferred.

---

### Option 3: Remove Auth Entirely

**Approach**: Remove all authentication code, always use Open Mode.

**Implementation**:
- Delete `src/sef_agents/auth.py`
- Remove `auth_verifier` from `server.py`
- Always create `FastMCP("SEF-Agents")` without auth

**Pros**:
- ✅ Simplest codebase
- ✅ No auth complexity
- ✅ Consistent behavior everywhere

**Cons**:
- ❌ Removes security option entirely
- ❌ Cannot enable auth if needed later
- ❌ Breaking change for existing cloud deployments

**Risk**: Medium
**Effort**: Medium (requires test updates)
**Production Ready**: Conditional (if security acceptable)

**Recommendation**: **NOT RECOMMENDED** - Too aggressive, removes future flexibility.

---

## FastMCP Cloud Entry Point Clarification

**Current Configuration** (`fastmcp.json`):
```json
{
  "source": {
    "path": "src/sef_agents/server.py",
    "entrypoint": "mcp"
  }
}
```

**Entry Point Definition**:
- `entrypoint: "mcp"` refers to the `FastMCP` instance variable at module level
- FastMCP Cloud automatically:
  1. Imports `src/sef_agents/server.py`
  2. Accesses `server.mcp` (the FastMCP instance)
  3. Configures HTTP transport via `deployment.transport: "http"`
  4. Invokes `mcp.run()` to start server

**No Changes Required**: Current entry point configuration is correct. Removing auth doesn't affect entry point.

## Recommended Solution

**Primary**: Option 1 - Remove Cloud Auth Requirement

### Implementation Plan

1. **Modify `load_api_keys()`**:
   - Check for non-empty `SEF_API_KEYS` before processing
   - Return empty set if env var empty or missing
   - Cloud defaults to Open Mode (matches local)

2. **Update Tests**:
   - Verify cloud mode with empty `SEF_API_KEYS` → Open Mode
   - Verify cloud mode with non-empty `SEF_API_KEYS` → Auth enabled (backward compat)

3. **Documentation**:
   - Update README: Cloud version uses Open Mode by default
   - Note: Set `SEF_API_KEYS` to enable authentication (optional)

### Security Considerations

**Risk Assessment**:
- **Low Risk**: MCP servers are guidance tools, not data stores
- **No Sensitive Data**: All operations are local codebase analysis
- **Public Access**: Cloud version becomes publicly accessible

**Mitigation** (if needed later):
- Option 2 can be implemented if access control required
- FastMCP Cloud may provide platform-level auth (check FastMCP docs)

## Decision Matrix

| Option | Effort | Risk | Security | Flexibility | Recommendation |
|--------|--------|------|----------|-------------|---------------|
| Option 1 | Low | Low | Low | Medium | ✅ **PRIMARY** |
| Option 2 | Low-Med | Low | Medium | High | ⚠️ Alternative |
| Option 3 | Medium | Medium | Low | Low | ❌ Not Recommended |

## Next Steps

1. ✅ **Strategy Complete** - Option 1 recommended
2. ⏳ **Developer Implementation** - Modify `auth.py` per Option 1
3. ⏳ **Testing** - Verify cloud Open Mode behavior
4. ⏳ **Documentation** - Update README with cloud auth behavior
