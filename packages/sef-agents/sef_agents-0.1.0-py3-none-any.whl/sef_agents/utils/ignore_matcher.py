"""Ignore pattern matcher for .gitignore and .dockerignore files.

Parses ignore files and checks if paths match ignore patterns.
Used to avoid flagging intentionally ignored files as dead code.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class IgnorePattern:
    """Represents a single ignore pattern.

    Attributes:
        pattern: Original pattern string.
        regex: Compiled regex for matching.
        negated: True if pattern starts with ! (negation).
        directory_only: True if pattern ends with / (directory only).
    """

    pattern: str
    regex: re.Pattern[str]
    negated: bool = False
    directory_only: bool = False


@dataclass
class IgnorePatternMatcher:
    """Matches file paths against .gitignore/.dockerignore patterns.

    Attributes:
        patterns: List of parsed ignore patterns.
        base_dir: Base directory for relative path resolution.
    """

    patterns: list[IgnorePattern] = field(default_factory=list)
    base_dir: Path = field(default_factory=Path.cwd)

    @classmethod
    def from_file(
        cls,
        ignore_file: Path,
        base_dir: Path | None = None,
    ) -> "IgnorePatternMatcher":
        """Create matcher from ignore file.

        Args:
            ignore_file: Path to .gitignore or .dockerignore file.
            base_dir: Base directory for pattern matching.

        Returns:
            Configured IgnorePatternMatcher instance.
        """
        matcher = cls(base_dir=base_dir or ignore_file.parent)

        if not ignore_file.exists():
            return matcher

        try:
            content = ignore_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                pattern = matcher._parse_line(line)
                if pattern:
                    matcher.patterns.append(pattern)
        except OSError as e:
            logger.warning(
                "ignore_file_read_error", file=str(ignore_file), error=str(e)
            )

        return matcher

    @classmethod
    def from_directory(cls, directory: Path) -> "IgnorePatternMatcher":
        """Create matcher from all ignore files in directory.

        Loads .gitignore and .dockerignore if present.

        Args:
            directory: Directory to scan for ignore files.

        Returns:
            Combined IgnorePatternMatcher instance.
        """
        matcher = cls(base_dir=directory)

        for ignore_name in [".gitignore", ".dockerignore"]:
            ignore_file = directory / ignore_name
            if ignore_file.exists():
                file_matcher = cls.from_file(ignore_file, directory)
                matcher.patterns.extend(file_matcher.patterns)
                logger.debug(
                    "loaded_ignore_file",
                    file=ignore_name,
                    patterns=len(file_matcher.patterns),
                )

        return matcher

    def _parse_line(self, line: str) -> IgnorePattern | None:
        """Parse a single ignore pattern line.

        Args:
            line: Line from ignore file.

        Returns:
            Parsed IgnorePattern or None if line is empty/comment.
        """
        # Strip whitespace
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return None

        negated = False
        directory_only = False

        # Check for negation
        if line.startswith("!"):
            negated = True
            line = line[1:]

        # Check for directory-only pattern
        if line.endswith("/"):
            directory_only = True
            line = line[:-1]

        # Convert gitignore pattern to regex
        regex = self._pattern_to_regex(line)

        return IgnorePattern(
            pattern=line,
            regex=regex,
            negated=negated,
            directory_only=directory_only,
        )

    def _pattern_to_regex(self, pattern: str) -> re.Pattern[str]:
        """Convert gitignore pattern to compiled regex.

        Args:
            pattern: Gitignore-style pattern.

        Returns:
            Compiled regex pattern.
        """
        # Handle leading slash (anchor to root)
        anchored = pattern.startswith("/")
        if anchored:
            pattern = pattern[1:]

        # Escape special regex characters except * and ?
        escaped = ""
        i = 0
        while i < len(pattern):
            char = pattern[i]
            if char == "*":
                if i + 1 < len(pattern) and pattern[i + 1] == "*":
                    # ** matches any path including /
                    escaped += ".*"
                    i += 2
                    # Skip following /
                    if i < len(pattern) and pattern[i] == "/":
                        i += 1
                    continue
                else:
                    # * matches anything except /
                    escaped += "[^/]*"
            elif char == "?":
                escaped += "[^/]"
            elif char in ".^$+{}[]|()":
                escaped += "\\" + char
            else:
                escaped += char
            i += 1

        # Build final regex
        if anchored:
            regex_str = f"^{escaped}"
        else:
            # Match anywhere in path
            regex_str = f"(^|/){escaped}"

        # Match end of string or path separator
        regex_str += "(/|$)"

        try:
            return re.compile(regex_str)
        except re.error as e:
            logger.warning("invalid_ignore_pattern", pattern=pattern, error=str(e))
            # Return pattern that matches nothing
            return re.compile(r"^\b$")

    def is_ignored(self, path: Path | str, is_dir: bool = False) -> bool:
        """Check if path matches any ignore pattern.

        Args:
            path: File or directory path (relative to base_dir).
            is_dir: True if path is a directory.

        Returns:
            True if path should be ignored.
        """
        if isinstance(path, str):
            path = Path(path)

        # Make path relative to base_dir
        try:
            rel_path = path.relative_to(self.base_dir)
        except ValueError:
            rel_path = path

        # Convert to forward slashes for matching
        path_str = str(rel_path).replace("\\", "/")

        ignored = False

        for pattern in self.patterns:
            # For directory-only patterns, check if any parent matches
            if pattern.directory_only:
                if is_dir:
                    if pattern.regex.search(path_str):
                        ignored = not pattern.negated
                else:
                    # Check if file is under a matching directory (not the file itself)
                    # Only check parent directories, not the file's own name
                    if len(rel_path.parts) > 1:
                        for part_idx in range(len(rel_path.parts) - 1):
                            parent_path = "/".join(rel_path.parts[: part_idx + 1])
                            if pattern.regex.search(parent_path):
                                ignored = not pattern.negated
                                break
            elif pattern.regex.search(path_str):
                # Regular pattern
                ignored = not pattern.negated

        return ignored

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        """Filter list of paths, removing ignored ones.

        Args:
            paths: List of paths to filter.

        Returns:
            Paths that are NOT ignored.
        """
        return [p for p in paths if not self.is_ignored(p, is_dir=p.is_dir())]


def is_intentionally_ignored(file_path: Path, project_root: Path) -> bool:
    """Check if file is in .gitignore or .dockerignore.

    Convenience function for dead code detection.

    Args:
        file_path: Path to check.
        project_root: Project root directory.

    Returns:
        True if file is intentionally ignored.
    """
    matcher = IgnorePatternMatcher.from_directory(project_root)
    return matcher.is_ignored(file_path)
