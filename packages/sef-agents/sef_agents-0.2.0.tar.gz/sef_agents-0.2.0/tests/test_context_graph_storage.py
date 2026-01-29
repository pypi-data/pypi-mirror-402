"""Tests for ContextGraph storage and dual-location behavior."""

import json
from pathlib import Path

import pytest
from sef_agents.tools.context_graph import ContextGraph, ContextNode

GRAPH_FILENAME = "context_graph.json"


@pytest.fixture
def context_graph(tmp_path: Path) -> ContextGraph:
    """Provide a fresh ContextGraph with a temporary root."""
    return ContextGraph(root=tmp_path)


def test_save_writes_to_both_locations(
    context_graph: ContextGraph, tmp_path: Path
) -> None:
    """Verify save writes to sef-reports (primary) and .sef_cache (cache)."""
    # 1. Add some data
    node = ContextNode(id="test-node", node_type="decision", content="Test")
    context_graph.add_node(node)

    # 2. Save
    primary_path = context_graph.save()

    # 3. Verify paths
    reports_file = tmp_path / "sef-reports" / GRAPH_FILENAME
    cache_file = tmp_path / ".sef_cache" / GRAPH_FILENAME

    assert primary_path == reports_file
    assert reports_file.exists()
    assert cache_file.exists()

    # 4. Verify content matches
    primary_data = json.loads(reports_file.read_text())
    cache_data = json.loads(cache_file.read_text())
    assert primary_data == cache_data
    assert primary_data["nodes"][0]["id"] == "test-node"


def test_load_prefers_primary(tmp_path: Path) -> None:
    """Verify load reads from sef-reports if it exists."""
    reports_file = tmp_path / "sef-reports" / GRAPH_FILENAME
    cache_file = tmp_path / ".sef_cache" / GRAPH_FILENAME

    reports_file.parent.mkdir(parents=True)
    cache_file.parent.mkdir(parents=True)

    # Create different content in primary vs cache
    primary_json = json.dumps(
        {
            "nodes": [{"id": "primary-node", "node_type": "file", "content": "P"}],
            "edges": [],
        }
    )
    cache_json = json.dumps(
        {
            "nodes": [{"id": "cache-node", "node_type": "file", "content": "C"}],
            "edges": [],
        }
    )

    reports_file.write_text(primary_json)
    cache_file.write_text(cache_json)

    # Load
    graph = ContextGraph.load(tmp_path)

    assert graph.get_node("primary-node") is not None
    assert graph.get_node("cache-node") is None


def test_load_fallbacks_to_cache(tmp_path: Path) -> None:
    """Verify load reads from .sef_cache if sef-reports missing."""
    cache_file = tmp_path / ".sef_cache" / GRAPH_FILENAME
    cache_file.parent.mkdir(parents=True)

    cache_json = json.dumps(
        {
            "nodes": [{"id": "cache-node", "node_type": "file", "content": "C"}],
            "edges": [],
        }
    )
    cache_file.write_text(cache_json)

    # Load
    graph = ContextGraph.load(tmp_path)

    assert graph.get_node("cache-node") is not None


def test_save_handles_cache_failure_gracefully(
    context_graph: ContextGraph, monkeypatch
) -> None:
    """Verify save raises OSError when cache write fails (no bare except)."""
    # Mock Path.write_text to fail ONLY for cache file
    original_write = Path.write_text

    def mock_write(self, data, encoding=None, errors=None):
        if ".sef_cache" in str(self):
            raise OSError("Cache permission denied")
        return original_write(self, data, encoding, errors)

    monkeypatch.setattr(Path, "write_text", mock_write)

    node = ContextNode(id="n1", node_type="file", content="c")
    context_graph.add_node(node)

    # Per E002 policy: exceptions must propagate
    with pytest.raises(OSError, match="Cache permission denied"):
        context_graph.save()
