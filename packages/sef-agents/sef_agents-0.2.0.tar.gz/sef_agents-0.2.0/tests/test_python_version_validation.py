"""Tests for Python version validation script."""

import sys
from pathlib import Path
from unittest.mock import patch


# Add scripts to path for testing
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from validate_python_version import (  # noqa: E402
    get_required_python_version,
    get_current_python_version,
    check_version_compatibility,
)


def test_get_current_python_version():
    """Test getting current Python version."""
    version = get_current_python_version()
    assert isinstance(version, tuple)
    assert len(version) == 3
    assert all(isinstance(v, int) for v in version)


def test_get_required_python_version():
    """Test extracting required Python version from pyproject.toml."""
    # Test with actual pyproject.toml (integration test)
    version = get_required_python_version()
    assert version == ">=3.12"
    assert version.startswith(">=")


def test_check_version_compatibility_satisfies():
    """Test version compatibility check when version satisfies requirement."""
    assert check_version_compatibility(">=3.13", (3, 13, 0)) is True
    assert check_version_compatibility(">=3.13", (3, 13, 1)) is True
    assert check_version_compatibility(">=3.13", (3, 14, 0)) is True


def test_check_version_compatibility_fails():
    """Test version compatibility check when version doesn't satisfy requirement."""
    assert check_version_compatibility(">=3.13", (3, 12, 0)) is False
    assert check_version_compatibility(">=3.13", (3, 11, 0)) is False


def test_check_version_compatibility_with_range():
    """Test version compatibility with version range."""
    # Test >=3.13,<3.14 style
    assert check_version_compatibility(">=3.13,<3.14", (3, 13, 0)) is True
    assert check_version_compatibility(">=3.13,<3.14", (3, 12, 0)) is False
    assert check_version_compatibility(">=3.13,<3.14", (3, 14, 0)) is False


def test_main_success(capsys):
    """Test main function with compatible Python version."""
    with (
        patch(
            "validate_python_version.get_required_python_version", return_value=">=3.13"
        ),
        patch(
            "validate_python_version.get_current_python_version",
            return_value=(3, 13, 0),
        ),
        patch("validate_python_version.check_version_compatibility", return_value=True),
        patch("sys.exit") as mock_exit,
    ):
        from validate_python_version import main

        main()

        mock_exit.assert_called_once_with(0)
        output = capsys.readouterr()
        assert "✅" in output.out


def test_main_failure(capsys):
    """Test main function with incompatible Python version."""
    with (
        patch(
            "validate_python_version.get_required_python_version", return_value=">=3.13"
        ),
        patch(
            "validate_python_version.get_current_python_version",
            return_value=(3, 12, 0),
        ),
        patch(
            "validate_python_version.check_version_compatibility", return_value=False
        ),
        patch("sys.exit") as mock_exit,
    ):
        from validate_python_version import main

        main()

        mock_exit.assert_called_once_with(1)
        output = capsys.readouterr()
        assert "❌" in output.err
