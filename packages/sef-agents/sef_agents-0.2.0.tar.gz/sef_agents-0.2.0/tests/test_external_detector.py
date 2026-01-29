"""Tests for external dependency detector.

Real execution tests - no mocking of the unit under test.
"""

import tempfile
from pathlib import Path


from sef_agents.tools.external_detector import (
    ExternalDependency,
    ScanResult,
    _scan_file_for_api_clients,
    _scan_file_for_env_vars,
    _scan_file_for_urls,
    generate_codemap_section,
    scan_directory,
)


class TestScanFileForEnvVars:
    """Tests for environment variable detection."""

    def test_detects_getenv_api_url(self) -> None:
        """Detect os.getenv with API URL pattern."""
        content = """
import os
api_url = os.getenv("PAYMENT_API_URL")
"""
        result = _scan_file_for_env_vars(Path("test.py"), content)

        assert len(result) == 1
        assert result[0].name == "PAYMENT_API_URL"
        assert result[0].dep_type == "env_var"

    def test_detects_environ_bracket(self) -> None:
        """Detect os.environ[] with endpoint pattern."""
        content = """
import os
endpoint = os.environ["STRIPE_API_ENDPOINT"]
"""
        result = _scan_file_for_env_vars(Path("test.py"), content)

        assert len(result) == 1
        assert result[0].name == "STRIPE_API_ENDPOINT"

    def test_detects_environ_get(self) -> None:
        """Detect os.environ.get() pattern."""
        content = """
host = os.environ.get("AUTH_SERVICE_HOST")
"""
        result = _scan_file_for_env_vars(Path("test.py"), content)

        assert len(result) == 1
        assert result[0].name == "AUTH_SERVICE_HOST"

    def test_ignores_non_endpoint_vars(self) -> None:
        """Ignore env vars that don't match endpoint patterns."""
        content = """
debug = os.getenv("DEBUG")
log_level = os.getenv("LOG_LEVEL")
"""
        result = _scan_file_for_env_vars(Path("test.py"), content)

        assert len(result) == 0

    def test_deduplicates_same_var(self) -> None:
        """Same var used multiple times should appear once."""
        content = """
url1 = os.getenv("PAYMENT_API_URL")
url2 = os.getenv("PAYMENT_API_URL")
"""
        result = _scan_file_for_env_vars(Path("test.py"), content)

        assert len(result) == 1


class TestScanFileForApiClients:
    """Tests for API client library detection."""

    def test_detects_stripe_import(self) -> None:
        """Detect stripe library import."""
        content = """
import stripe

stripe.api_key = "sk_test"  # pragma: allowlist secret
"""
        result = _scan_file_for_api_clients(Path("test.py"), content)

        assert len(result) == 1
        assert result[0].name == "stripe"
        assert result[0].dep_type == "api_client"
        assert "Payment" in result[0].description

    def test_detects_boto3_import(self) -> None:
        """Detect boto3 AWS library."""
        content = """
import boto3

s3 = boto3.client("s3")
"""
        result = _scan_file_for_api_clients(Path("test.py"), content)

        assert len(result) == 1
        assert result[0].name == "boto3"
        assert "AWS" in result[0].description

    def test_detects_from_import(self) -> None:
        """Detect from X import Y pattern."""
        content = """
from twilio.rest import Client
"""
        result = _scan_file_for_api_clients(Path("test.py"), content)

        assert len(result) == 1
        assert result[0].name == "twilio"

    def test_detects_requests_as_external(self) -> None:
        """Detect requests library as external HTTP client."""
        content = """
import requests

response = requests.get("https://api.example.com")
"""
        result = _scan_file_for_api_clients(Path("test.py"), content)

        assert len(result) == 1
        assert result[0].name == "requests"

    def test_ignores_stdlib_imports(self) -> None:
        """Ignore standard library imports."""
        content = """
import os
import json
from pathlib import Path
"""
        result = _scan_file_for_api_clients(Path("test.py"), content)

        assert len(result) == 0


