"""Tests for Greenfield integration features."""

from unittest.mock import patch

import pytest
from sef_agents.tools.context_graph import ContextGraph, ContextNode
from sef_agents.tools.pattern_learner import PatternLearner
from sef_agents.tools.workflow_tools import _auto_capture_decision


@pytest.fixture
def mock_context_graph(tmp_path):
    """Provide a ContextGraph with temporary storage."""
    graph = ContextGraph(root=tmp_path)

    # Patch the source since functions import it locally
    with patch("sef_agents.tools.context_graph.get_context_graph", return_value=graph):
        yield graph


def test_auto_capture_decision_creates_node(mock_context_graph):
    """Verify _auto_capture_decision adds a decision node."""
    story_id = "STORY-123"
    phase = "design"
    summary = "Design completed"

    _auto_capture_decision(story_id, phase, summary)

    # Verify node exists
    nodes = mock_context_graph.get_nodes_by_story(story_id)
    assert len(nodes) == 1
    assert nodes[0].node_type == "decision"
    assert f"[{phase}]" in nodes[0].content
    assert summary in nodes[0].content


def test_pattern_capture_adds_graph_node(mock_context_graph, tmp_path):
    """Verify capturing a pattern adds a pattern node and link to story."""
    registry_path = tmp_path / "patterns.jsonl"
    learner = PatternLearner(registry_path=registry_path)

    # 1. Create story node first
    story_id = "STORY-456"
    story_node = ContextNode(id=story_id, node_type="story", content="Test Story")
    mock_context_graph.add_node(story_node)

    # 2. Capture pattern
    pattern = learner.capture_pattern(
        name="Test Pattern",
        domain="test",
        tech=["python"],
        story_id=story_id,
        files=["test.py"],
        snippet="code",
        tags=["tag"],
        description="desc",
    )

    # 3. Verify graph node created
    pattern_node = mock_context_graph.get_node(pattern.pattern_id)
    assert pattern_node is not None
    assert pattern_node.node_type == "pattern"
    assert pattern_node.content == "Test Pattern (python)"

    # 4. Verify link to story
    related = mock_context_graph.get_related(story_id, edge_types=["led_to"])
    assert any(n.id == pattern.pattern_id for n in related)


def test_auto_capture_handles_errors_gracefully(mock_context_graph):
    """Verify error in auto-capture propagates OSError (no bare except)."""
    with patch(
        "sef_agents.tools.context_graph.ContextGraph.save",
        side_effect=OSError("Save failed"),
    ):
        # Per E002 policy: exceptions must propagate
        with pytest.raises(OSError, match="Save failed"):
            _auto_capture_decision("S-1", "phase", "summary")
