"""Dependency Audit Scanner.

Parses pyproject.toml to list all dependencies with their versions
and license information for security review.
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# Known safe licenses for enterprise use
SAFE_LICENSES: set[str] = {
    "MIT",
    "MIT License",
    "Apache 2.0",
    "Apache-2.0",
    "Apache Software License",
    "BSD",
    "BSD License",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "ISC License",
    "PSF",
    "Python Software Foundation License",
    "MPL-2.0",
    "Mozilla Public License 2.0",
    "Unlicense",
    "Public Domain",
    "CC0",
}


@dataclass
class DependencyInfo:
    """Information about a single dependency."""

    name: str
    version: str
    license: str
    license_safe: bool


@dataclass
class DependencyAuditResult:
    """Result of dependency audit."""

    passed: bool
    dependencies: list[DependencyInfo] = field(default_factory=list)
    unsafe_licenses: list[str] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """One-line summary for CLI output."""
        if self.passed:
            return f"{len(self.dependencies)} dependencies, all licenses compatible"
        return f"{len(self.unsafe_licenses)} dependencies with unsafe licenses"


def _parse_pyproject(pyproject_path: Path) -> list[str]:
    """Parse dependencies from pyproject.toml."""
    try:
        content = pyproject_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []

    # Simple parsing for dependencies section
    dependencies: list[str] = []
    in_deps = False

    for line in content.split("\n"):
        line = line.strip()
        if line == "dependencies = [":
            in_deps = True
            continue
        if in_deps:
            if line == "]":
                break
            # Extract package name from dependency string
            if line.startswith('"') or line.startswith("'"):
                dep = line.strip("\",' ")
                # Extract just the package name (before version specifier)
                pkg_name = dep.split(">=")[0].split("==")[0].split("<")[0].split("[")[0]
                if pkg_name:
                    dependencies.append(pkg_name.strip())

    return dependencies


def _get_package_info(package_name: str) -> tuple[str, str]:
    """Get version and license info for an installed package."""
    try:
        # Use pip show to get package info
        result = subprocess.run(
            ["uv", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return "unknown", "Unknown"

        version = "unknown"
        license_info = "Unknown"

        for line in result.stdout.split("\n"):
            if line.startswith("Version:"):
                version = line.split(":", 1)[1].strip()
            elif line.startswith("License:"):
                license_info = line.split(":", 1)[1].strip()

        return version, license_info

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown", "Unknown"


def audit_dependencies(
    directory: Path,
) -> DependencyAuditResult:
    """
    Audit project dependencies for versions and licenses.

    Args:
        directory: Project root directory containing pyproject.toml

    Returns:
        DependencyAuditResult with dependency information
    """
    pyproject_path = directory / "pyproject.toml"
    dependencies: list[DependencyInfo] = []
    unsafe_licenses: list[str] = []
    parse_errors: list[str] = []

    if not pyproject_path.exists():
        parse_errors.append("pyproject.toml not found")
        return DependencyAuditResult(
            passed=True,  # No deps means no issues
            dependencies=[],
            unsafe_licenses=[],
            parse_errors=parse_errors,
        )

    dep_names = _parse_pyproject(pyproject_path)

    for dep_name in dep_names:
        version, license_info = _get_package_info(dep_name)

        license_safe = any(
            safe.lower() in license_info.lower() for safe in SAFE_LICENSES
        )

        dep_info = DependencyInfo(
            name=dep_name,
            version=version,
            license=license_info,
            license_safe=license_safe,
        )
        dependencies.append(dep_info)

        if not license_safe and license_info != "Unknown":
            unsafe_licenses.append(f"{dep_name}: {license_info}")
            logger.warning(
                "unsafe_license_detected",
                package=dep_name,
                license=license_info,
            )

    passed = len(unsafe_licenses) == 0

    logger.info(
        "dependency_audit_complete",
        passed=passed,
        total_dependencies=len(dependencies),
        unsafe_count=len(unsafe_licenses),
    )

    return DependencyAuditResult(
        passed=passed,
        dependencies=dependencies,
        unsafe_licenses=unsafe_licenses,
        parse_errors=parse_errors,
    )
