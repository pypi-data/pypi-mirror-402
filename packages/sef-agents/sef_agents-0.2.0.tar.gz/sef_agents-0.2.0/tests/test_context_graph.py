"""Tests for Context Graph module.

Real execution tests - no mocking of the code under test.
Each test uses temporary directories for isolation.
"""

from pathlib import Path

import pytest

from sef_agents.tools.context_graph import (
    ContextEdge,
    ContextGraph,
    ContextNode,
    VALID_EDGE_TYPES,
    VALID_NODE_TYPES,
    reset_context_graph,
)


class TestContextNode:
    """Tests for ContextNode dataclass."""

    def test_create_node(self) -> None:
        """Test ContextNode creation with all fields."""
        node = ContextNode(
            id="decision-001",
            node_type="decision",
            content="Use Stripe v3 API",
            story_id="STORY-042",
            metadata={"reason": "v2 deprecated"},
        )
        assert node.id == "decision-001"
        assert node.node_type == "decision"
        assert node.content == "Use Stripe v3 API"
        assert node.story_id == "STORY-042"
        assert node.metadata == {"reason": "v2 deprecated"}
        assert node.timestamp  # Auto-generated

    def test_node_to_dict(self) -> None:
        """Test ContextNode serialization."""
        node = ContextNode(
            id="pattern-001",
            node_type="pattern",
            content="Repository pattern",
        )
        d = node.to_dict()
        assert d["id"] == "pattern-001"
        assert d["node_type"] == "pattern"
        assert d["content"] == "Repository pattern"

    def test_node_from_dict(self) -> None:
        """Test ContextNode deserialization."""
        data = {
            "id": "file-001",
            "node_type": "file",
            "content": "src/payment.py",
            "timestamp": "2024-01-01T00:00:00",
            "story_id": "STORY-001",
            "metadata": {"lines": 150},
        }
        node = ContextNode.from_dict(data)
        assert node.id == "file-001"
        assert node.node_type == "file"
        assert node.content == "src/payment.py"
        assert node.metadata == {"lines": 150}


class TestContextEdge:
    """Tests for ContextEdge dataclass."""

    def test_create_edge(self) -> None:
        """Test ContextEdge creation."""
        edge = ContextEdge(
            from_id="decision-001",
            to_id="file-001",
            edge_type="affects",
        )
        assert edge.from_id == "decision-001"
        assert edge.to_id == "file-001"
        assert edge.edge_type == "affects"
        assert edge.timestamp

    def test_edge_to_dict(self) -> None:
        """Test ContextEdge serialization."""
        edge = ContextEdge(
            from_id="a",
            to_id="b",
            edge_type="led_to",
            metadata={"reason": "test"},
        )
        d = edge.to_dict()
        assert d["from_id"] == "a"
        assert d["to_id"] == "b"
        assert d["edge_type"] == "led_to"
        assert d["metadata"] == {"reason": "test"}


