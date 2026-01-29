"""SEF Compliance Validation Tool.

This module provides file validation against SEF quality standards including
linting, type hints, logging requirements, MCP tool descriptions, and curator protocol.
"""

import re
from pathlib import Path

import structlog

from sef_agents.tools.report_utils import write_report

logger = structlog.get_logger(__name__)

# Pattern: @mcp.tool() followed by def without docstring
MCP_TOOL_NO_DOCSTRING = re.compile(
    r"@mcp\.tool\(\)\s*\n\s*def\s+(\w+)\([^)]*\)\s*->[^:]+:\s*\n\s*(?!\"\"\")",
    re.MULTILINE,
)

# Code-echoing comment patterns (curator protocol violation)
CODE_ECHO_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"#\s*increment\s+\w+", re.IGNORECASE),
        "Code-echoing: 'increment' comment",
    ),
    (
        re.compile(r"#\s*decrement\s+\w+", re.IGNORECASE),
        "Code-echoing: 'decrement' comment",
    ),
    (
        re.compile(r"#\s*return\s+(true|false|none|null)", re.IGNORECASE),
        "Code-echoing: return comment",
    ),
    (
        re.compile(r"#\s*set\s+\w+\s*(to|=)", re.IGNORECASE),
        "Code-echoing: assignment comment",
    ),
    (re.compile(r"#\s*get\s+\w+", re.IGNORECASE), "Code-echoing: getter comment"),
    (re.compile(r"#\s*call\s+\w+", re.IGNORECASE), "Code-echoing: call comment"),
    (
        re.compile(r"#\s*create\s+(new\s+)?\w+", re.IGNORECASE),
        "Code-echoing: instantiation comment",
    ),
    (re.compile(r"#\s*initialize", re.IGNORECASE), "Code-echoing: init comment"),
    (
        re.compile(r"#\s*loop\s+(through|over)", re.IGNORECASE),
        "Code-echoing: loop comment",
    ),
    (re.compile(r"#\s*iterate", re.IGNORECASE), "Code-echoing: iteration comment"),
    (re.compile(r"#\s*check\s+if", re.IGNORECASE), "Code-echoing: conditional comment"),
    (
        re.compile(r"//\s*increment\s+\w+", re.IGNORECASE),
        "Code-echoing: 'increment' comment",
    ),
    (
        re.compile(r"//\s*return\s+(true|false|null)", re.IGNORECASE),
        "Code-echoing: return comment",
    ),
]

# AI-generated docstring fluff patterns (token waste, exaggeration)
DOCSTRING_FLUFF_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Redundant introductions
    (
        re.compile(
            r"this\s+(function|method|class)\s+is\s+(designed\s+)?to", re.IGNORECASE
        ),
        "Fluff: 'This function is designed to'",
    ),
    (
        re.compile(r"the\s+purpose\s+of\s+this", re.IGNORECASE),
        "Fluff: 'The purpose of this'",
    ),
    (
        re.compile(
            r"this\s+(function|method|class)\s+is\s+responsible\s+for", re.IGNORECASE
        ),
        "Fluff: 'is responsible for'",
    ),
    # Hedging/uncertainty
    (
        re.compile(r"\b(it\s+)?should\s+be\s+noted\s+that", re.IGNORECASE),
        "Fluff: 'It should be noted that'",
    ),
    (re.compile(r"please\s+note\s+that", re.IGNORECASE), "Fluff: 'Please note that'"),
    (
        re.compile(r"it\s+is\s+important\s+to\s+note", re.IGNORECASE),
        "Fluff: 'It is important to note'",
    ),
    (
        re.compile(r"it\s+is\s+worth\s+mentioning", re.IGNORECASE),
        "Fluff: 'It is worth mentioning'",
    ),
    # Unnecessary phrases
    (re.compile(r"in\s+order\s+to", re.IGNORECASE), "Fluff: 'In order to' (use 'to')"),
    (re.compile(r"as\s+you\s+can\s+see", re.IGNORECASE), "Fluff: 'As you can see'"),
    (re.compile(r"in\s+other\s+words", re.IGNORECASE), "Fluff: 'In other words'"),
    (re.compile(r"that\s+is\s+to\s+say", re.IGNORECASE), "Fluff: 'That is to say'"),
    # Excessive adjectives (in docstrings)
    (
        re.compile(r"\b(extremely|very|highly|significantly)\s+\w+", re.IGNORECASE),
        "Fluff: Excessive adjective",
    ),
    # Hedging words in docstrings
    (
        re.compile(
            r"\b(might|could|possibly|potentially|probably)\s+\w+", re.IGNORECASE
        ),
        "Fluff: Hedging word",
    ),
]


