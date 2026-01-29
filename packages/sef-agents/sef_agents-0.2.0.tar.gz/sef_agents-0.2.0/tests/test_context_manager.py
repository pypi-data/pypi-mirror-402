"""Tests for Context Persistence Manager.

Real execution tests - no mocking of the code under test.
Each test uses temporary directories for isolation.
"""

from pathlib import Path

import pytest

from sef_agents.tools.context_manager import (
    ContextEntry,
    ContextManager,
    add_context,
    get_context,
)


class TestContextEntry:
    """Tests for ContextEntry dataclass."""

    def test_create_entry(self) -> None:
        """Test ContextEntry creation with all fields."""
        entry = ContextEntry(
            timestamp="2024-12-22T10:00:00",
            entry_type="decision",
            content="Use Stripe v3",
            user="alice@example.com",
            metadata={"reason": "v2 deprecated"},
        )
        assert entry.timestamp == "2024-12-22T10:00:00"
        assert entry.entry_type == "decision"
        assert entry.content == "Use Stripe v3"
        assert entry.user == "alice@example.com"
        assert entry.metadata == {"reason": "v2 deprecated"}

    def test_entry_without_metadata(self) -> None:
        """Test ContextEntry with no metadata."""
        entry = ContextEntry(
            timestamp="2024-12-22T10:00:00",
            entry_type="note",
            content="Simple note",
            user="bob@example.com",
        )
        assert entry.metadata is None


class TestContextManager:
    """Tests for ContextManager class."""

    def test_add_project_entry(self, tmp_path: Path) -> None:
        """Test adding entry to project context."""
        manager = ContextManager(root=tmp_path)

        entry = manager.add_entry(
            layer="project",
            entry_type="convention",
            content="Always use structlog",
        )

        assert entry.entry_type == "convention"
        assert entry.content == "Always use structlog"
        assert (tmp_path / "project.jsonl").exists()

    def test_add_story_entry(self, tmp_path: Path) -> None:
        """Test adding entry to story context."""
        manager = ContextManager(root=tmp_path)

        entry = manager.add_entry(
            layer="story",
            entry_type="decision",
            content="Using async approach",
            identifier="STORY-042",
        )

        assert entry.entry_type == "decision"
        assert (tmp_path / "story_STORY-042.jsonl").exists()

    def test_add_epic_entry(self, tmp_path: Path) -> None:
        """Test adding entry to epic context."""
        manager = ContextManager(root=tmp_path)

        entry = manager.add_entry(
            layer="epic",
            entry_type="pattern",
            content="Repository pattern for data access",
            identifier="EPIC-10",
        )

        assert entry.entry_type == "pattern"
        assert (tmp_path / "epic_EPIC-10.jsonl").exists()

    def test_story_requires_identifier(self, tmp_path: Path) -> None:
        """Test that story layer requires identifier."""
        manager = ContextManager(root=tmp_path)

        with pytest.raises(ValueError, match="story layer requires identifier"):
            manager.add_entry(
                layer="story",
                entry_type="note",
                content="Test",
            )

    def test_invalid_layer(self, tmp_path: Path) -> None:
        """Test error for invalid layer."""
        manager = ContextManager(root=tmp_path)

        with pytest.raises(ValueError, match="Invalid layer"):
            manager.add_entry(
                layer="invalid",
                entry_type="note",
                content="Test",
            )

    def test_get_entries_empty(self, tmp_path: Path) -> None:
        """Test getting entries from non-existent file."""
        manager = ContextManager(root=tmp_path)

        entries = manager.get_entries("project")

        assert entries == []

    def test_get_entries_single(self, tmp_path: Path) -> None:
        """Test getting a single entry."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("project", "decision", "Use Python 3.12")

        entries = manager.get_entries("project")

        assert len(entries) == 1
        assert entries[0].content == "Use Python 3.12"

    def test_get_entries_multiple_ordered(self, tmp_path: Path) -> None:
        """Test entries returned most recent first."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("project", "decision", "First decision")
        manager.add_entry("project", "decision", "Second decision")
        manager.add_entry("project", "decision", "Third decision")

        entries = manager.get_entries("project")

        # Most recent first
        assert entries[0].content == "Third decision"
        assert entries[1].content == "Second decision"
        assert entries[2].content == "First decision"

    def test_get_entries_respects_limit(self, tmp_path: Path) -> None:
        """Test that limit parameter works."""
        manager = ContextManager(root=tmp_path)

        for i in range(10):
            manager.add_entry("project", "note", f"Note {i}")

        entries = manager.get_entries("project", limit=3)

        assert len(entries) == 3
        # Should be most recent 3
        assert entries[0].content == "Note 9"
        assert entries[1].content == "Note 8"
        assert entries[2].content == "Note 7"

    def test_get_entries_default_limits(self, tmp_path: Path) -> None:
        """Test default limits are applied per layer."""
        limits = {"project": 2, "story": 3}
        manager = ContextManager(root=tmp_path, limits=limits)

        for i in range(5):
            manager.add_entry("project", "note", f"Project note {i}")
            manager.add_entry("story", "note", f"Story note {i}", identifier="S1")

        project_entries = manager.get_entries("project")
        story_entries = manager.get_entries("story", identifier="S1")

        assert len(project_entries) == 2
        assert len(story_entries) == 3


