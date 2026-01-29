"""SEF Code Map Generation Tool.

Generates centralized CODE_MAP.md files in codemap/ directory.
Supports merge strategy with SEF:MANUAL/SEF:AUTO section markers.
Finds Python packages by __init__.py presence.

Usage:
    from sef_agents.tools.codemap import generate_codemaps
    result = generate_codemaps("/path/to/project")
"""

from pathlib import Path
from typing import NamedTuple

import structlog

from sef_agents.tools.external_detector import scan_directory

logger = structlog.get_logger(__name__)

# Directories to skip during package discovery
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".tox",
    "htmlcov",
    ".eggs",
    "*.egg-info",
}


class Section(NamedTuple):
    """Parsed markdown section."""

    name: str
    content: str
    is_manual: bool  # True if marked SEF:MANUAL


def find_python_packages(root: Path) -> list[Path]:
    """Find all Python packages (dirs with __init__.py).

    Args:
        root: Project root directory.

    Returns:
        List of package directories sorted by path.
    """
    packages: list[Path] = []

    for path in root.rglob("__init__.py"):
        pkg_dir = path.parent

        # Skip if in excluded directory
        skip = False
        for part in pkg_dir.parts:
            if part in SKIP_DIRS or part.endswith(".egg-info"):
                skip = True
                break
        if skip:
            continue

        packages.append(pkg_dir)

    # Sort by path depth then alphabetically
    return sorted(packages, key=lambda p: (len(p.parts), str(p)))


def _parse_sections(content: str) -> dict[str, Section]:
    """Parse markdown into sections by ## headers.

    Args:
        content: Markdown content.

    Returns:
        Dict mapping section name to Section.
    """
    sections: dict[str, Section] = {}
    current_name = "_header"
    current_lines: list[str] = []
    is_manual = False

    for line in content.splitlines():
        if line.startswith("## "):
            # Save previous section
            if current_lines:
                sections[current_name] = Section(
                    name=current_name,
                    content="\n".join(current_lines),
                    is_manual=is_manual,
                )
            current_name = line[3:].strip()
            current_lines = [line]
            is_manual = False
        elif "<!-- SEF:MANUAL -->" in line:
            is_manual = True
            current_lines.append(line)
        else:
            current_lines.append(line)

    # Save last section
    if current_lines:
        sections[current_name] = Section(
            name=current_name,
            content="\n".join(current_lines),
            is_manual=is_manual,
        )

    return sections


def _merge_sections(existing: str, new: str) -> str:
    """Merge existing and new content, preserving manual sections.

    Args:
        existing: Existing file content.
        new: Newly generated content.

    Returns:
        Merged content.
    """
    existing_sections = _parse_sections(existing)
    new_sections = _parse_sections(new)

    # Start with new content structure
    merged_lines: list[str] = []

    for section_name, new_section in new_sections.items():
        if section_name in existing_sections:
            existing_section = existing_sections[section_name]
            if existing_section.is_manual:
                # Preserve manual sections
                merged_lines.append(existing_section.content)
            else:
                # Use new content for auto sections
                merged_lines.append(new_section.content)
        else:
            merged_lines.append(new_section.content)

    return "\n\n".join(merged_lines)


def _generate_external_deps_section(directory: Path) -> str:
    """Generate External Dependencies section using auto-detection.

    Args:
        directory: Path to scan for external dependencies.

    Returns:
        Markdown formatted External Dependencies section.
    """
    result = scan_directory(directory)

    output = "## External Dependencies\n"
    output += "<!-- SEF:AUTO -->\n"
    output += "*Auto-detected by external_detector.py*\n\n"

    if not result.dependencies:
        output += "No external dependencies detected.\n\n"
        return output

    # Environment variables
    if result.env_vars:
        output += "### Environment Variables (External Endpoints)\n\n"
        output += "| Variable | File | Line | Notes |\n"
        output += "|----------|------|------|-------|\n"
        for dep in result.env_vars:
            filename = Path(dep.source_file).name
            line = dep.line_number if dep.line_number else "-"
            output += f"| `{dep.name}` | `{filename}` | {line} | {dep.description} |\n"
        output += "\n"

    # API clients
    if result.api_clients:
        output += "### External API Clients\n\n"
        output += "| Library | Service | File | Line |\n"
        output += "|---------|---------|------|------|\n"
        for dep in result.api_clients:
            filename = Path(dep.source_file).name
            line = dep.line_number if dep.line_number else "-"
            output += f"| `{dep.name}` | {dep.description} | `{filename}` | {line} |\n"
        output += "\n"

    # Hardcoded URLs
    if result.urls:
        output += "### Hardcoded External URLs\n\n"
        output += "| Domain | File | Line | Notes |\n"
        output += "|--------|------|------|-------|\n"
        for dep in result.urls:
            filename = Path(dep.source_file).name
            line = dep.line_number if dep.line_number else "-"
            output += f"| `{dep.name}` | `{filename}` | {line} | ⚠️ Consider env var |\n"
        output += "\n"

    logger.info(
        "external_deps_detected",
        env_vars=len(result.env_vars),
        api_clients=len(result.api_clients),
        urls=len(result.urls),
    )

    return output


