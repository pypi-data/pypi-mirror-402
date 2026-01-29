"""Status emoji constants for SEF Agents output formatting.

These emojis provide visual clarity for agent outputs across all MCP clients.
SEF Agents is built on Anthropic's Model Context Protocol (MCP).

Usage:
    from sef_agents.constants import Status, Severity, Icons

    # Status indicators
    f"{Status.SUCCESS} Tests passed"  # ✅ Tests passed
    f"{Status.ERROR} Build failed"    # ❌ Build failed

    # Severity levels (for debt, issues, etc.)
    f"{Severity.CRITICAL} Security vulnerability"  # 🔴 Critical
    f"{Severity.HIGH} Type hints missing"          # 🟠 High

    # Formatting helpers
    Icons.banner("SECURITY AUDIT")  # ═══ SECURITY AUDIT ═══
"""

from enum import Enum
from typing import Final

AVAILABLE_AGENTS: dict[str, str] = {
    "discovery": "Discovery (Phase 0) - Codebase Archaeology",
    "product_manager": "Product Manager (Phase 1) - Requirements & AC",
    "qa_lead": "QA Lead (Phase 2) - AC Validation",
    "architect": "Architect (Phase 3) - System Design",
    "developer": "Developer (Phase 4) - Implementation",
    "pr_reviewer": "PR Reviewer (Phase 5) - Compliance Check",
    "tester": "Tester (Phase 6) - Verification & E2E",
    "security_owner": "Security Owner (Phase 6) - Vulnerability Audit",
    "scrum_master": "Scrum Master (Phase 7) - Workflow Completion",
    "test_designer": "Test Designer (Parallel) - Conceptual Test Design",
    "forensic_engineer": "Forensic Engineer (On-Demand) - Incident Investigation",
    "strategist": "Strategist (On-Demand) - Solution Brainstorming",
    "platform_engineer": "Platform Engineer (On-Demand) - DevEx & Health Scanning",
}


class Status:
    """Status indicator emojis for consistent output formatting."""

    SUCCESS: Final[str] = "✅"
    WARNING: Final[str] = "⚠️"
    ERROR: Final[str] = "❌"
    HALT: Final[str] = "🛑"
    ESCALATE: Final[str] = "↗️"
    PARALLEL: Final[str] = "⚡"
    INFO: Final[str] = "ℹ️"
    BLOCKED: Final[str] = "🚫"
    DELEGATING: Final[str] = "🔄"
    PASS: Final[str] = "✅ PASS"
    FAIL: Final[str] = "❌ FAIL"


class Severity:
    """Severity level indicators for issues, debt, and scan results."""

    CRITICAL: Final[str] = "🔴 Critical"
    HIGH: Final[str] = "🟠 High"
    MEDIUM: Final[str] = "🟡 Medium"
    LOW: Final[str] = "🟢 Low"

    # Short versions (emoji only)
    CRITICAL_ICON: Final[str] = "🔴"
    HIGH_ICON: Final[str] = "🟠"
    MEDIUM_ICON: Final[str] = "🟡"
    LOW_ICON: Final[str] = "🟢"

    @classmethod
    def from_string(cls, severity: str) -> str:
        """Convert severity string to formatted constant.

        Args:
            severity: One of 'critical', 'high', 'medium', 'low'

        Returns:
            Formatted severity string with emoji.
        """
        mapping = {
            "critical": cls.CRITICAL,
            "high": cls.HIGH,
            "medium": cls.MEDIUM,
            "low": cls.LOW,
        }
        return mapping.get(severity.lower(), cls.MEDIUM)


class Icons:
    """Box drawing and formatting characters for terminal output."""

    # Box drawing
    HEAVY_LINE: Final[str] = "═"
    LIGHT_LINE: Final[str] = "─"
    VERTICAL: Final[str] = "│"

    # Bullet points
    BULLET: Final[str] = "•"
    ARROW: Final[str] = "→"
    CHECK: Final[str] = "✓"
    CROSS: Final[str] = "✗"

    @classmethod
    def banner(cls, text: str, width: int = 60) -> str:
        """Create a centered banner with heavy lines.

        Args:
            text: Banner text
            width: Total width (default 60)

        Returns:
            Formatted banner string.
        """
        padding = (width - len(text) - 2) // 2
        return (
            f"{cls.HEAVY_LINE * width}\n{' ' * padding}{text}\n{cls.HEAVY_LINE * width}"
        )

    @classmethod
    def header(cls, text: str, width: int = 60) -> str:
        """Create a section header with light underline.

        Args:
            text: Header text
            width: Underline width

        Returns:
            Formatted header string.
        """
        return f"{text}\n{cls.LIGHT_LINE * min(len(text), width)}"


