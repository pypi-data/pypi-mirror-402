"""Unit tests for JSON serialization and output."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory


from sef_agents.models.hierarchy import Epic
from sef_agents.tools.json_output import generate_json_output, serialize_to_json
from sef_agents.tools.requirements_serializer import (
    epic_to_json,
    feature_to_json,
    story_to_json,
)


def test_serialize_to_json_dict():
    """Test serializing dictionary to JSON."""
    data = {"key": "value", "number": 42}

    json_str = serialize_to_json(data)

    parsed = json.loads(json_str)
    assert parsed == data


def test_serialize_to_json_pydantic_model():
    """Test serializing Pydantic model to JSON."""
    epic = Epic(epic_id="EPIC-001", title="Test Epic", description="Test")

    json_str = serialize_to_json(epic)

    parsed = json.loads(json_str)
    assert parsed["epic_id"] == "EPIC-001"
    assert parsed["title"] == "Test Epic"


def test_generate_json_output_from_dict():
    """Test generating JSON output file from dictionary."""
    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.md"
        data = {"test": "data", "number": 123}

        json_path = generate_json_output("test", data, output_path)

        assert json_path.exists()
        assert json_path.suffix == ".json"
        content = json.loads(json_path.read_text())
        assert content == data


def test_generate_json_output_auto_extension():
    """Test JSON output generation with automatic .json extension."""
    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report"
        data = {"report": "content"}

        json_path = generate_json_output("report", data, output_path)

        assert json_path.suffix == ".json"
        assert json_path.stem == "report"


def test_story_to_json_basic():
    """Test converting story markdown to JSON."""
    with TemporaryDirectory() as tmpdir:
        story_path = Path(tmpdir) / "STORY-001.md"
        story_path.write_text(
            """# Requirement: [STORY-001] Test Story

**Status:** Draft
**Priority:** P1

## User Story
As a user, I want to test, so that I can verify functionality.

## Description
Test description

## Acceptance Criteria
### AC-1: Test AC
**Given** a precondition
**When** an action occurs
**Then** a result happens
""",
            encoding="utf-8",
        )

        story_data = story_to_json(story_path)

        assert story_data["story_id"] == "STORY-001"
        assert story_data["title"] == "Test Story"
        assert story_data["status"] == "Draft"
        assert story_data["priority"] == "P1"


def test_epic_to_json_basic():
    """Test converting epic markdown to JSON."""
    with TemporaryDirectory() as tmpdir:
        epic_path = Path(tmpdir) / "EPIC-001.md"
        epic_path.write_text(
            """# Epic: [EPIC-001] Test Epic

**Status:** Draft

## Description
Test epic description
""",
            encoding="utf-8",
        )

        epic_data = epic_to_json(epic_path)

        assert epic_data["epic_id"] == "EPIC-001"
        assert epic_data["title"] == "Test Epic"
        assert epic_data["status"] == "Draft"


def test_feature_to_json_basic():
    """Test converting feature markdown to JSON."""
    with TemporaryDirectory() as tmpdir:
        feature_path = Path(tmpdir) / "FEAT-001.md"
        feature_path.write_text(
            """# Feature: [FEAT-001] Test Feature

**Epic:** EPIC-001
**Status:** Draft

## Description
Test feature description
""",
            encoding="utf-8",
        )

        feature_data = feature_to_json(feature_path)

        assert feature_data["feature_id"] == "FEAT-001"
        assert feature_data["epic_id"] == "EPIC-001"
        assert feature_data["title"] == "Test Feature"


def test_story_to_json_with_hierarchy():
    """Test story JSON includes epic_id and feature_id."""
    with TemporaryDirectory() as tmpdir:
        story_path = Path(tmpdir) / "STORY-001.md"
        story_path.write_text(
            """# Requirement: [STORY-001] Test Story

**Epic:** EPIC-001
**Feature:** FEAT-001
**Status:** Draft

## User Story
As a user, I want to test, so that I can verify.
""",
            encoding="utf-8",
        )

        story_data = story_to_json(story_path)

        assert story_data["epic_id"] == "EPIC-001"
        assert story_data["feature_id"] == "FEAT-001"
