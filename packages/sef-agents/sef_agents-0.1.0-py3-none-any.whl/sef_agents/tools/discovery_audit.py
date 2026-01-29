"""SEF Discovery Audit Tool.

Post-completion verification for discovery artifacts.
Checks existence, placement, and content compliance.

Usage:
    from sef_agents.tools.discovery_audit import audit_discovery
    result = audit_discovery("/path/to/project")
"""

from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AuditCheck:
    """Single audit check result."""

    name: str
    passed: bool
    message: str


@dataclass
class AuditResult:
    """Complete audit result."""

    status: str  # "PASS" or "FAIL"
    checks: list[AuditCheck] = field(default_factory=list)
    remediation: list[str] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed)


def _check_artifact_existence(root: Path) -> list[AuditCheck]:
    """Check required artifacts exist.

    Args:
        root: Project root directory.

    Returns:
        List of audit checks.
    """
    checks: list[AuditCheck] = []

    required = {
        "codemap/CODE_MAP.md": "Root codemap meta-map",
        "FEATURES.md": "Features manifest",
        "AGENTS.md": "AI protocol file",
        "docs/ARCHITECTURE.md": "Architecture documentation",
        "docs/EXTERNAL_DEPS.md": "External dependencies",
        "docs/TECH_DEBT.md": "Technical debt registry",
        "sef-reports/context_graph.json": "Context graph for dashboard",
    }

    for path, desc in required.items():
        full_path = root / path
        exists = full_path.exists()
        checks.append(
            AuditCheck(
                name=f"artifact_{path.replace('/', '_')}",
                passed=exists,
                message=f"{desc}: {'✅ Found' if exists else '❌ Missing'}",
            )
        )

    # Check codemap has package maps
    codemap_dir = root / "codemap"
    if codemap_dir.exists():
        package_maps = list(codemap_dir.glob("*.md"))
        # Exclude meta-map
        package_maps = [p for p in package_maps if p.name != "CODE_MAP.md"]
        has_package_maps = len(package_maps) > 0
        checks.append(
            AuditCheck(
                name="codemap_package_maps",
                passed=has_package_maps,
                message=f"Package codemaps: {'✅ ' + str(len(package_maps)) + ' found' if has_package_maps else '❌ None found'}",
            )
        )

    return checks


def _check_placement_validation(root: Path) -> list[AuditCheck]:
    """Check artifacts are in correct locations.

    Args:
        root: Project root directory.

    Returns:
        List of audit checks.
    """
    checks: list[AuditCheck] = []

    # Should NOT be at root
    misplaced_at_root = [
        ("ARCHITECTURE.md", "docs/ARCHITECTURE.md"),
        ("EXTERNAL_DEPS.md", "docs/EXTERNAL_DEPS.md"),
        ("EXTERNAL_APIS.md", "docs/EXTERNAL_DEPS.md"),
    ]

    for src, expected in misplaced_at_root:
        src_path = root / src
        if src_path.exists():
            checks.append(
                AuditCheck(
                    name=f"misplaced_{src}",
                    passed=False,
                    message=f"⚠️ `{src}` at root should be at `{expected}`",
                )
            )

    # Should NOT have unknown/ directory
    unknown_dir = root / "sef-reports" / "unknown"
    if unknown_dir.exists():
        checks.append(
            AuditCheck(
                name="unknown_directory",
                passed=False,
                message="❌ `sef-reports/unknown/` exists - indicates agent routing issue",
            )
        )
    else:
        checks.append(
            AuditCheck(
                name="unknown_directory",
                passed=True,
                message="✅ No `unknown/` directory in sef-reports",
            )
        )

    # CODE_MAP.md should NOT be scattered in source dirs
    scattered_codemaps: list[Path] = []
    for codemap in root.rglob("CODE_MAP.md"):
        # Skip if in codemap/ directory
        if "codemap" in codemap.parts:
            continue
        # Skip if in docs/
        if "docs" in codemap.parts:
            continue
        # This is a scattered codemap
        scattered_codemaps.append(codemap)

    if scattered_codemaps:
        checks.append(
            AuditCheck(
                name="scattered_codemaps",
                passed=False,
                message=f"⚠️ Found {len(scattered_codemaps)} CODE_MAP.md in source dirs (should be in codemap/)",
            )
        )

    return checks


