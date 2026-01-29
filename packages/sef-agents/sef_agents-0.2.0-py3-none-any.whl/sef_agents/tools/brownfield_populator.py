"""Brownfield Context Graph Populator.

Orchestrates discovery-time population of the context graph from existing codebase.
Layers:
1. Structural: File nodes, patterns, dependency edges (Universal)
2. Archaeological: Git history -> Decision nodes (L1/L2 only)
3. Synthesized: LLM -> Enriched Decision nodes (L1/L2 only)
"""

from pathlib import Path
from typing import Literal

import structlog

from sef_agents.tools.context_graph import (
    ContextNode,
    get_context_graph,
)

logger = structlog.get_logger(__name__)

CriticalityLevel = Literal["L1", "L2", "L3"]


class BrownfieldPopulator:
    """Populates context graph during discovery."""

    def __init__(self, directory: Path | None = None):
        self.root = directory or Path.cwd()
        self.graph = get_context_graph(self.root)

    def populate(
        self,
        levels: list[CriticalityLevel] = None,
        include_git: bool = True,
        include_llm: bool = True,
    ) -> dict:
        """Run full brownfield population.

        Args:
            levels: List of criticality levels to process for deep analysis (git/llm).
                   Defaults to ["L1", "L2"].
            include_git: Whether to mine git history.
            include_llm: Whether to use LLM synthesis.

        Returns:
            Dict with counts of nodes/edges added.
        """
        if levels is None:
            levels = ["L1", "L2"]

        logger.info("brownfield_population_start", root=str(self.root), levels=levels)

        # 1. Structural Scan (All files)
        file_nodes = self._scan_structural()

        # 2. Classify Criticality
        classification = self._classify_criticality(file_nodes)

        # Filter files for deep analysis based on levels
        deep_analysis_files = []
        for level in levels:
            deep_analysis_files.extend(classification.get(level, []))

        # 3. Archaeological Mining (Git)
        if include_git:
            self._mine_git_decisions(deep_analysis_files)

        # 4. Synthesized Decisions (LLM)
        if include_llm:
            self._synthesize_decisions(deep_analysis_files)

        # 5. Export for Dashboard (handled by save)
        self.graph.save()

        return {
            "files_scanned": len(file_nodes),
            "deep_analysis_files": len(deep_analysis_files),
            "total_nodes": self.graph.node_count,
            "total_edges": self.graph.edge_count,
        }

    def _scan_structural(self) -> list[str]:
        """Layer 1: Create file nodes and dependency edges."""
        added_files = []

        # Walk directory, excluding hidden/ignored
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if any(p.startswith(".") for p in path.parts):
                continue
            if "__pycache__" in path.parts:
                continue

            rel_path = str(path.relative_to(self.root))
            node_id = f"file-{rel_path.replace('/', '-')}"

            node = ContextNode(
                id=node_id,
                node_type="file",
                content=rel_path,
                metadata={"path": rel_path},
            )
            self.graph.add_node(node)
            added_files.append(rel_path)

            # TODO: Add dependency inference here (import_analyzer)

        return added_files

    def _classify_criticality(
        self, files: list[str]
    ) -> dict[CriticalityLevel, list[str]]:
        """Classify files into L1/L2/L3."""
        classified = {"L1": [], "L2": [], "L3": []}

        for rel_path in files:
            # Heuristics
            level: CriticalityLevel = "L2"  # Default

            parts = Path(rel_path).parts
            name = Path(rel_path).name

            if name in ["main.py", "app.py", "server.py", "manage.py"]:
                level = "L1"
            elif "tests" in parts or name.startswith("test_"):
                level = "L3"
            elif name.endswith((".md", ".json", ".yaml", ".toml", ".txt")):
                level = "L3"
            elif "core" in parts or "api" in parts:
                level = "L1"

            classified[level].append(rel_path)

        return classified

    def _mine_git_decisions(self, files: list[str]) -> None:
        """Layer 2: Create decision nodes from git history."""
        # Placeholder for git miner integration
        pass

    def _synthesize_decisions(self, files: list[str]) -> None:
        """Layer 3: Create decision nodes from LLM analysis."""
        # Placeholder for LLM synthesizer integration
        pass
