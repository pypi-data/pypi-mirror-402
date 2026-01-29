"""Common utilities for generating SEF reports.

This module provides functions to create reports in the standardized format:
- Location: sef-reports/<agent>/*.md (markdown) and *.json (JSON, automatic)
- Includes date and time of generation
- Auto-generates both markdown and JSON formats
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog

from sef_agents.tools.json_output import generate_json_output

logger = structlog.get_logger(__name__)

# Valid SEF agent names - prevents unknown/ directory creation
VALID_AGENTS = frozenset(
    {
        "developer",
        "architect",
        "qa_lead",
        "security_owner",
        "docs_curator",
        "platform_engineer",
        "pr_reviewer",
        "tester",
        "product_manager",
        "strategist",
        "forensic_engineer",
        "discovery",
    }
)


def get_report_path(
    agent: str, report_name: str, base_dir: Optional[Path] = None
) -> Path:
    """
    Generate the standardized report path for an agent.

    Args:
        agent: The SEF agent name (e.g., 'developer', 'qa_lead')
        report_name: Name of the report file (without .md extension)
        base_dir: Base directory for reports. Defaults to project_root if set,
                  otherwise current working directory.

    Returns:
        Path object pointing to sef-reports/<agent>/<report_name>.md
    """
    if base_dir is None:
        from sef_agents.session import SessionManager

        session = SessionManager.get()
        base_dir = session.project_root or Path.cwd()

    # Validate agent name - fallback to platform_engineer if invalid
    if not agent or agent not in VALID_AGENTS:
        logger.warning("invalid_agent_name", provided=agent, using="platform_engineer")
        agent = "platform_engineer"

    report_dir = base_dir / "sef-reports" / agent
    return report_dir / f"{report_name}.md"


def add_report_header(content: str, title: Optional[str] = None) -> str:
    """
    Add a standardized header with date/time to report content.

    Args:
        content: The report content (markdown)
        title: Optional title for the report. If None, uses "Report"

    Returns:
        Report content with header prepended
    """
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    date_only = now.strftime("%Y-%m-%d")
    time_only = now.strftime("%H:%M:%S")

    if title is None:
        title = "Report"

    header = f"""# {title}

**Generated:** {timestamp}
**Date:** {date_only}
**Time:** {time_only}

---

"""

    return header + content


def write_report(
    agent: str,
    report_name: str,
    content: str,
    title: Optional[str] = None,
    base_dir: Optional[Path] = None,
    json_data: Optional[dict[str, Any]] = None,
) -> Path:
    """
    Write a report to the standardized location with date/time header.

    Automatically generates both markdown and JSON formats.

    Args:
        agent: The SEF agent name
        report_name: Name of the report file (without .md extension)
        content: The report content (markdown)
        title: Optional title for the report header
        base_dir: Base directory for reports. Defaults to current working directory.
        json_data: Optional structured data for JSON output. If None, generates
                   JSON from markdown content metadata.

    Returns:
        Path to the written markdown report file (JSON is auto-generated)

    Raises:
        OSError: If the file cannot be written
    """
    report_path = get_report_path(agent, report_name, base_dir)

    # Ensure directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    full_content = add_report_header(content, title)

    # Write the markdown report
    report_path.write_text(full_content, encoding="utf-8")

    logger.info(
        "Report written", agent=agent, report_name=report_name, path=str(report_path)
    )

    # Auto-generate JSON output
    if json_data is None:
        # Generate JSON from markdown metadata
        json_data = {
            "agent": agent,
            "report_name": report_name,
            "title": title or "Report",
            "content": full_content,
            "generated_at": datetime.now().isoformat(),
        }

    generate_json_output("report", json_data, report_path)

    return report_path
