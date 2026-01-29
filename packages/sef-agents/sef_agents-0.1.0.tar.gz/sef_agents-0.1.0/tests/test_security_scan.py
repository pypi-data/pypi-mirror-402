"""Tests for the SEF Agents Security Scanner."""

from pathlib import Path


from sef_agents.security.network_scan import scan_network_imports, FORBIDDEN_IMPORTS
from sef_agents.security.url_scan import scan_urls
from sef_agents.security.secret_scan import scan_secrets
from sef_agents.security.file_audit import audit_file_operations
from sef_agents.security.dependency_audit import audit_dependencies
from sef_agents.security.report_generator import SecurityReport, generate_report

from datetime import datetime


class TestNetworkScan:
    """Tests for network import scanning."""

    def test_clean_file_passes(self, tmp_path: Path) -> None:
        """A file with no network imports should pass."""
        (tmp_path / "clean.py").write_text(
            "import os\nimport json\nfrom pathlib import Path\n"
        )
        result = scan_network_imports(tmp_path)
        assert result.passed
        assert result.files_scanned == 1
        assert len(result.violations) == 0

    def test_requests_import_fails(self, tmp_path: Path) -> None:
        """A file importing requests should fail."""
        (tmp_path / "network.py").write_text("import requests\n")
        result = scan_network_imports(tmp_path)
        assert not result.passed
        assert len(result.violations) == 1
        assert result.violations[0]["matched"] == "requests"

    def test_httpx_import_fails(self, tmp_path: Path) -> None:
        """A file importing httpx should fail."""
        (tmp_path / "http.py").write_text("import httpx\n")
        result = scan_network_imports(tmp_path)
        assert not result.passed
        assert result.violations[0]["matched"] == "httpx"

    def test_from_import_fails(self, tmp_path: Path) -> None:
        """From imports of network libraries should fail."""
        (tmp_path / "client.py").write_text("from urllib.request import urlopen\n")
        result = scan_network_imports(tmp_path)
        assert not result.passed

    def test_forbidden_imports_list(self) -> None:
        """Verify expected libraries are in forbidden list."""
        expected = {"requests", "httpx", "aiohttp", "urllib", "socket"}
        assert expected.issubset(FORBIDDEN_IMPORTS)


class TestURLScan:
    """Tests for URL scanning."""

    def test_no_urls_passes(self, tmp_path: Path) -> None:
        """A file with no URLs should pass."""
        (tmp_path / "clean.py").write_text("x = 'hello world'\n")
        result = scan_urls(tmp_path)
        assert result.passed
        assert len(result.external_urls) == 0

    def test_localhost_whitelisted(self, tmp_path: Path) -> None:
        """Localhost URLs should be whitelisted."""
        (tmp_path / "local.py").write_text('url = "http://localhost:8000"\n')
        result = scan_urls(tmp_path)
        assert result.passed
        assert len(result.whitelisted_urls) == 1

    def test_external_url_fails(self, tmp_path: Path) -> None:
        """External URLs should fail (if not whitelisted)."""
        (tmp_path / "external.py").write_text(
            'url = "https://malicious-site.xyz/exfiltrate"\n'
        )
        result = scan_urls(tmp_path)
        assert not result.passed
        assert len(result.external_urls) == 1

    def test_github_whitelisted(self, tmp_path: Path) -> None:
        """GitHub URLs in docs should be whitelisted."""
        (tmp_path / "readme.md").write_text("See https://github.com/org/repo\n")
        result = scan_urls(tmp_path)
        assert result.passed


class TestSecretScan:
    """Tests for secret detection."""

    def test_no_secrets_passes(self, tmp_path: Path) -> None:
        """A file with no secrets should pass."""
        (tmp_path / "clean.py").write_text("x = 123\nname = 'test'\n")
        result = scan_secrets(tmp_path)
        assert result.passed

    def test_api_key_detected(self, tmp_path: Path) -> None:
        """Hardcoded API keys should be detected."""
        (tmp_path / "config.py").write_text(
            'API_KEY = "sk-abcdefghijklmnopqrstuvwxyz123456"  # pragma: allowlist secret\n'
        )
        result = scan_secrets(tmp_path)
        assert not result.passed
        assert len(result.secrets_found) >= 1

    def test_example_key_skipped(self, tmp_path: Path) -> None:
        """Example/placeholder keys should be skipped as false positives."""
        (tmp_path / "docs.py").write_text(
            'API_KEY = "your_api_key_here"  # pragma: allowlist secret\n'
        )
        result = scan_secrets(tmp_path)
        assert result.passed

    def test_github_token_detected(self, tmp_path: Path) -> None:
        """GitHub tokens should be detected."""
        # Use a realistic-looking fake token (not repeating chars which trigger false positive filter)
        (tmp_path / "auth.py").write_text(
            'token = "ghp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"  # pragma: allowlist secret\n'
        )
        result = scan_secrets(tmp_path)
        assert not result.passed


