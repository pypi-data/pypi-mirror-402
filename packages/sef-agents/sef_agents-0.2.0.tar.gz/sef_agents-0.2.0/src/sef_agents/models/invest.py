"""INVEST scoring models for user story quality assessment.

INVEST principles: Independent, Negotiable, Valuable, Estimable, Small, Testable.
"""

from enum import Enum

from pydantic import BaseModel, Field


class INVESTPrinciple(str, Enum):
    """INVEST principle enumeration."""

    INDEPENDENT = "Independent"
    NEGOTIABLE = "Negotiable"
    VALUABLE = "Valuable"
    ESTIMABLE = "Estimable"
    SMALL = "Small"
    TESTABLE = "Testable"


class INVESTScores(BaseModel):
    """INVEST scores for a user story.

    Each principle scored 0-5:
    - 0: Not met
    - 1-2: Poor
    - 3: Acceptable
    - 4-5: Excellent
    """

    independent: int = Field(ge=0, le=5, description="Independent score (0-5)")
    negotiable: int = Field(ge=0, le=5, description="Negotiable score (0-5)")
    valuable: int = Field(ge=0, le=5, description="Valuable score (0-5)")
    estimable: int = Field(ge=0, le=5, description="Estimable score (0-5)")
    small: int = Field(ge=0, le=5, description="Small score (0-5)")
    testable: int = Field(ge=0, le=5, description="Testable score (0-5)")

    def overall_score(self) -> float:
        """Calculate overall INVEST score (average of all principles)."""
        return (
            self.independent
            + self.negotiable
            + self.valuable
            + self.estimable
            + self.small
            + self.testable
        ) / 6.0

    def to_dict(self) -> dict[str, int]:
        """Convert scores to dictionary."""
        return {
            "independent": self.independent,
            "negotiable": self.negotiable,
            "valuable": self.valuable,
            "estimable": self.estimable,
            "small": self.small,
            "testable": self.testable,
        }
