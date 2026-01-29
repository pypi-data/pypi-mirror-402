"""Tests for sequencing_engine module."""

import tempfile
from pathlib import Path

import pytest

from sef_agents.tools.dependency_graph import DependencyGraph, StoryNode
from sef_agents.tools.sequencing_engine import (
    SequencingResult,
    analyze_directory,
    get_blocked_stories,
    get_completed_stories,
    get_critical_path,
    get_critical_path_report,
    get_next_ready_stories,
    get_ready_stories,
)


@pytest.fixture
def sample_graph() -> DependencyGraph:
    """Create sample dependency graph for testing."""
    graph = DependencyGraph()

    # STORY-000: Done, no dependencies (root)
    graph.add_node(StoryNode(story_id="STORY-000", status="Done"))

    # STORY-001: In Progress, depends on STORY-000
    graph.add_node(
        StoryNode(story_id="STORY-001", status="In Progress", depends_on=["STORY-000"])
    )

    # STORY-002: Draft, depends on STORY-001
    graph.add_node(
        StoryNode(story_id="STORY-002", status="Draft", depends_on=["STORY-001"])
    )

    # STORY-003: Draft, depends on STORY-000 (parallel to STORY-001)
    graph.add_node(
        StoryNode(story_id="STORY-003", status="Draft", depends_on=["STORY-000"])
    )

    # STORY-004: Draft, depends on both STORY-002 and STORY-003
    graph.add_node(
        StoryNode(
            story_id="STORY-004",
            status="Draft",
            depends_on=["STORY-002", "STORY-003"],
        )
    )

    return graph


@pytest.fixture
def req_directory() -> Path:
    """Create temporary directory with REQ.md files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        req_dir = Path(tmpdir)

        # STORY-000: Done
        (req_dir / "STORY-000-REQ.md").write_text(
            """# Requirement: [STORY-000] Setup
**Status:** Done
"""
        )

        # STORY-001: In Progress, depends on STORY-000
        (req_dir / "STORY-001-REQ.md").write_text(
            """# Requirement: [STORY-001] Auth
**Status:** In Progress

## Dependencies
| Dependency | Story ID | Status | Type |
|------------|----------|--------|------|
| Depends On | STORY-000 | Done | - |
"""
        )

        # STORY-002: Draft, depends on STORY-001
        (req_dir / "STORY-002-REQ.md").write_text(
            """# Requirement: [STORY-002] Dashboard
**Status:** Draft

## Dependencies
| Dependency | Story ID | Status | Type |
|------------|----------|--------|------|
| Depends On | STORY-001 | In Progress | - |
"""
        )

        yield req_dir


class TestSequencingResult:
    """Tests for SequencingResult dataclass."""

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        result = SequencingResult(
            ready_stories=["STORY-001"],
            blocked_stories={"STORY-002": ["STORY-001"]},
            critical_path=["STORY-000", "STORY-001"],
            completed_stories=["STORY-000"],
        )
        d = result.to_dict()

        assert d["ready"] == ["STORY-001"]
        assert d["blocked"] == {"STORY-002": ["STORY-001"]}
        assert d["critical_path"] == ["STORY-000", "STORY-001"]

    def test_to_json(self) -> None:
        """Test JSON serialization."""
        result = SequencingResult(ready_stories=["STORY-001"])
        json_str = result.to_json()

        assert "STORY-001" in json_str
        assert "ready" in json_str


class TestGetReadyStories:
    """Tests for get_ready_stories function."""

    def test_ready_with_completed_deps(self, sample_graph: DependencyGraph) -> None:
        """Test finding stories with completed dependencies."""
        ready = get_ready_stories(sample_graph)

        # STORY-001 depends on STORY-000 (Done) - but STORY-001 is In Progress
        # STORY-003 depends on STORY-000 (Done) - should be ready
        assert "STORY-003" in ready

    def test_excludes_completed(self, sample_graph: DependencyGraph) -> None:
        """Test that completed stories are excluded."""
        ready = get_ready_stories(sample_graph)
        assert "STORY-000" not in ready

    def test_excludes_blocked(self, sample_graph: DependencyGraph) -> None:
        """Test that blocked stories are excluded."""
        ready = get_ready_stories(sample_graph)
        # STORY-002 depends on STORY-001 (In Progress) - should NOT be ready
        assert "STORY-002" not in ready


class TestGetBlockedStories:
    """Tests for get_blocked_stories function."""

    def test_blocked_stories(self, sample_graph: DependencyGraph) -> None:
        """Test finding blocked stories."""
        blocked = get_blocked_stories(sample_graph)

        # STORY-002 blocked by STORY-001
        assert "STORY-002" in blocked
        assert "STORY-001" in blocked["STORY-002"]

        # STORY-004 blocked by STORY-002 and STORY-003
        assert "STORY-004" in blocked

    def test_excludes_completed(self, sample_graph: DependencyGraph) -> None:
        """Test that completed stories are excluded."""
        blocked = get_blocked_stories(sample_graph)
        assert "STORY-000" not in blocked


class TestGetCompletedStories:
    """Tests for get_completed_stories function."""

    def test_completed_stories(self, sample_graph: DependencyGraph) -> None:
        """Test finding completed stories."""
        completed = get_completed_stories(sample_graph)

        assert "STORY-000" in completed
        assert len(completed) == 1


class TestGetCriticalPath:
    """Tests for get_critical_path function."""

    def test_critical_path(self, sample_graph: DependencyGraph) -> None:
        """Test finding critical path."""
        path = get_critical_path(sample_graph)

        # Longest path should start from STORY-000
        assert path[0] == "STORY-000"
        # Should include multiple nodes
        assert len(path) >= 3

    def test_empty_graph(self) -> None:
        """Test with empty graph."""
        graph = DependencyGraph()
        path = get_critical_path(graph)
        assert path == []


class TestAnalyzeDirectory:
    """Tests for analyze_directory function."""

    def test_analyze(self, req_directory: Path) -> None:
        """Test analyzing requirements directory."""
        result = analyze_directory(req_directory)

        assert len(result.errors) == 0
        assert len(result.completed_stories) == 1
        assert "STORY-000" in result.completed_stories

    def test_nonexistent_directory(self) -> None:
        """Test with nonexistent directory."""
        result = analyze_directory("/nonexistent/path")
        assert len(result.errors) > 0


class TestGetNextReadyStories:
    """Tests for get_next_ready_stories function."""

    def test_formatted_output(self, req_directory: Path) -> None:
        """Test formatted output."""
        output = get_next_ready_stories(str(req_directory))

        assert "Ready Stories" in output or "Blocked Stories" in output


class TestGetCriticalPathReport:
    """Tests for get_critical_path_report function."""

    def test_report(self, req_directory: Path) -> None:
        """Test critical path report."""
        output = get_critical_path_report(str(req_directory))

        assert "Critical Path" in output or "No critical path" in output
