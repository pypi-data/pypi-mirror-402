"""Workflow State Machine for SEF Agents.

This package provides SDLC workflow tracking:
- State persistence per story
- Phase transitions with artifact validation
- Parallel task coordination
- Capability detection for tools
"""

from sef_agents.workflow.capabilities import CapabilityDetector
from sef_agents.workflow.state_machine import WorkflowManager, WorkflowState
from sef_agents.workflow.transitions import TransitionValidator

__all__ = [
    "CapabilityDetector",
    "TransitionValidator",
    "WorkflowManager",
    "WorkflowState",
]
