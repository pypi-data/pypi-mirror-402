"""Tests for Workflow State Machine.

Real-execution tests for:
- State persistence
- Phase transitions
- Parallel task coordination
- Capability detection
"""

import pytest

from sef_agents.constants import Phase, StoryType, TaskStatus
from sef_agents.workflow.capabilities import (
    CapabilityDetector,
    detect_story_type_from_diff,
)
from sef_agents.workflow.state_machine import WorkflowManager, WorkflowState
from sef_agents.workflow.transitions import TransitionValidator


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""

    def test_state_creation_defaults(self):
        """State creates with sensible defaults."""
        state = WorkflowState(story_id="STORY-001")

        assert state.story_id == "STORY-001"
        assert state.current_phase == Phase.DISCOVERY.value
        assert state.active_agents == []
        assert state.completed_phases == []
        assert state.artifacts == {}
        assert state.created_at != ""
        assert state.last_updated != ""

    def test_state_to_dict(self):
        """State serializes to dict correctly."""
        state = WorkflowState(
            story_id="STORY-001",
            epic_id="EPIC-10",
            story_type=StoryType.FRONTEND.value,
        )

        data = state.to_dict()

        assert data["story_id"] == "STORY-001"
        assert data["epic_id"] == "EPIC-10"
        assert data["story_type"] == "frontend"

    def test_state_from_dict(self):
        """State deserializes from dict correctly."""
        data = {
            "story_id": "STORY-002",
            "epic_id": "EPIC-20",
            "current_phase": Phase.IMPLEMENTATION.value,
            "active_agents": ["developer"],
            "completed_phases": [Phase.DISCOVERY.value, Phase.REQUIREMENTS.value],
            "artifacts": {"CODE_MAP.md": True},
            "parallel_status": None,
            "story_type": "backend",
            "capabilities": {},
            "blockers": [],
            "last_updated": "2024-12-22T10:00:00",
            "created_at": "2024-12-22T09:00:00",
        }

        state = WorkflowState.from_dict(data)

        assert state.story_id == "STORY-002"
        assert state.current_phase == Phase.IMPLEMENTATION.value
        assert len(state.completed_phases) == 2


class TestWorkflowManager:
    """Tests for WorkflowManager persistence."""

    def test_create_state(self, tmp_path):
        """Creates and persists new state."""
        manager = WorkflowManager(root=tmp_path)

        state = manager.create_state("STORY-001", "EPIC-10")

        assert state.story_id == "STORY-001"
        assert state.epic_id == "EPIC-10"

        # Verify file created
        state_file = tmp_path / "STORY-001.json"
        assert state_file.exists()

    def test_create_state_duplicate_raises(self, tmp_path):
        """Creating duplicate state raises error."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")

        with pytest.raises(FileExistsError):
            manager.create_state("STORY-001")

    def test_get_state(self, tmp_path):
        """Gets persisted state correctly."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001", "EPIC-10")

        state = manager.get_state("STORY-001")

        assert state is not None
        assert state.story_id == "STORY-001"
        assert state.epic_id == "EPIC-10"

    def test_get_state_not_found(self, tmp_path):
        """Returns None for non-existent state."""
        manager = WorkflowManager(root=tmp_path)

        state = manager.get_state("STORY-999")

        assert state is None

    def test_update_phase(self, tmp_path):
        """Updates phase and marks previous complete."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")

        state = manager.update_phase("STORY-001", Phase.REQUIREMENTS.value)

        assert state.current_phase == Phase.REQUIREMENTS.value
        assert Phase.DISCOVERY.value in state.completed_phases
        assert "product_manager" in state.active_agents

    def test_set_artifact(self, tmp_path):
        """Sets artifact status correctly."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")

        state = manager.set_artifact("STORY-001", "CODE_MAP.md", True)

        assert state.artifacts["CODE_MAP.md"] is True

    def test_start_parallel(self, tmp_path):
        """Starts parallel phase correctly."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")

        state = manager.start_parallel("STORY-001", ["tester", "security_owner"])

        assert state.parallel_status is not None
        assert "tester" in state.parallel_status["tasks"]
        assert "security_owner" in state.parallel_status["tasks"]
        assert state.parallel_status["tasks"]["tester"] == TaskStatus.PENDING.value

    def test_update_parallel_task(self, tmp_path):
        """Updates parallel task status."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")
        manager.start_parallel("STORY-001", ["tester", "security_owner"])

        state = manager.update_parallel_task(
            "STORY-001",
            "tester",
            TaskStatus.PASSED.value,
            "All tests passed",
        )

        assert state.parallel_status["tasks"]["tester"] == TaskStatus.PASSED.value
        assert "All tests passed" in state.parallel_status["notifications"]

    def test_add_blocker(self, tmp_path):
        """Adds blocker to state."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")

        state = manager.add_blocker(
            "STORY-001",
            "L2",
            "Design unclear",
            "developer",
        )

        assert len(state.blockers) == 1
        assert state.blockers[0]["level"] == "L2"
        assert state.blockers[0]["source_agent"] == "developer"

    def test_resolve_blocker(self, tmp_path):
        """Resolves blocker from state."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")
        manager.add_blocker("STORY-001", "L1", "Test blocker", "tester")

        state = manager.resolve_blocker("STORY-001")

        assert len(state.blockers) == 0

    def test_active_story(self, tmp_path):
        """Tracks active story correctly."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")

        manager.set_active_story("STORY-001")
        active = manager.get_active_story()

        assert active == "STORY-001"

    def test_list_stories(self, tmp_path):
        """Lists all stories with state."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")
        manager.create_state("STORY-002")
        manager.create_state("STORY-003")

        stories = manager.list_stories()

        assert len(stories) == 3
        assert "STORY-001" in stories
        assert "STORY-002" in stories


