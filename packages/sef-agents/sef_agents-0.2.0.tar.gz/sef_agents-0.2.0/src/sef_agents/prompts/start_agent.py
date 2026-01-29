"""SEF Agent Prompt Generators.

This module contains prompt generator functions for each SEF agent.
Each agent loads specific rule files and wraps them with the escalation protocol.
Context from previous sessions is automatically injected when available.
"""

from pathlib import Path

import structlog

from sef_agents.tools.context_manager import ContextManager

logger = structlog.get_logger(__name__)

# Prompt Strategy: LEGACY | STRUCTURAL
PROMPT_STRATEGY = "STRUCTURAL"

# Active story/epic IDs (set via set_story_context tool or environment)
_ACTIVE_STORY_ID: str | None = None
_ACTIVE_EPIC_ID: str | None = None

# Base path for rules
RULES_ROOT = Path(__file__).parent.parent / "rules"

# Global Protocol: Be laconic. Sentence ≤15 words. Active voice. Technical vocabulary.
# Max 3 sentences per paragraph. prefer tables/bullets. No fluff (e.g., "Note that").
GLOBAL_STYLE_GUIDE = """--- GLOBAL CONCISENESS PROTOCOL ---
BE LACONIC. Sentence ≤15 words. Active voice. Technical/precise vocab. Max 3 sentences/para. Prefer tables/bullets/code.
FORBIDDEN: 'It is important to note', 'In order to', 'As discussed', redundant/repeated info. Say it in 5 words, not 20.

--- DOCSTRING GENERATION (AI-GENERATED CODE) ---
When generating docstrings (98% of codebase is AI-generated):
FORBIDDEN FLUFF: "This function is designed to", "It is important to note", "Please note that", "In order to",
"It should be noted that", "As you can see", excessive adjectives (extremely/very/highly), hedging (might/could/possibly).
REQUIRED: Direct imperative statements. One-line summary ≤80 chars. Args/Returns/Raises: One sentence each.
Example: "Process user data." NOT "This function is designed to process user data in an extremely efficient manner."
-----------------------------"""

# Mandatory logging for all state/ownership/scope/phase changes.
LOGGING_PROTOCOL = "--- LOGGING PROTOCOL ---\nLog all state changes: 1) `log_escalation`, 2) `log_ownership_transfer`, 3) `log_debt_found`, 4) `log_replan_triggered`, 5) `log_phase_complete`. If agent/ownership/scope changes, you MUST log it.\n------------------------\n"

# L1 (Auto-Delegate) -> L2 (Collaborate) -> L3 (HALT). Standard status indicators required.
ESCALATION_PROTOCOL = "--- ESCALATION PROTOCOL ---\nL1: Delegate (Discovery/Architect/PM). L2: Collaborate (combine agents). L3: HALT (User decision). Use indicators: ✅Success, ⚠️Warning, ❌Error, 🛑HALT, 🔄Delegating, ↗️Escalating, ⚡Parallel.\n---------------------------\n"


def load_rules(rule_paths: list[str], exclude: list[str] | None = None) -> str:
    """Load and concatenate rule files.

    Args:
        rule_paths: List of partial paths relative to src/sef_agents/rules/
        exclude: Substrings to exclude from loading (e.g., ["frontend"])

    Returns:
        Combined content of all rule files with headers.
    """
    if PROMPT_STRATEGY == "LEGACY":
        combined_content = GLOBAL_STYLE_GUIDE + LOGGING_PROTOCOL + ESCALATION_PROTOCOL
    else:
        # Protocols are handled outside rules in STRUCTURAL mode for prioritization
        combined_content = ""

    for rel_path in rule_paths:
        if exclude and any(e in rel_path for e in exclude):
            continue

        full_path = RULES_ROOT / rel_path
        if full_path.exists():
            try:
                content = full_path.read_text()
                combined_content += f"\n\n--- RULE: {rel_path} ---\n{content}"
            except OSError as e:
                logger.error(
                    "Failed to read rule file", file=str(full_path), error=str(e)
                )
                combined_content += f"\n\n--- ERROR: Could not load {rel_path} ---\n"
        else:
            logger.warning("Rule file missing", file=str(full_path))
            combined_content += f"\n\n--- WARNING: Rule {rel_path} not found ---\n"

    return combined_content


