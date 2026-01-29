"""Unit tests for INVEST scoring tool."""

from sef_agents.models.invest import INVESTScores
from sef_agents.tools.invest_scorer import score_invest_principles


def test_score_independent_no_dependencies():
    """Test Independent scoring with no dependencies."""
    user_story = "As a user, I want to login, so that I can access the system."
    ac = ["Given a user exists, When they login, Then they are authenticated"]

    scores = score_invest_principles(user_story, ac)

    assert scores.independent >= 4  # High score for no dependencies


def test_score_independent_with_dependencies():
    """Test Independent scoring with dependencies."""
    user_story = "As a user, I want to checkout, so that I can purchase items. This depends on STORY-001 and requires payment API."
    ac = ["Given items in cart, When checkout, Then order is created"]

    scores = score_invest_principles(user_story, ac)

    assert scores.independent <= 3  # Lower score for dependencies


def test_score_negotiable_no_implementation_details():
    """Test Negotiable scoring without implementation details."""
    user_story = "As a user, I want to search products, so that I can find what I need."
    ac = ["Given products exist, When user searches, Then results are shown"]

    scores = score_invest_principles(user_story, ac)

    assert scores.negotiable >= 4  # High score for negotiable story


def test_score_valuable_with_clear_value():
    """Test Valuable scoring with clear value statement."""
    user_story = "As a user, I want to save my preferences, so that I don't have to reconfigure every time."
    ac = ["Given user preferences, When saved, Then they persist"]

    scores = score_invest_principles(user_story, ac)

    assert scores.valuable >= 4  # High score for clear value


def test_score_valuable_without_value():
    """Test Valuable scoring without value statement."""
    user_story = "As a user, I want to login."
    ac = ["Given credentials, When login, Then authenticated"]

    scores = score_invest_principles(user_story, ac)

    assert scores.valuable <= 3  # Lower score without "So that..."


def test_score_estimable_with_specific_ac():
    """Test Estimable scoring with specific, measurable AC."""
    user_story = "As a user, I want to submit a form, so that data is saved."
    ac = [
        "Given valid form data, When submitted, Then status code 200 is returned",
        "Given invalid form data, When submitted, Then status code 400 is returned",
    ]

    scores = score_invest_principles(user_story, ac)

    assert scores.estimable >= 4  # High score for specific AC


def test_score_small_ideal_size():
    """Test Small scoring with ideal AC count (3-8)."""
    user_story = (
        "As a user, I want to manage my profile, so that I can update my information."
    )
    ac = [
        "Given user is logged in, When viewing profile, Then profile is displayed",
        "Given user edits profile, When saving, Then changes are saved",
        "Given invalid data, When saving, Then error is shown",
        "Given user deletes profile, When confirmed, Then profile is deleted",
    ]

    scores = score_invest_principles(user_story, ac)

    assert scores.small == 5  # Perfect score for 4 AC


def test_score_testable_with_gherkin():
    """Test Testable scoring with Gherkin format."""
    user_story = "As a user, I want to login, so that I can access the system."
    ac = [
        "Given a user exists, When they login with valid credentials, Then they are authenticated",
        "Given a user exists, When they login with invalid credentials, Then error is shown",
    ]

    scores = score_invest_principles(user_story, ac)

    assert scores.testable >= 4  # High score for Gherkin format


def test_score_testable_without_gherkin():
    """Test Testable scoring without Gherkin format."""
    user_story = "As a user, I want to login, so that I can access the system."
    ac = ["User can login", "Invalid login shows error"]

    scores = score_invest_principles(user_story, ac)

    assert scores.testable <= 2  # Low score without Gherkin


def test_overall_score_calculation():
    """Test overall score calculation."""
    scores = INVESTScores(
        independent=5,
        negotiable=5,
        valuable=5,
        estimable=5,
        small=5,
        testable=5,
    )

    assert scores.overall_score() == 5.0


def test_invest_scores_to_dict():
    """Test INVESTScores to_dict conversion."""
    scores = INVESTScores(
        independent=4,
        negotiable=3,
        valuable=5,
        estimable=4,
        small=3,
        testable=5,
    )

    result = scores.to_dict()

    assert result == {
        "independent": 4,
        "negotiable": 3,
        "valuable": 5,
        "estimable": 4,
        "small": 3,
        "testable": 5,
    }
