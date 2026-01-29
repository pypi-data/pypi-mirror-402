"""SEF Agents Security Scanner CLI.

A single command that runs all security checks and produces a professional
security audit report for enterprise customers.

Usage:
    uv run python -m sef_agents.security_scan
    uv run python -m sef_agents.security_scan --verbose
    uv run python -m sef_agents.security_scan --format json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import structlog

from sef_agents.constants import Icons, Status
from sef_agents.security.network_scan import scan_network_imports
from sef_agents.security.url_scan import scan_urls
from sef_agents.security.secret_scan import scan_secrets
from sef_agents.security.dependency_audit import audit_dependencies
from sef_agents.security.file_audit import audit_file_operations
from sef_agents.security.report_generator import SecurityReport, save_report

# Configure structlog for CLI output
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger(__name__)


def echo(message: str = "") -> None:
    """Write message to stdout for CLI output.

    Args:
        message: Text to display. Empty string prints blank line.
    """
    sys.stdout.write(message + "\n")
    sys.stdout.flush()


def print_status(check_num: int, total: int, name: str, passed: bool) -> None:
    """Print formatted status line to stdout."""
    status = Status.PASS if passed else Status.FAIL
    dots = "." * (30 - len(name))
    echo(f"[{check_num}/{total}] {name}{dots} {status}")


def run_security_scan(
    directory: Path,
    verbose: bool = False,
    output_format: str = "text",
    no_report: bool = False,
) -> bool:
    """
    Run all security scans and generate report.

    Args:
        directory: Root directory to scan
        verbose: Print detailed output
        output_format: Output format (text, json, markdown)
        no_report: If True, skip saving report to disk

    Returns:
        True if all scans passed, False otherwise
    """
    echo(Icons.HEAVY_LINE * 60)
    echo("          SEF-AGENTS SECURITY AUDIT")
    echo(Icons.HEAVY_LINE * 60)
    echo()
    echo(f"Scanning: {directory}")
    echo(f"Started:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    echo()

    # Run all scans
    src_dir = directory / "src"
    if not src_dir.exists():
        src_dir = directory

    # 1. Network Import Scan
    if verbose:
        echo("Running network import scan...")
    network_result = scan_network_imports(src_dir)
    print_status(1, 6, "Network Import Scan", network_result.passed)

    # 2. URL Scan
    if verbose:
        echo("Running URL scan...")
    url_result = scan_urls(directory)
    print_status(2, 6, "Outbound URL Scan", url_result.passed)

    # 3. Secret Scan
    if verbose:
        echo("Running secret scan...")
    secret_result = scan_secrets(directory)
    print_status(3, 6, "Secret Detection", secret_result.passed)

    # 4. Dependency Audit
    if verbose:
        echo("Running dependency audit...")
    dependency_result = audit_dependencies(directory)
    print_status(4, 6, "Dependency Audit", dependency_result.passed)

    # 5. License Check (part of dependency audit)
    license_passed = len(dependency_result.unsafe_licenses) == 0
    print_status(5, 6, "License Check", license_passed)

    # 6. File Operation Audit
    if verbose:
        echo("Running file operation audit...")
    file_result = audit_file_operations(src_dir)
    print_status(6, 6, "File Operation Audit", file_result.passed)

    echo()

    # Generate report
    report = SecurityReport(
        network_result=network_result,
        url_result=url_result,
        secret_result=secret_result,
        dependency_result=dependency_result,
        file_result=file_result,
        generated_at=datetime.now(),
    )

    if output_format == "json":
        # JSON output for CI
        result = {
            "passed": report.overall_passed,
            "timestamp": report.generated_at.isoformat(),
            "checks": {
                "network_scan": {
                    "passed": network_result.passed,
                    "violations": len(network_result.violations),
                },
                "url_scan": {
                    "passed": url_result.passed,
                    "external_urls": len(url_result.external_urls),
                },
                "secret_scan": {
                    "passed": secret_result.passed,
                    "secrets_found": len(secret_result.secrets_found),
                },
                "dependency_audit": {
                    "passed": dependency_result.passed,
                    "dependencies": len(dependency_result.dependencies),
                },
                "file_audit": {
                    "passed": file_result.passed,
                    "dangerous_ops": len(file_result.dangerous_operations),
                },
            },
        }
        echo(json.dumps(result, indent=2))
    else:
        # Save markdown report (unless --no-report)
        if not no_report:
            report_path = save_report(report)
            echo(f"Report saved: {report_path}")
        echo()

        # Overall status
        if report.overall_passed:
            echo(Icons.HEAVY_LINE * 60)
            echo(f"               {Status.SUCCESS} ALL CHECKS PASSED")
            echo(Icons.HEAVY_LINE * 60)
        else:
            echo(Icons.HEAVY_LINE * 60)
            echo(f"               {Status.ERROR} SOME CHECKS FAILED")
            echo(Icons.HEAVY_LINE * 60)
            echo()
            echo("Review the report for details on failures.")

    return report.overall_passed


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SEF Agents Security Scanner - Enterprise Security Audit Tool"
    )
    parser.add_argument(
        "--directory",
        "-d",
        type=Path,
        default=Path.cwd(),
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed output",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip saving report to disk (for pre-commit hooks)",
    )

    args = parser.parse_args()

    # Find project root (look for pyproject.toml)
    directory = args.directory.resolve()
    if not (directory / "pyproject.toml").exists():
        # Try parent directories
        for parent in directory.parents:
            if (parent / "pyproject.toml").exists():
                directory = parent
                break

    passed = run_security_scan(
        directory=directory,
        verbose=args.verbose,
        output_format=args.format,
        no_report=args.no_report,
    )

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