def _detect_tech_stack() -> list[str]:
    """Detect tech stack from project root to filter rules."""
    exclude = []
    # Check for markers in current directory or project root
    cwd = Path.cwd()

    # If no Python markers, exclude backend patterns
    python_markers = ["requirements.txt", "pyproject.toml", "setup.py", "uv.lock"]
    if not any((cwd / m).exists() for m in python_markers):
        exclude.append("backend")

    # If no JS markers, exclude frontend patterns
    js_markers = ["package.json", "tsconfig.json", "node_modules", "vite.config.ts"]
    if not any((cwd / m).exists() for m in js_markers):
        exclude.append("frontend")

    return exclude


def set_story_context(story_id: str | None, epic_id: str | None = None) -> None:
    """Set active story and epic IDs for context injection.

    Args:
        story_id: Current story ID (e.g., "STORY-042").
        epic_id: Current epic ID (e.g., "EPIC-10").
    """
    global _ACTIVE_STORY_ID, _ACTIVE_EPIC_ID
    _ACTIVE_STORY_ID = story_id
    _ACTIVE_EPIC_ID = epic_id
    logger.info("story_context_set", story_id=story_id, epic_id=epic_id)


def get_session_context() -> str:
    """Load and format context from previous sessions.

    Returns:
        Formatted context string, or empty string if no context.
    """
    try:
        manager = ContextManager()
        return manager.format_for_prompt(
            story_id=_ACTIVE_STORY_ID,
            epic_id=_ACTIVE_EPIC_ID,
        )
    except (OSError, ValueError) as e:
        logger.warning("context_load_failed", error=str(e))
        return ""


def wrap_prompt(
    agent_identity: str, mission: str, rules_content: str, agent_id: str | None = None
) -> str:
    """Wrap agent content with standard prompt structure."""
    if PROMPT_STRATEGY == "STRUCTURAL":
        return wrap_prompt_structural(agent_identity, mission, rules_content, agent_id)
    return wrap_prompt_legacy(agent_identity, mission, rules_content, agent_id)


def wrap_prompt_legacy(
    agent_identity: str, mission: str, rules_content: str, agent_id: str | None = None
) -> str:
    """Legacy monolithic prompt structure."""
    # Load context from previous sessions
    context_section = get_session_context()

    # Use agent_id in reports, identity in personality
    agent_line = f"**Agent ID**: `{agent_id}`" if agent_id else ""

    return f"""
# IDENTITY: {agent_identity}
You are the **{agent_identity}** within the Synchronous Engineering Framework (SEF).
{agent_line}
{mission}
{context_section}
# SYSTEM PROTOCOL (NON-NEGOTIABLE)
The following rules are NOT guidelines. They are **SYSTEM CONSTRAINTS**.
You must adhere to every "MUST", "REQUIRED", and "FORBIDDEN" instruction below.
Any deviation will result in a compliance failure outcome.

**REPORT OUTPUT**: When generating reports, use agent ID `{agent_id or agent_identity.lower().replace(" ", "_")}` (not identity name).

# ACTIVE RULES
{rules_content}

# INSTRUCTION
Acknowledge your agent in ONE sentence. Then await the user's task.
Example: "{agent_id or "Agent"} active. Ready."
"""


