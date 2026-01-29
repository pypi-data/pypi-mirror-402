# Windows Troubleshooting Guide

## Issue: `pywin32` Access Denied Error

**Error:**
```
Failed to download `pywin32==311`
Access is denied. (os error 5)
```

**Root Cause:**
- `pywin32` is a Windows-specific dependency required by `mcp` package
- Windows file locking/permissions issue with `uv` cache directory
- Common causes: Antivirus interference, concurrent processes, or corrupted cache

## Solutions (Try in Order)

### Solution 1: Use PyPI Version (Recommended)

**Instead of GitHub installation, use PyPI:**

```json
{
  "mcpServers": {
    "sef-agents": {
      "command": "uvx",
      "args": ["sef-agents"]
    }
  }
}
```

This avoids GitHub-specific resolution issues and uses pre-built wheels.

### Solution 2: Clear uv Cache

```powershell
# Clear uv cache
uv cache clean

# Retry installation
uvx sef-agents
```

### Solution 3: Use --no-cache Flag

**Temporary workaround** (slower but avoids cache issues):

```json
{
  "mcpServers": {
    "sef-agents": {
      "command": "uvx",
      "args": [
        "--no-cache",
        "sef-agents"
      ]
    }
  }
}
```

### Solution 4: Set Custom Cache Directory

If antivirus is blocking `AppData\Local\uv\cache`:

```powershell
# Set custom cache location
$env:UV_CACHE_DIR = "C:\temp\uv-cache"
uvx sef-agents
```

Then update MCP config:
```json
{
  "mcpServers": {
    "sef-agents": {
      "command": "uvx",
      "args": ["sef-agents"],
      "env": {
        "UV_CACHE_DIR": "C:\\temp\\uv-cache"
      }
    }
  }
}
```

### Solution 5: Run as Administrator

If permission issues persist:

1. Close Cursor/Claude Desktop
2. Run PowerShell as Administrator
3. Clear cache: `uv cache clean`
4. Retry installation

### Solution 6: Check Antivirus

**Common culprits:**
- Windows Defender (may need exclusion)
- Avast, Norton, McAfee

**Add exclusions for:**
- `C:\Users\<username>\AppData\Local\uv\`
- `C:\Users\<username>\AppData\Local\Temp\`

## Verification

After applying a solution, verify installation:

```powershell
uvx sef-agents --help
```

Should output server help without errors.

## Still Having Issues?

1. **Check uv version**: `uv --version` (should be 0.5.5+)
2. **Update uv**: `pip install --upgrade uv` or download from https://github.com/astral-sh/uv
3. **Check Python**: `python --version` (should be 3.12+)
4. **Report issue**: Include Windows version, uv version, and full error log

## Alternative: Local Installation

If `uvx` continues to fail, install locally:

```powershell
# Clone repository
git clone https://github.com/Mishtert/sef-agents.git
cd sef-agents

# Install with uv
uv sync

# Use local installation in MCP config
```

Then in MCP config:
```json
{
  "mcpServers": {
    "sef-agents": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\sef-agents",
        "run",
        "sef-agents"
      ]
    }
  }
}
```
