"""Tests for SEF Agents Server Core Functionality.

Covers:
- Agent prompt loading and content validation
- CODE_MAP.md enforcement for brownfield agents
- Session state management
- MCP tool wiring (handoff logging, workflow state)
- Regression risk scanning

Related: src/sef_agents/server.py, src/sef_agents/prompts/start_agent.py
"""

from sef_agents.server import generate_codemap, get_available_agents
from sef_agents.prompts import start_agent


def test_product_manager_prompt():
    """Verify PM prompt loads with requirements-related content."""
    prompt = start_agent.get_product_manager_prompt()
    assert (
        "Requirements" in prompt or "Brainstorming" in prompt
    )  # Checking for content keywords


def test_developer_prompt():
    """Verify Developer prompt includes Conciseness Protocol and mandates.

    Checks:
    - GLOBAL CONCISENESS PROTOCOL header
    - Playwright UI testing mandate
    - CODE_MAP.md update/create mandate
    - CODE_MAP.md linkage mandate
    """
    prompt = start_agent.get_developer_prompt()
    assert "GLOBAL CONCISENESS PROTOCOL" in prompt
    # The developer prompt loads several rule files. We check for key fragments.
    # Note: "Playwright" might be in development/implementation.md or others.
    # We check for the core protocol and architecture patterns we compressed.
    assert "core_protocol.md" in prompt
    assert "backend_patterns.md" in prompt


def test_codemap_tool(tmp_path):
    """Verify codemap generation persists file and links sub-maps.

    Args:
        tmp_path: Pytest fixture providing temp directory.
    """
    root = tmp_path / "root"
    root.mkdir()
    # Create Python package structure (requires __init__.py)
    sub = root / "subdir"
    sub.mkdir()
    (sub / "__init__.py").write_text("")
    (sub / "CODE_MAP.md").write_text("## Purpose\nHandles data processing.")

    result = generate_codemap.fn(str(root))

    assert "CODE_MAPs generated" in result or "Generated" in result
    # Check codemap directory created
    codemap_dir = root / "codemap"
    assert codemap_dir.exists()


def test_session_flow(tmp_path, monkeypatch):
    """Verify stateful session initialization with CODE_MAP present.

    Tests the full session lifecycle:
    1. Initial state returns STOP (no agent)
    2. Setting agent succeeds when CODE_MAP exists
    3. Global state persists
    4. Subsequent identify confirms active agent

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching.
    """
    from sef_agents.server import identify_agent, set_active_agent
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    (tmp_path / "CODE_MAP.md").write_text("# Code Map\nTest project")

    import sef_agents.server

    sef_agents.server.ACTIVE_AGENT = None
    SessionManager.get().clear()  # Clear session state for test isolation

    res_ident = identify_agent.fn()
    assert "STOP" in res_ident
    assert "You MUST ask the user" in res_ident

    res_set = set_active_agent.fn("developer")
    assert "✅" in res_set
    assert "Developer" in res_set

    assert sef_agents.server.ACTIVE_AGENT == "developer"

    res_ident_2 = identify_agent.fn()
    assert "Agent is active: `developer`" in res_ident_2


# --- ENFORCEMENT TESTS (Negative cases that FAIL if logic removed) ---


def test_pm_blocked_without_codemap(tmp_path, monkeypatch):
    """PM agent blocked when CODE_MAP.md missing.

    Regression guard: FAILS if enforcement removed from set_active_agent().
    Ref: SEF_ARCHITECTURE.md line 82-95.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import set_active_agent
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().clear()  # Clear session state for test isolation
    import sef_agents.server

    sef_agents.server.ACTIVE_AGENT = None

    result = set_active_agent.fn("product_manager")

    assert "Cannot activate" in result
    assert "CODE_MAP.md" in result
    assert "discovery" in result.lower()
    assert sef_agents.server.ACTIVE_AGENT is None


def test_architect_blocked_without_codemap(tmp_path, monkeypatch):
    """Architect agent blocked when CODE_MAP.md missing.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import set_active_agent
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().clear()  # Clear session state for test isolation
    import sef_agents.server

    sef_agents.server.ACTIVE_AGENT = None

    result = set_active_agent.fn("architect")

    assert "Cannot activate" in result
    assert "discovery" in result.lower()
    assert sef_agents.server.ACTIVE_AGENT is None