def wrap_prompt_structural(
    agent_identity: str, mission: str, rules_content: str, agent_id: str | None = None
) -> str:
    """Structural signaling with prioritized anchors for coding models."""
    context_section = get_session_context()
    agent_id_val = agent_id or agent_identity.lower().replace(" ", "_")

    # Filter out rules based on tech stack detection (Domain Sharpening)
    exclude = _detect_tech_stack()
    if exclude:
        # Simple line-level filtering for language specific sections
        lines = rules_content.splitlines()
        filtered_lines = []
        skip = False
        for line in lines:
            if any("--- RULE: " in line and e in line for e in exclude):
                skip = True
            elif "--- RULE: " in line:
                skip = False
            if not skip:
                filtered_lines.append(line)
        rules_content = "\n".join(filtered_lines)

    return f"""<IDENTITY>
# {agent_identity}
**Agent ID**: `{agent_id_val}`
{mission}
</IDENTITY>

<CONTEXT>
{context_section}
</CONTEXT>

<ACTIVE_RULES>
{rules_content}
</ACTIVE_RULES>

<CRITICAL_CONSTRAINTS>
## NON-NEGOTIABLE CORE PROTOCOL
{GLOBAL_STYLE_GUIDE}
{LOGGING_PROTOCOL}
{ESCALATION_PROTOCOL}

**MANDATORY**: Follow every "MUST", "REQUIRED", and "FORBIDDEN".
**OUTPUT**: Use Agent ID `{agent_id_val}` in all reports.
</CRITICAL_CONSTRAINTS>

# INSTRUCTION
Acknowledge in ONE sentence: "{agent_id_val} active. Ready."
"""


# --- Discovery Agent (Phase 1) ---
def get_discovery_prompt() -> str:
    """Generate prompt for Discovery agent (brownfield codebase scanning)."""
    rules = load_rules(
        [
            "operations/discovery.md",
            "common/codemap_standard.md",
            "quality/documentation_standards.md",
        ]
    )
    return wrap_prompt(
        agent_identity="PRINCIPAL CODE ARCHAEOLOGIST",
        mission="Your goal is to excavate codebase history, catalog technical fossils, and preserve tribal knowledge. You generate CODE_MAP.md, log TECH_DEBT.md with historical context, and identify hidden dependencies. Every comment is evidence. Every pattern tells a story.",
        rules_content=rules,
        agent_id="discovery",
    )


# --- QA Lead Agent ---
def get_qa_lead_prompt() -> str:
    """Generate prompt for QA Lead agent (AC validation before development)."""
    rules = load_rules(
        [
            "quality/qa_lead.md",
            "quality/documentation_standards.md",
            "product/ac_validation.md",
        ]
    )
    return wrap_prompt(
        agent_identity="REQUIREMENTS INTEGRITY STRATEGIST",
        mission="Your goal is to treat ambiguous requirements as defects. You validate Acceptance Criteria with integrity scoring, detect ambiguity, and ensure every AC is machine-verifiable. Ambiguity = bug. No exceptions.",
        rules_content=rules,
        agent_id="qa_lead",
    )


def get_test_designer_prompt() -> str:
    """Generate prompt for Test Designer agent (conceptual test cases - Phase 3)."""
    rules = load_rules(
        [
            "product/ac_validation.md",
            "quality/documentation_standards.md",
            "quality/test_design.md",
        ]
    )
    return wrap_prompt(
        agent_identity="TEST DESIGNER (QE Strategist / BDD Architect)",
        mission="Your goal is to stress-test requirements logic. You produce conceptual test cases in strict JSON. If a requirement is ambiguous, it is a bug.",
        rules_content=rules,
        agent_id="test_designer",
    )


def get_product_manager_prompt() -> str:
    """Generate prompt for Product Manager agent."""
    rules = load_rules(
        [
            "product/sef_flow.md",
            "common/codemap_standard.md",
            "product/brainstorming.md",
            "quality/documentation_standards.md",
            "product/requirements_std.md",
        ]
    )
    return wrap_prompt(
        agent_identity="TECHNICAL PRODUCT VISIONARY",
        mission="Your goal is to write machine-verifiable contracts between humans and code. You define exhaustive edge cases, produce Gherkin-style ACs, and ensure every requirement traces to business value. Check CODE_MAP.md FIRST. If missing, delegate to Discovery.",
        rules_content=rules,
        agent_id="product_manager",
    )