def _check_content_validation(root: Path) -> list[AuditCheck]:
    """Check artifact content meets requirements.

    Args:
        root: Project root directory.

    Returns:
        List of audit checks.
    """
    checks: list[AuditCheck] = []

    # AGENTS.md must contain fix workflow
    agents_path = root / "AGENTS.md"
    if agents_path.exists():
        content = agents_path.read_text(encoding="utf-8")
        has_workflow = "forensic_engineer" in content and "strategist" in content
        checks.append(
            AuditCheck(
                name="agents_fix_workflow",
                passed=has_workflow,
                message=f"AGENTS.md fix workflow: {'✅ Present' if has_workflow else '❌ Missing mandatory workflow'}",
            )
        )

    # FEATURES.md must have at least 1 feature
    features_path = root / "FEATURES.md"
    if features_path.exists():
        content = features_path.read_text(encoding="utf-8")
        has_features = "|" in content and "Feature" in content
        checks.append(
            AuditCheck(
                name="features_content",
                passed=has_features,
                message=f"FEATURES.md content: {'✅ Has features' if has_features else '❌ No features listed'}",
            )
        )

    # Codemaps must have Purpose section
    codemap_dir = root / "codemap"
    if codemap_dir.exists():
        package_maps = [p for p in codemap_dir.glob("*.md") if p.name != "CODE_MAP.md"]
        if package_maps:
            sample = package_maps[0]
            content = sample.read_text(encoding="utf-8")
            has_purpose = "## Purpose" in content
            checks.append(
                AuditCheck(
                    name="codemap_purpose_section",
                    passed=has_purpose,
                    message=f"Codemap purpose sections: {'✅ Present' if has_purpose else '❌ Missing'}",
                )
            )

    return checks


def _generate_remediation(result: AuditResult, root: Path) -> list[str]:
    """Generate remediation steps for failed checks.

    Args:
        result: Audit result with checks.
        root: Project root.

    Returns:
        List of remediation commands/steps.
    """
    remediation: list[str] = []

    for check in result.checks:
        if check.passed:
            continue

        if "codemap" in check.name and "Missing" in check.message:
            remediation.append("Run: generate_codemaps()")

        if "FEATURES" in check.message and "Missing" in check.message:
            remediation.append("Run: generate_features_file()")

        if "AGENTS" in check.message and "Missing" in check.message:
            remediation.append("Run: generate_agents_file()")

        if "TECH_DEBT" in check.message:
            remediation.append("Run: scan_health() to generate docs/TECH_DEBT.md")

        if "context_graph" in check.name:
            remediation.append("Run: populate_context_graph()")

        if "misplaced" in check.name:
            remediation.append("Run: scan_health() to relocate artifacts")

        if "unknown_directory" in check.name and not check.passed:
            remediation.append("Delete sef-reports/unknown/ and re-run scans")

    return list(set(remediation))  # Dedupe


def audit_discovery(directory: str) -> str:
    """Audit discovery artifacts for completeness and compliance.

    Checks:
    - Artifact existence (codemap/, FEATURES.md, AGENTS.md, etc.)
    - Placement validation (no misplaced files, no unknown/)
    - Content validation (required sections present)

    Args:
        directory: Path to project root.

    Returns:
        Status message with audit results.
    """
    root = Path(directory)

    if not root.exists():
        return f"Error: Directory {directory} does not exist."

    result = AuditResult(status="PASS")

    # Run all checks
    result.checks.extend(_check_artifact_existence(root))
    result.checks.extend(_check_placement_validation(root))
    result.checks.extend(_check_content_validation(root))

    # Determine overall status
    if result.failed_count > 0:
        result.status = "FAIL"
        result.remediation = _generate_remediation(result, root)

    # Format output
    status_icon = "✅" if result.status == "PASS" else "❌"
    output = f"{status_icon} **Discovery Audit: {result.status}**\n\n"
    output += (
        f"**Passed:** {result.passed_count} | **Failed:** {result.failed_count}\n\n"
    )

    output += "## Check Results\n\n"
    for check in result.checks:
        output += f"- {check.message}\n"

    if result.remediation:
        output += "\n## Remediation Steps\n\n"
        for step in result.remediation:
            output += f"1. {step}\n"

    logger.info(
        "discovery_audit_complete",
        status=result.status,
        passed=result.passed_count,
        failed=result.failed_count,
    )

    return output