class TestTransitionValidator:
    """Tests for phase transition validation."""

    def test_can_transition_missing_artifacts(self, tmp_path):
        """Blocks transition when artifacts missing."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")
        validator = TransitionValidator(manager, tmp_path)

        can_trans, reason = validator.can_transition(
            "STORY-001",
            Phase.REQUIREMENTS.value,
        )

        assert can_trans is False
        assert "CODE_MAP.md" in reason

    def test_can_transition_with_artifacts(self, tmp_path):
        """Allows transition when artifacts exist."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")
        manager.set_artifact("STORY-001", "CODE_MAP.md", True)
        manager.set_artifact("STORY-001", "docs/ARCHITECTURE.md", True)

        # Create actual files - REQUIREMENTS phase needs both
        (tmp_path / "CODE_MAP.md").write_text("# Code Map")
        (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "ARCHITECTURE.md").write_text("# Architecture")

        validator = TransitionValidator(manager, tmp_path)

        can_trans, reason = validator.can_transition(
            "STORY-001",
            Phase.REQUIREMENTS.value,
        )

        assert can_trans is True

    def test_suggest_next_agent_sequential(self, tmp_path):
        """Suggests correct next agent in sequence."""
        manager = WorkflowManager(root=tmp_path)
        state = manager.create_state("STORY-001")
        state.active_agents = ["architect"]  # Architect -> developer (sequential)
        manager._save_state(state)

        validator = TransitionValidator(manager)

        suggestion = validator.suggest_next_agent("STORY-001", "Design complete")

        assert suggestion["next_agent"] == "developer"
        assert suggestion["is_parallel"] is False

    def test_suggest_next_agent_qa_gate_parallel(self, tmp_path):
        """Suggests parallel QA Gate agents after PM."""
        manager = WorkflowManager(root=tmp_path)
        state = manager.create_state("STORY-001")
        state.active_agents = ["product_manager"]
        manager._save_state(state)

        validator = TransitionValidator(manager)

        suggestion = validator.suggest_next_agent("STORY-001", "Defined requirements")

        assert suggestion["is_parallel"] is True
        assert "qa_lead" in suggestion["parallel_agents"]
        assert "test_designer" in suggestion["parallel_agents"]

    def test_suggest_next_agent_parallel(self, tmp_path):
        """Suggests parallel agents when appropriate."""
        manager = WorkflowManager(root=tmp_path)
        state = manager.create_state("STORY-001")
        state.active_agents = ["pr_reviewer"]
        manager._save_state(state)

        validator = TransitionValidator(manager)

        suggestion = validator.suggest_next_agent("STORY-001", "Review complete")

        assert suggestion["is_parallel"] is True
        assert "tester" in suggestion["parallel_agents"]
        assert "security_owner" in suggestion["parallel_agents"]

    def test_get_phase_status(self, tmp_path):
        """Returns complete phase status."""
        manager = WorkflowManager(root=tmp_path)
        manager.create_state("STORY-001")

        # Create CODE_MAP.md file for artifact detection
        (tmp_path / "CODE_MAP.md").write_text("# Code Map")

        # Move to Requirements phase which requires CODE_MAP.md
        manager.update_phase("STORY-001", Phase.REQUIREMENTS.value)

        validator = TransitionValidator(manager, tmp_path)

        status = validator.get_phase_status("STORY-001")

        assert status["story_id"] == "STORY-001"
        assert status["current_phase"] == Phase.REQUIREMENTS.value
        assert "CODE_MAP.md" in status["artifacts"]
        assert status["artifacts"]["CODE_MAP.md"] is True