class EscalationLevel:
    """Escalation ladder levels."""

    L1_AUTO: Final[str] = "L1"
    L2_COLLAB: Final[str] = "L2"
    L3_USER: Final[str] = "L3"


class Phase(str, Enum):
    """SDLC workflow phases."""

    DISCOVERY = "PHASE_0"
    REQUIREMENTS = "PHASE_1"
    QA_GATE = "PHASE_2"
    DESIGN = "PHASE_3"
    IMPLEMENTATION = "PHASE_4"
    REVIEW = "PHASE_5"
    VERIFICATION = "PHASE_6"
    COMPLETION = "PHASE_7"


class TaskStatus(str, Enum):
    """Status for parallel tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StoryType(str, Enum):
    """Story type classification for capability detection."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    FULLSTACK = "fullstack"
    UNKNOWN = "unknown"


# Phase configuration with agents and artifacts
PHASE_CONFIG: dict[str, dict] = {
    Phase.DISCOVERY.value: {
        "name": "Discovery",
        "primary_agent": "discovery",
        "required_artifacts": [],
        "produces": [
            "CODE_MAP.md",
            "docs/ARCHITECTURE.md",
            "docs/EXTERNAL_DEPS.md",
            "docs/TECH_DEBT.md",
        ],
        "next_phase": Phase.REQUIREMENTS.value,
    },
    Phase.REQUIREMENTS.value: {
        "name": "Requirements",
        "primary_agent": "product_manager",
        "required_artifacts": ["CODE_MAP.md", "docs/ARCHITECTURE.md"],
        "produces": [
            "requirements/*.md",
            "requirements/DEPENDENCY_GRAPH.md",
            "requirements/FLOW_DIAGRAM.md",
        ],
        "next_phase": Phase.QA_GATE.value,
    },
    Phase.QA_GATE.value: {
        "name": "QA Gate",
        "primary_agent": "qa_lead",
        "parallel_agent": "test_designer",  # Parallel: conceptual test cases
        "background_agent": "architect",  # Background: pre-scan
        "required_artifacts": ["requirements/*.md"],
        "produces": ["ac_validated", "conceptual_tests"],
        "next_phase": Phase.DESIGN.value,
    },
    Phase.DESIGN.value: {
        "name": "Design",
        "primary_agent": "architect",
        "required_artifacts": ["ac_validated"],
        "produces": ["design"],
        "next_phase": Phase.IMPLEMENTATION.value,
    },
    Phase.IMPLEMENTATION.value: {
        "name": "Implementation",
        "primary_agent": "developer",
        "required_artifacts": ["design", "conceptual_tests"],
        "produces": ["implementation"],
        "next_phase": Phase.REVIEW.value,
    },
    Phase.REVIEW.value: {
        "name": "Review",
        "primary_agent": "pr_reviewer",
        "background_agent": "security_owner",  # Parallel: security scan
        "required_artifacts": ["implementation"],
        "produces": ["review_passed"],
        "next_phase": Phase.VERIFICATION.value,
    },
    Phase.VERIFICATION.value: {
        "name": "Verification",
        "primary_agent": "tester",
        "parallel_agent": "security_owner",  # Full parallel
        "required_artifacts": ["review_passed"],
        "produces": ["tests_passed", "security_passed"],
        "next_phase": Phase.COMPLETION.value,
    },
    Phase.COMPLETION.value: {
        "name": "Completion",
        "primary_agent": "scrum_master",
        "required_artifacts": ["tests_passed", "security_passed"],
        "produces": ["project_status.md"],
        "next_phase": None,
    },
}