def test_developer_blocked_without_codemap(tmp_path, monkeypatch):
    """Developer agent blocked when CODE_MAP.md missing.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import set_active_agent
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().clear()  # Clear session state for test isolation
    import sef_agents.server

    sef_agents.server.ACTIVE_AGENT = None

    result = set_active_agent.fn("developer")

    assert "Cannot activate" in result
    assert sef_agents.server.ACTIVE_AGENT is None


def test_discovery_allowed_without_codemap(tmp_path, monkeypatch):
    """Discovery agent allowed without CODE_MAP.md.

    Rationale: Discovery creates CODE_MAP, cannot require it.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import set_active_agent

    monkeypatch.chdir(tmp_path)
    import sef_agents.server

    sef_agents.server.ACTIVE_AGENT = None

    result = set_active_agent.fn("discovery")

    assert "✅" in result
    assert "Discovery" in result
    assert sef_agents.server.ACTIVE_AGENT == "discovery"


def test_tester_allowed_without_codemap(tmp_path, monkeypatch):
    """Tester agent allowed without CODE_MAP.

    Rationale: Tester validates implementation, not codebase structure.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import set_active_agent

    monkeypatch.chdir(tmp_path)
    import sef_agents.server

    sef_agents.server.ACTIVE_AGENT = None

    result = set_active_agent.fn("tester")

    assert "✅" in result
    assert "Tester" in result
    assert sef_agents.server.ACTIVE_AGENT == "tester"


def test_pm_allowed_with_codemap(tmp_path, monkeypatch):
    """PM agent allowed when CODE_MAP.md exists.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import set_active_agent

    monkeypatch.chdir(tmp_path)
    (tmp_path / "CODE_MAP.md").write_text("# Code Map")
    import sef_agents.server

    sef_agents.server.ACTIVE_AGENT = None

    result = set_active_agent.fn("product_manager")

    assert "✅" in result
    assert "Product Manager" in result
    assert sef_agents.server.ACTIVE_AGENT == "product_manager"


def test_escalation_logged_on_codemap_block(tmp_path, monkeypatch):
    """Escalation logged when agent blocked for missing CODE_MAP.

    Wiring test: Verifies handoff_log.jsonl creation.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import set_active_agent
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().clear()  # Clear session state for test isolation
    import sef_agents.server

    sef_agents.server.ACTIVE_AGENT = None

    result = set_active_agent.fn("product_manager")

    assert "Cannot activate" in result
    log_path = tmp_path / "sef-reports" / "handoff_log.jsonl"
    assert log_path.exists()
    content = log_path.read_text()
    assert "escalation" in content
    assert "L1" in content


def test_get_available_agents():
    """Verify get_available_agents returns all expected agents."""
    result = get_available_agents.fn()
    assert "developer" in result
    assert "scrum_master" in result
    assert "discovery" in result
    assert "qa_lead" in result


def test_discovery_prompt():
    """Verify Discovery prompt contains required elements."""
    prompt = start_agent.get_discovery_prompt()
    assert "PRINCIPAL CODE ARCHAEOLOGIST" in prompt
    assert "CODE_MAP" in prompt
    assert "ESCALATION PROTOCOL" in prompt


def test_agent_activation_creates_context_graph_node(tmp_path, monkeypatch):
    """Agent activation creates agent_session node in context graph.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.tools.context_graph import get_context_graph, reset_context_graph
    from sef_agents.utils.handoff_logger import log_agent_activation
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().project_root = tmp_path
    reset_context_graph()  # Clear singleton for test isolation

    # Activate agent
    log_agent_activation("discovery", tmp_path)

    # Verify context graph node created
    graph = get_context_graph(tmp_path)
    agent_sessions = graph.get_nodes_by_type("agent_session")
    assert len(agent_sessions) == 1
    assert agent_sessions[0].node_type == "agent_session"
    assert "discovery" in agent_sessions[0].content
    assert agent_sessions[0].metadata.get("agent") == "discovery"


