"""Tests for API Key Authentication.

Covers:
- API keys file loading (missing, valid, invalid)
- Token validation (valid, invalid)
- Verifier creation with/without keys file

Related: src/sef_agents/auth.py
"""

import json


def test_load_api_keys_missing_file(tmp_path):
    """Returns empty dict when file missing."""
    from sef_agents.auth import load_api_keys

    result = load_api_keys(tmp_path / "nonexistent.json")

    assert result == set()


def test_load_api_keys_valid(tmp_path, monkeypatch):
    """Loads keys from valid JSON."""
    monkeypatch.setenv("SEF_ENABLE_AUTH", "true")
    from sef_agents.auth import load_api_keys

    keys_file = tmp_path / "api_keys.json"
    keys_file.write_text(
        json.dumps(
            {
                "sk-test-123": {"user": "test@example.com", "scopes": ["mcp:access"]},
                "sk-test-456": {"user": "admin@example.com", "scopes": ["mcp:access"]},
            }
        )
    )

    result = load_api_keys(keys_file)

    assert len(result) == 2
    assert "sk-test-123" in result
    assert "sk-test-456" in result


def test_load_api_keys_invalid_json(tmp_path, monkeypatch):
    """Returns empty dict for invalid JSON."""
    monkeypatch.setenv("SEF_ENABLE_AUTH", "true")
    from sef_agents.auth import load_api_keys

    keys_file = tmp_path / "api_keys.json"
    keys_file.write_text("{ invalid json }")

    result = load_api_keys(keys_file)

    assert result == set()


def test_create_verifier_no_keys_file(tmp_path):
    """Returns passthrough verifier when no keys file (Open Mode)."""
    from fastmcp.server.auth.providers.debug import DebugTokenVerifier
    from sef_agents.auth import create_api_key_verifier

    result = create_api_key_verifier(tmp_path / "nonexistent.json")

    # Should return passthrough verifier (accepts all tokens)
    assert result is not None
    assert isinstance(result, DebugTokenVerifier)
    # Passthrough verifier accepts any token
    assert result.validate("any-token") is True


def test_create_verifier_with_keys(tmp_path, monkeypatch):
    """Creates verifier when keys file exists."""
    monkeypatch.setenv("SEF_ENABLE_AUTH", "true")
    from sef_agents.auth import create_api_key_verifier

    keys_file = tmp_path / "api_keys.json"
    keys_file.write_text(json.dumps({"sk-test-123": {"user": "test@example.com"}}))

    result = create_api_key_verifier(keys_file)

    assert result is not None


def test_validate_token_valid(tmp_path, monkeypatch):
    """Valid token passes verification."""
    monkeypatch.setenv("SEF_ENABLE_AUTH", "true")
    from sef_agents.auth import load_api_keys

    keys_file = tmp_path / "api_keys.json"
    keys_file.write_text(json.dumps({"sk-valid-token": {"user": "test@example.com"}}))

    keys = load_api_keys(keys_file)

    assert "sk-valid-token" in keys


def test_validate_token_invalid(tmp_path, monkeypatch):
    """Invalid token not in keys."""
    monkeypatch.setenv("SEF_ENABLE_AUTH", "true")
    from sef_agents.auth import load_api_keys

    keys_file = tmp_path / "api_keys.json"
    keys_file.write_text(json.dumps({"sk-valid-token": {"user": "test@example.com"}}))

    keys = load_api_keys(keys_file)

    assert "sk-invalid-token" not in keys
