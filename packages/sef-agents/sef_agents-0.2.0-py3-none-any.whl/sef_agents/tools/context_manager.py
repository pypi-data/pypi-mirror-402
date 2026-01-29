"""Context Persistence Manager for SEF.

This module provides hierarchical context storage across sessions:
- Story level: Decisions, blockers, patterns for a single story
- Epic level: Shared patterns across related stories
- Project level: Long-term conventions and recurring fixes

Context is stored as JSONL files in .sef_cache/context/ directory.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from sef_agents.utils.git_utils import get_current_user_id, get_sef_cache_dir

logger = structlog.get_logger(__name__)

# Default limits for context injection
DEFAULT_LIMITS = {
    "story": 10,
    "epic": 5,
    "project": 3,
}


@dataclass
class ContextEntry:
    """Single context entry.

    Attributes:
        timestamp: ISO format timestamp.
        entry_type: decision, blocker, pattern, or note.
        content: Human-readable description.
        user: Who created the entry.
        metadata: Optional additional data.
    """

    timestamp: str
    entry_type: str
    content: str
    user: str
    metadata: dict[str, Any] | None = None


class ContextManager:
    """Manages hierarchical context persistence.

    Attributes:
        root: Root directory for context files.
        limits: Max entries to load per layer.
    """

    def __init__(
        self,
        root: Path | None = None,
        limits: dict[str, int] | None = None,
    ) -> None:
        """Initialize context manager.

        Args:
            root: Context storage directory. Defaults to {project_root}/.sef_cache/context/.
            limits: Max entries per layer. Defaults to story=10, epic=5, project=3.

        Raises:
            RuntimeError: If project root cannot be determined.
        """
        if root is None:
            root = get_sef_cache_dir() / "context"
        self.root = root
        self.limits = limits or DEFAULT_LIMITS

    def _get_file_path(self, layer: str, identifier: str | None = None) -> Path:
        """Get file path for a context layer.

        Args:
            layer: One of 'story', 'epic', or 'project'.
            identifier: Story/epic ID. Required for story/epic, ignored for project.

        Returns:
            Path to the JSONL file.

        Raises:
            ValueError: If layer is invalid or identifier missing for story/epic.
        """
        if layer == "project":
            return self.root / "project.jsonl"
        elif layer in ("story", "epic"):
            if not identifier:
                raise ValueError(f"{layer} layer requires identifier")
            return self.root / f"{layer}_{identifier}.jsonl"
        else:
            raise ValueError(f"Invalid layer: {layer}. Use story, epic, or project.")

    def _ensure_dir(self) -> None:
        """Create context directory if it doesn't exist."""
        self.root.mkdir(parents=True, exist_ok=True)

    def add_entry(
        self,
        layer: str,
        entry_type: str,
        content: str,
        identifier: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContextEntry:
        """Add a context entry.

        Args:
            layer: One of 'story', 'epic', or 'project'.
            entry_type: Type of entry (decision, blocker, pattern, note).
            content: Human-readable description.
            identifier: Story/epic ID. Required for story/epic layers.
            metadata: Optional additional data.

        Returns:
            The created ContextEntry.

        Raises:
            ValueError: If layer invalid or identifier missing.
        """
        self._ensure_dir()
        file_path = self._get_file_path(layer, identifier)

        entry = ContextEntry(
            timestamp=datetime.now().isoformat(),
            entry_type=entry_type,
            content=content,
            user=get_current_user_id(),
            metadata=metadata,
        )

        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry)) + "\n")

            logger.info(
                "context_entry_added",
                layer=layer,
                entry_type=entry_type,
                identifier=identifier,
            )
        except OSError as e:
            logger.error("context_write_failed", error=str(e), path=str(file_path))
            raise

        return entry

    def get_entries(
        self,
        layer: str,
        identifier: str | None = None,
        limit: int | None = None,
    ) -> list[ContextEntry]:
        """Get context entries for a layer.

        Args:
            layer: One of 'story', 'epic', or 'project'.
            identifier: Story/epic ID. Required for story/epic layers.
            limit: Max entries to return (most recent). Defaults to layer limit.

        Returns:
            List of ContextEntry objects, most recent first.
        """
        try:
            file_path = self._get_file_path(layer, identifier)
        except ValueError:
            return []

        if not file_path.exists():
            return []

        entries: list[ContextEntry] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        entries.append(ContextEntry(**data))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("context_read_failed", error=str(e), path=str(file_path))
            return []

        max_entries = limit or self.limits.get(layer, 10)
        return entries[-max_entries:][::-1]  # Reverse for most recent first

    def get_combined_context(
        self,
        story_id: str | None = None,
        epic_id: str | None = None,
    ) -> dict[str, list[ContextEntry]]:
        """Get combined context from all applicable layers.

        Args:
            story_id: Current story ID (optional).
            epic_id: Current epic ID (optional).

        Returns:
            Dict with 'project', 'epic', 'story' keys containing entries.
        """
        result: dict[str, list[ContextEntry]] = {
            "project": self.get_entries("project"),
            "epic": [],
            "story": [],
        }

        if epic_id:
            result["epic"] = self.get_entries("epic", epic_id)

        if story_id:
            result["story"] = self.get_entries("story", story_id)

        return result

    def format_for_prompt(
        self,
        story_id: str | None = None,
        epic_id: str | None = None,
    ) -> str:
        """Format context for injection into agent prompts.

        Args:
            story_id: Current story ID (optional).
            epic_id: Current epic ID (optional).

        Returns:
            Formatted markdown string for prompt injection.
        """
        context = self.get_combined_context(story_id, epic_id)

        total_entries = sum(len(v) for v in context.values())
        if total_entries == 0:
            return ""

        lines: list[str] = [
            "\n--- SESSION CONTEXT (from previous sessions) ---\n",
        ]

        # Project context
        if context["project"]:
            lines.append("**📁 Project Conventions:**")
            for entry in context["project"]:
                lines.append(f"• [{entry.entry_type}] {entry.content}")
            lines.append("")

        # Epic context
        if context["epic"]:
            lines.append(f"**📦 Epic ({epic_id}) Patterns:**")
            for entry in context["epic"]:
                lines.append(f"• [{entry.entry_type}] {entry.content}")
            lines.append("")

        # Story context
        if context["story"]:
            lines.append(f"**📝 Story ({story_id}) History:**")
            for entry in context["story"]:
                lines.append(f"• [{entry.entry_type}] {entry.content} ({entry.user})")
            lines.append("")

        lines.append("--- END CONTEXT ---\n")

        return "\n".join(lines)

    def prune(
        self,
        layer: str,
        identifier: str | None = None,
        keep: int = 20,
    ) -> int:
        """Prune old entries from a context file.

        Args:
            layer: One of 'story', 'epic', or 'project'.
            identifier: Story/epic ID. Required for story/epic layers.
            keep: Number of most recent entries to keep.

        Returns:
            Number of entries removed.
        """
        file_path = self._get_file_path(layer, identifier)

        if not file_path.exists():
            return 0

        entries: list[str] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                entries = [line.strip() for line in f if line.strip()]
        except OSError as e:
            logger.error("context_prune_read_failed", error=str(e))
            return 0

        if len(entries) <= keep:
            return 0

        removed = len(entries) - keep
        kept_entries = entries[-keep:]

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for entry in kept_entries:
                    f.write(entry + "\n")

            logger.info(
                "context_pruned",
                layer=layer,
                identifier=identifier,
                removed=removed,
            )
        except OSError as e:
            logger.error("context_prune_write_failed", error=str(e))
            return 0

        return removed

    def clear(self, layer: str, identifier: str | None = None) -> bool:
        """Clear all entries for a context layer.

        Args:
            layer: One of 'story', 'epic', or 'project'.
            identifier: Story/epic ID. Required for story/epic layers.

        Returns:
            True if cleared successfully, False otherwise.
        """
        file_path = self._get_file_path(layer, identifier)

        if not file_path.exists():
            return True

        try:
            file_path.unlink()
            logger.info("context_cleared", layer=layer, identifier=identifier)
            return True
        except OSError as e:
            logger.error("context_clear_failed", error=str(e))
            return False


