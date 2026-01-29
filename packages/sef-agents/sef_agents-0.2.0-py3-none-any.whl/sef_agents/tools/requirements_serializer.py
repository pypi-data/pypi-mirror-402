"""Requirements serializer for converting markdown requirements to JSON."""

import re
from pathlib import Path
from typing import Any, Optional

import structlog

from sef_agents.tools.gherkin_parser import parse_markdown_ac

logger = structlog.get_logger(__name__)


def story_to_json(story_path: Path) -> dict[str, Any]:
    """Convert a story markdown file to JSON format.

    Args:
        story_path: Path to STORY-XXX.md file

    Returns:
        Dictionary with story data in JSON-serializable format
    """
    content = story_path.read_text(encoding="utf-8")

    # Extract story ID from filename
    story_id_match = re.search(r"STORY-(\d+)", story_path.stem, re.IGNORECASE)
    story_id = story_id_match.group(0).upper() if story_id_match else story_path.stem

    # Parse markdown content
    story_data = _parse_story_markdown(content, story_id)

    return story_data


def epic_to_json(epic_path: Path) -> dict[str, Any]:
    """Convert an epic markdown file to JSON format.

    Args:
        epic_path: Path to EPIC-XXX.md file

    Returns:
        Dictionary with epic data in JSON-serializable format
    """
    content = epic_path.read_text(encoding="utf-8")

    # Extract epic ID from filename
    epic_id_match = re.search(r"EPIC-(\d+)", epic_path.stem, re.IGNORECASE)
    epic_id = epic_id_match.group(0).upper() if epic_id_match else epic_path.stem

    # Parse markdown content
    epic_data = _parse_epic_markdown(content, epic_id)

    return epic_data


def feature_to_json(feature_path: Path) -> dict[str, Any]:
    """Convert a feature markdown file to JSON format.

    Args:
        feature_path: Path to FEAT-XXX.md file

    Returns:
        Dictionary with feature data in JSON-serializable format
    """
    content = feature_path.read_text(encoding="utf-8")

    # Extract feature ID from filename
    feat_id_match = re.search(r"FEAT-(\d+)", feature_path.stem, re.IGNORECASE)
    feature_id = feat_id_match.group(0).upper() if feat_id_match else feature_path.stem

    # Parse markdown content
    feature_data = _parse_feature_markdown(content, feature_id)

    return feature_data


def requirements_to_json(requirements_dir: Path) -> list[dict[str, Any]]:
    """Convert all requirements in a directory to JSON format.

    Args:
        requirements_dir: Directory containing requirement files

    Returns:
        List of requirement dictionaries (stories, epics, features)
    """
    requirements = []

    # Find all requirement files
    for path in requirements_dir.glob("*.md"):
        if path.stem.startswith("STORY-"):
            try:
                requirements.append(story_to_json(path))
            except Exception as e:
                logger.warning("failed_to_parse_story", path=str(path), error=str(e))
        elif path.stem.startswith("EPIC-"):
            try:
                requirements.append(epic_to_json(path))
            except Exception as e:
                logger.warning("failed_to_parse_epic", path=str(path), error=str(e))
        elif path.stem.startswith("FEAT-"):
            try:
                requirements.append(feature_to_json(path))
            except Exception as e:
                logger.warning("failed_to_parse_feature", path=str(path), error=str(e))

    return requirements


def _parse_story_markdown(content: str, story_id: str) -> dict[str, Any]:
    """Parse story markdown content into structured data."""
    # Extract title
    title_match = re.search(r"#\s+Requirement:\s+\[?STORY-[\d]+\]?\s*(.+)", content)
    title = title_match.group(1).strip() if title_match else ""

    # Extract epic_id and feature_id
    epic_id = _extract_field(content, r"\*\*Epic:\*\*\s*(\S+)", r"epic_id[:\s]+(\S+)")
    feature_id = _extract_field(
        content, r"\*\*Feature:\*\*\s*(\S+)", r"feature_id[:\s]+(\S+)"
    )

    # Extract user story
    user_story_match = re.search(
        r"##\s+User Story\s+(?:As a|As an)\s+(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL,
    )
    user_story = user_story_match.group(1).strip() if user_story_match else ""

    # Extract acceptance criteria
    ac_section_match = re.search(
        r"##\s+Acceptance Criteria\s+(.+?)(?=\n##|\Z)", content, re.DOTALL
    )
    ac_text = ac_section_match.group(1) if ac_section_match else ""
    acceptance_criteria = parse_markdown_ac(ac_text)

    # Extract status and priority
    status = _extract_field(content, r"\*\*Status:\*\*\s*(\S+)", r"status[:\s]+(\S+)")
    priority = _extract_field(
        content, r"\*\*Priority:\*\*\s*(\S+)", r"priority[:\s]+(\S+)"
    )

    # Extract description
    description_match = re.search(
        r"##\s+Description\s+(.+?)(?=\n##|\Z)", content, re.DOTALL
    )
    description = description_match.group(1).strip() if description_match else ""

    return {
        "story_id": story_id,
        "title": title,
        "description": description,
        "user_story": user_story,
        "epic_id": epic_id,
        "feature_id": feature_id,
        "status": status or "Draft",
        "priority": priority or "P2",
        "acceptance_criteria": [
            {
                "scenario": ac.scenario,
                "steps": [
                    {"keyword": step.keyword, "text": step.text} for step in ac.steps
                ],
            }
            for ac in acceptance_criteria
        ],
    }


def _parse_epic_markdown(content: str, epic_id: str) -> dict[str, Any]:
    """Parse epic markdown content into structured data."""
    # Extract title
    title_match = re.search(r"#\s+Epic:\s+\[?EPIC-[\d]+\]?\s*(.+)", content)
    title = title_match.group(1).strip() if title_match else ""

    # Extract description
    description_match = re.search(
        r"##\s+Description\s+(.+?)(?=\n##|\Z)", content, re.DOTALL
    )
    description = description_match.group(1).strip() if description_match else ""

    # Extract status
    status = _extract_field(content, r"\*\*Status:\*\*\s*(\S+)", r"status[:\s]+(\S+)")

    return {
        "epic_id": epic_id,
        "title": title,
        "description": description,
        "status": status or "Draft",
    }


def _parse_feature_markdown(content: str, feature_id: str) -> dict[str, Any]:
    """Parse feature markdown content into structured data."""
    # Extract title
    title_match = re.search(r"#\s+Feature:\s+\[?FEAT-[\d]+\]?\s*(.+)", content)
    title = title_match.group(1).strip() if title_match else ""

    # Extract epic_id
    epic_id = _extract_field(content, r"\*\*Epic:\*\*\s*(\S+)", r"epic_id[:\s]+(\S+)")

    # Extract description
    description_match = re.search(
        r"##\s+Description\s+(.+?)(?=\n##|\Z)", content, re.DOTALL
    )
    description = description_match.group(1).strip() if description_match else ""

    # Extract status
    status = _extract_field(content, r"\*\*Status:\*\*\s*(\S+)", r"status[:\s]+(\S+)")

    return {
        "feature_id": feature_id,
        "epic_id": epic_id,
        "title": title,
        "description": description,
        "status": status or "Draft",
    }


def _extract_field(content: str, *patterns: str) -> Optional[str]:
    """Extract field value using multiple regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
