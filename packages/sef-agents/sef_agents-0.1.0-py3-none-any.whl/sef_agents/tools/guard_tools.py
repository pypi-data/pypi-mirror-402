from pathlib import Path
import structlog
from sef_agents.constants import Status, PHASE_CONFIG, AVAILABLE_AGENTS
from sef_agents.workflow.state_machine import WorkflowManager
from sef_agents.tools.context_tools import find_project_root

logger = structlog.get_logger(__name__)

# Pre-compute agent requirements from PHASE_CONFIG for performance
_AGENT_REQUIREMENTS: dict[str, list[str]] = {}
for phase in PHASE_CONFIG.values():
    _AGENT_REQUIREMENTS[phase["primary_agent"]] = phase["required_artifacts"]
    # Handle parallel/background agents if needed, though usually they share phase reqs
    if "parallel_agent" in phase:
        _AGENT_REQUIREMENTS[phase["parallel_agent"]] = phase["required_artifacts"]


def _check_codemap_exists() -> bool:
    """Check if CODE_MAP.md exists using priority-based detection.

    Detection priority (industry best practice):
    1. Session project_root (explicit user setting via set_project_root)
    2. CWD (current working directory - primary for test isolation)
    3. CWD parent traversal (find project root)
    4. Secondary endpoint: docs/CODE_MAP.md in root locations

    Returns:
        True if CODE_MAP.md found in any checked location.
    """
    from sef_agents.session import SessionManager

    # Priority 1: Explicit session project_root (highest priority)
    # Verify path still exists (handles stale session state)
    session_root = SessionManager.get().project_root
    if session_root and session_root.exists():
        if (session_root / "CODE_MAP.md").exists():
            logger.debug("codemap_found", source="session_root", path=str(session_root))
            return True
        # Secondary endpoint: docs/CODE_MAP.md
        if (session_root / "docs" / "CODE_MAP.md").exists():
            logger.debug(
                "codemap_found",
                source="session_root_docs",
                path=str(session_root / "docs" / "CODE_MAP.md"),
            )
            return True

    # Priority 2: CWD (important for test isolation)
    cwd = Path.cwd()
    if (cwd / "CODE_MAP.md").exists():
        logger.debug("codemap_found", source="cwd", path=str(cwd))
        return True
    # Secondary endpoint: docs/CODE_MAP.md in CWD
    if (cwd / "docs" / "CODE_MAP.md").exists():
        logger.debug(
            "codemap_found", source="cwd_docs", path=str(cwd / "docs" / "CODE_MAP.md")
        )
        return True

    # Priority 3: CWD parent traversal (find project root)
    for parent in cwd.parents:
        if (parent / "CODE_MAP.md").exists():
            logger.debug("codemap_found", source="cwd_parent", path=str(parent))
            return True
        # Secondary endpoint: docs/CODE_MAP.md in parent
        if (parent / "docs" / "CODE_MAP.md").exists():
            logger.debug(
                "codemap_found",
                source="cwd_parent_docs",
                path=str(parent / "docs" / "CODE_MAP.md"),
            )
            return True

    logger.debug(
        "codemap_not_found", checked_session=str(session_root), checked_cwd=str(cwd)
    )
    return False


def _check_artifact_exists(artifact: str) -> bool:
    """Check if an artifact exists using found root."""
    if artifact == "CODE_MAP.md":
        return _check_codemap_exists()

    root = find_project_root()
    if not root:
        root = Path.cwd()

    if artifact == "requirements":
        req_dir = root / "docs/requirements"
        return req_dir.exists() and any(req_dir.glob("*.md"))

    # Handle wildcards correctly
    if artifact == "requirements/*.md":
        req_dir = root / "docs/requirements"
        return req_dir.exists() and any(req_dir.glob("*.md"))

    if artifact in ("design", "implementation", "ac_validated", "review_passed"):
        manager = WorkflowManager()
        active = manager.get_active_story()
        if active:
            state = manager.get_state(active)
            if state:
                return state.artifacts.get(artifact, False)
        return False

    # Handle regular file paths (e.g., docs/ARCHITECTURE.md)
    artifact_path = root / artifact
    return artifact_path.exists()


def _check_agent_artifacts(agent_name: str) -> tuple[bool, list[str]]:
    """Check required artifacts for agent."""
    required = _AGENT_REQUIREMENTS.get(agent_name, [])
    missing = [art for art in required if not _check_artifact_exists(art)]
    return len(missing) == 0, missing


def check_agent_prerequisites_impl(agent_name: str) -> str:
    """Implementation of check_agent_prerequisites tool."""
    if agent_name not in AVAILABLE_AGENTS:
        return f"{Status.ERROR} Invalid agent: {agent_name}"

    all_exist, missing = _check_agent_artifacts(agent_name)

    if all_exist:
        return f"{Status.SUCCESS} All prerequisites met for `{agent_name}`."

    lines = [
        f"{Status.ERROR} Prerequisites not met for `{agent_name}`",
        "",
        "Missing artifacts:",
    ]
    for art in missing:
        lines.append(f"  - {art}")

    lines.append("")
    lines.append("Complete these before activating the agent.")
    return "\n".join(lines)
