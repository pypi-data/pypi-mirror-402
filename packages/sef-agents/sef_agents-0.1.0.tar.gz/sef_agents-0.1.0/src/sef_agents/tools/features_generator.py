"""SEF Features Generator.

Infers FEATURES.md from codemap/ directory structure.
Features are user-visible capabilities + modular structures.

Usage:
    from sef_agents.tools.features_generator import generate_features_file
    result = generate_features_file("/path/to/project")
"""

from dataclasses import dataclass
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# Keywords indicating user-facing features
FEATURE_KEYWORDS = {
    "api",
    "auth",
    "authentication",
    "authorization",
    "cache",
    "client",
    "config",
    "connector",
    "consumer",
    "core",
    "database",
    "discovery",
    "export",
    "handler",
    "import",
    "index",
    "indexing",
    "integration",
    "loader",
    "manager",
    "metrics",
    "migration",
    "notification",
    "orchestrator",
    "parser",
    "pipeline",
    "processor",
    "provider",
    "queue",
    "report",
    "scheduler",
    "search",
    "security",
    "service",
    "storage",
    "sync",
    "telemetry",
    "transform",
    "upload",
    "validation",
    "worker",
}


@dataclass
class Feature:
    """Inferred feature from codemap."""

    name: str
    module: str
    description: str
    category: str


def _extract_purpose(content: str) -> str:
    """Extract purpose section from codemap content.

    Args:
        content: Codemap markdown content.

    Returns:
        Purpose section text or empty string.
    """
    lines = content.splitlines()
    in_purpose = False
    purpose_lines: list[str] = []

    for line in lines:
        if line.startswith("## Purpose"):
            in_purpose = True
            continue
        if in_purpose:
            if line.startswith("## "):
                break
            if line.strip() and not line.startswith("<!--"):
                purpose_lines.append(line.strip())

    return " ".join(purpose_lines)


def _infer_category(module_name: str) -> str:
    """Infer feature category from module name.

    Args:
        module_name: Module/package name.

    Returns:
        Category string.
    """
    name_lower = module_name.lower()

    if any(k in name_lower for k in ["api", "client", "connector"]):
        return "Integration"
    if any(k in name_lower for k in ["auth", "security"]):
        return "Security"
    if any(k in name_lower for k in ["index", "search", "discovery"]):
        return "Data Processing"
    if any(k in name_lower for k in ["config", "core", "shared"]):
        return "Core"
    if any(k in name_lower for k in ["metrics", "telemetry", "report"]):
        return "Observability"
    if any(k in name_lower for k in ["queue", "consumer", "worker"]):
        return "Messaging"

    return "Utility"


def _format_feature_name(module_name: str) -> str:
    """Convert module name to readable feature name.

    Args:
        module_name: Underscore-separated module name.

    Returns:
        Title-cased feature name.
    """
    # Remove common prefixes/suffixes
    name = module_name.replace("_service", "").replace("_handler", "")
    name = name.replace("_manager", "").replace("_processor", "")

    # Title case
    words = name.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def infer_features(codemap_dir: Path) -> list[Feature]:
    """Infer features from codemap directory.

    Args:
        codemap_dir: Path to codemap/ directory.

    Returns:
        List of inferred features.
    """
    features: list[Feature] = []

    if not codemap_dir.exists():
        return features

    for map_file in codemap_dir.glob("*.md"):
        if map_file.name == "CODE_MAP.md":
            continue  # Skip meta-map

        try:
            content = map_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Module name from filename (e.g., app_discovery.md -> discovery)
        module_name = map_file.stem
        if "_" in module_name:
            # Take last component (e.g., app_discovery -> discovery)
            parts = module_name.split("_")
            module_name = parts[-1] if len(parts) > 1 else module_name

        # Check if module name suggests a feature
        is_feature = any(kw in module_name.lower() for kw in FEATURE_KEYWORDS)

        if is_feature:
            purpose = _extract_purpose(content)
            if not purpose or purpose.startswith("["):
                purpose = (
                    f"Handles {_format_feature_name(module_name).lower()} functionality"
                )

            features.append(
                Feature(
                    name=_format_feature_name(module_name),
                    module=map_file.stem,
                    description=purpose,
                    category=_infer_category(module_name),
                )
            )

    # Sort by category then name
    return sorted(features, key=lambda f: (f.category, f.name))


def generate_features_md(features: list[Feature]) -> str:
    """Generate FEATURES.md content.

    Args:
        features: List of features.

    Returns:
        Markdown content.
    """
    content = """# FEATURES.md

## Overview

This document lists user-facing features inferred from the codebase structure.

> **Note:** Features are identified by analyzing module names and purposes in `codemap/`.
> Update module purposes to refine this list.

## Features by Category

"""

    # Group by category
    categories: dict[str, list[Feature]] = {}
    for feature in features:
        if feature.category not in categories:
            categories[feature.category] = []
        categories[feature.category].append(feature)

    for category in sorted(categories.keys()):
        content += f"### {category}\n\n"
        content += "| Feature | Module | Description |\n"
        content += "|---------|--------|-------------|\n"
        for f in categories[category]:
            content += f"| **{f.name}** | `{f.module}` | {f.description} |\n"
        content += "\n"

    content += f"""## Summary

- **Total Features:** {len(features)}
- **Categories:** {len(categories)}

---
*Auto-generated by discovery agent. Edit module purposes in `codemap/` to refine.*
"""

    return content


def generate_features_file(directory: str) -> str:
    """Generate FEATURES.md at project root.

    Args:
        directory: Path to project root.

    Returns:
        Status message.
    """
    root = Path(directory)
    codemap_dir = root / "codemap"

    if not codemap_dir.exists():
        return "Error: codemap/ directory not found. Run generate_codemaps first."

    features = infer_features(codemap_dir)

    if not features:
        return (
            "No features inferred. Ensure codemap/ contains module maps with purposes."
        )

    content = generate_features_md(features)

    features_path = root / "FEATURES.md"
    features_path.write_text(content, encoding="utf-8")

    logger.info(
        "features_generated", path=str(features_path), feature_count=len(features)
    )

    return (
        f"✅ FEATURES.md generated at `{features_path}`\n\n"
        f"**Features found:** {len(features)}\n"
        f"**Categories:** {len({f.category for f in features})}"
    )