class TestContextGraph:
    """Tests for ContextGraph class."""

    def test_add_node(self, tmp_path: Path) -> None:
        """Test adding a node to the graph."""
        graph = ContextGraph(root=tmp_path)

        node = ContextNode(id="n1", node_type="decision", content="Test decision")
        graph.add_node(node)

        assert graph.node_count == 1
        retrieved = graph.get_node("n1")
        assert retrieved is not None
        assert retrieved.content == "Test decision"

    def test_add_node_invalid_type(self, tmp_path: Path) -> None:
        """Test adding node with invalid type raises error."""
        graph = ContextGraph(root=tmp_path)
        node = ContextNode(id="n1", node_type="invalid", content="Test")  # type: ignore

        with pytest.raises(ValueError, match="Invalid node_type"):
            graph.add_node(node)

    def test_add_edge(self, tmp_path: Path) -> None:
        """Test adding an edge between nodes."""
        graph = ContextGraph(root=tmp_path)

        graph.add_node(ContextNode(id="n1", node_type="decision", content="Decision 1"))
        graph.add_node(ContextNode(id="n2", node_type="decision", content="Decision 2"))
        graph.add_edge("n1", "n2", "led_to")

        assert graph.edge_count == 1

    def test_add_edge_invalid_type(self, tmp_path: Path) -> None:
        """Test adding edge with invalid type raises error."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="n1", node_type="decision", content="D1"))
        graph.add_node(ContextNode(id="n2", node_type="decision", content="D2"))

        with pytest.raises(ValueError, match="Invalid edge_type"):
            graph.add_edge("n1", "n2", "invalid")  # type: ignore

    def test_add_edge_missing_source(self, tmp_path: Path) -> None:
        """Test adding edge with missing source node raises error."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="n2", node_type="decision", content="D2"))

        with pytest.raises(ValueError, match="Source node not found"):
            graph.add_edge("n1", "n2", "led_to")

    def test_add_edge_missing_target(self, tmp_path: Path) -> None:
        """Test adding edge with missing target node raises error."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="n1", node_type="decision", content="D1"))

        with pytest.raises(ValueError, match="Target node not found"):
            graph.add_edge("n1", "n2", "led_to")

    def test_get_node_not_found(self, tmp_path: Path) -> None:
        """Test getting non-existent node returns None."""
        graph = ContextGraph(root=tmp_path)
        assert graph.get_node("nonexistent") is None

    def test_get_related_outgoing(self, tmp_path: Path) -> None:
        """Test getting related nodes via outgoing edges."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="d1", node_type="decision", content="Decision"))
        graph.add_node(ContextNode(id="f1", node_type="file", content="file.py"))
        graph.add_node(ContextNode(id="f2", node_type="file", content="other.py"))
        graph.add_edge("d1", "f1", "affects")
        graph.add_edge("d1", "f2", "affects")

        related = graph.get_related("d1", direction="outgoing")
        assert len(related) == 2

    def test_get_related_incoming(self, tmp_path: Path) -> None:
        """Test getting related nodes via incoming edges."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="a1", node_type="agent_session", content="dev"))
        graph.add_node(ContextNode(id="i1", node_type="issue", content="Bug"))
        graph.add_edge("a1", "i1", "discovered_by")

        related = graph.get_related("i1", direction="incoming")
        assert len(related) == 1
        assert related[0].id == "a1"

    def test_get_related_filter_edge_type(self, tmp_path: Path) -> None:
        """Test filtering related nodes by edge type."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="d1", node_type="decision", content="D1"))
        graph.add_node(ContextNode(id="d2", node_type="decision", content="D2"))
        graph.add_node(ContextNode(id="f1", node_type="file", content="file.py"))
        graph.add_edge("d1", "d2", "led_to")
        graph.add_edge("d1", "f1", "affects")

        related = graph.get_related("d1", edge_types=["led_to"])
        assert len(related) == 1
        assert related[0].id == "d2"


