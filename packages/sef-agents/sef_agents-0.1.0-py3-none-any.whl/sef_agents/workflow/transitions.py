"""Phase Transition Rules for SEF Workflow.

Validates phase transitions based on artifact requirements
and determines next suggested agents.
"""

from pathlib import Path

import structlog

from sef_agents.constants import (
    PHASE_CONFIG,
    AGENT_NEXT_SUGGESTION,
)
from sef_agents.workflow.state_machine import WorkflowManager, WorkflowState

logger = structlog.get_logger(__name__)


class TransitionValidator:
    """Validates and executes phase transitions.

    Attributes:
        manager: WorkflowManager instance.
        project_root: Root directory for artifact detection.
    """

    def __init__(
        self,
        manager: WorkflowManager | None = None,
        project_root: Path | None = None,
    ) -> None:
        """Initialize transition validator.

        Args:
            manager: WorkflowManager instance. Creates default if None.
            project_root: Project root for artifact detection.
        """
        self.manager = manager or WorkflowManager()
        self.project_root = project_root or Path(".")

    def check_artifacts(self, state: WorkflowState, phase: str) -> dict[str, bool]:
        """Check if required artifacts exist for a phase.

        Args:
            state: Current workflow state.
            phase: Target phase ID.

        Returns:
            Dict of artifact name -> exists flag.
        """
        config = PHASE_CONFIG.get(phase, {})
        required = config.get("required_artifacts", [])

        results: dict[str, bool] = {}

        for artifact in required:
            if artifact in state.artifacts:
                results[artifact] = state.artifacts[artifact]
            elif artifact == "CODE_MAP.md":
                results[artifact] = (self.project_root / "CODE_MAP.md").exists()
            elif artifact.startswith("requirements/"):
                req_dir = self.project_root / "docs" / "requirements"
                results[artifact] = req_dir.exists() and any(req_dir.glob("*.md"))
            elif artifact == "conceptual_tests":
                # Check for tests/plans/STORY-XXX.json file
                plan_file = (
                    self.project_root / "tests" / "plans" / f"{state.story_id}.json"
                )
                results[artifact] = plan_file.exists() or state.artifacts.get(
                    artifact, False
                )
            elif artifact in (
                "ac_validated",
                "design",
                "implementation",
                "review_passed",
            ):
                results[artifact] = state.artifacts.get(artifact, False)
            elif artifact in ("tests_passed", "security_passed"):
                if state.parallel_status:
                    tasks = state.parallel_status.get("tasks", {})
                    if artifact == "tests_passed":
                        results[artifact] = tasks.get("tester") == "passed"
                    else:
                        results[artifact] = tasks.get("security_owner") == "passed"
                else:
                    results[artifact] = state.artifacts.get(artifact, False)
            else:
                results[artifact] = state.artifacts.get(artifact, False)

        return results

    def can_transition(self, story_id: str, target_phase: str) -> tuple[bool, str]:
        """Check if transition to target phase is valid.

        Args:
            story_id: Story identifier.
            target_phase: Target phase ID.

        Returns:
            Tuple of (can_transition, reason).
        """
        state = self.manager.get_state(story_id)
        if not state:
            return False, f"No workflow state found for {story_id}"

        if target_phase not in PHASE_CONFIG:
            return False, f"Invalid phase: {target_phase}"

        current_config = PHASE_CONFIG.get(state.current_phase, {})
        if current_config.get("next_phase") != target_phase:
            # Allow skipping back or jumping if artifacts exist
            pass

        # Check required artifacts
        artifact_status = self.check_artifacts(state, target_phase)
        missing = [name for name, exists in artifact_status.items() if not exists]

        if missing:
            return False, f"Missing artifacts: {', '.join(missing)}"

        # Check for blockers
        if state.blockers:
            return False, f"Active blockers: {len(state.blockers)}"

        return True, "All requirements met"

    def transition(self, story_id: str, target_phase: str) -> WorkflowState:
        """Execute transition to target phase.

        Args:
            story_id: Story identifier.
            target_phase: Target phase ID.

        Returns:
            Updated WorkflowState.

        Raises:
            ValueError: If transition not valid.
        """
        can_trans, reason = self.can_transition(story_id, target_phase)
        if not can_trans:
            raise ValueError(f"Cannot transition: {reason}")

        return self.manager.update_phase(story_id, target_phase)

    def get_next_phase(self, story_id: str) -> str | None:
        """Get the next phase for a story.

        Args:
            story_id: Story identifier.

        Returns:
            Next phase ID or None if at end.
        """
        state = self.manager.get_state(story_id)
        if not state:
            return None

        config = PHASE_CONFIG.get(state.current_phase, {})
        return config.get("next_phase")

    def suggest_next_agent(
        self,
        story_id: str,
        completed_task: str = "",
    ) -> dict:
        """Suggest next agent after task completion.

        Args:
            story_id: Story identifier.
            completed_task: Description of completed task.

        Returns:
            Dict with suggestion details.
        """
        state = self.manager.get_state(story_id)
        if not state:
            return {
                "error": f"No workflow state found for {story_id}",
                "suggestion": None,
            }

        current_agent = state.active_agents[0] if state.active_agents else None
        current_config = PHASE_CONFIG.get(state.current_phase, {})

        # Check for background notifications
        notifications = []
        if state.parallel_status:
            notifications = state.parallel_status.get("notifications", [])

        next_suggestion = AGENT_NEXT_SUGGESTION.get(current_agent)

        is_parallel = isinstance(next_suggestion, list)
        parallel_agents = next_suggestion if is_parallel else None

        background_agent = current_config.get("background_agent")
        background_notification = None
        if background_agent and notifications:
            background_notification = notifications[-1] if notifications else None

        # Determine single next agent
        if is_parallel:
            next_agent = next_suggestion  # List of parallel agents
        else:
            next_agent = next_suggestion

        return {
            "story_id": story_id,
            "current_phase": state.current_phase,
            "current_agent": current_agent,
            "completed_task": completed_task,
            "next_agent": next_agent,
            "is_parallel": is_parallel,
            "parallel_agents": parallel_agents,
            "background_notification": background_notification,
            "notifications": notifications,
            "reason": self._get_suggestion_reason(current_agent, next_agent),
        }

    def _get_suggestion_reason(
        self,
        current_agent: str | None,
        next_agent: str | list | None,
    ) -> str:
        """Generate reason for agent suggestion.

        Args:
            current_agent: Current agent name.
            next_agent: Suggested next agent(s).

        Returns:
            Human-readable reason.
        """
        if not next_agent:
            return "Workflow complete"

        if isinstance(next_agent, list):
            agents_str = " + ".join(next_agent)
            return f"Ready for parallel validation: {agents_str}"

        reasons = {
            "product_manager": "CODE_MAP ready → Define requirements",
            "qa_lead": "Requirements ready → Validate AC",
            "test_designer": "Requirements ready → Design conceptual tests",
            "architect": "AC validated → Design system",
            "developer": "Design ready → Implement",
            "pr_reviewer": "Implementation ready → Review code",
            "tester": "Review passed → Write executable tests",
            "security_owner": "Review passed → Security audit",
            "scrum_master": "All validations passed → Close loop",
        }

        return reasons.get(next_agent, f"Proceed to {next_agent}")

    def get_phase_status(self, story_id: str) -> dict:
        """Get current phase status summary.

        Args:
            story_id: Story identifier.

        Returns:
            Dict with phase status details.
        """
        state = self.manager.get_state(story_id)
        if not state:
            return {"error": f"No workflow state found for {story_id}"}

        current_config = PHASE_CONFIG.get(state.current_phase, {})
        artifact_status = self.check_artifacts(state, state.current_phase)

        # Check next phase readiness
        next_phase = current_config.get("next_phase")
        next_ready = False
        next_missing = []

        if next_phase:
            next_artifact_status = self.check_artifacts(state, next_phase)
            next_missing = [k for k, v in next_artifact_status.items() if not v]
            next_ready = len(next_missing) == 0

        return {
            "story_id": story_id,
            "story_type": state.story_type,
            "current_phase": state.current_phase,
            "phase_name": current_config.get("name", "Unknown"),
            "active_agents": state.active_agents,
            "completed_phases": state.completed_phases,
            "artifacts": artifact_status,
            "next_phase": next_phase,
            "next_phase_ready": next_ready,
            "next_missing_artifacts": next_missing,
            "parallel_status": state.parallel_status,
            "blockers": state.blockers,
            "capabilities": state.capabilities,
        }