# Convenience functions for tool integration

# Valid actions for manage_context
CONTEXT_ACTIONS = ("add", "get", "clear")


def manage_context(
    action: str,
    layer: str = "",
    entry_type: str = "",
    content: str = "",
    identifier: str = "",
    story_id: str = "",
    epic_id: str = "",
) -> str:
    """Unified context management tool.

    Args:
        action: One of: add, get, clear.
        layer: Context layer (story, epic, project) - for add/clear.
        entry_type: Type: decision, blocker, pattern, note - for add.
        content: Description of the context - for add.
        identifier: Story/epic ID - for add/clear (required for story/epic layers).
        story_id: Current story ID - for get.
        epic_id: Current epic ID - for get.

    Returns:
        Success/error message or formatted context.
    """
    if action not in CONTEXT_ACTIONS:
        return f"❌ Invalid action. Use: {', '.join(CONTEXT_ACTIONS)}"

    manager = ContextManager()

    if action == "add":
        if not layer:
            return "❌ 'layer' required for add action"
        if not entry_type:
            return "❌ 'entry_type' required for add action"
        if not content:
            return "❌ 'content' required for add action"

        try:
            entry = manager.add_entry(
                layer, entry_type, content, identifier if identifier else None
            )
            return f"✅ Context added: [{entry.entry_type}] {entry.content}"
        except ValueError as e:
            return f"❌ Error: {e}"
        except OSError as e:
            return f"❌ Failed to save: {e}"

    if action == "get":
        formatted = manager.format_for_prompt(
            story_id if story_id else None,
            epic_id if epic_id else None,
        )
        if not formatted:
            return "📭 No context found for this session."
        return formatted

    if action == "clear":
        if not layer:
            return "❌ 'layer' required for clear action"
        try:
            success = manager.clear(layer, identifier if identifier else None)
            if success:
                return f"✅ Context cleared for {layer}"
            return f"❌ Failed to clear context for {layer}"
        except ValueError as e:
            return f"❌ Error: {e}"

    return f"❌ Unknown action: {action}"


# Backward compatibility wrappers for tests and server.py
def add_context(
    layer: str,
    entry_type: str,
    content: str,
    identifier: str = "",
) -> str:
    """Add context entry (backward compatibility wrapper).

    Args:
        layer: Context layer (story, epic, project).
        entry_type: Type: decision, blocker, pattern, note.
        content: Description of the context.
        identifier: Story/epic ID (required for story/epic layers).

    Returns:
        Success/error message.
    """
    return manage_context(
        action="add",
        layer=layer,
        entry_type=entry_type,
        content=content,
        identifier=identifier,
    )


def get_context(story_id: str = "", epic_id: str = "") -> str:
    """Get formatted context (backward compatibility wrapper).

    Args:
        story_id: Current story ID.
        epic_id: Current epic ID.

    Returns:
        Formatted context string or empty message.
    """
    return manage_context(action="get", story_id=story_id, epic_id=epic_id)