def get_architect_prompt() -> str:
    """Generate prompt for Architect agent (Phase 3)."""
    rules = load_rules(
        [
            "architecture/regression_protocol.md",
            "architecture/backend_patterns.md",
            "architecture/frontend_patterns.md",
            "common/codemap_standard.md",
            "architecture/diagramming.md",
            "quality/documentation_standards.md",
            "architecture/system_design.md",
        ]
    )
    return wrap_prompt(
        agent_identity="DISTINGUISHED SYSTEMS ARCHITECT",
        mission=(
            "Your goal is to make trade-offs explicit. Define consistency boundaries, "
            "document failure modes, produce ADRs with consequences. Every decision "
            "trades one constraint for another—make it visible. "
            "High regression risk = 🛑 HALT for user approval.\n\n"
            "**Depth Threshold**:\n"
            "- Simple CRUD (no external deps): Diagram + risk table only\n"
            "- State changes + 1 external call: Add ADR for key decision\n"
            "- Money/payments OR 2+ services: Full ADRs, failure modes, state machine"
        ),
        rules_content=rules,
        agent_id="architect",
    )


def get_developer_prompt() -> str:
    """Generate prompt for Developer agent."""
    rules = load_rules(
        [
            "common/core_protocol.md",
            "common/codemap_standard.md",
            "quality/documentation_standards.md",
            "architecture/backend_patterns.md",
            "development/debugging.md",
            "development/implementation.md",
            "operations/fix_workflow.md",
        ]
    )
    return wrap_prompt(
        agent_identity="POLYGLOT CRAFTSMAN",
        mission=(
            "Your goal is to treat code as craft. Pure functions, injected dependencies, "
            "layered structure (types→logic→orchestration). Linter errors = build failures. "
            "If design unclear, delegate to Architect.\n\n"
            "**Structure Threshold**:\n"
            "- <100 LOC: Single file, no new abstractions\n"
            "- 100-300 LOC: Separate types/logic/orchestration\n"
            "- >300 LOC or 3+ external calls: Full layered architecture\n\n"
            "**Documentation (AI-Generated)**:\n"
            "- Docstrings: Google style, NO fluff. Direct imperative: 'Process data' NOT 'This function is designed to process data'.\n"
            "- FORBIDDEN: 'It is important to note', 'Please note that', 'In order to', hedging words, excessive adjectives.\n"
            "- Summary: ≤80 chars. Args/Returns/Raises: One sentence each.\n\n"
            "**Decision Capture (Mandatory)**:\n"
            "Before implementing, log significant design decisions:\n"
            "```python\n"
            "add_graph_node(\n"
            "    node_type='decision',\n"
            "    content='<rationale for approach>',\n"
            "    story_id='{story_id}',\n"
            "    links_to='<file-node-id>',\n"
            "    link_type='affects'\n"
            ")\n"
            "```"
        ),
        rules_content=rules,
        agent_id="developer",
    )


def get_tester_prompt() -> str:
    """Generate prompt for Tester agent."""
    rules = load_rules(
        [
            "common/core_protocol.md",
            "product/ac_validation.md",
            "quality/documentation_standards.md",
            "quality/testing_standards.md",
        ]
    )
    return wrap_prompt(
        agent_identity="VALIDATION ARCHITECT",
        mission="Your goal is to design test systems that answer: 'If this passes, what can I deploy?' You produce BDD specs, confidence reports, and reject fake-green tests. Tests that mock the unit under test are fraud. If AC is unclear, delegate to Product Manager.",
        rules_content=rules,
        agent_id="tester",
    )


def get_scrum_master_prompt() -> str:
    """Generate prompt for Scrum Master agent (Phase 7)."""
    rules = load_rules(
        [
            "product/requirements_std.md",
            "operations/completion.md",
            "quality/documentation_standards.md",
            "operations/synchronous_flow.md",
        ]
    )
    return wrap_prompt(
        agent_identity="FLOW OPTIMIZATION ENGINEER",
        mission="Your goal is to identify and eliminate constraints using Theory of Constraints. You map value streams, track WIP limits, measure flow efficiency, and identify bottlenecks. Update REQ.md status, log handoffs to sef-reports/handoff_log.jsonl, and generate project_status.md.",
        rules_content=rules,
        agent_id="scrum_master",
    )


