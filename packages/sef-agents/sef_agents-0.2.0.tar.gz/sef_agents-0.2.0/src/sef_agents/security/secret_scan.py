"""Secret Detection Scanner.

Scans files for hardcoded secrets, API keys, passwords, and tokens
that could pose a security risk.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# Directories to skip during scanning
IGNORED_DIRS: set[str] = {
    ".venv",
    "venv",
    ".env",
    "node_modules",
    ".git",
    "dist",
    "build",
    ".tox",
}


def _should_skip(path: Path) -> bool:
    """Check if path should be skipped."""
    for part in path.parts:
        if part in IGNORED_DIRS:
            return True
        if part.endswith("_cache") or part.endswith("cache__"):
            return True
    return False


# Patterns to detect various types of secrets
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # API Keys and Tokens
    (
        "API Key Assignment",
        re.compile(r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][a-zA-Z0-9_\-]{16,}["\']'),
    ),
    (
        "Secret/Password Assignment",
        re.compile(r'(?i)(secret|password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']'),
    ),
    (
        "Token Assignment",
        re.compile(
            r'(?i)(token|auth_token|access_token)\s*[=:]\s*["\'][^"\']{16,}["\']'
        ),
    ),
    (
        "Bearer Token",
        re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"),
    ),
    # Platform-specific tokens
    (
        "GitHub Personal Access Token",
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    ),
    (
        "GitHub OAuth Token",
        re.compile(r"gho_[a-zA-Z0-9]{36}"),
    ),
    (
        "OpenAI API Key",
        re.compile(r"sk-[a-zA-Z0-9]{32,}"),
    ),
    (
        "AWS Access Key",
        re.compile(r"AKIA[0-9A-Z]{16}"),
    ),
    (
        "AWS Secret Key",
        re.compile(r'(?i)aws_secret_access_key\s*[=:]\s*["\'][^"\']{40}["\']'),
    ),
    # Generic high-entropy strings that look like secrets
    (
        "Private Key Header",
        re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"),
    ),
]

# Patterns that indicate false positives (test data, examples, etc.)
FALSE_POSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"example", re.IGNORECASE),
    re.compile(r"your[_-]?(api[_-]?)?key", re.IGNORECASE),
    re.compile(r"placeholder", re.IGNORECASE),
    re.compile(r"<[a-z_]+>", re.IGNORECASE),  # <your_key_here>
    re.compile(r"\$\{[^}]+\}"),  # ${ENV_VAR}
    re.compile(r"xxx+", re.IGNORECASE),
    re.compile(r"test[_-]?key", re.IGNORECASE),
    re.compile(r"dummy", re.IGNORECASE),
    re.compile(r"sample", re.IGNORECASE),
]


@dataclass
class SecretScanResult:
    """Result of secret detection scan."""

    passed: bool
    files_scanned: int
    secrets_found: list[dict[str, str]] = field(default_factory=list)
    false_positives_skipped: int = 0

    @property
    def summary(self) -> str:
        """One-line summary for CLI output."""
        if self.passed:
            return f"0 secrets detected in {self.files_scanned} files"
        return f"{len(self.secrets_found)} potential secrets found"


def _is_false_positive(match_text: str, line: str) -> bool:
    """Check if the match is likely a false positive."""
    combined = f"{match_text} {line}"
    return any(pattern.search(combined) for pattern in FALSE_POSITIVE_PATTERNS)


def _should_scan_file(file_path: Path, include_extensions: set[str]) -> bool:
    """Check if file should be scanned."""
    # Skip directories and non-matching extensions
    if file_path.is_dir():
        return False
    if file_path.suffix not in include_extensions:
        return False
    if _should_skip(file_path):
        return False
    # Skip test files (they contain test data)
    if "/tests/" in str(file_path) or "test_" in file_path.name:
        return False
    # Skip generated reports
    if "sef-reports" in str(file_path):
        return False
    # Skip lock files
    if file_path.name in {"uv.lock", "poetry.lock", "package-lock.json"}:
        return False
    # User defined ignores
    if "GAP_ANALYSIS.md" in file_path.name:
        return False
    if "docs/misc" in str(file_path):
        return False
    return True


def _process_file_secrets(
    file_path: Path,
    directory: Path,
    secrets_found: list[dict[str, str]],
) -> int:
    """Process a single file for secrets.

    Returns:
        Number of false positives skipped.
    """
    skipped_count = 0
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0

    relative_path = str(file_path.relative_to(directory))
    lines = content.split("\n")

    for line_num, line in enumerate(lines, start=1):
        for secret_type, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(line):
                match_text = match.group(0)

                if _is_false_positive(match_text, line):
                    skipped_count += 1
                    continue

                # Mask the actual secret value for reporting
                masked = match_text[:10] + "..." if len(match_text) > 10 else "***"

                secrets_found.append(
                    {
                        "file": relative_path,
                        "line": str(line_num),
                        "type": secret_type,
                        "masked_value": masked,
                    }
                )
                logger.warning(
                    "potential_secret_found",
                    file=relative_path,
                    line=line_num,
                    type=secret_type,
                )
    return skipped_count


def scan_secrets(
    directory: Path,
    include_extensions: set[str] | None = None,
) -> SecretScanResult:
    """
    Scan files for hardcoded secrets and credentials.

    Args:
        directory: Root directory to scan
        include_extensions: File extensions to scan

    Returns:
        SecretScanResult with pass/fail status and found secrets
    """
    include_extensions = include_extensions or {
        ".py",
        ".js",
        ".ts",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".env",
        ".conf",
        ".cfg",
    }
    secrets_found: list[dict[str, str]] = []
    false_positives_skipped = 0
    files_scanned = 0

    for file_path in directory.rglob("*"):
        if not _should_scan_file(file_path, include_extensions):
            continue

        files_scanned += 1
        false_positives_skipped += _process_file_secrets(
            file_path, directory, secrets_found
        )

    passed = len(secrets_found) == 0

    logger.info(
        "secret_scan_complete",
        passed=passed,
        files_scanned=files_scanned,
        secrets_count=len(secrets_found),
        false_positives_skipped=false_positives_skipped,
    )

    return SecretScanResult(
        passed=passed,
        files_scanned=files_scanned,
        secrets_found=secrets_found,
        false_positives_skipped=false_positives_skipped,
    )
