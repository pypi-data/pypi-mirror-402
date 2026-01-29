"""Gherkin parser for converting text to structured Gherkin models."""

import re
from typing import Optional

import structlog

from sef_agents.models.gherkin import GherkinScenario, GherkinStep

logger = structlog.get_logger(__name__)

# Gherkin keyword patterns
GHERKIN_KEYWORDS = ["Given", "When", "Then", "And", "But"]
GHERKIN_KEYWORDS_LOWER = [kw.lower() for kw in GHERKIN_KEYWORDS]


def parse_gherkin_text(text: str) -> list[GherkinScenario]:
    """Parse Gherkin text into structured scenarios.

    Args:
        text: Gherkin-formatted text (can include multiple scenarios)

    Returns:
        List of GherkinScenario objects

    Example:
        text = '''
        Scenario: User login
        Given a user exists
        When the user logs in
        Then the user is authenticated
        '''
    """
    scenarios = []
    lines = text.strip().split("\n")

    current_scenario: Optional[GherkinScenario] = None
    current_steps: list[GherkinStep] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for scenario title
        if line.lower().startswith("scenario:"):
            # Save previous scenario if exists
            if current_scenario:
                current_scenario.steps = current_steps
                scenarios.append(current_scenario)

            scenario_title = line.split(":", 1)[1].strip()
            current_scenario = GherkinScenario(scenario=scenario_title)
            current_steps = []

        # Check for Gherkin step
        elif _is_gherkin_step(line):
            step = _parse_step(line)
            if step:
                current_steps.append(step)

    # Save last scenario
    if current_scenario:
        current_scenario.steps = current_steps
        scenarios.append(current_scenario)
    elif current_steps:
        # If no scenario title, create default scenario
        scenarios.append(
            GherkinScenario(scenario="Default Scenario", steps=current_steps)
        )

    return scenarios


def parse_markdown_ac(markdown_text: str) -> list[GherkinScenario]:
    """Parse acceptance criteria from markdown format.

    Handles formats like:
    - **AC-1**: Given X, When Y, Then Z
    - ### AC-1: Title
      **Given** X
      **When** Y
      **Then** Z

    Args:
        markdown_text: Markdown-formatted acceptance criteria

    Returns:
        List of GherkinScenario objects
    """
    scenarios = []

    # Pattern for AC with title: ### AC-1: Title
    ac_title_pattern = r"^###\s*(AC-\d+|AC\d+):\s*(.+)$"
    # Pattern for bold keywords: **Given** text
    bold_keyword_pattern = r"\*\*(Given|When|Then|And|But)\*\*\s*(.+)$"

    lines = markdown_text.strip().split("\n")
    current_scenario: Optional[GherkinScenario] = None
    current_steps: list[GherkinStep] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for AC title
        title_match = re.match(ac_title_pattern, line, re.IGNORECASE)
        if title_match:
            # Save previous scenario
            if current_scenario:
                current_scenario.steps = current_steps
                scenarios.append(current_scenario)

            ac_id = title_match.group(1)
            ac_title = title_match.group(2).strip()
            current_scenario = GherkinScenario(scenario=f"{ac_id}: {ac_title}")
            current_steps = []

        # Check for bold keyword (markdown format)
        elif current_scenario:
            bold_match = re.match(bold_keyword_pattern, line, re.IGNORECASE)
            if bold_match:
                keyword = bold_match.group(1).capitalize()
                text = bold_match.group(2).strip()
                current_steps.append(GherkinStep(keyword=keyword, text=text))
        # Check for inline format: **AC1**: Given X, When Y, Then Z (even without current scenario)
        elif ":" in line and any(kw.lower() in line.lower() for kw in GHERKIN_KEYWORDS):
            inline_scenario = _parse_inline_ac(line)
            if inline_scenario:
                scenarios.append(inline_scenario)

    # Save last scenario
    if current_scenario:
        current_scenario.steps = current_steps
        scenarios.append(current_scenario)

    return scenarios


def validate_gherkin_syntax(text: str) -> tuple[bool, Optional[str]]:
    """Validate Gherkin syntax.

    Args:
        text: Gherkin text to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    scenarios = parse_gherkin_text(text)

    if not scenarios:
        return False, "No scenarios found"

    for scenario in scenarios:
        if not scenario.steps:
            return False, f"Scenario '{scenario.scenario}' has no steps"

        # Check for at least one Given/When/Then
        has_given = any(step.keyword == "Given" for step in scenario.steps)
        has_when = any(step.keyword == "When" for step in scenario.steps)

        if not (has_given or has_when):
            return (
                False,
                f"Scenario '{scenario.scenario}' must have at least one Given or When step",
            )

    return True, None


def _is_gherkin_step(line: str) -> bool:
    """Check if line starts with a Gherkin keyword."""
    line_lower = line.lower().strip()
    return any(line_lower.startswith(kw.lower()) for kw in GHERKIN_KEYWORDS)


def _parse_step(line: str) -> Optional[GherkinStep]:
    """Parse a single Gherkin step line."""
    line = line.strip()

    # Find keyword
    keyword = None
    for kw in GHERKIN_KEYWORDS:
        if line.lower().startswith(kw.lower()):
            keyword = kw
            break

    if not keyword:
        return None

    # Extract text (remove keyword)
    text = line[len(keyword) :].strip()
    return GherkinStep(keyword=keyword, text=text)


def _parse_inline_ac(line: str) -> Optional[GherkinScenario]:
    """Parse inline AC format: **AC1**: Given X, When Y, Then Z."""
    # Pattern: **AC-1** or **AC1**: Given X, When Y, Then Z
    pattern = r"\*\*(AC[- ]?\d+)\*\*:\s*(.+)$"
    match = re.match(pattern, line, re.IGNORECASE)

    if not match:
        return None

    ac_id = match.group(1)
    steps_text = match.group(2)

    # Parse steps from comma-separated or newline-separated format
    steps = []
    # Try splitting by comma first
    if "," in steps_text:
        parts = [p.strip() for p in steps_text.split(",")]
    else:
        parts = [steps_text.strip()]

    for part in parts:
        step = _parse_step(part)
        if step:
            steps.append(step)

    if steps:
        return GherkinScenario(scenario=f"{ac_id}", steps=steps)

    return None
