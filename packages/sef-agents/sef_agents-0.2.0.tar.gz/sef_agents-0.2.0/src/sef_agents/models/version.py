"""Version management models for requirement tracking."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VersionStatus(str, Enum):
    """Requirement version status."""

    CURRENT = "Current"
    SUPERSEDED = "Superseded"
    DRAFT = "Draft"


class RequirementVersion(BaseModel):
    """Version metadata for a requirement artifact."""

    artifact_id: str = Field(
        description="Artifact identifier (STORY-XXX, EPIC-XXX, etc.)"
    )
    version: str = Field(description="Version identifier (semantic or git commit hash)")
    status: VersionStatus = Field(
        default=VersionStatus.CURRENT, description="Version status"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Version creation timestamp"
    )
    modified_at: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )
    git_commit: Optional[str] = Field(default=None, description="Git commit hash")
    modified_by: Optional[str] = Field(
        default=None, description="Last modifier (git user email)"
    )

    def to_dict(self) -> dict:
        """Convert version to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "version": self.version,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "git_commit": self.git_commit,
            "modified_by": self.modified_by,
        }
