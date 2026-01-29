"""JIRA and Confluence export functions for requirements.

Provides functions to convert SEF-Agents requirements to JIRA/Confluence formats.
"""

from typing import Any

import structlog

from sef_agents.models.hierarchy import Epic, Feature, Story
from sef_agents.models.invest import INVESTScores

logger = structlog.get_logger(__name__)


def export_to_jira_format(
    story: Story,
    invest_scores: INVESTScores | None = None,
    acceptance_criteria: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Export story to JIRA issue format.

    Compatible with JIRA REST API for issue creation.

    Args:
        story: Story model
        invest_scores: Optional INVEST scores
        acceptance_criteria: Optional structured acceptance criteria

    Returns:
        Dictionary compatible with JIRA REST API createIssue endpoint
    """
    fields: dict[str, Any] = {
        "summary": story.title,
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": story.description or ""}],
                }
            ],
        },
        "issuetype": {"name": "Story"},
    }

    # Add user story
    if story.user_story:
        fields["description"]["content"].append(
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"User Story: {story.user_story}"}
                ],
            }
        )

    # Add epic link if present
    if story.epic_id:
        fields["customfield_10014"] = (
            story.epic_id
        )  # Epic Link field (varies by JIRA instance)

    # Add feature link if present (custom field)
    if story.feature_id:
        fields["customfield_10015"] = story.feature_id  # Feature Link (custom field)

    # Add INVEST scores as custom fields or labels
    if invest_scores:
        fields["labels"] = [
            f"INVEST-{k}:{v}" for k, v in invest_scores.to_dict().items()
        ]

    # Add acceptance criteria
    if acceptance_criteria:
        ac_content = [
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Acceptance Criteria"}],
            }
        ]
        for idx, ac in enumerate(acceptance_criteria, 1):
            scenario = ac.get("scenario", f"AC-{idx}")
            steps = ac.get("steps", [])
            ac_content.append(
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": f"{scenario}:"},
                    ],
                }
            )
            for step in steps:
                keyword = step.get("keyword", "")
                text = step.get("text", "")
                ac_content.append(
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": f"{keyword} {text}"},
                        ],
                    }
                )

        fields["description"]["content"].extend(ac_content)

    return {
        "fields": fields,
    }


def export_to_confluence_format(
    story: Story,
    invest_scores: INVESTScores | None = None,
    acceptance_criteria: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Export story to Confluence page format.

    Compatible with Confluence REST API for page creation.

    Args:
        story: Story model
        invest_scores: Optional INVEST scores
        acceptance_criteria: Optional structured acceptance criteria

    Returns:
        Dictionary compatible with Confluence REST API createPage endpoint
    """
    # Build Confluence storage format (Confluence Wiki or Storage format)
    body_content: list[dict[str, Any]] = []

    # Title and description
    body_content.append(
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": story.description or ""},
            ],
        }
    )

    # User story
    if story.user_story:
        body_content.append(
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"User Story: {story.user_story}"},
                ],
            }
        )

    # Epic and Feature links
    if story.epic_id or story.feature_id:
        links = []
        if story.epic_id:
            links.append(f"Epic: {story.epic_id}")
        if story.feature_id:
            links.append(f"Feature: {story.feature_id}")
        body_content.append(
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": " | ".join(links)},
                ],
            }
        )

    # INVEST scores
    if invest_scores:
        scores_text = ", ".join(f"{k}: {v}" for k, v in invest_scores.to_dict().items())
        body_content.append(
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"INVEST Scores: {scores_text}"},
                ],
            }
        )

    # Acceptance criteria
    if acceptance_criteria:
        body_content.append(
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Acceptance Criteria"}],
            }
        )
        for idx, ac in enumerate(acceptance_criteria, 1):
            scenario = ac.get("scenario", f"AC-{idx}")
            steps = ac.get("steps", [])
            body_content.append(
                {
                    "type": "heading",
                    "attrs": {"level": 4},
                    "content": [{"type": "text", "text": scenario}],
                }
            )
            for step in steps:
                keyword = step.get("keyword", "")
                text = step.get("text", "")
                body_content.append(
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": f"{keyword} {text}"},
                        ],
                    }
                )

    return {
        "title": story.title,
        "type": "page",
        "space": {"key": "SEF"},  # Default space, should be configurable
        "body": {
            "storage": {
                "value": _convert_to_storage_format(body_content),
                "representation": "storage",
            }
        },
    }


def export_epic_to_jira(epic: Epic) -> dict[str, Any]:
    """Export epic to JIRA format.

    Args:
        epic: Epic model

    Returns:
        Dictionary compatible with JIRA REST API
    """
    return {
        "fields": {
            "summary": epic.title,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": epic.description or ""}],
                    }
                ],
            },
            "issuetype": {"name": "Epic"},
            "customfield_10011": epic.title,  # Epic Name field
        },
    }


def export_feature_to_jira(feature: Feature) -> dict[str, Any]:
    """Export feature to JIRA format.

    Args:
        feature: Feature model

    Returns:
        Dictionary compatible with JIRA REST API
    """
    return {
        "fields": {
            "summary": feature.title,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": feature.description or ""}
                        ],
                    }
                ],
            },
            "issuetype": {"name": "Feature"},
            "customfield_10014": feature.epic_id,  # Epic Link
        },
    }


def _convert_to_storage_format(content: list[dict[str, Any]]) -> str:
    """Convert Confluence content to storage format string.

    Simplified implementation - in production, use Confluence API client.
    """
    # This is a placeholder - actual implementation would use Confluence's
    # storage format or use a Confluence API client library
    lines = []
    for item in content:
        if item["type"] == "paragraph":
            text = " ".join(
                c.get("text", "") for c in item.get("content", []) if "text" in c
            )
            lines.append(text)
        elif item["type"] == "heading":
            level = item.get("attrs", {}).get("level", 1)
            text = " ".join(
                c.get("text", "") for c in item.get("content", []) if "text" in c
            )
            lines.append(f"{'#' * level} {text}")

    return "\n\n".join(lines)