class TestCausalityChain:
    """Tests for causality chain traversal."""

    def test_causality_chain_simple(self, tmp_path: Path) -> None:
        """Test simple causality chain traversal."""
        graph = ContextGraph(root=tmp_path)

        # Create chain: d1 -> d2 -> d3
        graph.add_node(ContextNode(id="d1", node_type="decision", content="First"))
        graph.add_node(ContextNode(id="d2", node_type="decision", content="Second"))
        graph.add_node(ContextNode(id="d3", node_type="decision", content="Third"))
        graph.add_edge("d1", "d2", "led_to")
        graph.add_edge("d2", "d3", "led_to")

        chain = graph.get_causality_chain("d3")

        assert len(chain) == 3
        assert chain[0].id == "d1"
        assert chain[1].id == "d2"
        assert chain[2].id == "d3"

    def test_causality_chain_no_predecessors(self, tmp_path: Path) -> None:
        """Test causality chain for node with no predecessors."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="d1", node_type="decision", content="Root"))

        chain = graph.get_causality_chain("d1")

        assert len(chain) == 1
        assert chain[0].id == "d1"

    def test_causality_chain_nonexistent(self, tmp_path: Path) -> None:
        """Test causality chain for non-existent node."""
        graph = ContextGraph(root=tmp_path)
        chain = graph.get_causality_chain("nonexistent")
        assert chain == []


class TestNodeQueries:
    """Tests for node query methods."""

    def test_get_nodes_by_story(self, tmp_path: Path) -> None:
        """Test getting nodes by story ID."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(
            ContextNode(
                id="d1", node_type="decision", content="D1", story_id="STORY-001"
            )
        )
        graph.add_node(
            ContextNode(
                id="d2", node_type="decision", content="D2", story_id="STORY-001"
            )
        )
        graph.add_node(
            ContextNode(
                id="d3", node_type="decision", content="D3", story_id="STORY-002"
            )
        )

        nodes = graph.get_nodes_by_story("STORY-001")
        assert len(nodes) == 2
        assert all(n.story_id == "STORY-001" for n in nodes)

    def test_get_nodes_by_type(self, tmp_path: Path) -> None:
        """Test getting nodes by type."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="d1", node_type="decision", content="D1"))
        graph.add_node(ContextNode(id="f1", node_type="file", content="file.py"))
        graph.add_node(ContextNode(id="d2", node_type="decision", content="D2"))

        decisions = graph.get_nodes_by_type("decision")
        assert len(decisions) == 2
        assert all(n.node_type == "decision" for n in decisions)


class TestPersistence:
    """Tests for graph persistence."""

    def test_to_json(self, tmp_path: Path) -> None:
        """Test JSON serialization."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="n1", node_type="decision", content="Test"))

        json_str = graph.to_json()
        assert "n1" in json_str
        assert "decision" in json_str

    def test_from_json(self, tmp_path: Path) -> None:
        """Test JSON deserialization."""
        json_str = """
        {
            "nodes": [
                {"id": "n1", "node_type": "decision", "content": "Test", "timestamp": "", "story_id": "", "metadata": {}}
            ],
            "edges": []
        }
        """
        graph = ContextGraph.from_json(json_str, root=tmp_path)

        assert graph.node_count == 1
        node = graph.get_node("n1")
        assert node is not None
        assert node.content == "Test"

    def test_save_and_load(self, tmp_path: Path) -> None:
        """Test saving and loading graph from disk."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="d1", node_type="decision", content="Decision 1"))
        graph.add_node(ContextNode(id="d2", node_type="decision", content="Decision 2"))
        graph.add_edge("d1", "d2", "led_to")

        saved_path = graph.save()
        assert saved_path.exists()

        # Load into new graph
        loaded = ContextGraph.load(root=tmp_path)
        assert loaded.node_count == 2
        assert loaded.edge_count == 1
        assert loaded.get_node("d1") is not None

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        """Test loading from nonexistent file returns empty graph."""
        graph = ContextGraph.load(root=tmp_path)
        assert graph.node_count == 0


class TestVisualization:
    """Tests for visualization export."""

    def test_to_visualization_json(self, tmp_path: Path) -> None:
        """Test export for react-flow visualization."""
        graph = ContextGraph(root=tmp_path)
        graph.add_node(ContextNode(id="d1", node_type="decision", content="Use Stripe"))
        graph.add_node(ContextNode(id="f1", node_type="file", content="payment.py"))
        graph.add_edge("d1", "f1", "affects")

        viz_json = graph.to_visualization_json()

        import json

        viz = json.loads(viz_json)

        assert len(viz["nodes"]) == 2
        assert len(viz["edges"]) == 1
        assert viz["edges"][0]["label"] == "affects"


class TestValidTypes:
    """Tests for valid type constants."""

    def test_valid_node_types(self) -> None:
        """Test VALID_NODE_TYPES contains expected types."""
        expected = {"decision", "pattern", "file", "issue", "agent_session", "story"}
        assert VALID_NODE_TYPES == expected

    def test_valid_edge_types(self) -> None:
        """Test VALID_EDGE_TYPES contains expected types."""
        expected = {
            "led_to",
            "affects",
            "discovered_by",
            "applies_to",
            "supersedes",
            "depends_on",
        }
        assert VALID_EDGE_TYPES == expected


@pytest.fixture(autouse=True)
def cleanup_singleton() -> None:
    """Reset global context graph singleton between tests."""
    reset_context_graph()
