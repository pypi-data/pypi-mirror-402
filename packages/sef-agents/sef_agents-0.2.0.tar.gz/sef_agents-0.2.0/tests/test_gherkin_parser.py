"""Unit tests for Gherkin parser."""

from sef_agents.models.gherkin import GherkinScenario, GherkinStep
from sef_agents.tools.gherkin_parser import (
    parse_gherkin_text,
    parse_markdown_ac,
    validate_gherkin_syntax,
)


def test_parse_gherkin_text_single_scenario():
    """Test parsing single Gherkin scenario."""
    text = """
    Scenario: User login
    Given a user exists
    When the user logs in
    Then the user is authenticated
    """

    scenarios = parse_gherkin_text(text)

    assert len(scenarios) == 1
    assert scenarios[0].scenario == "User login"
    assert len(scenarios[0].steps) == 3
    assert scenarios[0].steps[0].keyword == "Given"
    assert scenarios[0].steps[1].keyword == "When"
    assert scenarios[0].steps[2].keyword == "Then"


def test_parse_gherkin_text_multiple_scenarios():
    """Test parsing multiple Gherkin scenarios."""
    text = """
    Scenario: User login success
    Given a user exists
    When the user logs in
    Then the user is authenticated

    Scenario: User login failure
    Given a user exists
    When the user logs in with wrong password
    Then an error is shown
    """

    scenarios = parse_gherkin_text(text)

    assert len(scenarios) == 2
    assert scenarios[0].scenario == "User login success"
    assert scenarios[1].scenario == "User login failure"


def test_parse_gherkin_text_with_and_but():
    """Test parsing Gherkin with And/But keywords."""
    text = """
    Scenario: Complex flow
    Given a user exists
    And the user has items in cart
    When the user checks out
    Then order is created
    And confirmation email is sent
    """

    scenarios = parse_gherkin_text(text)

    assert len(scenarios) == 1
    assert len(scenarios[0].steps) == 5
    assert scenarios[0].steps[1].keyword == "And"
    assert scenarios[0].steps[4].keyword == "And"


def test_parse_markdown_ac_with_bold_keywords():
    """Test parsing markdown AC with bold keywords."""
    markdown = """
    ### AC-1: User Login
    **Given** a user exists
    **When** the user logs in
    **Then** the user is authenticated
    """

    scenarios = parse_markdown_ac(markdown)

    assert len(scenarios) == 1
    assert "AC-1" in scenarios[0].scenario
    assert len(scenarios[0].steps) == 3


def test_parse_markdown_ac_inline_format():
    """Test parsing inline AC format."""
    markdown = """
    **AC1**: Given a user exists, When they login, Then they are authenticated
    """

    scenarios = parse_markdown_ac(markdown)

    assert len(scenarios) >= 1


def test_validate_gherkin_syntax_valid():
    """Test Gherkin syntax validation with valid input."""
    text = """
    Scenario: User login
    Given a user exists
    When the user logs in
    Then the user is authenticated
    """

    is_valid, error = validate_gherkin_syntax(text)

    assert is_valid is True
    assert error is None


def test_validate_gherkin_syntax_no_scenarios():
    """Test Gherkin syntax validation with no scenarios."""
    text = "Some random text without scenarios"

    is_valid, error = validate_gherkin_syntax(text)

    assert is_valid is False
    assert "No scenarios found" in error or "scenario" in error.lower()


def test_validate_gherkin_syntax_no_steps():
    """Test Gherkin syntax validation with scenario but no steps."""
    text = """
    Scenario: Empty scenario
    """

    is_valid, error = validate_gherkin_syntax(text)

    assert is_valid is False
    assert "no steps" in error.lower() or "steps" in error.lower()


def test_gherkin_step_to_markdown():
    """Test GherkinStep to_markdown conversion."""
    step = GherkinStep(keyword="Given", text="a user exists")

    markdown = step.to_markdown()

    assert markdown == "**Given** a user exists"


def test_gherkin_step_to_gherkin():
    """Test GherkinStep to_gherkin conversion."""
    step = GherkinStep(keyword="When", text="the user logs in")

    gherkin = step.to_gherkin()

    assert gherkin == "When the user logs in"


def test_gherkin_scenario_to_markdown():
    """Test GherkinScenario to_markdown conversion."""
    scenario = GherkinScenario(
        scenario="User login",
        steps=[
            GherkinStep(keyword="Given", text="a user exists"),
            GherkinStep(keyword="When", text="the user logs in"),
            GherkinStep(keyword="Then", text="the user is authenticated"),
        ],
    )

    markdown = scenario.to_markdown()

    assert "### User login" in markdown
    assert "**Given** a user exists" in markdown
    assert "**When** the user logs in" in markdown
    assert "**Then** the user is authenticated" in markdown
