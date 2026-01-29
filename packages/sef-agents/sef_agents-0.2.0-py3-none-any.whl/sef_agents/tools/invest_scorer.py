"""INVEST scoring tool for user story quality assessment."""

from typing import Optional

import structlog

from sef_agents.models.invest import INVESTScores

logger = structlog.get_logger(__name__)


def score_invest_principles(
    user_story: str,
    acceptance_criteria: list[str],
    description: Optional[str] = None,
) -> INVESTScores:
    """Score a user story against INVEST principles.

    Args:
        user_story: User story text (As a... I want... So that...)
        acceptance_criteria: List of acceptance criteria (Gherkin format preferred)
        description: Optional story description

    Returns:
        INVESTScores with 0-5 scores for each principle
    """
    story_text = f"{user_story} {description or ''} {' '.join(acceptance_criteria)}"

    # Independent: Check for dependencies, blockers, prerequisites
    independent_score = _score_independent(story_text, acceptance_criteria)

    # Negotiable: Check for specific implementation details (should be absent)
    negotiable_score = _score_negotiable(story_text)

    # Valuable: Check for value statement ("So that...")
    valuable_score = _score_valuable(user_story, description)

    # Estimable: Check for clear AC, testable criteria
    estimable_score = _score_estimable(acceptance_criteria)

    # Small: Check story size (AC count, complexity indicators)
    small_score = _score_small(acceptance_criteria, story_text)

    # Testable: Check for Gherkin format, binary pass/fail criteria
    testable_score = _score_testable(acceptance_criteria)

    return INVESTScores(
        independent=independent_score,
        negotiable=negotiable_score,
        valuable=valuable_score,
        estimable=estimable_score,
        small=small_score,
        testable=testable_score,
    )


def _score_by_keyword_count(
    text: str, keywords: list[str], reverse: bool = False
) -> int:
    """Score based on keyword count in text.

    Args:
        text: Text to analyze
        keywords: Keywords to search for
        reverse: If True, higher count = higher score (default: False, higher count = lower score)

    Returns:
        Score 0-5 based on keyword count
    """
    text_lower = text.lower()
    count = sum(1 for kw in keywords if kw in text_lower)

    if reverse:
        # Higher count = higher score
        if count == 0:
            return 1
        elif count == 1:
            return 2
        elif count == 2:
            return 3
        elif count <= 3:
            return 4
        else:
            return 5
    else:
        # Higher count = lower score
        if count == 0:
            return 5
        elif count == 1:
            return 4
        elif count == 2:
            return 3
        elif count <= 3:
            return 2
        else:
            return 1


def _score_independent(story_text: str, acceptance_criteria: list[str]) -> int:
    """Score Independent principle (0-5).

    Lower score if story mentions dependencies, blockers, or prerequisites.

    Args:
        story_text: Story text to analyze
        acceptance_criteria: Acceptance criteria (unused, kept for API consistency)
    """
    dependency_keywords = [
        "depends on",
        "requires",
        "blocked by",
        "must complete first",
        "prerequisite",
        "after",
        "before",
    ]
    _ = acceptance_criteria  # Unused but kept for API consistency
    return _score_by_keyword_count(story_text, dependency_keywords, reverse=False)


def _score_negotiable(story_text: str) -> int:
    """Score Negotiable principle (0-5).

    Lower score if story contains specific implementation details.
    """
    implementation_keywords = [
        "must use",
        "must implement",
        "exactly",
        "specifically",
        "only",
        "cannot use",
        "forbidden",
    ]
    return _score_by_keyword_count(story_text, implementation_keywords, reverse=False)


def _score_valuable(user_story: str, description: Optional[str] = None) -> int:
    """Score Valuable principle (0-5).

    Higher score if "So that..." clause is present and clear.
    """
    text = f"{user_story} {description or ''}"
    text_lower = text.lower()

    # Check for value statement
    if "so that" in text_lower:
        # Check if value is specific (not generic)
        generic_values = ["better", "good", "nice", "improve"]
        has_generic = any(gv in text_lower for gv in generic_values)

        if not has_generic:
            return 5
        else:
            return 3
    else:
        return 2


def _count_matches_in_list(items: list[str], keywords: list[str]) -> int:
    """Count items that contain any of the keywords.

    Args:
        items: List of strings to search
        keywords: Keywords to search for

    Returns:
        Count of items containing at least one keyword
    """
    return sum(
        1 for item in items if any(keyword in item.lower() for keyword in keywords)
    )


def _score_estimable(acceptance_criteria: list[str]) -> int:
    """Score Estimable principle (0-5).

    Higher score if AC are clear, specific, and measurable.
    """
    if not acceptance_criteria:
        return 1

    # Check for specific, measurable criteria
    specific_indicators = ["status:", "status code", "error", "timeout", "count"]
    ambiguous_terms = ["fast", "quickly", "user-friendly", "easy", "intuitive"]

    specific_count = _count_matches_in_list(acceptance_criteria, specific_indicators)
    ambiguous_count = _count_matches_in_list(acceptance_criteria, ambiguous_terms)

    if ambiguous_count > 0:
        return max(1, 3 - ambiguous_count)
    elif specific_count >= len(acceptance_criteria) * 0.5:
        return 5
    elif specific_count > 0:
        return 4
    else:
        return 3


def _score_small(acceptance_criteria: list[str], story_text: str) -> int:
    """Score Small principle (0-5).

    Higher score if story is appropriately sized (3-8 AC ideal).

    Args:
        acceptance_criteria: List of acceptance criteria
        story_text: Story text (unused, kept for API consistency)
    """
    ac_count = len(acceptance_criteria)
    _ = story_text  # Unused but kept for API consistency

    # Ideal: 3-8 AC
    if 3 <= ac_count <= 8:
        return 5
    elif ac_count == 2 or ac_count == 9:
        return 4
    elif ac_count == 1 or ac_count == 10:
        return 3
    elif ac_count == 0:
        return 1
    elif ac_count > 10:
        return 2
    else:
        return 4


def _score_testable(acceptance_criteria: list[str]) -> int:
    """Score Testable principle (0-5).

    Higher score if AC use Gherkin format and are binary (pass/fail).
    """
    if not acceptance_criteria:
        return 1

    gherkin_keywords = ["given", "when", "then", "and", "but"]
    gherkin_count = _count_matches_in_list(acceptance_criteria, gherkin_keywords)

    gherkin_ratio = gherkin_count / len(acceptance_criteria)

    if gherkin_ratio >= 0.8:
        return 5
    elif gherkin_ratio >= 0.6:
        return 4
    elif gherkin_ratio >= 0.4:
        return 3
    elif gherkin_ratio > 0:
        return 2
    else:
        return 1