# Agent to suggested next agent mapping
AGENT_NEXT_SUGGESTION: dict[str, str | list[str] | None] = {
    "discovery": "product_manager",
    "product_manager": ["qa_lead", "test_designer"],  # Parallel: QA Gate
    "qa_lead": "architect",
    "test_designer": "architect",  # Both QA agents feed into architect
    "architect": "developer",
    "developer": "pr_reviewer",
    "pr_reviewer": ["tester", "security_owner"],  # Parallel
    "tester": "scrum_master",
    "security_owner": "scrum_master",
    "scrum_master": None,
    "forensic_engineer": None,  # On-demand, no fixed next agent
    "strategist": None,  # On-demand, no fixed next agent
    "platform_engineer": None,  # On-demand, no fixed next agent
}

# Frontend detection keywords
FRONTEND_KEYWORDS: list[str] = [
    "ui",
    "component",
    "page",
    "button",
    "form",
    "modal",
    "dialog",
    "react",
    "vue",
    "angular",
    "frontend",
    "client-side",
    "browser",
    "css",
    "styling",
    "layout",
    "responsive",
    "animation",
]

# Backend detection keywords
BACKEND_KEYWORDS: list[str] = [
    "api",
    "endpoint",
    "service",
    "database",
    "server",
    "backend",
    "rest",
    "graphql",
    "authentication",
    "authorization",
    "migration",
]


# Agent capabilities for delegation routing
AGENT_CAPABILITIES: dict[str, dict[str, list[str] | str]] = {
    "discovery": {
        "duty": "Scan codebase, generate CODE_MAP.md",
        "requires": [],
        "provides": ["CODE_MAP.md"],
        "delegates_to": [],
    },
    "product_manager": {
        "duty": "Define requirements with testable AC",
        "requires": ["CODE_MAP.md"],
        "provides": ["requirements/*.md"],
        "delegates_to": ["discovery"],
    },
    "qa_lead": {
        "duty": "Validate AC testability and edge cases",
        "requires": ["requirements/*.md"],
        "provides": ["AC validation"],
        "delegates_to": ["product_manager"],
    },
    "test_designer": {
        "duty": "Design conceptual test cases from AC (BDD Architect)",
        "requires": ["requirements/*.md"],
        "provides": ["conceptual_tests"],
        "delegates_to": ["product_manager", "qa_lead"],
    },
    "architect": {
        "duty": "Design system structure, update CODE_MAP",
        "requires": ["requirements/*.md"],
        "provides": ["CODE_MAP.md", "design"],
        "delegates_to": ["product_manager", "discovery"],
    },
    "developer": {
        "duty": "Implement per Elite Quality Protocol",
        "requires": ["CODE_MAP.md", "design", "conceptual_tests"],
        "provides": ["implementation"],
        "delegates_to": ["architect", "test_designer"],
    },
    "pr_reviewer": {
        "duty": "Review code against compliance",
        "requires": ["implementation"],
        "provides": ["review report"],
        "delegates_to": ["developer"],
    },
    "tester": {
        "duty": "Convert conceptual tests to executable tests",
        "requires": ["requirements/*.md", "implementation", "conceptual_tests"],
        "provides": ["tests"],
        "delegates_to": ["product_manager", "developer", "test_designer"],
    },
    "security_owner": {
        "duty": "Audit vulnerabilities",
        "requires": ["implementation"],
        "provides": ["security audit"],
        "delegates_to": ["developer"],
    },
    "scrum_master": {
        "duty": "Track status, close loop",
        "requires": ["all artifacts"],
        "provides": ["project_status.md"],
        "delegates_to": ["any"],
    },
    "forensic_engineer": {
        "duty": "Investigate incidents, produce post-mortems with root cause analysis",
        "requires": [],  # Independent - self-assesses context needs
        "provides": ["incident_postmortem.md"],
        "delegates_to": ["discovery", "developer"],
    },
    "strategist": {
        "duty": "Brainstorm solutions, produce trade-off analysis matrices",
        "requires": [],  # Independent - self-assesses context needs
        "provides": ["strategy_decision_matrix.md"],
        "delegates_to": ["discovery", "architect"],
    },
    "platform_engineer": {
        "duty": "Scan codebase health, run quality checks, route findings to agents",
        "requires": [],  # Independent - scans any codebase
        "provides": ["health_report.md", "code_quality_report.md"],
        "delegates_to": ["developer", "architect", "pr_reviewer"],
    },
}
