"""Security Audit Tool - MCP wrapper for security scanning.

Generates sef-reports/security/security_audit_{date}.md
"""

from pathlib import Path

import structlog

from sef_agents.session import SessionManager
from sef_agents.security.network_scan import scan_network_imports
from sef_agents.security.url_scan import scan_urls
from sef_agents.security.secret_scan import scan_secrets
from sef_agents.security.dependency_audit import audit_dependencies
from sef_agents.security.file_audit import audit_file_operations
from sef_agents.security.report_generator import SecurityReport, save_report
from datetime import datetime

logger = structlog.get_logger(__name__)


def run_security_audit(directory: str = "") -> str:
    """Run security audit and generate report.

    Args:
        directory: Directory to scan. Defaults to project root.

    Returns:
        Summary with report path.
    """
    # Resolve directory
    if directory:
        scan_dir = Path(directory).resolve()
    else:
        session = SessionManager.get()
        scan_dir = session.project_root or Path.cwd()

    if not scan_dir.exists():
        return f"❌ Directory not found: {scan_dir}"

    # Find src directory if exists
    src_dir = scan_dir / "src"
    if not src_dir.exists():
        src_dir = scan_dir

    results = []
    results.append(f"# Security Audit: {scan_dir.name}")
    results.append(f"**Scanning:** `{scan_dir}`\n")

    # Run all scans
    try:
        # 1. Network Import Scan
        network_result = scan_network_imports(src_dir)
        status = "✅ PASS" if network_result.passed else "❌ FAIL"
        results.append(f"1. Network Import Scan: {status}")

        # 2. URL Scan
        url_result = scan_urls(scan_dir)
        status = "✅ PASS" if url_result.passed else "❌ FAIL"
        results.append(f"2. Outbound URL Scan: {status}")

        # 3. Secret Scan
        secret_result = scan_secrets(scan_dir)
        status = "✅ PASS" if secret_result.passed else "❌ FAIL"
        results.append(f"3. Secret Detection: {status}")

        # 4. Dependency Audit
        dependency_result = audit_dependencies(scan_dir)
        status = "✅ PASS" if dependency_result.passed else "❌ FAIL"
        results.append(f"4. Dependency Audit: {status}")

        # 5. File Operation Audit
        file_result = audit_file_operations(src_dir)
        status = "✅ PASS" if file_result.passed else "❌ FAIL"
        results.append(f"5. File Operation Audit: {status}")

        # Generate report
        report = SecurityReport(
            network_result=network_result,
            url_result=url_result,
            secret_result=secret_result,
            dependency_result=dependency_result,
            file_result=file_result,
            generated_at=datetime.now(),
        )

        # Save report to sef-reports/security/
        output_dir = scan_dir / "sef-reports" / "security"
        report_path = save_report(report, output_dir)

        results.append("")
        overall = "✅ PASSED" if report.overall_passed else "❌ FAILED"
        results.append(f"**Overall Status:** {overall}")
        results.append(f"**Report saved:** `{report_path}`")

        logger.info(
            "security_audit_complete",
            path=str(report_path),
            passed=report.overall_passed,
        )

        return "\n".join(results)

    except OSError as e:
        logger.error("security_audit_failed", error=str(e))
        return f"❌ Security audit failed: {e}"
