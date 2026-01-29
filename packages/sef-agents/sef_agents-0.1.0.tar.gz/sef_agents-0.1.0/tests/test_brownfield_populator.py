"""Tests for Brownfield Context Graph Population."""

from unittest.mock import MagicMock, patch

import pytest
from sef_agents.tools.brownfield_populator import BrownfieldPopulator


@pytest.fixture
def mock_context_graph():
    """Mock the singleton ContextGraph."""
    with patch("sef_agents.tools.brownfield_populator.get_context_graph") as mock_get:
        mock_graph = MagicMock()
        mock_graph.node_count = 10
        mock_graph.edge_count = 5
        mock_get.return_value = mock_graph
        yield mock_graph


def test_populate_structural_scan(mock_context_graph, tmp_path):
    """Verify structural scan finds files and adds them to graph."""
    # Create dummy files
    (tmp_path / "main.py").touch()
    (tmp_path / "utils.py").touch()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").touch()

    populator = BrownfieldPopulator(directory=tmp_path)

    # Mock methods to isolate structural scan
    with patch.object(populator, "_mine_git_decisions"):
        with patch.object(populator, "_synthesize_decisions"):
            stats = populator.populate(
                levels=["L1", "L2"], include_git=False, include_llm=False
            )

            # Verify file nodes added
            assert stats["files_scanned"] == 3
            # Check mock graph calls
            assert mock_context_graph.add_node.call_count == 3
            # Verify save called
            mock_context_graph.save.assert_called()


def test_criticality_classification(tmp_path):
    """Verify file classification logic."""
    populator = BrownfieldPopulator(directory=tmp_path)

    files = [
        "main.py",
        "app/services/user_service.py",
        "tests/test_user.py",
        "README.md",
        "core/config.py",
    ]

    classified = populator._classify_criticality(files)

    assert "main.py" in classified["L1"]
    assert "core/config.py" in classified["L1"]
    assert "app/services/user_service.py" in classified["L2"]
    assert "tests/test_user.py" in classified["L3"]
    assert "README.md" in classified["L3"]


def test_populate_runs_deep_analysis_only_on_selected_levels(
    mock_context_graph, tmp_path
):
    """Verify git/llm mining only runs on specified levels."""
    (tmp_path / "main.py").touch()  # L1
    (tmp_path / "utils.py").touch()  # L2
    (tmp_path / "test.py").touch()  # L3

    populator = BrownfieldPopulator(directory=tmp_path)

    with patch.object(populator, "_mine_git_decisions") as mock_git:
        with patch.object(populator, "_synthesize_decisions"):
            # Run only for L1
            populator.populate(levels=["L1"], include_git=True, include_llm=True)

            # Verify L1 files passed to miners
            args, _ = mock_git.call_args
            assert "main.py" in args[0]
            assert "utils.py" not in args[0]
            assert "test.py" not in args[0]


def test_export_is_delegated_to_save(mock_context_graph, tmp_path):
    """Verify that export logic is handled by graph.save()."""
    populator = BrownfieldPopulator(directory=tmp_path)
    populator.populate()
    mock_context_graph.save.assert_called_once()
