# Build Failure RCA #2 - FastMCP Cloud Base Image Limitation

**Date**: 2025-01-27
**Incident ID**: BUILD-FAIL-002
**Severity**: L2
**Status**: Root Cause Identified

## Executive Summary

FastMCP Cloud build continues to fail. Despite `fastmcp.json` specifying Python >=3.13, FastMCP Cloud's auto-generated Dockerfile still uses Python 3.12.12 base image (`mcp-base-python3.12`).

## Root Cause

**FastMCP Cloud platform limitation**: The platform auto-generates Dockerfiles and uses pre-built base images. Available base images appear limited to Python 3.12 (`mcp-base-python3.12`). No `mcp-base-python3.13` image exists in the registry.

### Evidence

1. **Build log shows**:
   - Base image: `342547628772.dkr.ecr.us-east-1.amazonaws.com/fastmcp-prd-base-images:mcp-base-python3.12`
   - Python runtime: 3.12.12
   - Error: Same Python version mismatch

2. **fastmcp.json configuration**:
   - Correctly specifies `"python": ">=3.13"`
   - Schema valid and properly formatted
   - **But**: FastMCP Cloud ignores this for base image selection

3. **Platform behavior**:
   - Auto-generates Dockerfile (not using our custom Dockerfile)
   - Base image selection appears hardcoded or limited to available images
   - `fastmcp.json` Python constraint may only affect local builds, not cloud builds

## Impact

- **Deployment**: Blocked on FastMCP Cloud
- **Workaround**: None available within FastMCP Cloud constraints
- **Options**: Lower Python requirement OR use alternative deployment

## Resolution Options

### Option 1: Lower Python Requirement (Quick Fix)
Change `requires-python` to `>=3.12` in `pyproject.toml`
- **Pros**: Immediate deployment unblock
- **Cons**: Violates project requirements, may break 3.13-specific features

### Option 2: Alternative Deployment (Recommended)
Use custom Dockerfile deployment (AWS Lambda, Google Cloud Run, etc.)
- **Pros**: Full control, Python 3.13 support
- **Cons**: Requires infrastructure setup

### Option 3: Wait for FastMCP Cloud Support
Request Python 3.13 base image from FastMCP team
- **Pros**: Maintains project requirements
- **Cons**: Unknown timeline, blocks deployment

## Recommendation

**Immediate**: Use Option 2 (alternative deployment) with our existing Dockerfile.
**Long-term**: Request Python 3.13 base image support from FastMCP Cloud.
