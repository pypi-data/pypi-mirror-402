"""SEF Agents Server.

SEF Agents is the AI-powered guidance layer for the Synchronous Engineering Framework (SEF).
Built on Anthropic's Model Context Protocol (MCP) for seamless AI assistant integration.

This module defines the FastMCP server exposing SEF agents, prompts, and tools.
It manages session state for the active agent and provides tools for code compliance
and codebase mapping.
"""

import sys

import structlog
from fastmcp import FastMCP
from pathlib import Path

from sef_agents.constants import Status, AVAILABLE_AGENTS, AGENT_CAPABILITIES
from sef_agents.prompts import start_agent
from sef_agents.session import SessionManager
from sef_agents.tools import (
    ai_pattern_detector,
    code_quality_scanner,
    complexity,
    compliance,
    context_manager,
    context_tools,
    cross_repo_linker,
    dead_code_scanner,
    debt_scanner,
    dependency_graph,
    docs_scanner,
    external_detector,
    flow_gap_detector,
    flow_mapper,
    guard_tools,
    handoff_tools,
    health_scanner,
    pattern_learner,
    security_audit_tool,
    sequencing_engine,
    summary_generator,
    workflow_tools,
)
from sef_agents.utils import handoff_logger
from sef_agents.workflow.state_machine import WorkflowManager
from sef_agents.auth import create_api_key_verifier

