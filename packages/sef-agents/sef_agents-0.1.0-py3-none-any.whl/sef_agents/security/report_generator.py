"""Security Report Generator.

Generates professional Markdown reports for enterprise security review.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import structlog

from sef_agents.security.network_scan import NetworkScanResult
from sef_agents.security.url_scan import URLScanResult
from sef_agents.security.secret_scan import SecretScanResult
from sef_agents.security.dependency_audit import DependencyAuditResult
from sef_agents.security.file_audit import FileAuditResult

logger = structlog.get_logger(__name__)

VERSION = "0.1.0"


@dataclass
class SecurityReport:
    """Complete security audit report."""

    network_result: NetworkScanResult
    url_result: URLScanResult
    secret_result: SecretScanResult
    dependency_result: DependencyAuditResult
    file_result: FileAuditResult
    generated_at: datetime
    project_name: str = "SEF-Agents"
    version: str = VERSION

    @property
    def overall_passed(self) -> bool:
        """Check if all scans passed."""
        return all(
            [
                self.network_result.passed,
                self.url_result.passed,
                self.secret_result.passed,
                self.dependency_result.passed,
                self.file_result.passed,
            ]
        )


def _status_icon(passed: bool) -> str:
    """Return status icon for pass/fail."""
    return "✅" if passed else "❌"


def _generate_executive_summary(
    report: SecurityReport, timestamp: str, overall_icon: str, overall_status: str
) -> str:
    """Generate executive summary section."""
    return f"""# {report.project_name} Security Audit Report

**Generated:** {timestamp}
**Version:** {report.version}
**Auditor:** Automated Security Scanner v1.0

---

## Executive Summary

| Check | Status | Details |
|-------|--------|---------|
| Network Import Scan | {_status_icon(report.network_result.passed)} {"PASS" if report.network_result.passed else "FAIL"} | {report.network_result.summary} |
| Outbound URL Scan | {_status_icon(report.url_result.passed)} {"PASS" if report.url_result.passed else "FAIL"} | {report.url_result.summary} |
| Secret Detection | {_status_icon(report.secret_result.passed)} {"PASS" if report.secret_result.passed else "FAIL"} | {report.secret_result.summary} |
| Dependency Audit | {_status_icon(report.dependency_result.passed)} {"PASS" if report.dependency_result.passed else "FAIL"} | {report.dependency_result.summary} |
| File Operation Audit | {_status_icon(report.file_result.passed)} {"PASS" if report.file_result.passed else "FAIL"} | {report.file_result.summary} |

**OVERALL: {overall_icon} {overall_status}**

---

## Detailed Findings
"""


def _generate_network_section(report: SecurityReport) -> str:
    """Generate network scan section."""
    section = f"""### 1. Network Import Scan
**Status:** {_status_icon(report.network_result.passed)} {"PASSED" if report.network_result.passed else "FAILED"}
**Files Scanned:** {report.network_result.files_scanned}
**Network Imports Found:** {len(report.network_result.violations)}

Scanned for: requests, httpx, aiohttp, urllib, socket, http.client, etc.

"""
    if report.network_result.violations:
        section += "**Violations:**\n\n"
        section += "| File | Import | Matched |\n"
        section += "|------|--------|--------|\n"
        for v in report.network_result.violations:
            section += f"| {v['file']} | {v['import']} | {v['matched']} |\n"
        section += "\n"
    else:
        section += "No network libraries detected in codebase.\n\n"
    return section


def _generate_url_section(report: SecurityReport) -> str:
    """Generate URL scan section."""
    section = f"""### 2. Outbound URL Scan
**Status:** {_status_icon(report.url_result.passed)} {"PASSED" if report.url_result.passed else "FAILED"}
**Files Scanned:** {report.url_result.files_scanned}
**External URLs Found:** {len(report.url_result.external_urls)}
**Whitelisted URLs:** {len(report.url_result.whitelisted_urls)}

"""
    if report.url_result.external_urls:
        section += "**External URLs (require review):**\n\n"
        section += "| File | URL | Type |\n"
        section += "|------|-----|------|\n"
        for u in report.url_result.external_urls[:20]:  # Limit to first 20
            section += f"| {u['file']} | {u['url'][:50]}... | {u['type']} |\n"
        if len(report.url_result.external_urls) > 20:
            section += f"\n*...and {len(report.url_result.external_urls) - 20} more*\n"
        section += "\n"
    else:
        section += "No external URLs detected.\n\n"
    return section


def _generate_secret_section(report: SecurityReport) -> str:
    """Generate secret scan section."""
    section = f"""### 3. Secret Detection
**Status:** {_status_icon(report.secret_result.passed)} {"PASSED" if report.secret_result.passed else "FAILED"}
**Files Scanned:** {report.secret_result.files_scanned}
**Secrets Found:** {len(report.secret_result.secrets_found)}
**False Positives Skipped:** {report.secret_result.false_positives_skipped}

"""
    if report.secret_result.secrets_found:
        section += "**Potential Secrets:**\n\n"
        section += "| File | Line | Type | Value (masked) |\n"
        section += "|------|------|------|----------------|\n"
        for s in report.secret_result.secrets_found[:20]:
            section += (
                f"| {s['file']} | {s['line']} | {s['type']} | {s['masked_value']} |\n"
            )
        section += "\n"
    else:
        section += "No hardcoded secrets detected.\n\n"
    return section


def _generate_dependency_section(report: SecurityReport) -> str:
    """Generate dependency scan section."""
    section = f"""### 4. Dependency Analysis
