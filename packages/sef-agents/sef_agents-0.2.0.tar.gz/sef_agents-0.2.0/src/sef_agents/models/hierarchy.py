"""Hierarchy models for Epic → Feature → Story structure."""

from typing import Optional

from pydantic import BaseModel, Field


class Epic(BaseModel):
    """Epic model (top-level requirement grouping)."""

    epic_id: str = Field(description="Unique epic identifier (e.g., EPIC-001)")
    title: str = Field(description="Epic title")
    description: str = Field(default="", description="Epic description")
    status: str = Field(default="Draft", description="Epic status")

    def to_dict(self) -> dict:
        """Convert epic to dictionary."""
        return {
            "epic_id": self.epic_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
        }


class Feature(BaseModel):
    """Feature model (mid-level requirement grouping under Epic)."""

    feature_id: str = Field(description="Unique feature identifier (e.g., FEAT-001)")
    epic_id: str = Field(description="Parent epic identifier")
    title: str = Field(description="Feature title")
    description: str = Field(default="", description="Feature description")
    status: str = Field(default="Draft", description="Feature status")

    def to_dict(self) -> dict:
        """Convert feature to dictionary."""
        return {
            "feature_id": self.feature_id,
            "epic_id": self.epic_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
        }


class Story(BaseModel):
    """Story model (low-level requirement, can be flat or hierarchical)."""

    story_id: str = Field(description="Unique story identifier (e.g., STORY-001)")
    title: str = Field(description="Story title")
    description: str = Field(default="", description="Story description")
    user_story: str = Field(
        default="", description="User story format: As a... I want... So that..."
    )
    epic_id: Optional[str] = Field(
        default=None, description="Parent epic identifier (optional for flat stories)"
    )
    feature_id: Optional[str] = Field(
        default=None,
        description="Parent feature identifier (optional for flat stories)",
    )
    status: str = Field(default="Draft", description="Story status")
    priority: str = Field(default="P2", description="Story priority (P1/P2/P3)")

    def is_flat(self) -> bool:
        """Check if story is flat (no epic/feature parent)."""
        return self.epic_id is None and self.feature_id is None

    def to_dict(self) -> dict:
        """Convert story to dictionary."""
        return {
            "story_id": self.story_id,
            "title": self.title,
            "description": self.description,
            "user_story": self.user_story,
            "epic_id": self.epic_id,
            "feature_id": self.feature_id,
            "status": self.status,
            "priority": self.priority,
        }
