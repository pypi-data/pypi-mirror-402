"""Pattern Learning System for SEF.

This module captures successful code patterns from completed stories
and suggests them for reuse in future work.

Flow:
1. Capture: On story completion, extract patterns from changed files
2. Store: Index patterns by domain, tech, and tags
3. Retrieve: On new story, find similar patterns
4. Suggest: Present patterns to developer for reuse
"""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import structlog

from sef_agents.utils.git_utils import get_current_user_id, get_sef_cache_dir

logger = structlog.get_logger(__name__)


@dataclass
class Pattern:
    """Captured code pattern.

    Attributes:
        pattern_id: Unique identifier (PAT-XXX).
        name: Human-readable pattern name.
        domain: Domain category (api, db, ui, auth, etc.).
        tech: Technologies used (python, fastapi, react, etc.).
        story_id: Source story ID.
        files: Files where pattern was implemented.
        snippet: Representative code snippet.
        tags: Searchable tags.
        description: Brief description of what pattern solves.
        captured_at: Timestamp of capture.
        captured_by: User who captured the pattern.
    """

    pattern_id: str
    name: str
    domain: str
    tech: list[str]
    story_id: str
    files: list[str]
    snippet: str
    tags: list[str]
    description: str
    captured_at: str = ""
    captured_by: str = ""

    def __post_init__(self) -> None:
        """Set defaults after initialization."""
        if not self.captured_at:
            self.captured_at = datetime.now().isoformat()
        if not self.captured_by:
            self.captured_by = get_current_user_id()


@dataclass
class PatternMatch:
    """Pattern match result with relevance score.

    Attributes:
        pattern: The matched pattern.
        score: Relevance score (0.0-1.0).
        match_reason: Why this pattern matched.
    """

    pattern: Pattern
    score: float
    match_reason: str