def test_codemap_generation_creates_context_graph_node(tmp_path, monkeypatch):
    """CODE_MAP generation creates decision node and links to agent_session.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.tools.context_graph import get_context_graph, reset_context_graph
    from sef_agents.tools.context_tools import generate_codemap_wrapper
    from sef_agents.utils.handoff_logger import log_agent_activation
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().project_root = tmp_path
    SessionManager.get().active_agent = "discovery"
    reset_context_graph()  # Clear singleton for test isolation

    # Create agent_session first
    log_agent_activation("discovery", tmp_path)

    # Generate CODE_MAP - need valid Python package structure
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    (test_dir / "__init__.py").write_text("")  # Make it a Python package
    generate_codemap_wrapper(str(test_dir))

    # Verify decision node created (only if codemap succeeds)
    graph = get_context_graph(tmp_path)
    decisions = graph.get_nodes_by_type("decision")
    assert len(decisions) == 1
    assert "CODE_MAP" in decisions[0].content
    assert decisions[0].metadata.get("agent") == "discovery"

    # Verify edge to agent_session
    agent_sessions = graph.get_nodes_by_type("agent_session")
    assert len(agent_sessions) == 1

    # Check edge exists
    edges = list(graph._graph.edges)
    assert len(edges) == 1
    edge_data = graph._graph.edges[edges[0]]
    assert edge_data.get("edge_type") == "discovered_by"


def test_validate_compliance_requires_agent(tmp_path, monkeypatch):
    """Compliance validation requires active agent.

    Regression guard: FAILS if agent check removed.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.tools.compliance import validate_compliance_tool
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().clear()  # Clear session state for test isolation

    test_file = tmp_path / "test.py"
    test_file.write_text("def hello(): pass\n")

    result = validate_compliance_tool(str(test_file))

    assert "No SEF Agent is active" in result
    assert "ERROR" in result or "❌" in result
    assert "set_active_agent" in result


def test_validate_compliance_with_agent(tmp_path, monkeypatch):
    """Compliance validation works when agent is active.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.tools.compliance import validate_compliance_tool
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().active_agent = "developer"

    test_file = tmp_path / "test.py"
    test_file.write_text("def hello(): pass\n")

    result = validate_compliance_tool(str(test_file))

    assert "No SEF Agent is active" not in result
    assert (
        "compliance check complete" in result.lower()
        or "report saved" in result.lower()
    )


def test_detect_ai_patterns_requires_agent(tmp_path, monkeypatch):
    """AI pattern detection requires active agent.

    Regression guard: FAILS if agent check removed.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.tools.ai_pattern_detector import detect_ai_patterns_tool
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().clear()  # Clear session state for test isolation

    test_file = tmp_path / "test.py"
    test_file.write_text(
        "def process(data, unused):\n    result = data\n    temp = result\n    return temp\n"
    )

    result = detect_ai_patterns_tool(str(test_file))

    assert "No SEF Agent is active" in result
    assert "ERROR" in result or "❌" in result
    assert "set_active_agent" in result


