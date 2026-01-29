"""Sequencing Engine for SEF Agents.

Reads dependency graph, determines execution order,
identifies ready stories and critical paths.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from sef_agents.tools.dependency_graph import (
    DependencyGraph,
    StoryNode,
    scan_requirements_directory,
)

logger = structlog.get_logger(__name__)

# Status values indicating completion
DONE_STATUSES = {"done", "completed", "closed", "verified"}


@dataclass
class SequencingResult:
    """Result of sequencing analysis."""

    ready_stories: list[str] = field(default_factory=list)
    blocked_stories: dict[str, list[str]] = field(default_factory=dict)
    critical_path: list[str] = field(default_factory=list)
    completed_stories: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str] | dict[str, list[str]]]:
        """Convert to dictionary."""
        return {
            "ready": self.ready_stories,
            "blocked": self.blocked_stories,
            "critical_path": self.critical_path,
            "completed": self.completed_stories,
        }

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)


def _is_completed(status: str) -> bool:
    """Check if status indicates completion."""
    return status.lower() in DONE_STATUSES


def _get_unmet_dependencies(node: StoryNode, graph: DependencyGraph) -> list[str]:
    """Get list of unmet dependencies for a story.

    Args:
        node: Story node to check.
        graph: Full dependency graph.

    Returns:
        List of story IDs that are not yet completed.
    """
    unmet = []
    for dep_id in node.depends_on:
        dep_node = graph.get_node(dep_id)
        if dep_node is None:
            # Dependency not in graph - treat as unmet
            unmet.append(f"{dep_id} (not found)")
        elif not _is_completed(dep_node.status):
            unmet.append(dep_id)
    return unmet


def get_ready_stories(graph: DependencyGraph) -> list[str]:
    """Get stories with all dependencies satisfied.

    Args:
        graph: Dependency graph to analyze.

    Returns:
        List of story IDs ready for work.
    """
    ready = []
    for node in graph.nodes.values():
        # Skip completed stories
        if _is_completed(node.status):
            continue

        unmet = _get_unmet_dependencies(node, graph)
        if not unmet:
            ready.append(node.story_id)

    return sorted(ready)


def get_blocked_stories(graph: DependencyGraph) -> dict[str, list[str]]:
    """Get stories blocked by unmet dependencies.

    Args:
        graph: Dependency graph to analyze.

    Returns:
        Dict mapping story ID to list of blocking dependencies.
    """
    blocked = {}
    for node in graph.nodes.values():
        # Skip completed stories
        if _is_completed(node.status):
            continue

        unmet = _get_unmet_dependencies(node, graph)
        if unmet:
            blocked[node.story_id] = unmet

    return blocked


def get_completed_stories(graph: DependencyGraph) -> list[str]:
    """Get list of completed stories.

    Args:
        graph: Dependency graph to analyze.

    Returns:
        List of completed story IDs.
    """
    return sorted(
        [node.story_id for node in graph.nodes.values() if _is_completed(node.status)]
    )


def _find_longest_path(
    graph: DependencyGraph,
    start_id: str,
    visited: set[str] | None = None,
) -> list[str]:
    """Find longest dependency path from a starting node.

    Args:
        graph: Dependency graph.
        start_id: Starting story ID.
        visited: Set of visited nodes (for cycle detection).

    Returns:
        List of story IDs in longest path.
    """
    if visited is None:
        visited = set()

    if start_id in visited:
        return []  # Cycle detected

    node = graph.get_node(start_id)
    if node is None:
        return []

    visited.add(start_id)

    # Find stories that depend on this one (via blocks or reverse depends_on)
    downstream = []
    for other in graph.nodes.values():
        if start_id in other.depends_on:
            downstream.append(other.story_id)

    if not downstream:
        return [start_id]

    # Find longest path through downstream nodes
    longest_downstream: list[str] = []
    for next_id in downstream:
        path = _find_longest_path(graph, next_id, visited.copy())
        if len(path) > len(longest_downstream):
            longest_downstream = path

    return [start_id] + longest_downstream


def get_critical_path(graph: DependencyGraph) -> list[str]:
    """Find the critical path (longest dependency chain).

    Args:
        graph: Dependency graph to analyze.

    Returns:
        List of story IDs forming the critical path.
    """
    # Find root nodes (no dependencies)
    roots = [node.story_id for node in graph.nodes.values() if not node.depends_on]

    if not roots:
        # No clear roots - try all nodes
        roots = list(graph.nodes.keys())

    longest_path: list[str] = []
    for root in roots:
        path = _find_longest_path(graph, root)
        if len(path) > len(longest_path):
            longest_path = path

    return longest_path


def analyze_directory(directory: str | Path) -> SequencingResult:
    """Analyze requirements directory and return sequencing result.

    Args:
        directory: Path to requirements directory.

    Returns:
        SequencingResult with ready, blocked, and critical path info.
    """
    result = SequencingResult()
    graph = scan_requirements_directory(directory)

    if graph.errors:
        result.errors = graph.errors
        return result

    if not graph.nodes:
        result.errors.append(f"No stories found in {directory}")
        return result

    result.ready_stories = get_ready_stories(graph)
    result.blocked_stories = get_blocked_stories(graph)
    result.critical_path = get_critical_path(graph)
    result.completed_stories = get_completed_stories(graph)

    logger.info(
        "sequencing_complete",
        ready=len(result.ready_stories),
        blocked=len(result.blocked_stories),
        critical_path_length=len(result.critical_path),
    )

    return result


def get_next_ready_stories(directory: str) -> str:
    """Get next stories ready for work.

    Args:
        directory: Path to requirements directory.

    Returns:
        Formatted string with ready stories.
    """
    result = analyze_directory(directory)

    if result.errors:
        return f"Errors: {result.errors}"

    if not result.ready_stories:
        return "No stories ready. Check blocked stories for dependencies."

    lines = ["## Ready Stories\n"]
    lines.extend(f"- `{story_id}`" for story_id in result.ready_stories)

    if result.blocked_stories:
        lines.append("\n## Blocked Stories\n")
        for story_id, blockers in result.blocked_stories.items():
            lines.append(f"- `{story_id}` ← waiting on: {', '.join(blockers)}")

    return "\n".join(lines)


def get_critical_path_report(directory: str) -> str:
    """Get critical path report.

    Args:
        directory: Path to requirements directory.

    Returns:
        Formatted string with critical path.
    """
    result = analyze_directory(directory)

    if result.errors:
        return f"Errors: {result.errors}"

    if not result.critical_path:
        return "No critical path found."

    path_str = " → ".join(result.critical_path)
    path_len = len(result.critical_path)
    return (
        f"## Critical Path\n\n```\n{path_str}\n```\n\n**Length:** {path_len} stories\n"
    )
