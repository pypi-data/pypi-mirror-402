"""Tests for dependency_graph module."""

import tempfile
from pathlib import Path

import pytest

from sef_agents.tools.dependency_graph import (
    DependencyGraph,
    StoryNode,
    generate_dependency_graph,
    get_graph_json,
    parse_req_file,
    scan_requirements_directory,
)


@pytest.fixture
def sample_req_content() -> str:
    """Sample REQ.md content."""
    return """# Requirement: [STORY-001] User Login

**Status:** In Progress
**Priority:** P1

---

## Dependencies

### Story Dependencies

| Dependency | Story ID | Status | Type |
|------------|----------|--------|------|
| Depends On | STORY-000 | Done | Must complete first |
| Blocks | STORY-002 | Draft | Waiting on this story |

## User Story

**As a** user
**I want** to log in
**So that** I can access my account
"""


@pytest.fixture
def req_directory(sample_req_content: str) -> Path:
    """Create temporary directory with REQ.md files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        req_dir = Path(tmpdir) / "requirements"
        req_dir.mkdir()

        # Create STORY-000 (no dependencies, Done)
        story0 = req_dir / "STORY-000-REQ.md"
        story0.write_text(
            """# Requirement: [STORY-000] Setup

**Status:** Done
**Priority:** P1

## User Story
Setup task.
"""
        )

        # Create STORY-001 (depends on STORY-000)
        story1 = req_dir / "STORY-001-REQ.md"
        story1.write_text(sample_req_content)

        # Create STORY-002 (depends on STORY-001)
        story2 = req_dir / "STORY-002-REQ.md"
        story2.write_text(
            """# Requirement: [STORY-002] Dashboard

**Status:** Draft
**Priority:** P2

## Dependencies

### Story Dependencies

| Dependency | Story ID | Status | Type |
|------------|----------|--------|------|
| Depends On | STORY-001 | In Progress | Provides API |

## User Story
Dashboard feature.
"""
        )

        yield req_dir


class TestStoryNode:
    """Tests for StoryNode dataclass."""

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        node = StoryNode(
            story_id="STORY-001",
            status="In Progress",
            depends_on=["STORY-000"],
            blocks=["STORY-002"],
            file_path="/path/to/req.md",
        )
        result = node.to_dict()

        assert result["story_id"] == "STORY-001"
        assert result["status"] == "In Progress"
        assert result["depends_on"] == ["STORY-000"]
        assert result["blocks"] == ["STORY-002"]


class TestDependencyGraph:
    """Tests for DependencyGraph class."""

    def test_add_and_get_node(self) -> None:
        """Test adding and retrieving nodes."""
        graph = DependencyGraph()
        node = StoryNode(story_id="STORY-001", status="Draft")
        graph.add_node(node)

        result = graph.get_node("STORY-001")
        assert result is not None
        assert result.story_id == "STORY-001"

    def test_get_nonexistent_node(self) -> None:
        """Test retrieving nonexistent node."""
        graph = DependencyGraph()
        assert graph.get_node("STORY-999") is None

    def test_to_json(self) -> None:
        """Test JSON serialization."""
        graph = DependencyGraph()
        graph.add_node(StoryNode(story_id="STORY-001", depends_on=["STORY-000"]))

        json_str = graph.to_json()
        assert "STORY-001" in json_str
        assert "STORY-000" in json_str
        assert "depends_on" in json_str

    def test_to_mermaid(self) -> None:
        """Test Mermaid diagram generation."""
        graph = DependencyGraph()
        graph.add_node(StoryNode(story_id="STORY-000", status="Done"))
        graph.add_node(StoryNode(story_id="STORY-001", depends_on=["STORY-000"]))

        mermaid = graph.to_mermaid()
        assert "graph LR" in mermaid
        assert "STORY-000" in mermaid
        assert "STORY-001" in mermaid
        assert "STORY-000 --> STORY-001" in mermaid


class TestParseReqFile:
    """Tests for parse_req_file function."""

    def test_parse_valid_req(self, req_directory: Path) -> None:
        """Test parsing valid REQ.md file."""
        req_file = req_directory / "STORY-001-REQ.md"
        node = parse_req_file(req_file)

        assert node is not None
        assert node.story_id == "STORY-001"
        assert node.status == "In Progress"
        assert "STORY-000" in node.depends_on
        assert "STORY-002" in node.blocks

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing nonexistent file."""
        result = parse_req_file(Path("/nonexistent/req.md"))
        assert result is None

    def test_parse_file_without_story_id(self) -> None:
        """Test parsing file without story ID."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Some other document\n\nNo story ID here.")
            f.flush()
            result = parse_req_file(Path(f.name))
            assert result is None


class TestScanRequirementsDirectory:
    """Tests for scan_requirements_directory function."""

    def test_scan_directory(self, req_directory: Path) -> None:
        """Test scanning requirements directory."""
        graph = scan_requirements_directory(req_directory)

        assert len(graph.nodes) == 3
        assert "STORY-000" in graph.nodes
        assert "STORY-001" in graph.nodes
        assert "STORY-002" in graph.nodes

    def test_scan_nonexistent_directory(self) -> None:
        """Test scanning nonexistent directory."""
        graph = scan_requirements_directory("/nonexistent/path")
        assert len(graph.errors) > 0

    def test_scan_empty_directory(self) -> None:
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = scan_requirements_directory(tmpdir)
            assert len(graph.nodes) == 0


class TestGenerateDependencyGraph:
    """Tests for generate_dependency_graph function."""

    def test_generate_artifact(self, req_directory: Path) -> None:
        """Test generating dependency graph artifact."""
        result = generate_dependency_graph(str(req_directory))

        assert "Generated:" in result
        assert "3 stories" in result

        # Check artifact was created
        artifact = req_directory / "DEPENDENCY_GRAPH.md"
        assert artifact.exists()

        content = artifact.read_text()
        assert "```mermaid" in content
        assert "STORY-000" in content

    def test_generate_no_stories(self) -> None:
        """Test generating with no stories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_dependency_graph(tmpdir)
            assert "No REQ.md files found" in result


class TestGetGraphJson:
    """Tests for get_graph_json function."""

    def test_get_json(self, req_directory: Path) -> None:
        """Test getting graph as JSON."""
        json_str = get_graph_json(str(req_directory))

        assert "STORY-000" in json_str
        assert "nodes" in json_str
        assert "edges" in json_str
