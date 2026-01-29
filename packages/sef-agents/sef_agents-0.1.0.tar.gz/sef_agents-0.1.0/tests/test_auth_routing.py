"""Tests for Smart Auth Routing logic."""

from pathlib import Path
from sef_agents.auth import load_api_keys


class TestAuthRouting:
    """Tests for auth mode switching logic."""

    def test_open_mode_default(self, tmp_path: Path, monkeypatch) -> None:
        """Test Default Open Mode (No Envs)."""
        # Clear envs
        monkeypatch.delenv("SEF_API_KEYS", raising=False)
        monkeypatch.delenv("SEF_ENABLE_AUTH", raising=False)

        # Create dummy keys file
        keys_file = tmp_path / "api_keys.json"
        keys_file.write_text('["local-key"]')

        # Should be empty (Open Mode) despite file existence
        keys = load_api_keys(keys_file)
        assert len(keys) == 0

    def test_cloud_mode(self, tmp_path: Path, monkeypatch) -> None:
        """Test Cloud Mode (SEF_API_KEYS set with valid keys)."""
        monkeypatch.setenv("SEF_API_KEYS", "cloud-key-1,cloud-key-2")
        # Ensure SEF_ENABLE_AUTH is OFF to prove precedence
        monkeypatch.delenv("SEF_ENABLE_AUTH", raising=False)

        keys = load_api_keys(tmp_path / "api_keys.json")
        assert "cloud-key-1" in keys
        assert "cloud-key-2" in keys
        assert len(keys) == 2

    def test_cloud_mode_empty_env(self, tmp_path: Path, monkeypatch) -> None:
        """Test Cloud Mode with empty SEF_API_KEYS → Open Mode."""
        monkeypatch.setenv("SEF_API_KEYS", "")
        monkeypatch.delenv("SEF_ENABLE_AUTH", raising=False)

        keys = load_api_keys(tmp_path / "api_keys.json")
        assert len(keys) == 0  # Open Mode

    def test_cloud_mode_whitespace_only(self, tmp_path: Path, monkeypatch) -> None:
        """Test Cloud Mode with whitespace-only SEF_API_KEYS → Open Mode."""
        monkeypatch.setenv("SEF_API_KEYS", "   ,  ,  ")
        monkeypatch.delenv("SEF_ENABLE_AUTH", raising=False)

        keys = load_api_keys(tmp_path / "api_keys.json")
        assert len(keys) == 0  # Open Mode

    def test_local_secure_mode(self, tmp_path: Path, monkeypatch) -> None:
        """Test Local Secure Mode (SEF_ENABLE_AUTH set)."""
        monkeypatch.delenv("SEF_API_KEYS", raising=False)
        monkeypatch.setenv("SEF_ENABLE_AUTH", "true")

        keys_file = tmp_path / "api_keys.json"
        keys_file.write_text('["local-secure-key"]')

        keys = load_api_keys(keys_file)
        assert "local-secure-key" in keys
        assert len(keys) == 1
