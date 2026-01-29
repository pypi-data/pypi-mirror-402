"""Tests for cross_repo_linker module."""

import tempfile
from pathlib import Path

import pytest

from sef_agents.tools.cross_repo_linker import (
    DependencyGap,
    LinkReport,
    get_unregistered_deps,
    link_dependencies,
    parse_registry,
    validate_external_deps,
)


@pytest.fixture
def sample_registry() -> str:
    """Sample EXTERNAL_APIS.md content."""
    return """# External APIs Registry

## Registered Dependencies

### Environment Variables

| Env Var | Purpose | Contract/Docs | Notes |
|---------|---------|---------------|-------|
| `STRIPE_API_KEY` | Payment processing | - | - |
| `DATABASE_URL` | Primary database | - | - |

### API Clients (Libraries)

| Library | Purpose | Version | Contract/Docs |
|---------|---------|---------|---------------|
| `stripe` | Payment API | `>=5.0.0` | - |
| `boto3` | AWS services | `>=1.26.0` | - |

### External URLs

| Domain | Purpose | Contract/Docs | Notes |
|--------|---------|---------------|-------|
| `api.partner.com` | Partner integration | - | - |
"""


@pytest.fixture
def registry_file(sample_registry: str) -> Path:
    """Create temp EXTERNAL_APIS.md file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_registry)
        return Path(f.name)


@pytest.fixture
def code_directory_matching() -> Path:
    """Create temp directory with matching dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        code_dir = Path(tmpdir)

        # Python file with matching dependencies
        (code_dir / "client.py").write_text(
            '''"""Client module."""
import os
import stripe
import boto3

API_KEY = os.getenv("STRIPE_API_KEY")
DB = os.environ.get("DATABASE_URL")
'''
        )

        # File with matching URL
        (code_dir / "partner.py").write_text(
            '''"""Partner integration."""
PARTNER_URL = "https://api.partner.com/v2/orders"
'''
        )

        yield code_dir


@pytest.fixture
def code_directory_with_gaps() -> Path:
    """Create temp directory with unregistered dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        code_dir = Path(tmpdir)

        # Python file with unregistered env var
        (code_dir / "service.py").write_text(
            '''"""Service module."""
import os
import requests  # Not registered

UNKNOWN_API = os.getenv("UNKNOWN_SERVICE_URL")  # Not registered
'''
        )

        # File with unregistered URL
        (code_dir / "external.py").write_text(
            '''"""External calls."""
UNKNOWN_URL = "https://api.unknown.com/endpoint"
'''
        )

        yield code_dir


class TestDependencyGap:
    """Tests for DependencyGap dataclass."""

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        gap = DependencyGap(
            gap_type="unregistered",
            dep_type="env_var",
            name="UNKNOWN_KEY",
            location="service.py:10",
        )
        result = gap.to_dict()

        assert result["gap_type"] == "unregistered"
        assert result["dep_type"] == "env_var"
        assert result["name"] == "UNKNOWN_KEY"
        assert result["location"] == "service.py:10"


class TestLinkReport:
    """Tests for LinkReport class."""

    def test_total_gaps(self) -> None:
        """Test total gaps calculation."""
        report = LinkReport()
        report.unregistered.append(DependencyGap("unregistered", "env_var", "A"))
        report.stale.append(DependencyGap("stale", "api_client", "B"))

        assert report.total_gaps == 2

    def test_to_markdown_no_gaps(self) -> None:
        """Test markdown with no gaps."""
        report = LinkReport(
            matched=["stripe", "boto3"],
            registry_count=2,
            detected_count=2,
        )
        markdown = report.to_markdown()

        assert "All dependencies are registered" in markdown
        assert "Matched: 2" in markdown

    def test_to_markdown_with_gaps(self) -> None:
        """Test markdown with gaps."""
        report = LinkReport()
        report.unregistered.append(
            DependencyGap("unregistered", "env_var", "UNKNOWN", "service.py:5")
        )
        report.stale.append(DependencyGap("stale", "api_client", "old_lib"))

        markdown = report.to_markdown()

        assert "Unregistered Dependencies" in markdown
        assert "UNKNOWN" in markdown
        assert "Stale Registry Entries" in markdown
        assert "old_lib" in markdown


class TestParseRegistry:
    """Tests for parse_registry function."""

    def test_parse_valid_registry(self, registry_file: Path) -> None:
        """Test parsing valid EXTERNAL_APIS.md."""
        registry = parse_registry(registry_file)

        assert "STRIPE_API_KEY" in registry["env_vars"]
        assert "DATABASE_URL" in registry["env_vars"]
        assert "stripe" in registry["api_clients"]
        assert "boto3" in registry["api_clients"]
        assert "api.partner.com" in registry["urls"]

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing nonexistent file."""
        registry = parse_registry(Path("/nonexistent.md"))

        assert len(registry["env_vars"]) == 0
        assert len(registry["api_clients"]) == 0
        assert len(registry["urls"]) == 0


class TestLinkDependencies:
    """Tests for link_dependencies function."""

    def test_all_matched(
        self,
        registry_file: Path,
        code_directory_matching: Path,
    ) -> None:
        """Test when all deps are matched."""
        report = link_dependencies(registry_file, code_directory_matching)

        # Should have matches for stripe, boto3, STRIPE_API_KEY, DATABASE_URL, api.partner.com
        assert len(report.matched) >= 3
        assert "stripe" in report.matched
        assert "boto3" in report.matched

    def test_detects_unregistered(
        self,
        registry_file: Path,
        code_directory_with_gaps: Path,
    ) -> None:
        """Test detecting unregistered dependencies."""
        report = link_dependencies(registry_file, code_directory_with_gaps)

        # Should find unregistered: requests, UNKNOWN_SERVICE_URL, api.unknown.com
        unregistered_names = [g.name for g in report.unregistered]
        assert (
            "requests" in unregistered_names
            or "UNKNOWN_SERVICE_URL" in unregistered_names
        )

    def test_detects_stale(
        self,
        registry_file: Path,
        code_directory_with_gaps: Path,
    ) -> None:
        """Test detecting stale registry entries."""
        report = link_dependencies(registry_file, code_directory_with_gaps)

        # stripe, boto3, etc. should be stale (in registry but not in code)
        stale_names = [g.name for g in report.stale]
        assert "stripe" in stale_names
        assert "boto3" in stale_names

    def test_handles_missing_registry(
        self,
        code_directory_matching: Path,
    ) -> None:
        """Test handling missing registry file."""
        report = link_dependencies("/nonexistent.md", code_directory_matching)

        # All detected should be unregistered
        assert report.registry_count == 0
        assert len(report.unregistered) > 0


class TestValidateExternalDeps:
    """Tests for validate_external_deps function."""

    def test_generates_report(
        self,
        registry_file: Path,
        code_directory_matching: Path,
    ) -> None:
        """Test generating validation report."""
        result = validate_external_deps(
            str(registry_file), str(code_directory_matching)
        )

        assert "Generated:" in result
        assert "External Dependency Link Report" in result


class TestGetUnregisteredDeps:
    """Tests for get_unregistered_deps function."""

    def test_lists_detected(self, code_directory_matching: Path) -> None:
        """Test listing detected dependencies."""
        result = get_unregistered_deps(str(code_directory_matching))

        assert "Detected External Dependencies" in result
        assert "STRIPE_API_KEY" in result or "stripe" in result

    def test_empty_directory(self) -> None:
        """Test with empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_unregistered_deps(tmpdir)
            assert "No external dependencies detected" in result