class TestScanFileForUrls:
    """Tests for URL detection."""

    def test_detects_https_url(self) -> None:
        """Detect HTTPS URLs."""
        content = """
API_URL = "https://api.stripe.com/v1/charges"
"""
        result = _scan_file_for_urls(Path("test.py"), content)

        assert len(result) == 1
        assert "api.stripe.com" in result[0].name

    def test_ignores_localhost(self) -> None:
        """Ignore localhost URLs."""
        content = """
url = "http://localhost:8000/api"
url2 = "http://127.0.0.1:3000"
"""
        result = _scan_file_for_urls(Path("test.py"), content)

        assert len(result) == 0

    def test_extracts_domain(self) -> None:
        """Extract domain from full URL."""
        content = """
endpoint = "https://payments.example.com/api/v2/charge"
"""
        result = _scan_file_for_urls(Path("test.py"), content)

        assert len(result) == 1
        assert result[0].name == "payments.example.com"

    def test_deduplicates_same_domain(self) -> None:
        """Same domain in multiple URLs appears once."""
        content = """
url1 = "https://api.example.com/users"
url2 = "https://api.example.com/orders"
"""
        result = _scan_file_for_urls(Path("test.py"), content)

        assert len(result) == 1


class TestScanDirectory:
    """Tests for directory scanning."""

    def test_scans_python_files(self) -> None:
        """Scan all Python files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "app.py"
            test_file.write_text("""
import stripe
url = os.getenv("PAYMENT_API_URL")
""")

            result = scan_directory(tmpdir)

            assert result.files_scanned == 1
            assert len(result.dependencies) >= 1

    def test_skips_pycache(self) -> None:
        """Skip __pycache__ directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create __pycache__ with Python file
            cache_dir = Path(tmpdir) / "__pycache__"
            cache_dir.mkdir()
            (cache_dir / "module.cpython-312.pyc").write_text("fake")

            # Create real Python file
            (Path(tmpdir) / "app.py").write_text("x = 1")

            result = scan_directory(tmpdir)

            assert result.files_scanned == 1

    def test_handles_missing_directory(self) -> None:
        """Handle non-existent directory gracefully."""
        result = scan_directory("/nonexistent/path")

        assert result.files_scanned == 0
        assert len(result.errors) == 1


class TestGenerateCodemapSection:
    """Tests for CODE_MAP section generation."""

    def test_generates_empty_section(self) -> None:
        """Generate section for no dependencies."""
        result = ScanResult()

        output = generate_codemap_section(result)

        assert "No external dependencies detected" in output

    def test_generates_env_var_section(self) -> None:
        """Generate section with env vars."""
        result = ScanResult(
            dependencies=[
                ExternalDependency(
                    name="PAYMENT_API_URL",
                    dep_type="env_var",
                    source_file="app.py",
                    line_number=10,
                )
            ]
        )

        output = generate_codemap_section(result)

        assert "PAYMENT_API_URL" in output
        assert "Environment Variables" in output

    def test_generates_api_client_section(self) -> None:
        """Generate section with API clients."""
        result = ScanResult(
            dependencies=[
                ExternalDependency(
                    name="stripe",
                    dep_type="api_client",
                    source_file="payment.py",
                    description="Stripe Payment API",
                )
            ]
        )

        output = generate_codemap_section(result)

        assert "stripe" in output
        assert "External API Clients" in output

    def test_generates_url_section_with_warning(self) -> None:
        """Generate URL section with env var warning."""
        result = ScanResult(
            dependencies=[
                ExternalDependency(
                    name="api.example.com",
                    dep_type="url",
                    source_file="client.py",
                )
            ]
        )

        output = generate_codemap_section(result)

        assert "api.example.com" in output
        assert "Consider using env var" in output


class TestScanResultProperties:
    """Tests for ScanResult helper properties."""

    def test_filters_by_type(self) -> None:
        """Filter dependencies by type."""
        result = ScanResult(
            dependencies=[
                ExternalDependency(name="VAR", dep_type="env_var", source_file="a.py"),
                ExternalDependency(
                    name="stripe", dep_type="api_client", source_file="b.py"
                ),
                ExternalDependency(
                    name="example.com", dep_type="url", source_file="c.py"
                ),
            ]
        )

        assert len(result.env_vars) == 1
        assert len(result.api_clients) == 1
        assert len(result.urls) == 1
