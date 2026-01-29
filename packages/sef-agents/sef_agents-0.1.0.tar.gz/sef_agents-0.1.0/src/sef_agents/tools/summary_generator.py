"""Executive Summary Generator for SEF Dashboard.

Aggregates metrics from security scans, debt scans, and compliance checks
to generate sef-reports/executive-summary.json for dashboard consumption.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import structlog

from sef_agents.tools.debt_scanner import get_cached_debt_count

logger = structlog.get_logger(__name__)


class ExecutiveSummary(TypedDict):
    """Schema for executive-summary.json."""

    generated_at: str
    score: float
    critical_issues: int
    debt_count: int
    security_passed: bool
    compliance_passed: bool


def _find_latest_security_report(base_dir: Path) -> Path | None:
    """Find the most recent security audit report.

    Args:
        base_dir: Base directory containing sef-reports.

    Returns:
        Path to latest security report or None if not found.
    """
    security_dir = base_dir / "sef-reports" / "security"
    if not security_dir.exists():
        return None

    reports = list(security_dir.glob("security_audit_*.md"))
    if not reports:
        return None

    # Sort by modification time, newest first
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0]


def _parse_security_report(report_path: Path) -> tuple[bool, int]:
    """Parse security report to extract pass/fail status and critical issues.

    Args:
        report_path: Path to security audit markdown file.

    Returns:
        Tuple of (security_passed, critical_issues_count).
    """
    try:
        content = report_path.read_text(encoding="utf-8")

        # Check for overall status
        security_passed = "OVERALL: ✅ PASSED" in content

        # Count critical issues (❌ FAIL lines, not FAILED overall status)
        fail_pattern = re.compile(r"❌\s*FAIL\b(?!ED)")
        critical_issues = len(fail_pattern.findall(content))

        return security_passed, critical_issues

    except OSError as e:
        logger.warning(
            "Failed to parse security report", path=str(report_path), error=str(e)
        )
        return True, 0  # Default to passed if can't read


def _get_debt_count(directory: Path) -> int:
    """Get technical debt item count from cache (non-blocking).

    Reads from existing cache. Returns 0 if no cache exists.
    Does NOT trigger a new scan - use scan_debt() separately.

    Args:
        directory: Directory containing .sef cache.

    Returns:
        Number of debt items in cache, or 0 if no cache.
    """
    # Try to read from cache first (instant, non-blocking)
    cached_count = get_cached_debt_count(directory)
    if cached_count is not None:
        logger.info("debt_count_from_cache", count=cached_count)
        return cached_count

    # No cache exists - return 0 (user should run scan_debt first)
    logger.info("no_debt_cache", directory=str(directory))
    return 0


def _check_compliance(base_dir: Path) -> bool:
    """Check if compliance reports indicate passing status.

    Args:
        base_dir: Base directory containing sef-reports.

    Returns:
        True if compliance passed or no compliance reports exist.
    """
    reports_dir = base_dir / "sef-reports"
    if not reports_dir.exists():
        return True

    # Look for compliance reports in any agent directory
    compliance_files = list(reports_dir.glob("*/compliance_*.md"))
    if not compliance_files:
        return True  # No compliance reports = passed

    # Check latest compliance report
    compliance_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest = compliance_files[0]

    try:
        content = latest.read_text(encoding="utf-8")
        # If "Issues Found" appears, compliance failed
        return "⚠️ Issues Found" not in content
    except OSError:
        return True


def _calculate_score(
    security_passed: bool,
    critical_issues: int,
    debt_count: int,
    compliance_passed: bool,
) -> float:
    """Calculate project health score from metrics.

    Args:
        security_passed: Whether security audit passed.
        critical_issues: Number of critical security issues.
        debt_count: Number of technical debt items.
        compliance_passed: Whether compliance checks passed.

    Returns:
        Score from 0.0 to 100.0.
    """
    score = 100.0

    # Security failures
    if not security_passed:
        score -= 20.0
    score -= min(critical_issues * 10.0, 30.0)

    # Technical debt penalty (capped)
    score -= min(debt_count * 2.0, 30.0)

    # Compliance failure
    if not compliance_passed:
        score -= 10.0

    return max(0.0, min(100.0, score))


def generate_executive_summary(directory: str = "") -> ExecutiveSummary:
    """Generate executive summary by aggregating all metrics.

    Args:
        directory: Base directory to scan. Defaults to project_root if set,
                   otherwise current working directory.

    Returns:
        ExecutiveSummary dictionary with all metrics.
    """
    if directory:
        base_dir = Path(directory)
    else:
        from sef_agents.session import SessionManager

        session = SessionManager.get()
        base_dir = session.project_root or Path.cwd()

    security_report = _find_latest_security_report(base_dir)
    if security_report:
        security_passed, critical_issues = _parse_security_report(security_report)
    else:
        security_passed = True
        critical_issues = 0

    src_dir = base_dir / "src"
    scan_dir = src_dir if src_dir.exists() else base_dir
    debt_count = _get_debt_count(scan_dir)

    compliance_passed = _check_compliance(base_dir)

    # Calculate score
    score = _calculate_score(
        security_passed, critical_issues, debt_count, compliance_passed
    )

    return ExecutiveSummary(
        generated_at=datetime.now().isoformat(),
        score=round(score, 1),
        critical_issues=critical_issues,
        debt_count=debt_count,
        security_passed=security_passed,
        compliance_passed=compliance_passed,
    )


def write_executive_summary(directory: str = "") -> Path:
    """Generate and write executive-summary.json to sef-reports/.

    Args:
        directory: Base directory. Defaults to project_root if set,
                   otherwise current working directory.

    Returns:
        Path to written executive-summary.json.

    Raises:
        OSError: If file cannot be written.
    """
    if directory:
        base_dir = Path(directory)
    else:
        from sef_agents.session import SessionManager

        session = SessionManager.get()
        base_dir = session.project_root or Path.cwd()
    summary = generate_executive_summary(directory)

    output_dir = base_dir / "sef-reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "executive-summary.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    logger.info(
        "executive_summary_written",
        path=str(output_path),
        score=summary["score"],
        debt_count=summary["debt_count"],
    )

    return output_path


def generate_project_summary_tool(directory: str = "") -> str:
    """MCP tool wrapper for generating executive summary.

    Args:
        directory: Base directory to scan. Empty string for current directory.

    Returns:
        Status message with path to generated file.
    """
    try:
        output_path = write_executive_summary(directory)
        summary = generate_executive_summary(directory)

        return (
            f"Executive summary generated: `{output_path}`\n\n"
            f"**Metrics:**\n"
            f"- Score: {summary['score']}/100\n"
            f"- Critical Issues: {summary['critical_issues']}\n"
            f"- Tech Debt Items: {summary['debt_count']}\n"
            f"- Security: {'✅ Passed' if summary['security_passed'] else '❌ Failed'}\n"
            f"- Compliance: {'✅ Passed' if summary['compliance_passed'] else '❌ Failed'}"
        )
    except OSError as e:
        return f"Error generating summary: {e}"