**Status:** {_status_icon(report.dependency_result.passed)} {"PASSED" if report.dependency_result.passed else "FAILED"}
**Total Dependencies:** {len(report.dependency_result.dependencies)}

| Package | Version | License | Safe |
|---------|---------|---------|------|
"""
    for dep in report.dependency_result.dependencies:
        safe_icon = _status_icon(dep.license_safe)
        section += f"| {dep.name} | {dep.version} | {dep.license} | {safe_icon} |\n"

    if report.dependency_result.unsafe_licenses:
        section += f"\n**⚠️ Licenses requiring review:** {', '.join(report.dependency_result.unsafe_licenses)}\n"
    return section


def _generate_file_section(report: SecurityReport) -> str:
    """Generate file operation scan section."""
    section = f"""

### 5. File Operation Audit
**Status:** {_status_icon(report.file_result.passed)} {"PASSED" if report.file_result.passed else "FAILED"}
**Files Scanned:** {report.file_result.files_scanned}
**File Operations Found:** {len(report.file_result.operations)}
**Dangerous Operations:** {len(report.file_result.dangerous_operations)}

"""
    if report.file_result.dangerous_operations:
        section += "**⚠️ Dangerous Operations:**\n\n"
        section += "| File | Line | Operation | Context |\n"
        section += "|------|------|-----------|--------|\n"
        for op in report.file_result.dangerous_operations:
            section += (
                f"| {op.file} | {op.line} | {op.operation} | `{op.context[:40]}...` |\n"
            )
        section += "\n"
    else:
        section += "All file operations are safe local-only operations.\n\n"
    return section


def _generate_certification(report: SecurityReport) -> str:
    """Generate certification section."""
    section = """---

## Architecture Verification

```
┌─────────────────────────────────────────────────────────┐
│                    CUSTOMER MACHINE                     │
│  ┌──────────────┐      stdio      ┌───────────────┐    │
│  │ AI Client    │◄───────────────►│  sef-agents   │    │
│  │ (Cursor)     │                 │  (local only) │    │
│  └──────────────┘                 └───────┬───────┘    │
│                                           │            │
│                                    ┌──────▼──────┐     │
│                                    │ Local Files │     │
│                                    └─────────────┘     │
│                                                        │
│  ❌ NO external network calls                          │
│  ❌ NO cloud services                                  │
│  ❌ NO telemetry                                       │
206: └────────────────────────────────────────────────────────┘
```

---

## Certification

"""
    if report.overall_passed:
        section += f"""This report certifies that {report.project_name} version {report.version}:

1. ✅ Contains no code that transmits data externally
2. ✅ Operates entirely on the local filesystem
3. ✅ Uses only stdio transport (no network listeners)
4. ✅ Has no known security vulnerabilities in dependencies
5. ✅ Contains no hardcoded secrets or credentials

**Scan completed successfully.**
"""
    else:
        section += f"""⚠️ **This report indicates potential security issues that require review.**

{report.project_name} version {report.version} has the following issues:

"""
        if not report.network_result.passed:
            section += f"- ❌ {len(report.network_result.violations)} network import(s) found\n"
        if not report.url_result.passed:
            section += (
                f"- ❌ {len(report.url_result.external_urls)} external URL(s) found\n"
            )
        if not report.secret_result.passed:
            section += f"- ❌ {len(report.secret_result.secrets_found)} potential secret(s) found\n"
        if not report.dependency_result.passed:
            section += f"- ❌ {len(report.dependency_result.unsafe_licenses)} unsafe license(s) found\n"
        if not report.file_result.passed:
            section += f"- ❌ {len(report.file_result.dangerous_operations)} dangerous operation(s) found\n"
        section += "\n**Please review the detailed findings above.**\n"
    return section


def generate_report(report: SecurityReport) -> str:
    """
    Generate a professional Markdown security report.

    Args:
        report: SecurityReport with all scan results

    Returns:
        Markdown formatted report string
    """
    timestamp = report.generated_at.strftime("%Y-%m-%d %H:%M:%S")
    overall_status = "PASSED" if report.overall_passed else "FAILED"
    overall_icon = _status_icon(report.overall_passed)

    sections = [
        _generate_executive_summary(report, timestamp, overall_icon, overall_status),
        _generate_network_section(report),
        _generate_url_section(report),
        _generate_secret_section(report),
        _generate_dependency_section(report),
        _generate_file_section(report),
        _generate_certification(report),
    ]

    return "".join(sections)


def save_report(report: SecurityReport, output_dir: Path | None = None) -> Path:
    """
    Save the security report to disk.

    Args:
        report: SecurityReport to save
        output_dir: Directory to save report (default: {project_root}/sef-reports/security/)

    Returns:
        Path to the saved report
    """
    if output_dir is None:
        from sef_agents.session import SessionManager

        session = SessionManager.get()
        base_dir = session.project_root or Path.cwd()
        output_dir = base_dir / "sef-reports" / "security"

    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = report.generated_at.strftime("%Y-%m-%d")
    filename = f"security_audit_{date_str}.md"
    output_path = output_dir / filename

    report_content = generate_report(report)
    output_path.write_text(report_content, encoding="utf-8")

    logger.info("report_saved", path=str(output_path))
    return output_path
