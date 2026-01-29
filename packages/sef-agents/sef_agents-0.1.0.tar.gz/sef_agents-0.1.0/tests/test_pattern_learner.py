"""Tests for Pattern Learning System.

Real execution tests - no mocking of code under test.
Uses temporary directories for isolation.
"""

from pathlib import Path

import pytest

from sef_agents.tools.pattern_learner import (
    Pattern,
    PatternLearner,
    PatternMatch,
    pattern_tool,
)


class TestPattern:
    """Tests for Pattern dataclass."""

    def test_create_pattern(self) -> None:
        """Test Pattern creation with all fields."""
        pattern = Pattern(
            pattern_id="PAT-001",
            name="cursor_pagination",
            domain="api",
            tech=["python", "fastapi"],
            story_id="STORY-001",
            files=["src/api/pagination.py"],
            snippet="def paginate(): pass",
            tags=["pagination", "cursor"],
            description="Cursor-based pagination for APIs",
            captured_at="2024-12-22T10:00:00",
            captured_by="alice@example.com",
        )

        assert pattern.pattern_id == "PAT-001"
        assert pattern.name == "cursor_pagination"
        assert pattern.domain == "api"
        assert "python" in pattern.tech

    def test_pattern_auto_timestamp(self) -> None:
        """Test Pattern sets timestamp automatically."""
        pattern = Pattern(
            pattern_id="PAT-001",
            name="test",
            domain="test",
            tech=[],
            story_id="S1",
            files=[],
            snippet="",
            tags=[],
            description="",
        )

        assert pattern.captured_at != ""
        assert pattern.captured_by != ""


class TestPatternMatch:
    """Tests for PatternMatch dataclass."""

    def test_create_match(self) -> None:
        """Test PatternMatch creation."""
        pattern = Pattern(
            pattern_id="PAT-001",
            name="test",
            domain="api",
            tech=["python"],
            story_id="S1",
            files=[],
            snippet="",
            tags=[],
            description="",
        )

        match = PatternMatch(
            pattern=pattern,
            score=0.75,
            match_reason="domain=api, tech=python",
        )

        assert match.score == 0.75
        assert "domain=api" in match.match_reason


