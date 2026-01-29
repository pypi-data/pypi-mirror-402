# API Key Authentication Implementation RCA

**Date**: 2026-01-19
**Issue**: AUTH-REMOVE-001
**Agent**: Forensic Engineer

## Current Implementation Analysis

### Authentication Flow

**File**: `src/sef_agents/auth.py`

1. **Key Loading Priority** (`load_api_keys()`):
   - **Priority 1**: `SEF_API_KEYS` env var (comma-separated) → **Cloud Mode**
   - **Priority 2**: JSON file (`api_keys.json`) → **Local Secure Mode** (only if `SEF_ENABLE_AUTH=true`)
   - **Default**: Empty set → **Open Mode** (no auth)

2. **Verifier Creation** (`create_api_key_verifier()`):
   - Returns `DebugTokenVerifier` if keys found
   - Returns `None` if no keys (auth disabled)

**File**: `src/sef_agents/server.py` (lines 60-65)

```python
auth_verifier = create_api_key_verifier()
mcp = (
    FastMCP("SEF-Agents", auth=auth_verifier)
    if auth_verifier
    else FastMCP("SEF-Agents")
)
```

### Current Behavior

| Mode | Condition | Auth Status |
|------|-----------|-------------|
| **Cloud** | `SEF_API_KEYS` env var set | ✅ **Auth Enabled** |
| **Local Secure** | `SEF_ENABLE_AUTH=true` + keys file | ✅ **Auth Enabled** |
| **Local Default** | No env vars, no explicit enable | ❌ **Auth Disabled** (Open Mode) |

### FastMCP Cloud Entry Point

**File**: `fastmcp.json`
```json
{
  "source": {
    "path": "src/sef_agents/server.py",
    "entrypoint": "mcp"
  }
}
```

- `entrypoint: "mcp"` refers to the `FastMCP` instance variable at module level
- FastMCP Cloud reads this and configures HTTP transport automatically
- Server initialization happens at import time (module-level `auth_verifier` and `mcp`)

## Issue: Cloud Version Requires API Key

**Current Problem**:
- Cloud deployment requires `SEF_API_KEYS` env var → forces authentication
- Local version defaults to Open Mode (no auth)
- User wants cloud version to match local behavior (no auth by default)

## Root Cause

**Code Location**: `src/sef_agents/auth.py:42-47`

```python
env_keys = os.environ.get(ENV_VAR_NAME)  # SEF_API_KEYS
if env_keys:
    keys = {k.strip() for k in env_keys.split(",") if k.strip()}
    logger.info("api_keys_loaded_from_env", count=len(keys))
    return keys  # ← Cloud mode always requires keys if env var exists
```

**Issue**: If `SEF_API_KEYS` is set (even empty string), cloud mode activates and requires valid keys.

## Impact

- **Cloud deployments** must configure API keys
- **Local development** works without auth (Open Mode)
- **Inconsistency** between local and cloud behavior
- **User requirement**: Cloud should match local (no auth by default)

## Technical Details

### FastMCP Cloud Configuration

- FastMCP Cloud reads `fastmcp.json` for deployment config
- Entry point `"mcp"` must be a `FastMCP` instance at module level
- HTTP transport configured automatically via `deployment.transport: "http"`
- Server runs via `mcp.run()` which FastMCP Cloud invokes

### Authentication Mechanism

- Uses `DebugTokenVerifier` from `fastmcp.server.auth.providers.debug`
- Validates Bearer tokens from `Authorization` header
- Token must match one of the keys in `SEF_API_KEYS` env var

## Next Steps

1. ✅ **Forensic Analysis Complete** - Current implementation documented
2. ⏳ **Strategist Review** - Determine approach for removing cloud auth requirement
3. ⏳ **Implementation** - Modify auth logic to allow cloud Open Mode