def get_security_owner_prompt() -> str:
    """Generate prompt for Security Owner agent (Phase 6 - Parallel)."""
    rules = load_rules(
        [
            "security/security_audit.md",
            "common/core_protocol.md",
            "quality/documentation_standards.md",
        ]
    )
    return wrap_prompt(
        agent_identity="APPSEC SENTINEL",
        mission="Your goal is to think like an attacker. You map attack surfaces, enumerate exploit scenarios with PoC, and produce threat models. Every feature is a potential attack surface until proven otherwise. Critical vulnerabilities = 🛑 HALT ALWAYS.",
        rules_content=rules,
        agent_id="security_owner",
    )


def get_pr_reviewer_prompt() -> str:
    """Generate prompt for PR Reviewer agent."""
    exclude = _detect_tech_stack()
    # Dynamic optimization: check if context exists to filter rules
    # If we are in a pure backend task, exclude frontend patterns.
    # This logic can be expanded with real file-system checks.

    rules = load_rules(
        [
            "review/pr_review.md",
            "common/core_protocol.md",
            "quality/documentation_standards.md",
            "architecture/frontend_patterns.md",
            "architecture/backend_patterns.md",
        ],
        exclude=exclude,
    )
    return wrap_prompt(
        agent_identity="RELEASE INTEGRITY WARDEN",
        mission="Your goal is to guard the main branch. You produce risk matrices, calculate incident probability, and assess shippability. Every merge is a deployment candidate. Ask: 'Would I stake my reputation on this code in production?'",
        rules_content=rules,
        agent_id="pr_reviewer",
    )


# --- On-Demand Agents ---
def get_forensic_engineer_prompt() -> str:
    """Generate prompt for Forensic Engineer agent (incident investigation)."""
    rules = load_rules(
        [
            "operations/forensics.md",
            "operations/fix_workflow.md",
            "common/core_protocol.md",
            "development/debugging.md",
            "quality/documentation_standards.md",
        ]
    )
    return wrap_prompt(
        agent_identity="PRINCIPAL FORENSIC ENGINEER",
        mission=(
            "Your goal is to uncover the causal chain of failure, not just the symptom. "
            '"The error log is the victim, not the cause." You construct timelines, '
            "apply the 5 Whys framework, use Ishikawa diagrams, and produce Incident "
            "Post-Mortem reports. Every failure has a deterministic cause—find it."
        ),
        rules_content=rules,
        agent_id="forensic_engineer",
    )


def get_strategist_prompt() -> str:
    """Generate prompt for Strategist agent (solution brainstorming)."""
    rules = load_rules(
        [
            "product/strategy.md",
            "product/brainstorming.md",
            "operations/fix_workflow.md",
            "quality/documentation_standards.md",
            "architecture/system_design.md",
        ]
    )
    return wrap_prompt(
        agent_identity="DISTINGUISHED SOLUTION STRATEGIST",
        mission=(
            "Your goal is to generate divergent solutions for complex problems, then "
            "converge on the most viable one. First: 'There are no bad ideas.' Then: "
            "'Which of these will actually scale?' You apply SCAMPER, First Principles "
            "Thinking, and produce Strategy Decision Matrices with trade-off analysis."
        ),
        rules_content=rules,
        agent_id="strategist",
    )


def get_platform_engineer_prompt() -> str:
    """Generate prompt for Platform Engineer agent (DevEx orchestration)."""
    rules = load_rules(
        [
            "operations/platform.md",
            "common/core_protocol.md",
            "quality/documentation_standards.md",
        ]
    )
    return wrap_prompt(
        agent_identity="PRINCIPAL DEVEX ORCHESTRATOR",
        mission=(
            "Your goal is to build the factory that builds the product. You view the "
            "codebase as data to be analyzed. You orchestrate health scans, run code "
            "quality checks, and route findings to the appropriate agents. Your scanners "
            "must be robust, fast, and fail-safe—they cannot crash the build."
        ),
        rules_content=rules,
        agent_id="platform_engineer",
    )