class TestPatternLearner:
    """Tests for PatternLearner class."""

    def test_capture_pattern(self, tmp_path: Path) -> None:
        """Test capturing a new pattern."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        pattern = learner.capture_pattern(
            name="cursor_pagination",
            domain="api",
            tech=["python", "fastapi"],
            story_id="STORY-001",
            files=["src/api/pagination.py"],
            snippet="def paginate(cursor): return []",
            tags=["pagination", "cursor", "api"],
            description="Cursor-based pagination",
        )

        assert pattern.pattern_id == "PAT-001"
        assert pattern.name == "cursor_pagination"
        assert registry.exists()

    def test_capture_increments_id(self, tmp_path: Path) -> None:
        """Test pattern IDs increment correctly."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        p1 = learner.capture_pattern(
            name="pattern1",
            domain="api",
            tech=["python"],
            story_id="S1",
            files=[],
            snippet="",
            tags=[],
            description="First",
        )
        p2 = learner.capture_pattern(
            name="pattern2",
            domain="api",
            tech=["python"],
            story_id="S2",
            files=[],
            snippet="",
            tags=[],
            description="Second",
        )

        assert p1.pattern_id == "PAT-001"
        assert p2.pattern_id == "PAT-002"

    def test_get_all_patterns(self, tmp_path: Path) -> None:
        """Test retrieving all patterns."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        learner.capture_pattern(
            name="p1",
            domain="api",
            tech=["python"],
            story_id="S1",
            files=[],
            snippet="",
            tags=[],
            description="",
        )
        learner.capture_pattern(
            name="p2",
            domain="db",
            tech=["python"],
            story_id="S2",
            files=[],
            snippet="",
            tags=[],
            description="",
        )

        patterns = learner.get_all_patterns()

        assert len(patterns) == 2
        assert patterns[0].name == "p1"
        assert patterns[1].name == "p2"

    def test_get_all_patterns_empty(self, tmp_path: Path) -> None:
        """Test get_all_patterns with no registry."""
        registry = tmp_path / "nonexistent.jsonl"
        learner = PatternLearner(registry_path=registry)

        patterns = learner.get_all_patterns()

        assert patterns == []

    def test_get_pattern_by_id(self, tmp_path: Path) -> None:
        """Test getting specific pattern by ID."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        learner.capture_pattern(
            name="target",
            domain="api",
            tech=["python"],
            story_id="S1",
            files=["file.py"],
            snippet="code",
            tags=["tag"],
            description="desc",
        )

        pattern = learner.get_pattern("PAT-001")

        assert pattern is not None
        assert pattern.name == "target"

    def test_get_pattern_not_found(self, tmp_path: Path) -> None:
        """Test getting non-existent pattern."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        pattern = learner.get_pattern("PAT-999")

        assert pattern is None

    def test_delete_pattern(self, tmp_path: Path) -> None:
        """Test deleting a pattern."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        learner.capture_pattern(
            name="to_delete",
            domain="api",
            tech=[],
            story_id="S1",
            files=[],
            snippet="",
            tags=[],
            description="",
        )
        learner.capture_pattern(
            name="to_keep",
            domain="api",
            tech=[],
            story_id="S2",
            files=[],
            snippet="",
            tags=[],
            description="",
        )

        result = learner.delete_pattern("PAT-001")
        patterns = learner.get_all_patterns()

        assert result is True
        assert len(patterns) == 1
        assert patterns[0].name == "to_keep"

    def test_delete_pattern_not_found(self, tmp_path: Path) -> None:
        """Test deleting non-existent pattern."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        result = learner.delete_pattern("PAT-999")

        assert result is False


class TestPatternMatching:
    """Tests for pattern matching/finding."""

    def test_find_by_domain(self, tmp_path: Path) -> None:
        """Test finding patterns by domain."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        learner.capture_pattern(
            name="api_pattern",
            domain="api",
            tech=["python"],
            story_id="S1",
            files=[],
            snippet="",
            tags=[],
            description="",
        )
        learner.capture_pattern(
            name="db_pattern",
            domain="db",
            tech=["python"],
            story_id="S2",
            files=[],
            snippet="",
            tags=[],
            description="",
        )

        matches = learner.find_patterns(domain="api")

        assert len(matches) == 1
        assert matches[0].pattern.name == "api_pattern"
        assert matches[0].score > 0

    def test_find_by_tech(self, tmp_path: Path) -> None:
        """Test finding patterns by technology."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        learner.capture_pattern(
            name="python_pattern",
            domain="api",
            tech=["python", "fastapi"],
            story_id="S1",
            files=[],
            snippet="",
            tags=[],
            description="",
        )
        learner.capture_pattern(
            name="js_pattern",
            domain="api",
            tech=["javascript", "react"],
            story_id="S2",
            files=[],
            snippet="",
            tags=[],
            description="",
        )

        matches = learner.find_patterns(tech=["python"])

        assert len(matches) == 1
        assert matches[0].pattern.name == "python_pattern"

    def test_find_by_tags(self, tmp_path: Path) -> None:
        """Test finding patterns by tags."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        learner.capture_pattern(
            name="pagination",
            domain="api",
            tech=["python"],
            story_id="S1",
            files=[],
            snippet="",
            tags=["pagination", "cursor"],
            description="",
        )
        learner.capture_pattern(
            name="auth",
            domain="api",
            tech=["python"],
            story_id="S2",
            files=[],
            snippet="",
            tags=["auth", "jwt"],
            description="",
        )

        matches = learner.find_patterns(tags=["pagination"])

        assert len(matches) == 1
        assert matches[0].pattern.name == "pagination"

    def test_find_combined_criteria(self, tmp_path: Path) -> None:
        """Test finding with multiple criteria scores higher."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        learner.capture_pattern(
            name="partial_match",
            domain="api",
            tech=["javascript"],
            story_id="S1",
            files=[],
            snippet="",
            tags=["pagination"],
            description="",
        )
        learner.capture_pattern(
            name="full_match",
            domain="api",
            tech=["python"],
            story_id="S2",
            files=[],
            snippet="",
            tags=["pagination"],
            description="",
        )

        matches = learner.find_patterns(
            domain="api", tech=["python"], tags=["pagination"]
        )

        # Full match should score higher
        assert len(matches) == 2
        assert matches[0].pattern.name == "full_match"
        assert matches[0].score > matches[1].score

    def test_find_respects_limit(self, tmp_path: Path) -> None:
        """Test that limit parameter works."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        for i in range(10):
            learner.capture_pattern(
                name=f"pattern_{i}",
                domain="api",
                tech=["python"],
                story_id=f"S{i}",
                files=[],
                snippet="",
                tags=[],
                description="",
            )

        matches = learner.find_patterns(domain="api", limit=3)

        assert len(matches) == 3


