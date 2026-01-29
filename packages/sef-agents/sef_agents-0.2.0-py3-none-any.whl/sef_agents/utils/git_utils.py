"""Git utilities for SEF Agents.

Provides user identification, repository context, and project root detection.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)

# Standard marker files for project root detection
PROJECT_MARKERS = (
    "pyproject.toml",
    "CODE_MAP.md",
    "package.json",
    "setup.py",
    "Cargo.toml",
    "go.mod",
)

# Cache directory name (consistent with .pytest_cache, .mypy_cache, .ruff_cache)
SEF_CACHE_DIR = ".sef_cache"


@dataclass
class GitUser:
    """Git user identity."""

    email: str
    name: str

    def __str__(self) -> str:
        """Return formatted user string."""
        return f"{self.name} <{self.email}>"


def is_git_repo(directory: str | Path | None = None) -> bool:
    """Check if directory is inside a git repository.

    Args:
        directory: Path to check. Defaults to current working directory.

    Returns:
        True if inside a git repo, False otherwise.
    """
    try:
        cmd = ["git", "rev-parse", "--git-dir"]
        kwargs = {"cwd": str(directory)} if directory else {}
        subprocess.run(
            cmd,
            capture_output=True,
            check=True,
            **kwargs,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        logger.warning("git_not_found", msg="Git is not installed")
        return False


def get_git_root(directory: str | Path | None = None) -> Path | None:
    """Get git repository root directory.

    Uses `git rev-parse --show-toplevel` - the industry standard approach.

    Args:
        directory: Directory to start search from.

    Returns:
        Path to git root, or None if not in a git repo.
    """
    try:
        kwargs = {"cwd": str(directory)} if directory else {}
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            **kwargs,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        logger.debug("git_not_installed")
        return None


def find_project_root(start_dir: Path | None = None) -> Path | None:
    """Find project root using marker file detection.

    Priority (industry best practice):
    1. Session project_root (explicit user setting via set_project_root)
    2. Git root (most reliable - used by pytest, mypy, ruff)
    3. Marker files (pyproject.toml, CODE_MAP.md, package.json, etc.)

    Args:
        start_dir: Directory to start search from. Defaults to cwd.

    Returns:
        Project root path, or None if not found.
    """
    # Avoid circular import
    from sef_agents.session import SessionManager

    # Priority 1: Explicit session setting (highest priority)
    session_root = SessionManager.get().project_root
    if session_root and session_root.exists():
        logger.debug("project_root_found", source="session", path=str(session_root))
        return session_root

    # Priority 2: Git root (most reliable)
    git_root = get_git_root(start_dir)
    if git_root:
        logger.debug("project_root_found", source="git", path=str(git_root))
        return git_root

    # Priority 3: Marker file traversal
    current = start_dir or Path.cwd()
    for path in [current, *current.parents]:
        if any((path / marker).exists() for marker in PROJECT_MARKERS):
            logger.debug("project_root_found", source="marker", path=str(path))
            return path

    logger.debug("project_root_not_found")
    return None


def get_sef_cache_dir(project_root: Path | None = None) -> Path:
    """Get SEF cache directory path.

    Args:
        project_root: Project root. If None, uses find_project_root().

    Returns:
        Path to .sef_cache directory.

    Raises:
        RuntimeError: If project root cannot be determined.
    """
    if project_root is None:
        project_root = find_project_root()
        if project_root is None:
            raise RuntimeError(
                "Cannot determine project root. "
                "Use set_project_root() or run from a git repository."
            )
    return project_root / SEF_CACHE_DIR


def get_git_user(directory: str | Path | None = None) -> GitUser | None:
    """Get git user from configuration.

    Args:
        directory: Repository directory. Defaults to current working directory.

    Returns:
        GitUser with email and name, or None if not in git repo or not configured.
    """
    if not is_git_repo(directory):
        logger.debug("not_git_repo", directory=str(directory))
        return None

    kwargs = {"cwd": str(directory)} if directory else {}

    try:
        email_result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=True,
            **kwargs,
        )
        name_result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
            **kwargs,
        )

        email = email_result.stdout.strip()
        name = name_result.stdout.strip()

        if not email:
            logger.warning("git_email_not_configured")
            return None

        return GitUser(email=email, name=name or "Unknown")

    except subprocess.CalledProcessError as e:
        logger.warning("git_config_error", error=str(e))
        return None
    except FileNotFoundError:
        logger.warning("git_not_found")
        return None


def get_current_user_id(directory: str | Path | None = None) -> str:
    """Get current user identifier for logging.

    Falls back to OS user if git not available.

    Args:
        directory: Repository directory.

    Returns:
        User identifier string (email or OS username).
    """
    import os

    git_user = get_git_user(directory)
    if git_user:
        return git_user.email

    # Fallback to OS user
    return os.environ.get("USER", "unknown")


def get_changed_files(
    directory: str | Path | None = None,
    extensions: set[str] | None = None,
) -> list[Path]:
    """Get list of files changed since last commit.

    Includes: modified, added, untracked files.

    Args:
        directory: Repository directory.
        extensions: Filter by file extensions (e.g., {'.py', '.ts'}).

    Returns:
        List of changed file paths relative to repo root.
    """
    if not is_git_repo(directory):
        return []

    dir_path = Path(directory) if directory else Path.cwd()
    changed: list[Path] = []

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(dir_path),
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                if line:
                    changed.append(Path(line))

        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            cwd=str(dir_path),
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                if line:
                    changed.append(Path(line))

    except FileNotFoundError:
        logger.warning("git_not_found")
        return []

    # Filter by extension if specified
    if extensions:
        changed = [f for f in changed if f.suffix in extensions]

    return list(set(changed))


def get_git_file_stats(file_path: Path) -> dict[str, int]:
    """Get commit statistics for a file (churn analysis).

    Args:
        file_path: Path to the file.

    Returns:
        Dict with keys: commit_count, author_count.
    """
    stats = {"commit_count": 0, "author_count": 0}

    if not is_git_repo(file_path.parent):
        return stats

    try:
        # Get commit count
        cmd_commits = ["git", "rev-list", "--count", "HEAD", "--", str(file_path)]
        result_commits = subprocess.run(
            cmd_commits,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(file_path.parent),
        )
        if result_commits.returncode == 0 and result_commits.stdout.strip():
            stats["commit_count"] = int(result_commits.stdout.strip())

        # Get unique authors
        cmd_authors = ["git", "log", "--format=%aE", "--", str(file_path)]
        result_authors = subprocess.run(
            cmd_authors,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(file_path.parent),
        )
        if result_authors.returncode == 0:
            authors = set(result_authors.stdout.strip().splitlines())
            # Filter empty lines
            authors = {a for a in authors if a}
            stats["author_count"] = len(authors)

    except (subprocess.SubprocessError, ValueError, OSError) as e:
        logger.debug("git_stats_failed", file=str(file_path), error=str(e))

    return stats
