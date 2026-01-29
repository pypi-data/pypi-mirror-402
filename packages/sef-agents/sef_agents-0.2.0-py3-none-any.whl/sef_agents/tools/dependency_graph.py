"""Dependency Graph Generator for SEF Agents.

Scans REQ.md files, extracts depends_on/blocks fields,
and generates Mermaid diagrams + JSON for sequencing engine.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# Regex patterns for REQ.md parsing
STORY_ID_PATTERN = re.compile(r"#\s*Requirement:\s*\[([A-Z]+-\d+)\]")
STATUS_PATTERN = re.compile(r"\*\*Status:\*\*\s*(\w+(?:\s+\w+)?)")
DEPENDS_ON_PATTERN = re.compile(r"\|\s*Depends On\s*\|\s*([A-Z]+-\d+)\s*\|")
BLOCKS_PATTERN = re.compile(r"\|\s*Blocks\s*\|\s*([A-Z]+-\d+)\s*\|")


@dataclass
class StoryNode:
    """Represents a story in the dependency graph."""

    story_id: str
    status: str = "Draft"
    depends_on: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)
    file_path: str = ""

    def to_dict(self) -> dict[str, str | list[str]]:
        """Convert to dictionary for JSON serialization."""
        return {
            "story_id": self.story_id,
            "status": self.status,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "file_path": self.file_path,
        }


@dataclass
class DependencyGraph:
    """Dependency graph containing all story nodes."""

    nodes: dict[str, StoryNode] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def add_node(self, node: StoryNode) -> None:
        """Add a story node to the graph."""
        self.nodes[node.story_id] = node

    def get_node(self, story_id: str) -> StoryNode | None:
        """Get a node by story ID."""
        return self.nodes.get(story_id)

    def to_json(self) -> str:
        """Serialize graph to JSON."""
        data = {
            "nodes": {sid: node.to_dict() for sid, node in self.nodes.items()},
            "edges": self._get_edges(),
        }
        return json.dumps(data, indent=2)

    def _get_edges(self) -> list[dict[str, str]]:
        """Extract all dependency edges."""
        edges = []
        for node in self.nodes.values():
            for dep in node.depends_on:
                edges.append({"from": dep, "to": node.story_id, "type": "depends_on"})
            for blocked in node.blocks:
                edges.append({"from": node.story_id, "to": blocked, "type": "blocks"})
        return edges

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram."""
        lines = ["graph LR"]

        for node in self.nodes.values():
            style = _get_status_style(node.status)
            lines.append(f"    {node.story_id}{style}")

        for node in self.nodes.values():
            for dep in node.depends_on:
                if dep in self.nodes:
                    lines.append(f"    {dep} --> {node.story_id}")

        return "\n".join(lines)


def _get_status_style(status: str) -> str:
    """Get Mermaid node style based on status."""
    status_lower = status.lower()
    if status_lower == "done":
        return ":::done"
    if status_lower in ("in progress", "in development"):
        return ":::inprogress"
    if status_lower == "blocked":
        return ":::blocked"
    return ""


def parse_req_file(file_path: Path) -> StoryNode | None:
    """Parse a REQ.md file and extract story metadata.

    Args:
        file_path: Path to REQ.md file.

    Returns:
        StoryNode if valid, None if parsing fails.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("req_file_read_error", file=str(file_path), error=str(e))
        return None

    # Extract story ID
    story_match = STORY_ID_PATTERN.search(content)
    if not story_match:
        logger.debug("no_story_id_found", file=str(file_path))
        return None

    story_id = story_match.group(1)

    # Extract status
    status_match = STATUS_PATTERN.search(content)
    status = status_match.group(1) if status_match else "Draft"

    # Extract dependencies
    depends_on = DEPENDS_ON_PATTERN.findall(content)
    blocks = BLOCKS_PATTERN.findall(content)

    return StoryNode(
        story_id=story_id,
        status=status,
        depends_on=depends_on,
        blocks=blocks,
        file_path=str(file_path),
    )


def scan_requirements_directory(directory: str | Path) -> DependencyGraph:
    """Scan directory for REQ.md files and build dependency graph.

    Args:
        directory: Path to requirements directory.

    Returns:
        DependencyGraph with all stories and dependencies.
    """
    graph = DependencyGraph()
    dir_path = Path(directory)

    if not dir_path.exists():
        graph.errors.append(f"Directory not found: {directory}")
        return graph

    # Find all REQ.md files (case-insensitive)
    req_files = list(dir_path.rglob("*REQ*.md")) + list(dir_path.rglob("*req*.md"))
    req_files = list(set(req_files))  # Deduplicate

    for req_file in req_files:
        node = parse_req_file(req_file)
        if node:
            graph.add_node(node)

    logger.info(
        "dependency_scan_complete",
        files_scanned=len(req_files),
        stories_found=len(graph.nodes),
    )

    return graph


def generate_dependency_graph(directory: str) -> str:
    """Generate dependency graph artifact.

    Args:
        directory: Path to requirements directory.

    Returns:
        Status message with artifact location.
    """
    graph = scan_requirements_directory(directory)

    if graph.errors:
        return f"Errors during scan: {graph.errors}"

    if not graph.nodes:
        return f"No REQ.md files found in {directory}"

    # Generate Mermaid markdown
    mermaid_content = f"""# Dependency Graph

*Auto-generated by dependency_graph.py*

## Story Dependencies

```mermaid
{graph.to_mermaid()}
```

## Style Legend

- Default: Draft/Pending
- `:::done`: Completed
- `:::inprogress`: In Progress
- `:::blocked`: Blocked

## Raw Data

```json
{graph.to_json()}
```
"""

    # Write artifact
    output_path = Path(directory) / "DEPENDENCY_GRAPH.md"
    try:
        output_path.write_text(mermaid_content, encoding="utf-8")
        return f"Generated: `{output_path}` ({len(graph.nodes)} stories)"
    except OSError as e:
        return f"Failed to write artifact: {e}"


def get_graph_json(directory: str) -> str:
    """Get dependency graph as JSON for sequencing engine.

    Args:
        directory: Path to requirements directory.

    Returns:
        JSON string with graph data.
    """
    graph = scan_requirements_directory(directory)
    return graph.to_json()