class TestSuggestPatterns:
    """Tests for pattern suggestion."""

    def test_suggest_from_title(self, tmp_path: Path) -> None:
        """Test suggesting patterns based on story title."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        learner.capture_pattern(
            name="cursor_pagination",
            domain="api",
            tech=["python"],
            story_id="S1",
            files=["pagination.py"],
            snippet="def paginate(): pass",
            tags=["pagination", "cursor"],
            description="Pagination pattern",
        )

        result = learner.suggest_patterns(
            "Add pagination to product list", domain="api"
        )

        assert "Similar Patterns Found" in result
        assert "cursor_pagination" in result
        assert "PAT-001" in result

    def test_suggest_no_matches(self, tmp_path: Path) -> None:
        """Test suggestion when no patterns match."""
        registry = tmp_path / "patterns.jsonl"
        learner = PatternLearner(registry_path=registry)

        result = learner.suggest_patterns("Something unique")

        assert "No similar patterns" in result


class TestToolFunctions:
    """Tests for MCP tool functions."""

    def test_capture_pattern_tool(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test capture_pattern_tool function."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        result = pattern_tool(
            action="capture",
            name="test_pattern",
            domain="api",
            tech="python,fastapi",
            story_id="STORY-001",
            files="src/api.py,src/utils.py",
            snippet="def test(): pass",
            tags="test,api",
            description="Test pattern",
        )

        assert "✅ Pattern captured" in result
        assert "PAT-001" in result

    def test_suggest_patterns_tool(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test suggest_patterns_tool function."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        # First capture a pattern
        pattern_tool(
            action="capture",
            name="pagination",
            domain="api",
            tech="python",
            story_id="S1",
            files="pag.py",
            snippet="code",
            tags="pagination",
            description="Pagination",
        )

        result = pattern_tool(
            action="suggest", story_title="Add pagination to users", domain="api"
        )

        assert "pagination" in result.lower()

    def test_get_pattern_tool(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test get_pattern_tool function."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        pattern_tool(
            action="capture",
            name="test_pattern",
            domain="api",
            tech="python",
            story_id="S1",
            files="test.py",
            snippet="def test(): return True",
            tags="test",
            description="Test description",
        )

        result = pattern_tool(action="get", pattern_id="PAT-001")

        assert "test_pattern" in result
        assert "def test(): return True" in result

    def test_get_pattern_tool_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test get_pattern_tool with invalid ID."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        result = pattern_tool(action="get", pattern_id="PAT-999")

        assert "not found" in result

    def test_list_patterns_tool(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_patterns_tool function."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        pattern_tool(
            action="capture",
            name="pattern1",
            domain="api",
            tech="python",
            story_id="S1",
            files="f.py",
            snippet="def pattern1(): pass",
            tags="t1",
            description="d1",
        )
        pattern_tool(
            action="capture",
            name="pattern2",
            domain="db",
            tech="python",
            story_id="S2",
            files="f.py",
            snippet="def pattern2(): pass",
            tags="t2",
            description="d2",
        )

        result = pattern_tool(action="list")

        assert "Pattern Registry" in result
        assert "pattern1" in result
        assert "pattern2" in result

    def test_list_patterns_tool_with_filter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_patterns_tool with domain filter."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        pattern_tool(
            action="capture",
            name="api_pattern",
            domain="api",
            tech="python",
            story_id="S1",
            files="f.py",
            snippet="def api(): pass",
            tags="t1",
            description="d1",
        )
        pattern_tool(
            action="capture",
            name="db_pattern",
            domain="db",
            tech="python",
            story_id="S2",
            files="f.py",
            snippet="def db(): pass",
            tags="t2",
            description="d2",
        )

        result = pattern_tool(action="list", domain="api")

        assert "api_pattern" in result
        assert "db_pattern" not in result

    def test_list_patterns_tool_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_patterns_tool with no patterns."""
        monkeypatch.setattr(
            "sef_agents.utils.git_utils.find_project_root",
            lambda *args, **kwargs: tmp_path,
        )

        result = pattern_tool(action="list")

        assert "No patterns" in result
