"""Handoff event logger for SEF Agents.

Logs ownership transfers, escalations, and other handoff events
to handoff_log.jsonl for audit trail.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import structlog

from sef_agents.utils.git_utils import get_current_user_id

logger = structlog.get_logger(__name__)

EventType = Literal[
    "ownership_transfer",
    "agent_activation",
    "escalation",
    "escalation_resolved",
    "replan_triggered",
    "debt_logged",
    "phase_complete",
]


def _get_log_path(project_root: Path | None = None) -> Path:
    """Get path to handoff log file.

    Args:
        project_root: Project root directory. Defaults to session project_root
                      if set, otherwise cwd.

    Returns:
        Path to handoff_log.jsonl.
    """
    if project_root is None:
        from sef_agents.session import SessionManager

        session = SessionManager.get()
        project_root = session.project_root or Path.cwd()

    return project_root / "sef-reports" / "handoff_log.jsonl"


def log_event(
    event_type: EventType,
    project_root: Path | None = None,
    **kwargs: str | list[str] | None,
) -> bool:
    """Log a handoff event to handoff_log.jsonl.

    Args:
        event_type: Type of event to log.
        project_root: Project root directory.
        **kwargs: Additional event-specific fields.

    Returns:
        True if logged successfully, False otherwise.
    """
    log_path = _get_log_path(project_root)

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    user = get_current_user_id(project_root)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "user": user,
        **{k: v for k, v in kwargs.items() if v is not None},
    }

    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        logger.info("event_logged", event_type=event_type, user=user)
        return True
    except OSError as e:
        logger.error("event_log_failed", error=str(e))
        return False


def log_agent_activation(agent: str, project_root: Path | None = None) -> bool:
    """Log agent activation event and create context graph node.

    Args:
        agent: Agent that was activated.
        project_root: Project root directory.

    Returns:
        True if logged successfully.
    """
    # Log to handoff_log.jsonl (existing behavior)
    result = log_event("agent_activation", project_root, agent=agent)

    # Create agent_session node in context graph (new behavior)
    try:
        from sef_agents.tools.context_graph import ContextNode, get_context_graph

        graph = get_context_graph(project_root)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        node_id = f"agent_session-{ts}"

        agent_desc = f"Agent session: {agent}"
        node = ContextNode(
            id=node_id,
            node_type="agent_session",
            content=agent_desc,
            metadata={"agent": agent},
        )
        graph.add_node(node)
        graph.save()
        logger.info("agent_session_node_created", node_id=node_id, agent=agent)
    except (OSError, ValueError, ImportError) as e:
        # Non-blocking: log error but don't fail activation
        logger.warning("context_graph_node_failed", agent=agent, error=str(e))

    return result


def log_ownership_transfer(
    story_id: str,
    from_owner: str,
    to_owner: str,
    reason: str,
    project_root: Path | None = None,
) -> bool:
    """Log ownership transfer event.

    Args:
        story_id: Story being transferred.
        from_owner: Previous owner.
        to_owner: New owner.
        reason: Reason for transfer.
        project_root: Project root directory.

    Returns:
        True if logged successfully.
    """
    return log_event(
        "ownership_transfer",
        project_root,
        story_id=story_id,
        from_owner=from_owner,
        to_owner=to_owner,
        reason=reason,
    )


def log_escalation(
    level: str,
    from_agent: str,
    to_agents: list[str],
    reason: str,
    story_id: str | None = None,
    project_root: Path | None = None,
) -> bool:
    """Log escalation event.

    Args:
        level: Escalation level (L1, L2, L3).
        from_agent: Agent that escalated.
        to_agents: Agents escalated to.
        reason: Reason for escalation.
        story_id: Related story ID.
        project_root: Project root directory.

    Returns:
        True if logged successfully.
    """
    return log_event(
        "escalation",
        project_root,
        level=level,
        from_agent=from_agent,
        to_agents=to_agents,
        reason=reason,
        story_id=story_id,
    )


def log_debt_found(
    debt_id: str,
    location: str,
    debt_type: str,
    severity: str,
    story_id: str | None = None,
    project_root: Path | None = None,
) -> bool:
    """Log technical debt discovery event.

    Args:
        debt_id: Debt registry ID.
        location: File and line location.
        debt_type: Type of debt.
        severity: Debt severity.
        story_id: Story during which debt was found.
        project_root: Project root directory.

    Returns:
        True if logged successfully.
    """
    return log_event(
        "debt_logged",
        project_root,
        debt_id=debt_id,
        location=location,
        debt_type=debt_type,
        severity=severity,
        story_id=story_id,
    )


def log_phase_complete(
    story_id: str,
    phase: str,
    outcome: str,
    next_phase: str | None = None,
    project_root: Path | None = None,
) -> bool:
    """Log phase completion event.

    Args:
        story_id: Story that completed phase.
        phase: Phase that was completed.
        outcome: Outcome (passed, failed).
        next_phase: Next phase in flow.
        project_root: Project root directory.

    Returns:
        True if logged successfully.
    """
    return log_event(
        "phase_complete",
        project_root,
        story_id=story_id,
        phase=phase,
        outcome=outcome,
        next_phase=next_phase,
    )


def log_replan_triggered(
    story_id: str,
    trigger: str,
    impact: str,
    project_root: Path | None = None,
) -> bool:
    """Log replan trigger event.

    Args:
        story_id: Story being replanned.
        trigger: What triggered the replan (new req, blocker, etc).
        impact: Expected impact (scope change, delay).
        project_root: Project root directory.

    Returns:
        True if logged successfully.
    """
    return log_event(
        "replan_triggered",
        project_root,
        story_id=story_id,
        trigger=trigger,
        impact=impact,
    )
