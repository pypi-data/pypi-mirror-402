"""Handoff Tools for SEF Agents.

Consolidated logging for workflow events: escalation, ownership, replan, debt, phase.
"""

import uuid

from sef_agents.constants import Status
from sef_agents.session import SessionManager
from sef_agents.utils import handoff_logger

# Valid event types
EVENT_TYPES = ("escalation", "ownership", "replan", "debt", "phase")


def _log_escalation_event(
    level: str,
    reason: str,
    to_agents: str,
    from_agent: str,
    active_agent: str,
    story_id: str | None,
) -> str:
    """Handle escalation event."""
    agents_list = [a.strip() for a in to_agents.split(",") if a.strip()]
    src_agent = from_agent if from_agent else active_agent
    success = handoff_logger.log_escalation(
        level=level,
        from_agent=src_agent,
        to_agents=agents_list,
        reason=reason,
        story_id=story_id,
    )
    if success:
        return (
            f"{Status.SUCCESS} Escalation logged\n"
            f"Level: {level}\n"
            f"From: {src_agent} → To: {', '.join(agents_list)}\n"
            f"Reason: {reason}"
        )
    return f"{Status.ERROR} Failed to log escalation"


def _log_ownership_event(
    story_id: str,
    active_agent: str,
    to_owner: str,
    reason: str,
) -> str:
    """Handle ownership transfer event."""
    success = handoff_logger.log_ownership_transfer(
        story_id=story_id,
        from_owner=active_agent,
        to_owner=to_owner,
        reason=reason,
    )
    if success:
        return (
            f"{Status.SUCCESS} Ownership transfer logged\n"
            f"Story: {story_id}\n"
            f"From: {active_agent} → To: {to_owner}\n"
            f"Reason: {reason}"
        )
    return f"{Status.ERROR} Failed to log ownership transfer"


def _log_replan_event(story_id: str, trigger: str, impact: str) -> str:
    """Handle replan event."""
    success = handoff_logger.log_replan_triggered(
        story_id=story_id,
        trigger=trigger,
        impact=impact,
    )
    if success:
        return (
            f"{Status.SUCCESS} Replan logged\n"
            f"Story: {story_id}\n"
            f"Trigger: {trigger}\n"
            f"Impact: {impact}"
        )
    return f"{Status.ERROR} Failed to log replan"


def _log_debt_event(
    debt_type: str, severity: str, location: str, story_id: str | None
) -> str:
    """Handle debt event."""
    debt_id = f"DEBT-{str(uuid.uuid4())[:8]}"
    success = handoff_logger.log_debt_found(
        debt_id=debt_id,
        location=location,
        debt_type=debt_type,
        severity=severity,
        story_id=story_id,
    )
    if success:
        return (
            f"{Status.SUCCESS} Debt logged: {debt_id}\n"
            f"Type: {debt_type} | Severity: {severity}\n"
            f"Location: {location}"
        )
    return f"{Status.ERROR} Failed to log debt"


def _log_phase_event(story_id: str, phase: str, outcome: str, next_phase: str) -> str:
    """Handle phase event."""
    next_p = next_phase if next_phase else None
    success = handoff_logger.log_phase_complete(story_id, phase, outcome, next_p)
    if success:
        return (
            f"{Status.SUCCESS} Phase completion logged\n"
            f"Story: {story_id}\n"
            f"Phase: {phase} → {outcome}\n"
            f"Next: {next_phase or 'None'}"
        )
    return f"{Status.ERROR} Failed to log phase completion"