class PatternLearner:
    """Manages pattern capture, storage, and retrieval.

    Attributes:
        registry_path: Path to patterns registry file.
    """

    def __init__(self, registry_path: Path | None = None) -> None:
        """Initialize pattern learner.

        Args:
            registry_path: Path to patterns registry.
                Defaults to {project_root}/.sef_cache/patterns_registry.jsonl.

        Raises:
            RuntimeError: If project root cannot be determined.
        """
        if registry_path is None:
            registry_path = get_sef_cache_dir() / "patterns_registry.jsonl"
        self.registry_path = registry_path

    def _ensure_dir(self) -> None:
        """Create registry directory if needed."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def _generate_id(self) -> str:
        """Generate unique pattern ID.

        Returns:
            Pattern ID in format PAT-XXX.
        """
        existing = self.get_all_patterns()
        if not existing:
            return "PAT-001"

        # Find max ID
        max_num = 0
        for p in existing:
            match = re.match(r"PAT-(\d+)", p.pattern_id)
            if match:
                max_num = max(max_num, int(match.group(1)))

        return f"PAT-{max_num + 1:03d}"

    def capture_pattern(
        self,
        name: str,
        domain: str,
        tech: list[str],
        story_id: str,
        files: list[str],
        snippet: str,
        tags: list[str],
        description: str,
    ) -> Pattern:
        """Capture a new pattern from completed story.

        Args:
            name: Human-readable pattern name.
            domain: Domain category (api, db, ui, auth, etc.).
            tech: Technologies used.
            story_id: Source story ID.
            files: Files where pattern implemented.
            snippet: Representative code snippet.
            tags: Searchable tags.
            description: Brief description.

        Returns:
            The captured Pattern.

        Raises:
            OSError: If registry write fails.
        """
        self._ensure_dir()

        pattern = Pattern(
            pattern_id=self._generate_id(),
            name=name,
            domain=domain,
            tech=tech,
            story_id=story_id,
            files=files,
            snippet=snippet,
            tags=tags,
            description=description,
        )

        try:
            with open(self.registry_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(pattern)) + "\n")

            # 4. Add to Context Graph
            try:
                from sef_agents.tools.context_graph import (
                    ContextNode,
                    get_context_graph,
                )

                graph = get_context_graph()
                graph_node = ContextNode(
                    id=pattern.pattern_id,
                    node_type="pattern",
                    content=f"{pattern.name} ({', '.join(pattern.tech)})",
                    story_id=story_id,
                    metadata={
                        "domain": domain,
                        "tags": tags,
                        "description": description,
                    },
                )
                graph.add_node(graph_node)
                # Link to story if exists
                if story_id and story_id in graph._graph:
                    graph.add_edge(story_id, pattern.pattern_id, "led_to")

                graph.save()
            except Exception as e:
                logger.warning("pattern_graph_add_failed", error=str(e))
                raise

            logger.info(
                "pattern_captured",
                pattern_id=pattern.pattern_id,
                name=name,
                story_id=story_id,
            )
        except OSError as e:
            logger.error("pattern_capture_failed", error=str(e))
            raise

        return pattern

    def get_all_patterns(self) -> list[Pattern]:
        """Get all stored patterns.

        Returns:
            List of all patterns in registry.
        """
        if not self.registry_path.exists():
            return []

        patterns: list[Pattern] = []
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        patterns.append(Pattern(**data))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("pattern_read_failed", error=str(e))
            return []

        return patterns

    def find_patterns(
        self,
        domain: str | None = None,
        tech: list[str] | None = None,
        tags: list[str] | None = None,
        limit: int = 5,
    ) -> list[PatternMatch]:
        """Find patterns matching criteria.

        Args:
            domain: Filter by domain.
            tech: Filter by technologies (any match).
            tags: Filter by tags (any match).
            limit: Max patterns to return.

        Returns:
            List of PatternMatch sorted by relevance.
        """
        all_patterns = self.get_all_patterns()
        matches: list[PatternMatch] = []

        for pattern in all_patterns:
            score = 0.0
            reasons: list[str] = []

            # Domain match (highest weight)
            if domain and pattern.domain.lower() == domain.lower():
                score += 0.4
                reasons.append(f"domain={domain}")

            # Tech match
            if tech:
                tech_lower = [t.lower() for t in tech]
                pattern_tech_lower = [t.lower() for t in pattern.tech]
                tech_matches = set(tech_lower) & set(pattern_tech_lower)
                if tech_matches:
                    score += 0.3 * (len(tech_matches) / len(tech))
                    reasons.append(f"tech={list(tech_matches)}")

            # Tag match
            if tags:
                tags_lower = [t.lower() for t in tags]
                pattern_tags_lower = [t.lower() for t in pattern.tags]
                tag_matches = set(tags_lower) & set(pattern_tags_lower)
                if tag_matches:
                    score += 0.3 * (len(tag_matches) / len(tags))
                    reasons.append(f"tags={list(tag_matches)}")

            if score > 0:
                matches.append(
                    PatternMatch(
                        pattern=pattern,
                        score=score,
                        match_reason=", ".join(reasons),
                    )
                )

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)

        return matches[:limit]

    def suggest_patterns(
        self,
        story_title: str,
        domain: str | None = None,
        tech: list[str] | None = None,
    ) -> str:
        """Generate pattern suggestions for a new story.

        Args:
            story_title: Title of the new story (used for tag extraction).
            domain: Expected domain.
            tech: Technologies to use.

        Returns:
            Formatted suggestion string.
        """
        # Extract potential tags from story title
        title_words = re.findall(r"\b\w+\b", story_title.lower())
        common_tags = [
            "pagination",
            "auth",
            "validation",
            "cache",
            "api",
            "crud",
            "filter",
            "search",
            "upload",
            "export",
            "import",
            "notification",
            "email",
            "payment",
        ]
        inferred_tags = [w for w in title_words if w in common_tags]

        matches = self.find_patterns(domain=domain, tech=tech, tags=inferred_tags)

        if not matches:
            return "📭 No similar patterns found in registry."

        lines: list[str] = [
            "📚 **Similar Patterns Found:**\n",
        ]

        for match in matches:
            p = match.pattern
            lines.append(f"**{p.pattern_id}: {p.name}** (score: {match.score:.0%})")
            lines.append(f"  - From: {p.story_id}")
            lines.append(f"  - Domain: {p.domain} | Tech: {', '.join(p.tech)}")
            lines.append(f"  - Files: {', '.join(p.files)}")
            lines.append(f"  - {p.description}")
            lines.append(f"  - Match: {match.match_reason}")
            lines.append("")

        lines.append("Use `get_pattern(pattern_id)` to see full snippet.")

        return "\n".join(lines)

    def get_pattern(self, pattern_id: str) -> Pattern | None:
        """Get a specific pattern by ID.

        Args:
            pattern_id: Pattern ID (e.g., PAT-001).

        Returns:
            Pattern if found, None otherwise.
        """
        for pattern in self.get_all_patterns():
            if pattern.pattern_id == pattern_id:
                return pattern
        return None

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern from registry.

        Args:
            pattern_id: Pattern ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        patterns = self.get_all_patterns()
        filtered = [p for p in patterns if p.pattern_id != pattern_id]

        if len(filtered) == len(patterns):
            return False  # Not found

        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                for p in filtered:
                    f.write(json.dumps(asdict(p)) + "\n")

            logger.info("pattern_deleted", pattern_id=pattern_id)
            return True
        except OSError as e:
            logger.error("pattern_delete_failed", error=str(e))
            return False


# Tool functions for MCP integration

# Valid actions for pattern_tool
PATTERN_ACTIONS = ("capture", "suggest", "get", "list")


def pattern_tool(
    action: str,
    pattern_id: str = "",
    name: str = "",
    domain: str = "",
    tech: str = "",
    story_id: str = "",
    story_title: str = "",
    files: str = "",
    snippet: str = "",
    tags: str = "",
    description: str = "",
) -> str:
    """Unified pattern management tool.

    Args:
        action: One of: capture, suggest, get, list.
        pattern_id: Pattern ID - for get action.
        name: Pattern name - for capture action.
        domain: Domain (api, db, ui, auth, etc.) - for capture/suggest/list.
        tech: Comma-separated technologies - for capture/suggest/list.
        story_id: Source story ID - for capture action.
        story_title: Story title - for suggest action.
        files: Comma-separated file paths - for capture action.
        snippet: Code snippet - for capture action.
        tags: Comma-separated tags - for capture action.
        description: Brief description - for capture action.

    Returns:
        Result based on action type.
    """
    if action not in PATTERN_ACTIONS:
        return f"❌ Invalid action. Use: {', '.join(PATTERN_ACTIONS)}"

    learner = PatternLearner()

    if action == "capture":
        if not all([name, domain, tech, story_id, files, snippet, tags, description]):
            return (
                "❌ capture requires: name, domain, tech, story_id, "
                "files, snippet, tags, description"
            )
        try:
            pattern = learner.capture_pattern(
                name=name,
                domain=domain,
                tech=[t.strip() for t in tech.split(",")],
                story_id=story_id,
                files=[f.strip() for f in files.split(",")],
                snippet=snippet,
                tags=[t.strip() for t in tags.split(",")],
                description=description,
            )
            return f"✅ Pattern captured: {pattern.pattern_id} ({pattern.name})"
        except OSError as e:
            return f"❌ Failed to capture pattern: {e}"

    if action == "suggest":
        if not story_title:
            return "❌ suggest requires: story_title"
        tech_list = [t.strip() for t in tech.split(",")] if tech else None
        return learner.suggest_patterns(
            story_title=story_title,
            domain=domain if domain else None,
            tech=tech_list,
        )

    if action == "get":
        if not pattern_id:
            return "❌ get requires: pattern_id"
        pattern = learner.get_pattern(pattern_id)
        if not pattern:
            return f"❌ Pattern {pattern_id} not found."
        return f"""**{pattern.pattern_id}: {pattern.name}**