def _generate_package_codemap(pkg_dir: Path, root: Path) -> str:
    """Generate CODE_MAP content for a Python package.

    Args:
        pkg_dir: Package directory path.
        root: Project root for relative path calculation.

    Returns:
        Markdown content for the package codemap.
    """
    rel_path = pkg_dir.relative_to(root)

    files = [
        f.name for f in pkg_dir.iterdir() if f.is_file() and not f.name.startswith(".")
    ]
    subdirs = [
        d.name for d in pkg_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    ]

    template = f"""# CODE_MAP: `{rel_path}`

## Purpose
<!-- SEF:MANUAL -->
[Describe the purpose of this module]

## Directory Structure
<!-- SEF:AUTO -->
| Item | Type | Purpose | Dependencies |
|------|------|---------|--------------|
"""
    for sub in subdirs:
        if sub in SKIP_DIRS:
            continue
        template += f"| `{sub}/` | Dir | [Desc] | - |\n"

    for f in files:
        template += f"| `{f}` | File | [Desc] | - |\n"

    template += """
## Key Classes / Functions
<!-- SEF:MANUAL -->
| Name | File | Purpose | Dependencies |
|------|------|---------|--------------|
| ...  | ...  | ...     | ...          |

"""

    # Auto-detect external dependencies
    template += _generate_external_deps_section(pkg_dir)

    template += """
## Integration Boundaries
<!-- SEF:MANUAL -->
*Where this module connects to external systems*

| Boundary Type | Local Code | External System | Data Flow | Risk Level |
|---------------|------------|-----------------|-----------|------------|
| API Call      | [file.py]  | [External API]  | Outbound  | Medium     |
"""

    return template


def _generate_meta_map(packages: list[Path], root: Path, codemap_dir: Path) -> str:
    """Generate root CODE_MAP.md linking all package maps.

    Args:
        packages: List of package directories.
        root: Project root.
        codemap_dir: Path to codemap/ directory.

    Returns:
        Markdown content for meta-map.
    """
    template = """# CODE_MAP: Project Overview

## Purpose
<!-- SEF:MANUAL -->
[Describe the overall project purpose]

## Package Index
<!-- SEF:AUTO -->
| Package | Path | Purpose |
|---------|------|---------|
"""
    for pkg in packages:
        rel_path = pkg.relative_to(root)
        map_name = str(rel_path).replace("/", "_") + ".md"
        template += f"| [{pkg.name}](./{map_name}) | `{rel_path}` | [Desc] |\n"

    template += f"""
## Project Statistics
<!-- SEF:AUTO -->
- **Total Packages:** {len(packages)}
- **Generated:** Auto-updated by discovery

## Quick Navigation
<!-- SEF:MANUAL -->
*Add frequently accessed modules here*

| Module | Description |
|--------|-------------|
| ...    | ...         |
"""

    return template


def generate_codemaps(directory: str) -> str:
    """Generate centralized CODE_MAPs for all Python packages.

    Creates codemap/ directory at project root with:
    - CODE_MAP.md (meta-map linking all packages)
    - <package>_CODE_MAP.md for each Python package

    Merges with existing files, preserving SEF:MANUAL sections.

    Args:
        directory: Path to project root.

    Returns:
        Status message with summary.
    """
    root = Path(directory)
    if not root.exists():
        return f"Error: Directory {directory} does not exist."

    # Create codemap directory
    codemap_dir = root / "codemap"
    codemap_dir.mkdir(exist_ok=True)

    packages = find_python_packages(root)

    if not packages:
        return (
            f"No Python packages found in {directory}. Ensure __init__.py files exist."
        )

    generated = 0
    updated = 0

    # Generate per-package maps
    for pkg in packages:
        rel_path = pkg.relative_to(root)
        map_name = str(rel_path).replace("/", "_") + ".md"
        map_path = codemap_dir / map_name

        new_content = _generate_package_codemap(pkg, root)

        if map_path.exists():
            existing_content = map_path.read_text(encoding="utf-8")
            merged = _merge_sections(existing_content, new_content)
            map_path.write_text(merged, encoding="utf-8")
            updated += 1
            logger.info("codemap_updated", package=str(rel_path), path=str(map_path))
        else:
            map_path.write_text(new_content, encoding="utf-8")
            generated += 1
            logger.info("codemap_generated", package=str(rel_path), path=str(map_path))

    # Generate meta-map
    meta_path = codemap_dir / "CODE_MAP.md"
    meta_content = _generate_meta_map(packages, root, codemap_dir)

    if meta_path.exists():
        existing_meta = meta_path.read_text(encoding="utf-8")
        merged_meta = _merge_sections(existing_meta, meta_content)
        meta_path.write_text(merged_meta, encoding="utf-8")
    else:
        meta_path.write_text(meta_content, encoding="utf-8")

    return (
        f"✅ CODE_MAPs generated in `{codemap_dir}`\n\n"
        f"**Packages:** {len(packages)}\n"
        f"**Generated:** {generated}\n"
        f"**Updated:** {updated}\n\n"
        f"Meta-map: `{meta_path}`"
    )


# Legacy function for backward compatibility
def generate_codemap_tool(directory: str) -> str:
    """Legacy wrapper - redirects to centralized codemap generation.

    Args:
        directory: Path to directory to scan.

    Returns:
        Status message with codemap paths.
    """
    return generate_codemaps(directory)
