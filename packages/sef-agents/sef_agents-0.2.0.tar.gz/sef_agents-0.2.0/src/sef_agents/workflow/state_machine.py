"""Workflow State Machine for SEF Agents.

Manages SDLC workflow state per story:
- Current phase tracking
- Artifact completion status
- Parallel task coordination
- State persistence to .sef_cache/workflow/
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from sef_agents.constants import (
    PHASE_CONFIG,
    Phase,
    StoryType,
    TaskStatus,
)
from sef_agents.utils.git_utils import get_sef_cache_dir

logger = structlog.get_logger(__name__)


@dataclass
class ParallelStatus:
    """Status tracking for parallel phase tasks.

    Attributes:
        phase: Phase ID where parallel execution occurs.
        tasks: Dict of agent -> TaskStatus.
        started_at: When parallel phase began.
        notifications: Background task notifications for primary agent.
    """

    phase: str
    tasks: dict[str, str] = field(default_factory=dict)
    started_at: str = ""
    notifications: list[str] = field(default_factory=list)

    def all_complete(self) -> bool:
        """Check if all parallel tasks are complete.

        Returns:
            True if all tasks passed or failed.
        """
        complete_statuses = {TaskStatus.PASSED.value, TaskStatus.FAILED.value}
        return all(status in complete_statuses for status in self.tasks.values())

    def all_passed(self) -> bool:
        """Check if all parallel tasks passed.

        Returns:
            True if all tasks passed.
        """
        return all(status == TaskStatus.PASSED.value for status in self.tasks.values())


@dataclass
class WorkflowState:
    """Workflow state for a single story.

    Attributes:
        story_id: Story identifier (e.g., STORY-001).
        epic_id: Parent epic identifier.
        current_phase: Current SDLC phase.
        active_agents: Currently active agents.
        completed_phases: List of completed phase IDs.
        artifacts: Dict of artifact name -> exists flag.
        parallel_status: Parallel task tracking (if in parallel phase).
        story_type: Backend, frontend, or fullstack.
        capabilities: Available tool capabilities.
        blockers: List of active escalations/blockers.
        last_updated: ISO timestamp of last update.
        created_at: ISO timestamp of creation.
    """

    story_id: str
    epic_id: str = ""
    current_phase: str = Phase.DISCOVERY.value
    active_agents: list[str] = field(default_factory=list)
    completed_phases: list[str] = field(default_factory=list)
    artifacts: dict[str, bool] = field(default_factory=dict)
    parallel_status: dict[str, Any] | None = None
    story_type: str = StoryType.UNKNOWN.value
    capabilities: dict[str, bool] = field(default_factory=dict)
    blockers: list[dict[str, str]] = field(default_factory=list)
    last_updated: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        """Initialize timestamps if not set."""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.last_updated:
            self.last_updated = now

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dict representation of state.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        """Create WorkflowState from dictionary.

        Args:
            data: Dict with state fields.

        Returns:
            WorkflowState instance.
        """
        return cls(**data)


class WorkflowManager:
    """Manages workflow state persistence and transitions.

    Attributes:
        root: Root directory for workflow files.
    """

    def __init__(self, root: Path | None = None) -> None:
        """Initialize workflow manager.

        Args:
            root: Workflow storage directory. Defaults to {project_root}/.sef_cache/workflow/.

        Raises:
            RuntimeError: If project root cannot be determined.
        """
        if root is None:
            root = get_sef_cache_dir() / "workflow"
        self.root = root

    def _ensure_dir(self) -> None:
        """Create workflow directory if it doesn't exist."""
        self.root.mkdir(parents=True, exist_ok=True)

    def _get_state_path(self, story_id: str) -> Path:
        """Get file path for story state.

        Args:
            story_id: Story identifier.

        Returns:
            Path to JSON state file.
        """
        return self.root / f"{story_id}.json"

    def _get_active_path(self) -> Path:
        """Get path to active story pointer file.

        Returns:
            Path to active.json.
        """
        return self.root / "active.json"

    def create_state(
        self,
        story_id: str,
        epic_id: str = "",
        story_type: str = StoryType.UNKNOWN.value,
    ) -> WorkflowState:
        """Create new workflow state for a story.

        Args:
            story_id: Story identifier.
            epic_id: Parent epic identifier.
            story_type: Backend, frontend, or fullstack.

        Returns:
            New WorkflowState instance.

        Raises:
            FileExistsError: If state already exists for story.
        """
        self._ensure_dir()
        state_path = self._get_state_path(story_id)

        if state_path.exists():
            raise FileExistsError(f"Workflow state already exists for {story_id}")

        state = WorkflowState(
            story_id=story_id,
            epic_id=epic_id,
            story_type=story_type,
        )

        self._save_state(state)
        logger.info("workflow_state_created", story_id=story_id, epic_id=epic_id)

        return state

    def get_state(self, story_id: str) -> WorkflowState | None:
        """Get workflow state for a story.

        Args:
            story_id: Story identifier.

        Returns:
            WorkflowState if exists, None otherwise.
        """
        state_path = self._get_state_path(story_id)

        if not state_path.exists():
            return None

        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WorkflowState.from_dict(data)
        except (OSError, json.JSONDecodeError) as e:
            logger.error("workflow_state_read_failed", story_id=story_id, error=str(e))
            return None

    def _save_state(self, state: WorkflowState) -> None:
        """Save workflow state to disk.

        Args:
            state: WorkflowState to save.

        Raises:
            OSError: If write fails.
        """
        self._ensure_dir()
        state.last_updated = datetime.now().isoformat()
        state_path = self._get_state_path(state.story_id)

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2)
        except OSError as e:
            logger.error(
                "workflow_state_write_failed",
                story_id=state.story_id,
                error=str(e),
            )
            raise

    def update_phase(self, story_id: str, new_phase: str) -> WorkflowState:
        """Update current phase for a story.

        Args:
            story_id: Story identifier.
            new_phase: New phase ID.

        Returns:
            Updated WorkflowState.

        Raises:
            ValueError: If story not found or invalid phase.
        """
        state = self.get_state(story_id)
        if not state:
            raise ValueError(f"No workflow state found for {story_id}")

        if new_phase not in PHASE_CONFIG:
            raise ValueError(f"Invalid phase: {new_phase}")

        # Mark current phase as complete
        if state.current_phase and state.current_phase not in state.completed_phases:
            state.completed_phases.append(state.current_phase)

        state.current_phase = new_phase
        state.active_agents = [PHASE_CONFIG[new_phase]["primary_agent"]]

        self._save_state(state)
        logger.info(
            "workflow_phase_updated",
            story_id=story_id,
            phase=new_phase,
        )

        return state

    def set_artifact(
        self, story_id: str, artifact: str, exists: bool = True
    ) -> WorkflowState:
        """Set artifact existence status.

        Args:
            story_id: Story identifier.
            artifact: Artifact name.
            exists: Whether artifact exists.

        Returns:
            Updated WorkflowState.

        Raises:
            ValueError: If story not found.
        """
        state = self.get_state(story_id)
        if not state:
            raise ValueError(f"No workflow state found for {story_id}")

        state.artifacts[artifact] = exists
        self._save_state(state)

        logger.info(
            "workflow_artifact_set",
            story_id=story_id,
            artifact=artifact,
            exists=exists,
        )

        return state

    def start_parallel(
        self,
        story_id: str,
        agents: list[str],
    ) -> WorkflowState:
        """Start parallel task execution.

        Args:
            story_id: Story identifier.
            agents: List of agents to run in parallel.

        Returns:
            Updated WorkflowState.

        Raises:
            ValueError: If story not found.
        """
        state = self.get_state(story_id)
        if not state:
            raise ValueError(f"No workflow state found for {story_id}")

        state.parallel_status = {
            "phase": state.current_phase,
            "tasks": {agent: TaskStatus.PENDING.value for agent in agents},
            "started_at": datetime.now().isoformat(),
            "notifications": [],
        }
        state.active_agents = agents

        self._save_state(state)
        logger.info(
            "workflow_parallel_started",
            story_id=story_id,
            agents=agents,
        )

        return state

    def update_parallel_task(
        self,
        story_id: str,
        agent: str,
        status: str,
        notification: str = "",
    ) -> WorkflowState:
        """Update parallel task status.

        Args:
            story_id: Story identifier.
            agent: Agent that completed task.
            status: New status (passed, failed).
            notification: Optional notification for primary agent.

        Returns:
            Updated WorkflowState.

        Raises:
            ValueError: If story not found or no parallel phase active.
        """
        state = self.get_state(story_id)
        if not state:
            raise ValueError(f"No workflow state found for {story_id}")

        if not state.parallel_status:
            raise ValueError(f"No parallel phase active for {story_id}")

        state.parallel_status["tasks"][agent] = status

        if notification:
            state.parallel_status["notifications"].append(notification)

        self._save_state(state)
        logger.info(
            "workflow_parallel_task_updated",
            story_id=story_id,
            agent=agent,
            status=status,
        )

        return state

    def add_blocker(
        self,
        story_id: str,
        level: str,
        description: str,
        source_agent: str,
    ) -> WorkflowState:
        """Add a blocker/escalation.

        Args:
            story_id: Story identifier.
            level: Escalation level (L1, L2, L3).
            description: Blocker description.
            source_agent: Agent that raised the blocker.

        Returns:
            Updated WorkflowState.

        Raises:
            ValueError: If story not found.
        """
        state = self.get_state(story_id)
        if not state:
            raise ValueError(f"No workflow state found for {story_id}")

        blocker = {
            "level": level,
            "description": description,
            "source_agent": source_agent,
            "timestamp": datetime.now().isoformat(),
        }
        state.blockers.append(blocker)

        self._save_state(state)
        logger.info(
            "workflow_blocker_added",
            story_id=story_id,
            level=level,
        )

        return state

    def resolve_blocker(self, story_id: str, index: int = -1) -> WorkflowState:
        """Resolve a blocker.

        Args:
            story_id: Story identifier.
            index: Blocker index to resolve. Defaults to last.

        Returns:
            Updated WorkflowState.

        Raises:
            ValueError: If story not found or no blockers.
        """
        state = self.get_state(story_id)
        if not state:
            raise ValueError(f"No workflow state found for {story_id}")

        if not state.blockers:
            raise ValueError(f"No blockers to resolve for {story_id}")

        resolved = state.blockers.pop(index)
        self._save_state(state)

        logger.info(
            "workflow_blocker_resolved",
            story_id=story_id,
            blocker=resolved["description"],
        )

        return state

    def set_active_story(self, story_id: str) -> None:
        """Set the currently active story.

        Args:
            story_id: Story identifier.
        """
        self._ensure_dir()
        active_path = self._get_active_path()

        try:
            with open(active_path, "w", encoding="utf-8") as f:
                json.dump({"active_story": story_id}, f)
        except OSError as e:
            logger.error("workflow_active_write_failed", error=str(e))

    def get_active_story(self) -> str | None:
        """Get the currently active story ID.

        Returns:
            Active story ID or None.
        """
        active_path = self._get_active_path()

        if not active_path.exists():
            return None

        try:
            with open(active_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("active_story")
        except (OSError, json.JSONDecodeError):
            return None

    def set_capabilities(
        self, story_id: str, capabilities: dict[str, bool]
    ) -> WorkflowState:
        """Set detected capabilities.

        Args:
            story_id: Story identifier.
            capabilities: Dict of capability name -> available.

        Returns:
            Updated WorkflowState.

        Raises:
            ValueError: If story not found.
        """
        state = self.get_state(story_id)
        if not state:
            raise ValueError(f"No workflow state found for {story_id}")

        state.capabilities = capabilities
        self._save_state(state)

        logger.info(
            "workflow_capabilities_set",
            story_id=story_id,
            capabilities=capabilities,
        )

        return state

    def set_story_type(self, story_id: str, story_type: str) -> WorkflowState:
        """Set story type classification.

        Args:
            story_id: Story identifier.
            story_type: Backend, frontend, or fullstack.

        Returns:
            Updated WorkflowState.

        Raises:
            ValueError: If story not found.
        """
        state = self.get_state(story_id)
        if not state:
            raise ValueError(f"No workflow state found for {story_id}")

        state.story_type = story_type
        self._save_state(state)

        logger.info(
            "workflow_story_type_set",
            story_id=story_id,
            story_type=story_type,
        )

        return state

    def list_stories(self) -> list[str]:
        """List all stories with workflow state.

        Returns:
            List of story IDs.
        """
        if not self.root.exists():
            return []

        return [p.stem for p in self.root.glob("*.json") if p.name != "active.json"]
