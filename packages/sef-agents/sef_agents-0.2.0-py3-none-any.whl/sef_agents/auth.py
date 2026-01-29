"""Authentication module for SEF-Agents MCP server.

Provides API key validation using FastMCP's DebugTokenVerifier.
Keys loaded from environment variable (cloud) or JSON file (local).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from fastmcp.server.auth.providers.debug import DebugTokenVerifier

logger = structlog.get_logger(__name__)

# Environment variable for cloud deployment
ENV_VAR_NAME = "SEF_API_KEYS"
# Default path for local API keys file
DEFAULT_KEYS_PATH = Path(__file__).parent / "api_keys.json"


def load_api_keys(keys_path: Path | None = None) -> set[str]:
    """Load API keys from environment variable or JSON file.

    Priority:
    1. SEF_API_KEYS env var (comma-separated keys for cloud)
    2. JSON file (for local development) - ONLY if SEF_ENABLE_AUTH is set.

    Args:
        keys_path: Path to JSON file. Defaults to api_keys.json in module dir.

    Returns:
        Set of valid API key strings.
        Empty set if no keys configured (Open Mode).
    """
    # Priority 1: Environment variable (cloud deployment)
    env_keys = os.environ.get(ENV_VAR_NAME)
    if env_keys and env_keys.strip():
        # Support comma-separated keys: "key1,key2,key3"
        keys = {k.strip() for k in env_keys.split(",") if k.strip()}
        if keys:
            logger.info("api_keys_loaded_from_env", count=len(keys))
            return keys
        # Empty env var or no valid keys → Open Mode
        logger.info("auth_open_mode", reason="SEF_API_KEYS_empty_or_invalid")

    # Priority 2: JSON file (local development)
    # Only load from file if explicitly enabled via environment variable
    enable_auth = os.environ.get("SEF_ENABLE_AUTH", "").lower() in ("true", "1", "yes")

    # If not cloud (Priority 1) and not explicitly enabled, return empty (Open Mode)
    if not enable_auth:
        logger.info("auth_open_mode", reason="SEF_ENABLE_AUTH_not_set")
        return set()

    path = keys_path or DEFAULT_KEYS_PATH
    if not path.exists():
        logger.debug("api_keys_file_missing", path=str(path))
        return set()

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        # Support both formats:
        # Simple list: ["key1", "key2"]
        # Dict with metadata: {"key1": {...}, "key2": {...}}
        if isinstance(data, list):
            keys = set(data)
        else:
            keys = set(data.keys())
        # Filter out comment keys
        keys = {k for k in keys if not k.startswith("_")}
        logger.info("api_keys_loaded_from_file", count=len(keys))
        return keys
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("api_keys_load_failed", error=str(e))
        return set()


def create_api_key_verifier(
    keys_path: Path | None = None,
) -> "DebugTokenVerifier | None":
    """Create verifier that validates tokens against configured keys.

    Args:
        keys_path: Path to JSON file with API keys (optional).

    Returns:
        DebugTokenVerifier configured for API key validation.
        Passthrough verifier (accepts all tokens) if no keys configured.
        This satisfies FastMCP Cloud's OAuth requirement while maintaining open access.
    """
    from fastmcp.server.auth.providers.debug import DebugTokenVerifier

    keys = load_api_keys(keys_path)

    if not keys:
        # No keys configured → Open Mode
        # For FastMCP Cloud compatibility, use passthrough verifier
        # that accepts all tokens (effectively no auth) but exposes OAuth endpoints
        logger.info("auth_open_mode_passthrough", reason="no_api_keys_configured")

        def passthrough_validate(token: str) -> bool:
            """Accept all tokens (effectively no authentication)."""
            return True

        return DebugTokenVerifier(
            validate=passthrough_validate,
            client_id="sef-agents-client",
            scopes=["mcp:access"],
        )

    def validate(token: str) -> bool:
        """Check if token exists in configured keys."""
        is_valid = token in keys
        if not is_valid:
            logger.warning("token_rejected", token_prefix=token[:8] + "...")
        return is_valid

    return DebugTokenVerifier(
        validate=validate,
        client_id="sef-agents-client",
        scopes=["mcp:access"],
    )