# Setup - Route logs to stderr (stdout reserved for MCP JSON-RPC)
structlog.configure(
    processors=[structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(30),  # WARNING+
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)
logger = structlog.get_logger(__name__)

# Module-level active agent tracking (also accessible via SessionManager)
ACTIVE_AGENT: str | None = None


auth_verifier = create_api_key_verifier()
# auth_verifier is always returned (passthrough when no keys, real auth when keys configured)
mcp = FastMCP("SEF-Agents", auth=auth_verifier)


# --- Prompts (Agents) ---
@mcp.prompt("activate_sef")
def activate_sef_prompt() -> str:
    """General entry point. Use this to start the SEF session."""
    return context_tools._format_available_agents_numbered()


@mcp.prompt("product_manager")
def product_manager_prompt() -> str:
    return start_agent.get_product_manager_prompt()


@mcp.prompt("architect")
def architect_prompt() -> str:
    return start_agent.get_architect_prompt()


@mcp.prompt("developer")
def developer_prompt() -> str:
    return start_agent.get_developer_prompt()


@mcp.prompt("tester")
def tester_prompt() -> str:
    return start_agent.get_tester_prompt()


@mcp.prompt("scrum_master")
def scrum_master_prompt() -> str:
    return start_agent.get_scrum_master_prompt()


@mcp.prompt("security_owner")
def security_owner_prompt() -> str:
    return start_agent.get_security_owner_prompt()


@mcp.prompt("pr_reviewer")
def pr_reviewer_prompt() -> str:
    return start_agent.get_pr_reviewer_prompt()


@mcp.prompt("discovery")
def discovery_prompt() -> str:
    return start_agent.get_discovery_prompt()


@mcp.prompt("qa_lead")
def qa_lead_prompt() -> str:
    return start_agent.get_qa_lead_prompt()


@mcp.prompt("test_designer")
def test_designer_prompt() -> str:
    return start_agent.get_test_designer_prompt()


@mcp.prompt("forensic_engineer")
def forensic_engineer_prompt() -> str:
    return start_agent.get_forensic_engineer_prompt()


@mcp.prompt("strategist")
def strategist_prompt() -> str:
    return start_agent.get_strategist_prompt()


@mcp.prompt("platform_engineer")
def platform_engineer_prompt() -> str:
    return start_agent.get_platform_engineer_prompt()


# --- Context Tools ---
@mcp.tool()
def identify_agent(context_history: str = "") -> str:
    """Checks if an agent is active."""
    return context_tools.identify_agent_impl(context_history)


@mcp.tool()
def set_active_agent(agent_name: str) -> str:
    """Sets the active SEF agent for the session."""
    # Logic: Validate agent -> Check Prerequisites -> Set Session -> Return Prompt

    # 1. Validation & Mapping
    target_agent = agent_name
    if agent_name.isdigit():
        agent_num = int(agent_name)
        agents_list = list(AVAILABLE_AGENTS.keys())
        if 1 <= agent_num <= len(agents_list):
            target_agent = agents_list[agent_num - 1]
        else:
            return f"{Status.ERROR} Invalid number `{agent_name}`. Select 1-{len(agents_list)}."

    if target_agent not in AVAILABLE_AGENTS:
        valid_agents = ", ".join(AVAILABLE_AGENTS.keys())
        return f"{Status.ERROR} Invalid agent `{target_agent}`. Valid agents: {valid_agents}"

    # 2. Prerequisite Check (Delegated to Guard Tools)
    # Some agents strictly require CODE_MAP
    if target_agent in ["product_manager", "architect", "developer", "pr_reviewer"]:
        if not guard_tools._check_codemap_exists():
            handoff_logger.log_escalation(
                level="L1",
                from_agent=target_agent,
                to_agents=["discovery"],
                reason="CODE_MAP.md missing - brownfield prerequisite not met",
            )
            return (
                f"🔄 Cannot activate `{target_agent}`. CODE_MAP.md not found.\n\n"
                "**This agent requires codebase context.**\n\n"
                "**Option 1 - Set project path** (if CODE_MAP.md exists):\n"
                "```\n"
                "set_project_root('/path/to/your/project')\n"
                "```\n\n"
                "**Option 2 - Generate CODE_MAP** (recommended):\n"
                "```\n"
                "set_active_agent('discovery')\n"
                "generate_codemap('/path/to/your/project')\n"
                "```\n\n"
                f"Then retry: `set_active_agent('{target_agent}')`\n\n"
                "**Ask the user** for their project path before proceeding."
            )

    # 3. State Update
    global ACTIVE_AGENT
    ACTIVE_AGENT = target_agent
    SessionManager.get().active_agent = target_agent

    handoff_logger.log_agent_activation(target_agent)
    logger.info("agent_activated", agent=target_agent)

    # Return minimal confirmation (full prompt available via @mcp.prompt)
    agent_info = AVAILABLE_AGENTS.get(target_agent, target_agent)
    duty = AGENT_CAPABILITIES.get(target_agent, {}).get("duty", "")
    return f"{Status.SUCCESS} Agent: **{agent_info}**\n\n**Duty:** {duty}\n\nReady. Awaiting task."


@mcp.tool()
def set_project_root(path: str) -> str:
    """Explicitly set the project root directory."""
    return context_tools.set_project_root_impl(path)


@mcp.tool()
def get_available_agents() -> str:
    """Lists available agents."""
    return context_tools._format_available_agents_numbered()


# --- Analysis Tools ---
@mcp.tool()
def generate_codemap(directory: str) -> str:
    """Scans directory and generates CODE_MAP.md."""
    return context_tools.generate_codemap_wrapper(directory)


@mcp.tool()
def validate_compliance(file_path: str) -> str:
    """Validates SEF quality standards."""
    return compliance.validate_compliance_tool(file_path)


@mcp.tool()
def detect_ai_patterns(file_path: str) -> str:
    """Detects AI anti-patterns."""
    return ai_pattern_detector.detect_ai_patterns_tool(file_path)


@mcp.tool()
def scan_complexity(files: str) -> str:
    """Scans for high cyclomatic complexity and LOC."""
    return complexity.scan_complexity_tool(files)


@mcp.tool()
def scan_external_dependencies(directory: str) -> str:
    """Scans for API clients and env vars."""
    return external_detector.scan_and_report(directory)


@mcp.tool()
def scan_debt(directory: str, summary: bool = False) -> str:
    """Scans for technical debt. Set summary=True for quick overview."""
    return debt_scanner.scan_debt_tool(directory, summary)


@mcp.tool()
def scan_dead_code(directory: str, summary: bool = False) -> str:
    """Scans for dead code. Set summary=True for quick overview."""
    return dead_code_scanner.scan_dead_code(directory, summary)


@mcp.tool()
def validate_docs(directory: str) -> str:
    """Validates documentation quality."""
    return docs_scanner.validate_docs_tool(directory)


@mcp.tool()
def scan_code_quality(directory: str) -> str:
    """Scans for code quality issues (pe_rules)."""
    return code_quality_scanner.scan_code_quality(directory)


@mcp.tool()
def run_security_audit(directory: str = "") -> str:
    """Runs security audit. Outputs sef-reports/security/security_audit_{date}.md."""
    return security_audit_tool.run_security_audit(directory)


@mcp.tool()
def scan_health(directory: str) -> str:
    """Orchestrates all scanners for codebase health report."""
    return health_scanner.scan_health(directory)


# --- Workflow Tools ---
@mcp.tool()
def init_workflow(story_id: str, epic_id: str = "") -> str:
    """Initializes workflow state machine for a story. Auto-detects story type."""
    return workflow_tools.init_workflow(story_id, epic_id)


@mcp.tool()
def get_workflow_state(story_id: str = "") -> str:
    """Returns current phase, artifacts, blockers, and parallel task status."""
    return workflow_tools.get_workflow_state(story_id)


@mcp.tool()
def suggest_next_agent(story_id: str = "", completed_task: str = "") -> str:
    """Recommends next agent based on phase completion and artifact status."""
    return workflow_tools.suggest_next_agent(story_id, completed_task)


@mcp.tool()
def start_parallel_validation(story_id: str = "") -> str:
    """Initiates parallel tester + security_owner validation in Phase 6."""
    return workflow_tools.start_parallel_validation(story_id)


@mcp.tool()
def complete_parallel_task(
    story_id: str = "", agent: str = "", status: str = "passed", notification: str = ""
) -> str:
    """Marks parallel task complete. status: passed | failed."""
    return workflow_tools.complete_parallel_task(story_id, agent, status, notification)


@mcp.tool()
def check_testing_capabilities(story_id: str = "") -> str:
    """Detects available testing tools (Playwright MCP, pytest) for story type."""
    return workflow_tools.check_testing_capabilities(story_id)


@mcp.tool()
def defer_e2e_testing(story_id: str = "", reason: str = "") -> str:
    """Defers E2E testing and logs to TECH_DEBT.md. Requires user confirmation."""
    return workflow_tools.defer_e2e_testing(story_id, reason)


@mcp.tool()
def set_story_context(story_id: str, epic_id: str = "") -> str:
    """Sets active story context for agent prompts and workflow tracking."""
    start_agent.set_story_context(story_id, epic_id)
    return f"{Status.SUCCESS} Context set: story={story_id}"


@mcp.tool()
def manage_context(
    action: str,
    layer: str = "",
    entry_type: str = "",
    content: str = "",
    identifier: str = "",
    story_id: str = "",
    epic_id: str = "",
) -> str:
    """Manages context. action: add | get | clear."""
    return context_manager.manage_context(
        action, layer, entry_type, content, identifier, story_id, epic_id
    )


# --- Handoff & Logging Tools ---
@mcp.tool()
def log_escalation(level: str, reason: str, to_agents: str, story_id: str = "") -> str:
    """Logs escalation event. level: L1|L2|L3."""
    return handoff_tools.log_event(
        "escalation", story_id=story_id, level=level, reason=reason, to_agents=to_agents
    )


@mcp.tool()
def log_ownership_transfer(story_id: str, to_owner: str, reason: str) -> str:
    """Logs ownership transfer between agents."""
    return handoff_tools.log_event(
        "ownership", story_id=story_id, to_owner=to_owner, reason=reason
    )


@mcp.tool()
def log_replan(story_id: str, trigger: str, impact: str) -> str:
    """Logs replan triggered event."""
    return handoff_tools.log_event(
        "replan", story_id=story_id, trigger=trigger, impact=impact
    )


@mcp.tool()
def log_debt(debt_type: str, severity: str, location: str, story_id: str = "") -> str:
    """Logs technical debt finding."""
    return handoff_tools.log_event(
        "debt",
        story_id=story_id,
        debt_type=debt_type,
        severity=severity,
        location=location,
    )


@mcp.tool()
def log_phase(story_id: str, phase: str, outcome: str, next_phase: str = "") -> str:
    """Logs phase completion."""
    # Auto-capture decision for context graph
    if outcome == "passed":
        workflow_tools._auto_capture_decision(
            story_id=story_id,
            phase=phase,
            summary=f"Completed {phase} -> Next: {next_phase}",
        )

    return handoff_tools.log_event(
        "phase", story_id=story_id, phase=phase, outcome=outcome, next_phase=next_phase
    )


@mcp.tool()
def mark_artifact_complete(story_id: str = "", artifact: str = "") -> str:
    """Marks workflow artifact as complete (e.g., 'design', 'ac_validated')."""
    return workflow_tools.mark_artifact_complete(story_id, artifact)


@mcp.tool()
def add_blocker(story_id: str, level: str, description: str, source_agent: str) -> str:
    """Adds blocker to story. level: L1 | L2 | L3. Triggers escalation log."""
    manager = WorkflowManager()
    try:
        state = manager.add_blocker(story_id, level, description, source_agent)
        handoff_logger.log_escalation(level, source_agent, [], description, story_id)
        return (
            f"🛑 Blocker added to {story_id}\n"
            f"Level: {level}\n"
            f"Description: {description}\n"
            f"Source: {source_agent}\n"
            f"Total blockers: {len(state.blockers)}"
        )
    except ValueError as e:
        return f"{Status.ERROR} Error: {e}"


@mcp.tool()
def resolve_blocker(story_id: str, index: int = -1) -> str:
    """Resolves blocker by index (-1 for most recent). Updates workflow state."""
    return workflow_tools.resolve_blocker_tool(story_id, index)


@mcp.tool()
def notify_background_agent(story_id: str, notification: str) -> str:
    """Queues notification for primary agent from background agent."""
    return workflow_tools.add_background_notification(story_id, notification)


@mcp.tool()
def request_debt_fix_approval(
    debt_id: str, description: str, story_id: str = ""
) -> str:
    """Requests approval to fix tech debt. Logs L3 escalation. Halts for decision."""
    return workflow_tools.request_debt_fix_approval_tool(debt_id, description, story_id)


@mcp.tool()
def check_agent_prerequisites(agent_name: str) -> str:
    """Validates required artifacts exist before agent activation."""
    return guard_tools.check_agent_prerequisites_impl(agent_name)


# --- Sequencing ---
@mcp.tool()
def generate_story_dependency_graph(directory: str) -> str:
    """Parses requirements directory and generates story dependency graph."""
    return dependency_graph.generate_dependency_graph(directory)


@mcp.tool()
def get_ready_stories(directory: str) -> str:
    """Returns stories with all dependencies satisfied, ready for work."""
    return sequencing_engine.get_next_ready_stories(directory)


@mcp.tool()
def get_critical_path(directory: str) -> str:
    """Identifies longest dependency chain (critical path) in story graph."""
    return sequencing_engine.get_critical_path_report(directory)


@mcp.tool()
def get_sequencing_analysis(directory: str) -> str:
    """Full sequencing analysis: ready, blocked, critical path, completed."""
    result = sequencing_engine.analyze_directory(directory)
    if result.errors:
        return f"Errors: {result.errors}"
    return result.to_json()


# --- Context Graph Tools ---
@mcp.tool()
def add_graph_node(
    node_type: str,
    content: str,
    story_id: str = "",
    links_to: str = "",
    link_type: str = "led_to",
) -> str:
    """Add node to context graph with optional edges.

    Args:
        node_type: Type of node (decision, pattern, file, issue, agent_session, story).
        content: Node content/description.
        story_id: Optional story identifier.
        links_to: Comma-separated node IDs to link to.
        link_type: Edge type (led_to, affects, discovered_by, applies_to, supersedes, depends_on).

    Returns:
        Confirmation with node ID.
    """
    from datetime import datetime, timezone

    from sef_agents.tools.context_graph import (
        ContextNode,
        VALID_NODE_TYPES,
        VALID_EDGE_TYPES,
        get_context_graph,
    )

    if node_type not in VALID_NODE_TYPES:
        return (
            f"{Status.ERROR} Invalid node_type: {node_type}. Valid: {VALID_NODE_TYPES}"
        )

    if links_to and link_type not in VALID_EDGE_TYPES:
        return (
            f"{Status.ERROR} Invalid link_type: {link_type}. Valid: {VALID_EDGE_TYPES}"
        )

    # Generate unique ID
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    node_id = f"{node_type}-{ts}"

    graph = get_context_graph()
    node = ContextNode(
        id=node_id,
        node_type=node_type,  # type: ignore
        content=content,
        story_id=story_id,
    )
    graph.add_node(node)

    # Add edges if specified
    edges_added = 0
    if links_to:
        for target_id in links_to.split(","):
            target_id = target_id.strip()
            if target_id and target_id in graph._graph:
                try:
                    graph.add_edge(node_id, target_id, link_type)  # type: ignore
                    edges_added += 1
                except ValueError:
                    pass  # Skip invalid edges

    graph.save()

    result = f"{Status.SUCCESS} Node added: {node_id}"
    if edges_added:
        result += f" (+{edges_added} edges)"
    return result


@mcp.tool()
def get_related_context(node_id: str, edge_types: str = "led_to,affects") -> str:
    """Get nodes related to a given node by edge type.

    Args:
        node_id: Source node identifier.
        edge_types: Comma-separated edge types to filter by.

    Returns:
        List of related nodes with their details.
    """
    from sef_agents.tools.context_graph import get_context_graph

    graph = get_context_graph()
    node = graph.get_node(node_id)
    if not node:
        return f"{Status.ERROR} Node not found: {node_id}"

    types_list = [t.strip() for t in edge_types.split(",") if t.strip()]
    related = graph.get_related(node_id, edge_types=types_list if types_list else None)

    if not related:
        return f"No related nodes found for {node_id} with edge types: {edge_types}"

    lines = [f"## Related to {node_id}", ""]
    for n in related:
        lines.append(f"- **{n.id}** ({n.node_type}): {n.content[:80]}")
        if n.story_id:
            lines.append(f"  - Story: {n.story_id}")

    return "\n".join(lines)


@mcp.tool()
def get_causality_chain(story_id: str) -> str:
    """Get decision chain for a story (provenance).

    Args:
        story_id: Story identifier.

    Returns:
        Causality chain showing decision provenance.
    """
    from sef_agents.tools.context_graph import get_context_graph

    graph = get_context_graph()

    # Find story node or latest decision for story
    story_nodes = graph.get_nodes_by_story(story_id)
    if not story_nodes:
        return f"No context graph nodes found for story: {story_id}"

    # Get decisions for this story
    decisions = [n for n in story_nodes if n.node_type == "decision"]

    if not decisions:
        lines = [f"## Context for {story_id}", ""]
        for n in story_nodes:
            lines.append(f"- **{n.id}** ({n.node_type}): {n.content[:80]}")
        return "\n".join(lines)

    # Get causality chain for most recent decision
    decisions.sort(key=lambda x: x.timestamp, reverse=True)
    chain = graph.get_causality_chain(decisions[0].id)

    lines = [f"## Decision Chain for {story_id}", ""]
    for i, n in enumerate(chain):
        prefix = "→ " if i > 0 else ""
        lines.append(f"{prefix}**{n.id}**: {n.content[:80]}")

    return "\n".join(lines)


@mcp.tool()
def get_context_graph_data(format: str = "json") -> str:
    """Get context graph data for dashboard visualization.

    Note: Graph is auto-saved to sef-reports/ during populate_context_graph
    and scan_health. This tool retrieves the in-memory graph state.

    Args:
        format: Output format (json or viz for react-flow).

    Returns:
        Graph data in requested format.
    """
    from sef_agents.tools.context_graph import get_context_graph

    graph = get_context_graph()

    if graph.node_count == 0:
        return f"{Status.ERROR} Context graph is empty. Run scan_health() first."

    if format == "viz":
        return graph.to_visualization_json()
    else:
        return graph.to_json()


@mcp.tool()
def populate_context_graph(
    directory: str = "",
    levels: str = "L1,L2",
    include_git: bool = True,
    include_llm: bool = True,
) -> str:
    """Populate context graph from existing codebase during discovery.

    Args:
        directory: Root directory to analyze. Empty for current project root.
        levels: Comma-separated criticality levels to process (L1,L2,L3).
        include_git: Mine git history for decisions.
        include_llm: Use LLM to infer design rationale.

    Returns:
        Summary of population results.
    """
    from sef_agents.tools.brownfield_populator import BrownfieldPopulator

    try:
        path = Path(directory) if directory else None
        populator = BrownfieldPopulator(path)

        level_list = [level.strip() for level in levels.split(",") if level.strip()]  # type: ignore

        stats = populator.populate(
            levels=level_list,  # type: ignore
            include_git=include_git,
            include_llm=include_llm,
        )

        return _format_population_stats(populator.root, stats, level_list)
    except Exception as e:
        logger.error("brownfield_population_failed", error=str(e))
        raise


# --- Flow ---
@mcp.tool()
def generate_flow(directory: str, output: str = "diagram") -> str:
    """Generates flow from requirements. output: diagram | summary."""
    return flow_mapper.generate_flow(directory, output)


@mcp.tool()
def detect_flow_gaps(flows_file: str, req_directory: str, summary: bool = False) -> str:
    """Detects flow gaps. Set summary=True for quick overview."""
    return flow_gap_detector.detect_flow_gaps(flows_file, req_directory, summary)


# --- External ---
@mcp.tool()
def validate_external_dependencies(registry_file: str, code_directory: str) -> str:
    """Validates code uses only registered external APIs from EXTERNAL_APIS.md."""
    return cross_repo_linker.validate_external_deps(registry_file, code_directory)


@mcp.tool()
def list_unregistered_dependencies(code_directory: str) -> str:
    """Lists external API calls not registered in EXTERNAL_APIS.md."""
    return cross_repo_linker.get_unregistered_deps(code_directory)


# --- Pattern ---
@mcp.tool()
def pattern(
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
    """Pattern management. action: capture | suggest | get | list."""
    return pattern_learner.pattern_tool(
        action,
        pattern_id,
        name,
        domain,
        tech,
        story_id,
        story_title,
        files,
        snippet,
        tags,
        description,
    )


# --- Other ---
@mcp.tool()
def generate_project_summary(directory: str = "") -> str:
    """Generates executive-summary.json with score, debt, security, compliance."""
    return summary_generator.generate_project_summary_tool(directory)


@mcp.tool()
def write_conceptual_tests(story_id: str, test_cases_json: str) -> str:
    """Writes conceptual test cases to tests/conceptual/{story_id}_tests.json."""
    return workflow_tools.write_conceptual_tests_tool(story_id, test_cases_json)


@mcp.tool()
def scan_regression_risk(files: str) -> str:
    """Scans for high-risk patterns."""
    return workflow_tools.scan_regression_risk_tool(files)


# --- Discovery Artifact Tools ---
@mcp.tool()
def generate_features(directory: str) -> str:
    """Infer FEATURES.md from codemap/ directory.

    Analyzes codemap package maps to identify user-facing features
    and generates a FEATURES.md file at project root.

    Args:
        directory: Path to project root (must have codemap/ first).

    Returns:
        Status with feature count and categories.
    """
    from sef_agents.tools.features_generator import generate_features_file

    return generate_features_file(directory)


@mcp.tool()
def generate_agents_md(directory: str) -> str:
    """Generate AGENTS.md with SEF protocol and fix workflow.

    Creates AGENTS.md at project root containing:
    - SEF-Agents MCP entry point requirement
    - Communication style protocol
    - Mandatory fix workflow (forensic_engineer -> strategist -> developer)

    Args:
        directory: Path to project root.

    Returns:
        Status message.
    """
    from sef_agents.tools.agents_generator import generate_agents_file

    return generate_agents_file(directory)


@mcp.tool()
def audit_discovery(directory: str) -> str:
    """Audit discovery artifacts for completeness.

    Post-completion verification checking:
    - Artifact existence (codemap/, FEATURES.md, AGENTS.md, etc.)
    - Placement validation (no misplaced files, no unknown/)
    - Content validation (required sections present)

    Args:
        directory: Path to project root.

    Returns:
        Audit result with pass/fail checks and remediation steps.
    """
    from sef_agents.tools.discovery_audit import audit_discovery as run_audit

    return run_audit(directory)


# --- Browser Testing Tools ---
@mcp.tool()
def execute_frontend_tests(story_id: str) -> str:
    """Execute conceptual frontend tests via Playwright MCP.

    Loads conceptual tests from tests/conceptual/{story_id}_tests.json
    and executes them using Playwright MCP browser tools.

    Args:
        story_id: Story identifier (e.g., STORY-011).

    Returns:
        Execution summary with pass/fail counts and report path.
    """
    from sef_agents.tools.browser.test_executor import (
        execute_frontend_tests as exec_tests,
    )

    return exec_tests(story_id)


@mcp.tool()
def verify_test_evidence(story_id: str) -> str:
    """Verify all test evidence for a story.

    Checks screenshots, execution logs, and timestamps
    to ensure test results are not hallucinated.

    Args:
        story_id: Story identifier.

    Returns:
        Verification result summary.
    """
    from sef_agents.tools.browser.evidence_verifier import (
        verify_test_evidence as verify,
    )

    result = verify(story_id)
    if result.valid:
        return (
            f"✅ Evidence verified for {story_id}\n"
            f"Screenshots: {result.screenshot_count}\n"
            f"Log entries: {result.log_entry_count}"
        )
    else:
        return (
            f"❌ Evidence verification FAILED for {story_id}\nIssues: {result.issues}"
        )


@mcp.tool()
def check_browser_tools() -> str:
    """Check if Playwright MCP browser tools are available.

    Returns:
        Availability status and guidance if not available.
    """
    from sef_agents.tools.browser.playwright_mcp_client import (
        check_browser_tools_available,
    )

    if check_browser_tools_available():
        return (
            "✅ Playwright MCP browser tools are available.\n"
            "Ready for frontend E2E testing."
        )
    else:
        return (
            "❌ Playwright MCP browser tools are NOT available.\n\n"
            "To enable:\n"
            "1. Ensure Playwright MCP is enabled in Cursor settings\n"
            "2. Check MCP server configuration\n"
            "3. Restart Cursor if needed\n\n"
            "Without browser tools, E2E tests must be run manually."
        )


def _format_population_stats(root: Path, stats: dict, levels: list[str]) -> str:
    """Format population statistics."""
    from sef_agents.constants import Status

    lines = [
        f"{Status.SUCCESS} Brownfield Population Complete",
        "",
        f"Root: {root}",
        f"Levels: {', '.join(levels)}",
        "",
        "Stats:",
        f"- Files Scanned: {stats.get('files_scanned', 0)}",
        f"- Deep Analysis: {stats.get('deep_analysis_files', 0)}",
        f"- Total Nodes: {stats.get('total_nodes', 0)}",
        f"- Total Edges: {stats.get('total_edges', 0)}",
    ]
    return "\n".join(lines)


def main() -> None:
    """Entry point for CLI execution via uvx/pip.

    Uses stdio transport (works with Cursor, Claude Desktop, Windsurf).
    Run via: `uvx sef-agents` (after publishing to PyPI)
    """
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
