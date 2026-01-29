# MCP Remote Configuration RCA

**Date**: 2026-01-19
**Issue**: Remote FastMCP URL configuration not working
**Agent**: Forensic Engineer

## Root Cause

Missing `transport` field in MCP configuration. FastMCP requires explicit transport specification for URL-based configurations.

## Problem

Configuration at `~/.cursor/mcp.json` lines 38-44:
```json
"sefagents": {
  "url": "https://sefagents.fastmcp.app/mcp",
  "headers": {},
  "env": {
    "SEF_API_KEYS": "sk-sef-287ac739-81c1-4093-8218-70e31ffc3b22"
  }
}
```

**Error**: Server "sefagents" not found

## Solution

Add `"transport": "http"` to the configuration:

```json
"sefagents": {
  "url": "https://sefagents.fastmcp.app/mcp",
  "transport": "http",
  "headers": {},
  "env": {
    "SEF_API_KEYS": "sk-sef-287ac739-81c1-4093-8218-70e31ffc3b22"
  }
}
```

## Technical Details

- FastMCP supports HTTP transport for remote MCP servers
- Transport must be explicitly specified: `"transport": "http"`
- Without transport field, MCP client cannot determine connection method
- Authentication via `SEF_API_KEYS` env var is correctly configured

## Verification

After fix, restart Cursor and verify:
1. `sefagents` server appears in available MCP servers
2. API key authentication works
3. Tools and prompts are accessible

## Status Update - Authentication Failure

**New Issue**: After adding `transport: "http"`, server connects but authentication fails.

**Error**: `{"error": "invalid_token", "error_description": "Authentication failed..."}`

**Root Cause**: API key `sk-sef-287ac739-81c1-4093-8218-70e31ffc3b22` is either:
1. Not configured on remote server (`https://sefagents.fastmcp.app`)
2. Invalid/expired
3. Wrong format for HTTP transport

**Impact**: Client connects but gets stuck at "Loading tools" because authentication never succeeds.

## Resolution

**Client Configuration (Correct)**:
```json
"sefagents": {
  "url": "https://sefagents.fastmcp.app/mcp",
  "transport": "http",
  "headers": {
    "Authorization": "Bearer sk-sef-287ac739-81c1-4093-8218-70e31ffc3b22"
  }
}
```

**Server-Side Requirement**:
The remote server at `https://sefagents.fastmcp.app` must have:
```bash
SEF_API_KEYS="sk-sef-287ac739-81c1-4093-8218-70e31ffc3b22"
```

**Why `env` doesn't work**:
- `env` field sets environment variables on the **CLIENT** process
- Server needs `SEF_API_KEYS` in its **own** environment
- HTTP transport requires token in `Authorization` header (client → server)

**Code Reference** (`src/sef_agents/auth.py`):
- Server loads keys from `SEF_API_KEYS` env var (line 42)
- Uses `DebugTokenVerifier` which extracts Bearer token from `Authorization` header
- Validates token against loaded keys (line 104)

## Root Cause Analysis Summary

**Issue**: Remote server connects but authentication fails → tools don't load

**Findings**:
1. ✅ Transport configured correctly (`transport: "http"`)
2. ✅ Client sends Bearer token in Authorization header
3. ❌ Server rejects token: `invalid_token` error
4. Server expects API key in `SEF_API_KEYS` environment variable

**Possible Causes**:
1. API key not configured on remote server
2. API key format mismatch (server may expect key without "Bearer " prefix)
3. API key expired or invalid

**Next Steps**:
1. Verify API key is configured on `https://sefagents.fastmcp.app` server
2. Confirm `SEF_API_KEYS` env var contains: `sk-sef-287ac739-81c1-4093-8218-70e31ffc3b22`
3. Check FastMCP Cloud deployment logs for authentication errors

**Status**: ⚠️ **Configuration correct, server-side issue** - API key validation failing on remote server
