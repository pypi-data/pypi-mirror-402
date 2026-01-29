"""Context Graph for SEF-Agents.

NetworkX-based graph for tracking relationships between:
- Decisions
- Patterns
- Files
- Issues
- Agent sessions
- Stories

Provides causality chains and impact analysis for agent context.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import networkx as nx

from sef_agents.utils.git_utils import find_project_root

# Valid node and edge types
NodeType = Literal["decision", "pattern", "file", "issue", "agent_session", "story"]
EdgeType = Literal[
    "led_to", "affects", "discovered_by", "applies_to", "supersedes", "depends_on"
]

VALID_NODE_TYPES: set[str] = {
    "decision",
    "pattern",
    "file",
    "issue",
    "agent_session",
    "story",
}
VALID_EDGE_TYPES: set[str] = {
    "led_to",
    "affects",
    "discovered_by",
    "applies_to",
    "supersedes",
    "depends_on",
}

GRAPH_FILENAME = "context_graph.json"


@dataclass
class ContextNode:
    """Node in the context graph."""

    id: str
    node_type: NodeType
    content: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    story_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "node_type": self.node_type,
            "content": self.content,
            "timestamp": self.timestamp,
            "story_id": self.story_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextNode:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            node_type=data["node_type"],
            content=data["content"],
            timestamp=data.get("timestamp", ""),
            story_id=data.get("story_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ContextEdge:
    """Edge in the context graph."""

    from_id: str
    to_id: str
    edge_type: EdgeType
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "edge_type": self.edge_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextEdge:
        """Create from dictionary."""
        return cls(
            from_id=data["from_id"],
            to_id=data["to_id"],
            edge_type=data["edge_type"],
            timestamp=data.get("timestamp", ""),
            metadata=data.get("metadata", {}),
        )


class ContextGraph:
    """Directed graph representing the codebase context and decision history."""

    def __init__(self, root: Path | None = None):
        self._root = root or find_project_root()

        # Primary storage (Dashboards, Recovery)
        self._primary_dir = self._root / "sef-reports"
        self._primary_file = self._primary_dir / GRAPH_FILENAME

        # Cache storage (Runtime performance)
        self._cache_dir = self._root / ".sef_cache"
        self._cache_file = self._cache_dir / GRAPH_FILENAME

        self._graph = nx.DiGraph()

    @property
    def node_count(self) -> int:
        """Number of nodes in graph."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Number of edges in graph."""
        return self._graph.number_of_edges()

    def add_node(self, node: ContextNode) -> None:
        """Add a node to the graph.

        Args:
            node: ContextNode to add.

        Raises:
            ValueError: If node_type is invalid.
        """
        if node.node_type not in VALID_NODE_TYPES:
            raise ValueError(
                f"Invalid node_type: {node.node_type}. Must be one of {VALID_NODE_TYPES}"
            )

        self._graph.add_node(node.id, **node.to_dict())

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: EdgeType,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add an edge between two nodes.

        Args:
            from_id: Source node ID.
            to_id: Target node ID.
            edge_type: Type of relationship.
            metadata: Optional edge metadata.

        Raises:
            ValueError: If edge_type is invalid or nodes don't exist.
        """
        if edge_type not in VALID_EDGE_TYPES:
            raise ValueError(
                f"Invalid edge_type: {edge_type}. Must be one of {VALID_EDGE_TYPES}"
            )

        if from_id not in self._graph:
            raise ValueError(f"Source node not found: {from_id}")
        if to_id not in self._graph:
            raise ValueError(f"Target node not found: {to_id}")

        edge = ContextEdge(
            from_id=from_id,
            to_id=to_id,
            edge_type=edge_type,
            metadata=metadata or {},
        )
        self._graph.add_edge(from_id, to_id, **edge.to_dict())

    def get_node(self, node_id: str) -> ContextNode | None:
        """Get a node by ID.

        Args:
            node_id: Node identifier.

        Returns:
            ContextNode if found, None otherwise.
        """
        if node_id not in self._graph:
            return None

        data = dict(self._graph.nodes[node_id])
        return ContextNode.from_dict(data)

    def get_related(
        self,
        node_id: str,
        edge_types: list[str] | None = None,
        direction: Literal["outgoing", "incoming", "both"] = "both",
    ) -> list[ContextNode]:
        """Get nodes related to a given node.

        Args:
            node_id: Source node ID.
            edge_types: Filter by edge types. None = all types.
            direction: Which edges to follow.

        Returns:
            List of related ContextNodes.
        """
        if node_id not in self._graph:
            return []

        related_ids: set[str] = set()

        if direction in ("outgoing", "both"):
            for _, target, data in self._graph.out_edges(node_id, data=True):
                if edge_types is None or data.get("edge_type") in edge_types:
                    related_ids.add(target)

        if direction in ("incoming", "both"):
            for source, _, data in self._graph.in_edges(node_id, data=True):
                if edge_types is None or data.get("edge_type") in edge_types:
                    related_ids.add(source)

        return [self.get_node(nid) for nid in related_ids if self.get_node(nid)]

    def get_causality_chain(
        self, node_id: str, max_depth: int = 10
    ) -> list[ContextNode]:
        """Get the causal ancestry of a node (led_to, caused_by edges).

        Args:
            node_id: Starting node ID.
            max_depth: Maximum traversal depth.

        Returns:
            List of nodes in causal chain, oldest first.
        """
        if node_id not in self._graph:
            return []

        chain: list[str] = []
        visited: set[str] = set()
        current = node_id

        for _ in range(max_depth):
            visited.add(current)
            chain.append(current)

            # Find predecessor via led_to edge
            predecessors = [
                source
                for source, _, data in self._graph.in_edges(current, data=True)
                if data.get("edge_type") == "led_to" and source not in visited
            ]

            if not predecessors:
                break
            current = predecessors[0]

        # Reverse to get oldest first
        chain.reverse()
        return [self.get_node(nid) for nid in chain if self.get_node(nid)]

    def get_nodes_by_story(self, story_id: str) -> list[ContextNode]:
        """Get all nodes associated with a story.

        Args:
            story_id: Story identifier.

        Returns:
            List of ContextNodes for the story.
        """
        nodes = []
        for node_id in self._graph.nodes:
            data = self._graph.nodes[node_id]
            if data.get("story_id") == story_id:
                nodes.append(ContextNode.from_dict(data))
        return nodes

    def get_nodes_by_type(self, node_type: NodeType) -> list[ContextNode]:
        """Get all nodes of a specific type.

        Args:
            node_type: Type of node to filter by.

        Returns:
            List of ContextNodes of the given type.
        """
        nodes = []
        for node_id in self._graph.nodes:
            data = self._graph.nodes[node_id]
            if data.get("node_type") == node_type:
                nodes.append(ContextNode.from_dict(data))
        return nodes

    def to_json(self) -> str:
        """Serialize graph to JSON string.

        Returns:
            JSON string representation of graph.
        """
        nodes = [dict(self._graph.nodes[n]) for n in self._graph.nodes]
        edges = [dict(self._graph.edges[e]) for e in self._graph.edges]

        return json.dumps({"nodes": nodes, "edges": edges}, indent=2)

    @classmethod
    def from_json(cls, data: str, root: Path | None = None) -> ContextGraph:
        """Deserialize graph from JSON string.

        Args:
            data: JSON string.
            root: Project root directory.

        Returns:
            New ContextGraph instance.
        """
        graph = cls(root=root)
        parsed = json.loads(data)

        for node_data in parsed.get("nodes", []):
            node = ContextNode.from_dict(node_data)
            graph._graph.add_node(node.id, **node.to_dict())

        for edge_data in parsed.get("edges", []):
            from_id = edge_data["from_id"]
            to_id = edge_data["to_id"]
            if from_id in graph._graph and to_id in graph._graph:
                graph._graph.add_edge(from_id, to_id, **edge_data)

        return graph

    def save(self) -> Path:
        """Save graph to disk (Primary: sef-reports, Cache: .sef_cache).

        Returns:
            Path to primary file.
        """
        # Save to primary (sef-reports)
        self._primary_dir.mkdir(parents=True, exist_ok=True)
        self._primary_file.write_text(self.to_json())

        # Save to cache (runtime optimization)
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache_file.write_text(self.to_json())
        except Exception as e:
            import structlog

            structlog.get_logger(__name__).warning(
                "context_graph_cache_save_failed", error=str(e)
            )
            raise

        return self._primary_file

    @classmethod
    def load(cls, root: Path | None = None) -> ContextGraph:
        """Load graph from disk (Try Primary -> Try Cache -> Empty).

        Args:
            root: Project root directory.

        Returns:
            Loaded ContextGraph or empty graph if no files exist.
        """
        graph = cls(root=root)

        # Try primary first
        if graph._primary_file.exists():
            try:
                data = graph._primary_file.read_text()
                loaded = cls.from_json(data, root=root)
                graph._graph = loaded._graph
                return graph
            except Exception as e:
                import structlog

                structlog.get_logger(__name__).warning(
                    "context_graph_primary_load_failed", error=str(e)
                )
                raise

        # Try cache if primary missing or failed
        if graph._cache_file.exists():
            try:
                data = graph._cache_file.read_text()
                loaded = cls.from_json(data, root=root)
                graph._graph = loaded._graph
                # Self-heal: save back to primary if we loaded from cache?
                # For now, just return loaded state
            except Exception as e:
                import structlog

                structlog.get_logger(__name__).warning(
                    "context_graph_cache_load_failed", error=str(e)
                )
                raise

        return graph

    def to_visualization_json(self) -> str:
        """Export graph in format suitable for react-flow visualization.

        Returns:
            JSON string with nodes and edges for frontend.
        """
        viz_nodes = []
        for node_id in self._graph.nodes:
            data = self._graph.nodes[node_id]
            viz_nodes.append(
                {
                    "id": node_id,
                    "type": data.get("node_type", "decision"),
                    "data": {
                        "label": data.get("content", "")[:50],
                        "fullContent": data.get("content", ""),
                        "nodeType": data.get("node_type", ""),
                        "storyId": data.get("story_id", ""),
                        "timestamp": data.get("timestamp", ""),
                    },
                    "position": {"x": 0, "y": 0},  # Layout computed by frontend
                }
            )

        viz_edges = []
        for idx, (source, target) in enumerate(self._graph.edges):
            data = self._graph.edges[(source, target)]
            viz_edges.append(
                {
                    "id": f"e{idx}",
                    "source": source,
                    "target": target,
                    "label": data.get("edge_type", ""),
                    "type": "smoothstep",
                }
            )

        return json.dumps({"nodes": viz_nodes, "edges": viz_edges}, indent=2)


# Singleton instance for global access
_context_graph: ContextGraph | None = None


def get_context_graph(root: Path | None = None) -> ContextGraph:
    """Get or create the global context graph instance.

    Args:
        root: Optional project root. Only used on first call.

    Returns:
        Global ContextGraph instance.
    """
    global _context_graph
    if _context_graph is None:
        _context_graph = ContextGraph.load(root)
    return _context_graph


def reset_context_graph() -> None:
    """Reset the global context graph instance. Primarily for testing."""
    global _context_graph
    _context_graph = None