- **Domain:** {pattern.domain}
- **Tech:** {", ".join(pattern.tech)}
- **Source:** {pattern.story_id}
- **Files:** {", ".join(pattern.files)}
- **Tags:** {", ".join(pattern.tags)}
- **Description:** {pattern.description}
- **Captured:** {pattern.captured_at} by {pattern.captured_by}

**Snippet:**
```
{pattern.snippet}
```
"""

    if action == "list":
        patterns = learner.get_all_patterns()
        if not patterns:
            return "📭 No patterns in registry."

        # Apply filters
        if domain:
            patterns = [p for p in patterns if p.domain.lower() == domain.lower()]
        if tech:
            tech_filter = tech.lower()
            patterns = [
                p for p in patterns if any(t.lower() == tech_filter for t in p.tech)
            ]

        if not patterns:
            return f"📭 No patterns matching filters (domain={domain}, tech={tech})."

        lines = [f"📚 **Pattern Registry** ({len(patterns)} patterns)\n"]
        lines.append("| ID | Name | Domain | Tech | Story |")
        lines.append("|-----|------|--------|------|-------|")

        for p in patterns:
            tech_str = ", ".join(p.tech[:2])
            if len(p.tech) > 2:
                tech_str += "..."
            lines.append(
                f"| {p.pattern_id} | {p.name} | {p.domain} | {tech_str} | {p.story_id} |"
            )

        return "\n".join(lines)

    return f"❌ Unknown action: {action}"
