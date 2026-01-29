"""Version management tool for requirement tracking (git-based)."""

import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import structlog

from sef_agents.models.version import RequirementVersion, VersionStatus
from sef_agents.utils.git_utils import (
    get_git_file_stats,
    get_git_user,
    is_git_repo,
)

logger = structlog.get_logger(__name__)


def get_requirement_version(
    artifact_path: Path, artifact_id: str
) -> RequirementVersion:
    """Get version metadata for a requirement artifact.

    Args:
        artifact_path: Path to requirement file
        artifact_id: Artifact identifier (STORY-XXX, EPIC-XXX, etc.)

    Returns:
        RequirementVersion with git-based metadata
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    # Get git commit hash for file
    git_commit = _get_file_commit(artifact_path)
    git_user = get_git_user(artifact_path.parent)

    # Get file modification time
    modified_at = datetime.fromtimestamp(artifact_path.stat().st_mtime)

    # Get file stats (commit count, author count)
    stats = get_git_file_stats(artifact_path)

    # Determine status (Current if recently modified, Draft if new)
    status = VersionStatus.CURRENT
    if stats["commit_count"] == 0:
        status = VersionStatus.DRAFT

    return RequirementVersion(
        artifact_id=artifact_id,
        version=git_commit or "0.0.0",
        status=status,
        created_at=datetime.fromtimestamp(artifact_path.stat().st_ctime),
        modified_at=modified_at,
        git_commit=git_commit,
        modified_by=git_user.email if git_user else None,
    )


def check_stale_requirements(
    requirements_dir: Path, days_threshold: int = 90
) -> list[RequirementVersion]:
    """Check for stale requirements (not updated in X days).

    Args:
        requirements_dir: Directory containing requirements
        days_threshold: Days threshold for stale detection (default: 90)

    Returns:
        List of RequirementVersion objects for stale requirements
    """
    stale_requirements = []
    threshold_date = datetime.now() - timedelta(days=days_threshold)

    for req_file in requirements_dir.glob("*.md"):
        if req_file.stem.startswith(("STORY-", "EPIC-", "FEAT-")):
            try:
                version = get_requirement_version(req_file, req_file.stem)
                if version.modified_at and version.modified_at < threshold_date:
                    stale_requirements.append(version)
            except Exception as e:
                logger.warning(
                    "failed_to_check_version",
                    file=str(req_file),
                    error=str(e),
                )

    return stale_requirements


def mark_superseded(artifact_path: Path, artifact_id: str) -> RequirementVersion:
    """Mark a requirement as superseded.

    Args:
        artifact_path: Path to requirement file
        artifact_id: Artifact identifier

    Returns:
        Updated RequirementVersion with SUPERSEDED status
    """
    version = get_requirement_version(artifact_path, artifact_id)
    version.status = VersionStatus.SUPERSEDED

    # Update markdown file with status
    content = artifact_path.read_text(encoding="utf-8")
    # Update status field in markdown
    import re

    content = re.sub(
        r"\*\*Status:\*\*\s*\S+",
        f"**Status:** {version.status.value}",
        content,
    )
    artifact_path.write_text(content, encoding="utf-8")

    logger.info("Requirement marked as superseded", artifact_id=artifact_id)

    return version


def get_version_history(artifact_path: Path) -> list[RequirementVersion]:
    """Get version history for an artifact (git commits).

    Args:
        artifact_path: Path to requirement file

    Returns:
        List of RequirementVersion objects (one per git commit)
    """
    if not is_git_repo(artifact_path.parent):
        return []

    versions = []
    try:
        # Get git log for file
        result = subprocess.run(
            ["git", "log", "--format=%H|%ai|%ae", "--", str(artifact_path)],
            capture_output=True,
            text=True,
            cwd=str(artifact_path.parent),
            check=False,
        )

        if result.returncode != 0:
            return []

        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 3:
                commit_hash = parts[0]
                commit_date = datetime.fromisoformat(parts[1].replace(" ", "T"))
                author_email = parts[2]

                versions.append(
                    RequirementVersion(
                        artifact_id=artifact_path.stem,
                        version=commit_hash[:8],  # Short hash
                        status=VersionStatus.CURRENT,
                        created_at=commit_date,
                        modified_at=commit_date,
                        git_commit=commit_hash,
                        modified_by=author_email,
                    )
                )

    except Exception as e:
        logger.warning("failed_to_get_version_history", error=str(e))

    return versions


def _get_file_commit(artifact_path: Path) -> Optional[str]:
    """Get latest git commit hash for a file.

    Args:
        artifact_path: Path to file

    Returns:
        Commit hash or None if not in git repo
    """
    if not is_git_repo(artifact_path.parent):
        return None

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", str(artifact_path)],
            capture_output=True,
            text=True,
            cwd=str(artifact_path.parent),
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

    except Exception as e:
        logger.debug("failed_to_get_commit", error=str(e))

    return None