def validate_compliance_tool(file_path: str) -> str:
    """Check a file against SEF quality standards.

    Performs static analysis checks for:
    - Python: structlog usage, type hints, MCP tool docstrings, curator protocol, docstring fluff
    - TypeScript: strict typing (no `any`)

    Args:
        file_path: Path to the file to validate.

    Returns:
        Status message with path to generated compliance report.
    """
    # Import here to avoid circular import
    from sef_agents.constants import Status
    from sef_agents.session import SessionManager
    from sef_agents.tools.context_tools import _format_available_agents_numbered

    # Enforce agent activation requirement
    active_agent = SessionManager.get().active_agent
    if not active_agent:
        agents_output = _format_available_agents_numbered()
        return (
            f"{Status.ERROR} No SEF Agent is active.\n\n"
            "**Compliance validation requires an active agent for proper context.**\n\n"
            f"{agents_output}\n\n"
            "Activate an agent first: `set_active_agent(agent_name)` or `set_active_agent(number)`"
        )

    p = Path(file_path)
    if not p.exists():
        return f"Error: File {file_path} not found."

    issues: list[str] = []

    # Simple static checks as proxies for real compliance
    try:
        content = p.read_text(encoding="utf-8")

        # Check 1: Structlog
        if p.suffix == ".py":
            if "print(" in content and "def " in content:
                # Heuristic: print in function body might be bad
                issues.append("Found `print()` statement. Use `structlog`.")
            if "logging." in content:
                issues.append("Found standard `logging`. Use `structlog`.")

        # Check 2: Types (Python)
        if p.suffix == ".py" and "def " in content:
            if "-> " not in content:
                issues.append("Potential missing return type hints.")

        # Check 3: Any (TS)
        if p.suffix in [".ts", ".tsx"]:
            if ": any" in content:
                issues.append("Found usage of `any` type. Strict typing required.")

        # Check 4: MCP tool docstrings (FastMCP uses as description)
        if p.suffix == ".py" and "@mcp.tool()" in content:
            missing_tools = MCP_TOOL_NO_DOCSTRING.findall(content)
            for tool_name in missing_tools:
                issues.append(
                    f"MCP tool `{tool_name}` missing docstring (used as description)."
                )

        # Check 5: Curator protocol - code-echoing comments (FORBIDDEN)
        if p.suffix == ".py":
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                for pattern, message in CODE_ECHO_PATTERNS:
                    if pattern.search(line):
                        issues.append(
                            f"Line {i}: {message} (Curator protocol violation)."
                        )
                        break  # One issue per line

        # Check 6: AI-generated docstring fluff (token waste, exaggeration)
        if p.suffix == ".py":
            # Extract docstrings (triple-quoted strings)
            docstring_pattern = re.compile(r'"""(.*?)"""', re.DOTALL | re.MULTILINE)
            docstrings = docstring_pattern.findall(content)
            for docstring in docstrings:
                # Check each line of docstring
                for line in docstring.split("\n"):
                    line_stripped = line.strip()
                    if (
                        not line_stripped
                        or line_stripped.startswith("Args:")
                        or line_stripped.startswith("Returns:")
                        or line_stripped.startswith("Raises:")
                    ):
                        continue  # Skip empty lines and section headers
                    for pattern, message in DOCSTRING_FLUFF_PATTERNS:
                        if pattern.search(line_stripped):
                            issues.append(
                                f"Docstring fluff: {message} (Remove for token efficiency)."
                            )
                            break  # One issue per pattern match

    except (OSError, UnicodeDecodeError) as e:
        return f"Error reading file: {e}"

    # Generate Report Content
    report_content = ""
    if not issues:
        report_content += "✅ Passed basic compliance checks.\n"
    else:
        report_content += "⚠️ Issues Found:\n"
        for i in issues:
            report_content += f"- [ ] {i}\n"

    # Use standardized report utility
    # active_agent already validated above, safe to use
    agent = active_agent
    report_name = f"compliance_{p.stem}"
    title = f"Compliance Report: {p.name}"

    try:
        report_path = write_report(agent, report_name, report_content, title=title)
        return f"Compliance check complete. Report saved to: `{report_path}`"
    except OSError as e:
        return f"Check complete but failed to save report: {e}\n\n{report_content}"
