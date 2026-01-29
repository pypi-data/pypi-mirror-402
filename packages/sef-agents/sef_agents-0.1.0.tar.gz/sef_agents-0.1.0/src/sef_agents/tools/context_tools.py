from datetime import datetime, timezone
from pathlib import Path

import structlog

from sef_agents.constants import Status, AVAILABLE_AGENTS
from sef_agents.session import SessionManager
from sef_agents.tools import codemap

logger = structlog.get_logger(__name__)


def _format_available_agents_numbered() -> str:
    """Private helper to format agent list as numbered list for activation."""
    output = "🚀 SEF (Synchronous Engineering Framework) - Agent Selection\n\n"
    output += "Please select your agent by entering the corresponding number:\n\n"

    agents_list = list(AVAILABLE_AGENTS.items())
    for idx, (agent, desc) in enumerate(agents_list, start=1):
        output += f"{idx}. {desc}\n"
        output += f"   (Agent: `{agent}`)\n\n"

    output += f"Enter the number (1-{len(agents_list)}) to activate your agent."
    return output


def set_project_root_impl(path: str) -> str:
    """Implementation of set_project_root tool."""
    p = Path(path).resolve()
    if not p.exists():
        return f"{Status.ERROR} Directory {path} does not exist"

    SessionManager.get().project_root = p
    logger.info("project_root_set", path=str(p))

    return f"{Status.SUCCESS} Project root set to: `{p}`"


def identify_agent_impl(context_history: str = "") -> str:
    """Implementation of identify_agent tool."""
    active_agent = SessionManager.get().active_agent

    if active_agent:
        return f"{Status.SUCCESS} Agent is active: `{active_agent}`. Proceed with SEF Protocol."

    agents_output = _format_available_agents_numbered()

    return (
        "⛔ STOP. No SEF Agent is active.\n"
        "You MUST ask the user:\n\n"
        f"{agents_output}\n\n"
        "Once they answer, call `set_active_agent(agent_name)` or `set_active_agent(number)`."
    )


def find_project_root() -> Path | None:
    """Find the project root by looking for CODE_MAP.md.
    Prioritizes session state -> CWD traversal.
    """
    # 1. Prioritize session state
    root = SessionManager.get().project_root
    if root:
        return root

    # 2. Fallback to CWD traversal
    current = Path.cwd()
    for path in [current, *current.parents]:
        if (path / "CODE_MAP.md").exists():
            return path
    return None


def generate_codemap_wrapper(directory: str) -> str:
    """Wrapper that also sets project root context and creates context graph node."""
    result = codemap.generate_codemap_tool(directory)

    # Auto-set project root if successful
    if "Generated" in result or "exists" in result:
        p = Path(directory).resolve()
        if p.exists():
            SessionManager.get().project_root = p
            logger.info("project_root_auto_set", path=str(p))

            # Create context graph node for CODE_MAP generation
            try:
                from sef_agents.tools.context_graph import (
                    ContextNode,
                    get_context_graph,
                )

                active_agent = SessionManager.get().active_agent
                graph = get_context_graph(p)
                ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                node_id = f"decision-{ts}"

                content = f"Generated CODE_MAP.md for {p.name}"
                node = ContextNode(
                    id=node_id,
                    node_type="decision",
                    content=content,
                    metadata={"directory": str(p), "agent": active_agent or "unknown"},
                )
                graph.add_node(node)

                # Link to most recent agent_session if available
                agent_sessions = graph.get_nodes_by_type("agent_session")
                if agent_sessions:
                    latest_session = max(agent_sessions, key=lambda n: n.timestamp)
                    graph.add_edge(node_id, latest_session.id, "discovered_by")

                graph.save()
                logger.info(
                    "codemap_decision_node_created", node_id=node_id, directory=str(p)
                )
            except (OSError, ValueError, ImportError) as e:
                # Non-blocking: log error but don't fail codemap generation
                logger.warning(
                    "context_graph_node_failed", operation="codemap", error=str(e)
                )

    return result
