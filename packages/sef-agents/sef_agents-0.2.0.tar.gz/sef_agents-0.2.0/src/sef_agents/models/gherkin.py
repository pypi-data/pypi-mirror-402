"""Gherkin/BDD format models for structured acceptance criteria."""

from typing import Literal

from pydantic import BaseModel, Field


class GherkinStep(BaseModel):
    """Single Gherkin step (Given/When/Then/And/But)."""

    keyword: Literal["Given", "When", "Then", "And", "But"] = Field(
        description="Gherkin keyword"
    )
    text: str = Field(description="Step text content")

    def to_markdown(self) -> str:
        """Convert step to markdown format."""
        return f"**{self.keyword}** {self.text}"

    def to_gherkin(self) -> str:
        """Convert step to Gherkin text format."""
        return f"{self.keyword} {self.text}"


class GherkinScenario(BaseModel):
    """Gherkin scenario with multiple steps."""

    scenario: str = Field(description="Scenario title/description")
    steps: list[GherkinStep] = Field(
        default_factory=list, description="Ordered list of Gherkin steps"
    )

    def to_markdown(self) -> str:
        """Convert scenario to markdown format."""
        lines = [f"### {self.scenario}", ""]
        for step in self.steps:
            lines.append(step.to_markdown())
        return "\n".join(lines)

    def to_gherkin(self) -> str:
        """Convert scenario to Gherkin text format."""
        lines = [f"Scenario: {self.scenario}", ""]
        for step in self.steps:
            lines.append(step.to_gherkin())
        return "\n".join(lines)
