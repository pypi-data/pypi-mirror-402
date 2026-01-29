"""Hierarchy manager for Epic → Feature → Story structure."""

from pathlib import Path
from typing import Optional

import structlog

from sef_agents.models.hierarchy import Epic, Feature, Story
from sef_agents.tools.requirements_serializer import (
    epic_to_json,
    feature_to_json,
    story_to_json,
)
from sef_agents.tools.json_output import generate_json_output

logger = structlog.get_logger(__name__)


def create_epic(
    epic_id: str,
    title: str,
    description: str = "",
    requirements_dir: Path | None = None,
) -> Epic:
    """Create a new epic.

    Args:
        epic_id: Epic identifier (e.g., EPIC-001)
        title: Epic title
        description: Epic description
        requirements_dir: Directory for requirements. Defaults to docs/requirements.

    Returns:
        Created Epic model
    """
    if requirements_dir is None:
        requirements_dir = Path("docs/requirements")

    epic = Epic(epic_id=epic_id, title=title, description=description)

    # Write markdown file
    epic_path = requirements_dir / f"{epic_id}.md"
    epic_path.parent.mkdir(parents=True, exist_ok=True)
    epic_path.write_text(_epic_to_markdown(epic), encoding="utf-8")

    # Auto-generate JSON
    epic_data = epic.to_dict()
    generate_json_output("epic", epic_data, epic_path)

    logger.info("Epic created", epic_id=epic_id, path=str(epic_path))

    return epic


def create_feature(
    feature_id: str,
    epic_id: str,
    title: str,
    description: str = "",
    requirements_dir: Path | None = None,
) -> Feature:
    """Create a new feature under an epic.

    Args:
        feature_id: Feature identifier (e.g., FEAT-001)
        epic_id: Parent epic identifier
        title: Feature title
        description: Feature description
        requirements_dir: Directory for requirements. Defaults to docs/requirements.

    Returns:
        Created Feature model
    """
    if requirements_dir is None:
        requirements_dir = Path("docs/requirements")

    feature = Feature(
        feature_id=feature_id,
        epic_id=epic_id,
        title=title,
        description=description,
    )

    # Write markdown file
    feature_path = requirements_dir / f"{feature_id}.md"
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    feature_path.write_text(_feature_to_markdown(feature), encoding="utf-8")

    # Auto-generate JSON
    feature_data = feature.to_dict()
    generate_json_output("feature", feature_data, feature_path)

    logger.info(
        "Feature created",
        feature_id=feature_id,
        epic_id=epic_id,
        path=str(feature_path),
    )

    return feature


def create_story(
    story_id: str,
    title: str,
    user_story: str,
    epic_id: Optional[str] = None,
    feature_id: Optional[str] = None,
    description: str = "",
    requirements_dir: Path | None = None,
) -> Story:
    """Create a new story (can be flat or hierarchical).

    Args:
        story_id: Story identifier (e.g., STORY-001)
        title: Story title
        user_story: User story text (As a... I want... So that...)
        epic_id: Optional parent epic identifier
        feature_id: Optional parent feature identifier
        description: Story description
        requirements_dir: Directory for requirements. Defaults to docs/requirements.

    Returns:
        Created Story model
    """
    if requirements_dir is None:
        requirements_dir = Path("docs/requirements")

    story = Story(
        story_id=story_id,
        title=title,
        user_story=user_story,
        epic_id=epic_id,
        feature_id=feature_id,
        description=description,
    )

    # Write markdown file
    story_path = requirements_dir / f"{story_id}.md"
    story_path.parent.mkdir(parents=True, exist_ok=True)
    story_path.write_text(_story_to_markdown(story), encoding="utf-8")

    # Auto-generate JSON
    story_data = story.to_dict()
    generate_json_output("story", story_data, story_path)

    logger.info(
        "Story created",
        story_id=story_id,
        epic_id=epic_id,
        feature_id=feature_id,
        path=str(story_path),
    )

    return story


def get_epic(epic_id: str, requirements_dir: Path | None = None) -> Optional[Epic]:
    """Get an epic by ID.

    Args:
        epic_id: Epic identifier
        requirements_dir: Directory for requirements

    Returns:
        Epic model if found, None otherwise
    """
    if requirements_dir is None:
        requirements_dir = Path("docs/requirements")

    epic_path = requirements_dir / f"{epic_id}.md"
    if not epic_path.exists():
        return None

    epic_data = epic_to_json(epic_path)
    return Epic(**epic_data)


def get_feature(
    feature_id: str, requirements_dir: Path | None = None
) -> Optional[Feature]:
    """Get a feature by ID.

    Args:
        feature_id: Feature identifier
        requirements_dir: Directory for requirements

    Returns:
        Feature model if found, None otherwise
    """
    if requirements_dir is None:
        requirements_dir = Path("docs/requirements")

    feature_path = requirements_dir / f"{feature_id}.md"
    if not feature_path.exists():
        return None

    feature_data = feature_to_json(feature_path)
    return Feature(**feature_data)


def get_story(story_id: str, requirements_dir: Path | None = None) -> Optional[Story]:
    """Get a story by ID.

    Args:
        story_id: Story identifier
        requirements_dir: Directory for requirements

    Returns:
        Story model if found, None otherwise
    """
    if requirements_dir is None:
        requirements_dir = Path("docs/requirements")

    story_path = requirements_dir / f"{story_id}.md"
    if not story_path.exists():
        return None

    story_data = story_to_json(story_path)
    return Story(**story_data)


def _epic_to_markdown(epic: Epic) -> str:
    """Convert epic to markdown format."""
    lines = [
        f"# Epic: [{epic.epic_id}] {epic.title}",
        "",
        f"**Status:** {epic.status}",
        "",
        "## Description",
        "",
        epic.description or "",
    ]
    return "\n".join(lines)


def _feature_to_markdown(feature: Feature) -> str:
    """Convert feature to markdown format."""
    lines = [
        f"# Feature: [{feature.feature_id}] {feature.title}",
        "",
        f"**Epic:** {feature.epic_id}",
        f"**Status:** {feature.status}",
        "",
        "## Description",
        "",
        feature.description or "",
    ]
    return "\n".join(lines)


def _story_to_markdown(story: Story) -> str:
    """Convert story to markdown format."""
    lines = [
        f"# Requirement: [{story.story_id}] {story.title}",
        "",
        f"**Status:** {story.status}",
        f"**Priority:** {story.priority}",
    ]

    if story.epic_id:
        lines.append(f"**Epic:** {story.epic_id}")
    if story.feature_id:
        lines.append(f"**Feature:** {story.feature_id}")

    lines.extend(
        [
            "",
            "## User Story",
            "",
            story.user_story or "",
            "",
            "## Description",
            "",
            story.description or "",
            "",
            "## Acceptance Criteria",
            "",
            "*Acceptance criteria will be added here*",
        ]
    )

    return "\n".join(lines)