class TestCombinedContext:
    """Tests for combined context retrieval."""

    def test_combined_empty(self, tmp_path: Path) -> None:
        """Test combined context when all layers empty."""
        manager = ContextManager(root=tmp_path)

        result = manager.get_combined_context()

        assert result["project"] == []
        assert result["epic"] == []
        assert result["story"] == []

    def test_combined_project_only(self, tmp_path: Path) -> None:
        """Test combined context with only project entries."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("project", "convention", "Use type hints")

        result = manager.get_combined_context()

        assert len(result["project"]) == 1
        assert result["project"][0].content == "Use type hints"
        assert result["epic"] == []
        assert result["story"] == []

    def test_combined_all_layers(self, tmp_path: Path) -> None:
        """Test combined context from all layers."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("project", "convention", "Project convention")
        manager.add_entry("epic", "pattern", "Epic pattern", identifier="E1")
        manager.add_entry("story", "decision", "Story decision", identifier="S1")

        result = manager.get_combined_context(story_id="S1", epic_id="E1")

        assert len(result["project"]) == 1
        assert len(result["epic"]) == 1
        assert len(result["story"]) == 1

    def test_combined_wrong_identifiers(self, tmp_path: Path) -> None:
        """Test combined context with non-matching identifiers."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("story", "decision", "Story S1 decision", identifier="S1")

        # Request different story
        result = manager.get_combined_context(story_id="S2")

        assert result["story"] == []


class TestFormatForPrompt:
    """Tests for prompt formatting."""

    def test_format_empty(self, tmp_path: Path) -> None:
        """Test format returns empty string when no context."""
        manager = ContextManager(root=tmp_path)

        result = manager.format_for_prompt()

        assert result == ""

    def test_format_project_context(self, tmp_path: Path) -> None:
        """Test format includes project context."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("project", "convention", "Use structlog")

        result = manager.format_for_prompt()

        assert "Project Conventions" in result
        assert "[convention] Use structlog" in result

    def test_format_all_layers(self, tmp_path: Path) -> None:
        """Test format includes all layers."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("project", "convention", "Type hints required")
        manager.add_entry("epic", "pattern", "Service layer pattern", identifier="E1")
        manager.add_entry("story", "blocker", "API rate limit hit", identifier="S1")

        result = manager.format_for_prompt(story_id="S1", epic_id="E1")

        assert "Project Conventions" in result
        assert "Epic (E1)" in result
        assert "Story (S1)" in result
        assert "[convention]" in result
        assert "[pattern]" in result
        assert "[blocker]" in result

    def test_format_has_markers(self, tmp_path: Path) -> None:
        """Test format has start/end markers."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("project", "note", "Test note")

        result = manager.format_for_prompt()

        assert "--- SESSION CONTEXT" in result
        assert "--- END CONTEXT ---" in result


class TestPrune:
    """Tests for context pruning."""

    def test_prune_empty_file(self, tmp_path: Path) -> None:
        """Test prune on non-existent file returns 0."""
        manager = ContextManager(root=tmp_path)

        removed = manager.prune("project", keep=5)

        assert removed == 0

    def test_prune_under_limit(self, tmp_path: Path) -> None:
        """Test prune when entries under limit."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("project", "note", "Note 1")
        manager.add_entry("project", "note", "Note 2")

        removed = manager.prune("project", keep=5)

        assert removed == 0
        assert len(manager.get_entries("project", limit=100)) == 2

    def test_prune_over_limit(self, tmp_path: Path) -> None:
        """Test prune removes oldest entries."""
        manager = ContextManager(root=tmp_path)

        for i in range(10):
            manager.add_entry("project", "note", f"Note {i}")

        removed = manager.prune("project", keep=3)

        assert removed == 7

        entries = manager.get_entries("project", limit=100)
        assert len(entries) == 3
        # Should keep most recent
        assert entries[0].content == "Note 9"
        assert entries[2].content == "Note 7"


class TestClear:
    """Tests for context clearing."""

    def test_clear_non_existent(self, tmp_path: Path) -> None:
        """Test clear on non-existent file returns True."""
        manager = ContextManager(root=tmp_path)

        result = manager.clear("project")

        assert result is True

    def test_clear_existing(self, tmp_path: Path) -> None:
        """Test clear removes file."""
        manager = ContextManager(root=tmp_path)

        manager.add_entry("project", "note", "Test")
        file_path = tmp_path / "project.jsonl"
        assert file_path.exists()

        result = manager.clear("project")

        assert result is True
        assert not file_path.exists()


class TestToolFunctions:
    """Tests for convenience tool functions."""

    def test_add_context_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test add_context tool function."""
        # Mock find_project_root to return tmp_path
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        result = add_context(
            layer="project",
            entry_type="decision",
            content="Use pytest",
        )

        assert "✅ Context added" in result
        assert "Use pytest" in result

    def test_add_context_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test add_context error handling."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        result = add_context(
            layer="story",
            entry_type="note",
            content="Missing identifier",
            identifier=None,
        )

        assert "❌ Error" in result

    def test_get_context_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test get_context when empty."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        result = get_context()

        assert "No context found" in result

    def test_get_context_with_entries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test get_context returns formatted context."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        add_context("project", "convention", "Always document functions")

        result = get_context()

        assert "Project Conventions" in result
        assert "Always document functions" in result