class TestCapabilityDetector:
    """Tests for capability detection."""

    def test_classify_backend_story(self):
        """Classifies backend story correctly."""
        detector = CapabilityDetector()

        content = """
        # User Story
        As a developer, I need an API endpoint to fetch user data.
        The service should connect to the database and return JSON.
        """

        story_type = detector.classify_story_type(content)

        assert story_type == StoryType.BACKEND.value

    def test_classify_frontend_story(self):
        """Classifies frontend story correctly."""
        detector = CapabilityDetector()

        content = """
        # User Story
        As a user, I need a login form component.
        The UI should have a button and responsive layout.
        """

        story_type = detector.classify_story_type(content)

        assert story_type == StoryType.FRONTEND.value

    def test_classify_fullstack_story(self):
        """Classifies fullstack story correctly."""
        detector = CapabilityDetector()

        content = """
        # User Story
        As a user, I need a dashboard page that displays API data.
        The frontend component should fetch from the backend service.
        """

        story_type = detector.classify_story_type(content)

        assert story_type == StoryType.FULLSTACK.value

    def test_detect_browser_tools_from_config(self, tmp_path):
        """Detects browser tools from playwright config."""
        detector = CapabilityDetector(tmp_path)

        # Create playwright config
        (tmp_path / "playwright.config.ts").write_text("export default {}")

        result = detector.detect_browser_tools()

        assert result is True

    def test_detect_browser_tools_missing(self, tmp_path, monkeypatch):
        """Returns False when no browser tools detected."""
        # Mock check_browser_tools_available to return False (no MCP tools)
        import sef_agents.tools.browser.playwright_mcp_client as mcp_client

        monkeypatch.setattr(mcp_client, "check_browser_tools_available", lambda: False)

        detector = CapabilityDetector(tmp_path)

        result = detector.detect_browser_tools()

        assert result is False

    def test_check_capabilities_frontend_no_browser(self, tmp_path, monkeypatch):
        """Detects capability gap for frontend without browser."""
        # Mock check_browser_tools_available to return False (no MCP tools)
        import sef_agents.tools.browser.playwright_mcp_client as mcp_client

        monkeypatch.setattr(mcp_client, "check_browser_tools_available", lambda: False)

        detector = CapabilityDetector(tmp_path)

        # Create requirements file
        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True)
        (req_dir / "STORY-001.md").write_text(
            "# Story\nBuild a React component with button"
        )

        result = detector.check_capabilities("STORY-001")

        assert result["story_type"] == StoryType.FRONTEND.value
        assert result["requires_browser"] is True
        assert result["browser_available"] is False
        assert len(result["gaps"]) == 1

    def test_check_capabilities_backend(self, tmp_path):
        """No gaps for backend story."""
        detector = CapabilityDetector(tmp_path)

        # Create requirements file
        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True)
        (req_dir / "STORY-002.md").write_text(
            "# Story\nCreate API endpoint for user service"
        )

        result = detector.check_capabilities("STORY-002")

        assert result["story_type"] == StoryType.BACKEND.value
        assert result["requires_browser"] is False
        assert len(result["gaps"]) == 0


class TestDetectStoryTypeFromDiff:
    """Tests for diff-based story type detection."""

    def test_frontend_diff(self):
        """Detects frontend from diff."""
        diff = """
diff --git a/src/components/Button.tsx b/src/components/Button.tsx
+++ b/src/components/Button.tsx
+export const Button = () => <button>Click</button>;
"""

        story_type = detect_story_type_from_diff(diff)

        assert story_type == StoryType.FRONTEND.value

    def test_backend_diff(self):
        """Detects backend from diff."""
        diff = """
diff --git a/src/api/users.py b/src/api/users.py
+++ b/src/api/users.py
+def get_user(user_id: int):
+    return db.query(User).get(user_id)
"""

        story_type = detect_story_type_from_diff(diff)

        assert story_type == StoryType.BACKEND.value

    def test_fullstack_diff(self):
        """Detects fullstack from diff."""
        diff = """
diff --git a/src/api/users.py b/src/api/users.py
+++ b/src/api/users.py
+def get_user(): pass

diff --git a/src/components/UserList.tsx b/src/components/UserList.tsx
+++ b/src/components/UserList.tsx
+export const UserList = () => <div>Users</div>;
"""

        story_type = detect_story_type_from_diff(diff)

        assert story_type == StoryType.FULLSTACK.value