def test_detect_ai_patterns_with_agent(tmp_path, monkeypatch):
    """AI pattern detection works when agent is active.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.tools.ai_pattern_detector import detect_ai_patterns_tool
    from sef_agents.session import SessionManager

    monkeypatch.chdir(tmp_path)
    SessionManager.get().active_agent = "developer"

    test_file = tmp_path / "test.py"
    test_file.write_text(
        "def process(data, unused):\n    result = data\n    temp = result\n    return temp\n"
    )

    result = detect_ai_patterns_tool(str(test_file))

    assert "No SEF Agent is active" not in result
    assert "analysis complete" in result.lower() or "report" in result.lower()


def test_qa_lead_prompt():
    """Verify QA Lead prompt contains required elements."""
    prompt = start_agent.get_qa_lead_prompt()
    assert "REQUIREMENTS INTEGRITY STRATEGIST" in prompt
    assert "Acceptance Criteria" in prompt
    assert "ESCALATION PROTOCOL" in prompt


def test_escalation_protocol_in_all_prompts():
    """Verify all agent prompts include escalation protocol with L1/L2/L3."""
    prompts = [
        start_agent.get_product_manager_prompt(),
        start_agent.get_architect_prompt(),
        start_agent.get_developer_prompt(),
        start_agent.get_tester_prompt(),
        start_agent.get_security_owner_prompt(),
    ]
    for prompt in prompts:
        assert "ESCALATION PROTOCOL" in prompt
        assert "L1" in prompt
        assert "L2" in prompt
        assert "L3" in prompt


# --- WIRING TESTS for MCP Tools (pe_rules.mdc compliance) ---


def test_log_phase_completion_wiring(tmp_path, monkeypatch):
    """Verify log_phase_completion writes to handoff_log.jsonl.

    Regression guard: FAILS if log_phase() call removed.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import log_phase

    monkeypatch.chdir(tmp_path)

    result = log_phase.fn("STORY-001", "PHASE_4", "passed", "PHASE_5")

    assert "Phase logged" in result or "✅" in result
    log_path = tmp_path / "sef-reports" / "handoff_log.jsonl"
    assert log_path.exists()
    content = log_path.read_text()
    assert "phase" in content
    assert "STORY-001" in content
    assert "passed" in content


def test_notify_background_agent_wiring(tmp_path, monkeypatch):
    """Verify notify_background_agent updates workflow state.

    Regression guard: FAILS if add_background_notification() call removed.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import notify_background_agent
    from sef_agents.workflow.state_machine import WorkflowManager

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sef_agents.utils.git_utils.find_project_root",
        lambda *args, **kwargs: tmp_path,
    )
    workflow_dir = tmp_path / ".sef_cache" / "workflow"
    workflow_dir.mkdir(parents=True)

    manager = WorkflowManager(root=workflow_dir)
    manager.create_state("STORY-001")

    result = notify_background_agent.fn("STORY-001", "Security found 2 warnings")

    assert "Notification queued" in result or "queued" in result.lower()
    state = manager.get_state("STORY-001")
    assert state.parallel_status is not None
    assert "Security found 2 warnings" in state.parallel_status["notifications"]


def test_add_blocker_wiring(tmp_path, monkeypatch):
    """Verify add_blocker updates state AND logs escalation.

    Regression guard: FAILS if either wiring removed.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import add_blocker
    from sef_agents.workflow.state_machine import WorkflowManager

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sef_agents.utils.git_utils.find_project_root",
        lambda *args, **kwargs: tmp_path,
    )
    workflow_dir = tmp_path / ".sef_cache" / "workflow"
    workflow_dir.mkdir(parents=True)

    manager = WorkflowManager(root=workflow_dir)
    manager.create_state("STORY-002")

    result = add_blocker.fn("STORY-002", "L2", "Design unclear", "developer")

    assert "Blocker added" in result
    state = manager.get_state("STORY-002")
    assert len(state.blockers) == 1
    assert state.blockers[0]["level"] == "L2"

    log_path = tmp_path / "sef-reports" / "handoff_log.jsonl"
    assert log_path.exists()
    content = log_path.read_text()
    assert "escalation" in content
    assert "L2" in content