def log_event(
    event_type: str,
    story_id: str = "",
    level: str = "",
    reason: str = "",
    to_agents: str = "",
    from_agent: str = "",
    to_owner: str = "",
    trigger: str = "",
    impact: str = "",
    debt_type: str = "",
    severity: str = "",
    location: str = "",
    phase: str = "",
    outcome: str = "",
    next_phase: str = "",
) -> str:
    """Log a workflow event.

    Args:
        event_type: One of: escalation, ownership, replan, debt, phase.
        story_id: Story identifier.
        level: Escalation level (L1, L2, L3) - for escalation events.
        reason: Reason for event - for escalation, ownership events.
        to_agents: Comma-separated target agents - for escalation events.
        from_agent: Source agent - for escalation events.
        to_owner: New owner - for ownership events.
        trigger: Replan trigger - for replan events.
        impact: Replan impact - for replan events.
        debt_type: Debt type - for debt events.
        severity: Debt severity - for debt events.
        location: Debt location - for debt events.
        phase: Phase name - for phase events.
        outcome: Phase outcome - for phase events.
        next_phase: Next phase - for phase events.

    Returns:
        Success/error message.
    """
    if event_type not in EVENT_TYPES:
        return f"{Status.ERROR} Invalid event_type. Use: {', '.join(EVENT_TYPES)}"

    active_agent = SessionManager.get().active_agent or "unknown"
    story = story_id if story_id else None

    if event_type == "escalation":
        return _log_escalation_event(
            level, reason, to_agents, from_agent, active_agent, story
        )

    if event_type == "ownership":
        return _log_ownership_event(story_id, active_agent, to_owner, reason)

    if event_type == "replan":
        return _log_replan_event(story_id, trigger, impact)

    if event_type == "debt":
        return _log_debt_event(debt_type, severity, location, story)

    if event_type == "phase":
        return _log_phase_event(story_id, phase, outcome, next_phase)

    return f"{Status.ERROR} Unknown event type: {event_type}"


def log_phase_completion_impl(
    story_id: str, phase: str, outcome: str, next_phase: str = ""
) -> str:
    """Log phase completion event (wrapper for MCP tool).

    Args:
        story_id: Story identifier.
        phase: Phase that was completed.
        outcome: Outcome (passed, failed).
        next_phase: Next phase in flow.

    Returns:
        Success/error message.
    """
    return log_event(
        event_type="phase",
        story_id=story_id,
        phase=phase,
        outcome=outcome,
        next_phase=next_phase,
    )


def log_phase_complete_impl(
    story_id: str, phase: str, outcome: str, next_phase: str = ""
) -> str:
    """Log phase completion event (alias for compatibility).

    Args:
        story_id: Story identifier.
        phase: Phase that was completed.
        outcome: Outcome (passed, failed).
        next_phase: Next phase in flow.

    Returns:
        Success/error message.
    """
    return log_phase_completion_impl(story_id, phase, outcome, next_phase)


# Backward compatibility wrappers for server.py
def log_escalation_impl(
    level: str, reason: str, to_agents: str, story_id: str = ""
) -> str:
    """Log escalation event (wrapper)."""
    return log_event(
        event_type="escalation",
        level=level,
        reason=reason,
        to_agents=to_agents,
        story_id=story_id,
    )


def log_ownership_transfer_impl(story_id: str, to_owner: str, reason: str) -> str:
    """Log ownership transfer event (wrapper)."""
    return log_event(
        event_type="ownership",
        story_id=story_id,
        to_owner=to_owner,
        reason=reason,
    )


def log_replan_triggered_impl(story_id: str, trigger: str, impact: str) -> str:
    """Log replan triggered event (wrapper)."""
    return log_event(
        event_type="replan",
        story_id=story_id,
        trigger=trigger,
        impact=impact,
    )


def log_debt_found_impl(
    debt_type: str, severity: str, location: str, story_id: str = ""
) -> str:
    """Log debt found event (wrapper)."""
    return log_event(
        event_type="debt",
        debt_type=debt_type,
        severity=severity,
        location=location,
        story_id=story_id,
    )


def log_escalation_event_impl(
    level: str, from_agent: str, to_agents: str, reason: str, story_id: str = ""
) -> str:
    """Log escalation event with explicit from_agent (wrapper)."""
    return log_event(
        event_type="escalation",
        level=level,
        from_agent=from_agent,
        to_agents=to_agents,
        reason=reason,
        story_id=story_id,
    )