class TestFileAudit:
    """Tests for file operation auditing."""

    def test_safe_operations_pass(self, tmp_path: Path) -> None:
        """Safe file operations should pass."""
        (tmp_path / "safe.py").write_text(
            """
from pathlib import Path
p = Path('test.txt')
content = p.read_text()
"""
        )
        result = audit_file_operations(tmp_path)
        assert result.passed
        assert len(result.operations) > 0

    def test_dangerous_eval_detected(self, tmp_path: Path) -> None:
        """Dangerous operations like eval should be detected."""
        (tmp_path / "danger.py").write_text("result = eval(user_input)\n")
        result = audit_file_operations(tmp_path)
        assert not result.passed
        assert len(result.dangerous_operations) == 1


class TestDependencyAudit:
    """Tests for dependency auditing."""

    def test_missing_pyproject_handled(self, tmp_path: Path) -> None:
        """Missing pyproject.toml should be handled gracefully."""
        result = audit_dependencies(tmp_path)
        assert result.passed
        assert "pyproject.toml not found" in result.parse_errors

    def test_pyproject_parsed(self, tmp_path: Path) -> None:
        """pyproject.toml should be parsed correctly."""
        (tmp_path / "pyproject.toml").write_text(
            """
[project]
name = "test"
dependencies = [
    "requests>=2.0",
    "structlog>=25.0",
]
"""
        )
        result = audit_dependencies(tmp_path)
        # May pass or fail depending on installed packages
        assert len(result.parse_errors) == 0


class TestReportGenerator:
    """Tests for report generation."""

    def test_report_generation(self, tmp_path: Path) -> None:
        """Test that report can be generated."""
        from sef_agents.security.network_scan import NetworkScanResult
        from sef_agents.security.url_scan import URLScanResult
        from sef_agents.security.secret_scan import SecretScanResult
        from sef_agents.security.dependency_audit import DependencyAuditResult
        from sef_agents.security.file_audit import FileAuditResult

        report = SecurityReport(
            network_result=NetworkScanResult(passed=True, files_scanned=10),
            url_result=URLScanResult(passed=True, files_scanned=10),
            secret_result=SecretScanResult(passed=True, files_scanned=10),
            dependency_result=DependencyAuditResult(passed=True),
            file_result=FileAuditResult(passed=True, files_scanned=10),
            generated_at=datetime.now(),
        )

        md = generate_report(report)
        assert "Security Audit Report" in md
        assert "✅ PASS" in md
        assert "OVERALL: ✅ PASSED" in md

    def test_failed_report(self, tmp_path: Path) -> None:
        """Test report with failures."""
        from sef_agents.security.network_scan import NetworkScanResult
        from sef_agents.security.url_scan import URLScanResult
        from sef_agents.security.secret_scan import SecretScanResult
        from sef_agents.security.dependency_audit import DependencyAuditResult
        from sef_agents.security.file_audit import FileAuditResult

        report = SecurityReport(
            network_result=NetworkScanResult(
                passed=False,
                files_scanned=10,
                violations=[
                    {"file": "test.py", "import": "requests", "matched": "requests"}
                ],
            ),
            url_result=URLScanResult(passed=True, files_scanned=10),
            secret_result=SecretScanResult(passed=True, files_scanned=10),
            dependency_result=DependencyAuditResult(passed=True),
            file_result=FileAuditResult(passed=True, files_scanned=10),
            generated_at=datetime.now(),
        )

        md = generate_report(report)
        assert "❌ FAIL" in md
        assert "requires review" in md.lower() or "issues" in md.lower()


class TestSEFAgentsScan:
    """Integration test: scan the actual SEF Agents codebase."""

    def test_sef_agents_passes_security_scan(self) -> None:
        """SEF Agents itself should pass the security scan."""
        # Find project root
        current = Path(__file__).parent.parent
        src_dir = current / "src"

        # Network scan
        network_result = scan_network_imports(src_dir)
        assert network_result.passed, f"Network violations: {network_result.violations}"

        # Secret scan (only scan src, not tests which contain test data)
        secret_result = scan_secrets(src_dir)
        assert secret_result.passed, f"Secrets found: {secret_result.secrets_found}"

        # File audit
        file_result = audit_file_operations(src_dir)
        assert file_result.passed, f"Dangerous ops: {file_result.dangerous_operations}"