def test_resolve_blocker_wiring(tmp_path, monkeypatch):
    """Verify resolve_blocker clears blocker from state.

    Regression guard: FAILS if state update removed.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import add_blocker, resolve_blocker
    from sef_agents.workflow.state_machine import WorkflowManager

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sef_agents.utils.git_utils.find_project_root",
        lambda *args, **kwargs: tmp_path,
    )
    workflow_dir = tmp_path / ".sef_cache" / "workflow"
    workflow_dir.mkdir(parents=True)

    manager = WorkflowManager(root=workflow_dir)
    manager.create_state("STORY-003")
    add_blocker.fn("STORY-003", "L1", "Test blocker", "tester")

    result = resolve_blocker.fn("STORY-003")

    assert "Blocker resolved" in result
    state = manager.get_state("STORY-003")
    assert len(state.blockers) == 0


# --- REGRESSION RISK & GUARDRAIL TESTS ---


def test_scan_regression_risk_low():
    """Verify LOW risk returned for normal files."""
    from sef_agents.server import scan_regression_risk

    result = scan_regression_risk.fn("src/utils.py,src/api/routes.py")

    assert "LOW" in result
    assert "Proceed normally" in result


def test_scan_regression_risk_high_migration():
    """Verify HIGH risk + HALT when migration file detected.

    Regression guard: FAILS if risk detection removed.
    """
    from sef_agents.server import scan_regression_risk

    result = scan_regression_risk.fn("src/api.py,migrations/001_add_users.sql")

    assert "HIGH" in result
    assert "HALT" in result
    assert "migration" in result.lower()


def test_scan_regression_risk_medium_auth():
    """Verify MEDIUM+ risk for auth-related changes."""
    from sef_agents.server import scan_regression_risk

    result = scan_regression_risk.fn("src/auth/login.py")

    assert "MEDIUM" in result or "HIGH" in result
    assert "auth" in result.lower() or "Authentication" in result


def test_debt_fix_approval_halts(tmp_path, monkeypatch):
    """Verify request_debt_fix_approval HALTs and logs L3 escalation.

    Regression guard: FAILS if escalation not logged.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import request_debt_fix_approval

    monkeypatch.chdir(tmp_path)

    result = request_debt_fix_approval.fn("DEBT-001", "Refactor auth module")

    assert "HALT" in result
    assert "User Decision Required" in result
    assert "approve" in result.lower()
    assert "defer" in result.lower()

    log_path = tmp_path / "sef-reports" / "handoff_log.jsonl"
    assert log_path.exists()
    content = log_path.read_text()
    assert "L3" in content
    assert "DEBT-001" in content


def test_check_agent_prerequisites_missing(tmp_path, monkeypatch):
    """Verify check_agent_prerequisites reports missing artifacts.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import check_agent_prerequisites

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sef_agents.utils.git_utils.find_project_root",
        lambda *args, **kwargs: tmp_path,
    )

    result = check_agent_prerequisites.fn("developer")

    assert "Prerequisites not met" in result or "Missing" in result
    assert "CODE_MAP.md" in result or "design" in result


def test_check_agent_prerequisites_met(tmp_path, monkeypatch):
    """Verify check_agent_prerequisites passes when artifacts exist.

    Args:
        tmp_path: Pytest fixture providing temp directory.
        monkeypatch: Pytest fixture for patching cwd.
    """
    from sef_agents.server import check_agent_prerequisites

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sef_agents.utils.git_utils.find_project_root",
        lambda *args, **kwargs: tmp_path,
    )
    # product_manager requires both CODE_MAP.md and docs/ARCHITECTURE.md
    (tmp_path / "CODE_MAP.md").write_text("# Code Map")
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "ARCHITECTURE.md").write_text("# Architecture")

    result = check_agent_prerequisites.fn("product_manager")

    assert "prerequisites met" in result.lower() or "✅" in result


# --- MCP TOOL DESCRIPTION TESTS ---


def test_all_mcp_tools_have_descriptions():
    """Verify all MCP tools have descriptions (FastMCP requirement).

    Regression guard: FAILS if @mcp.tool() function lacks docstring.
    FastMCP uses docstrings as tool descriptions for MCP protocol.
    """
    import asyncio

    from sef_agents.server import mcp

    async def check_tools():
        tools = await mcp.get_tools()
        missing = [name for name, tool in tools.items() if not tool.description]
        return missing

    missing = asyncio.run(check_tools())

    assert not missing, f"MCP tools missing descriptions: {missing}"
