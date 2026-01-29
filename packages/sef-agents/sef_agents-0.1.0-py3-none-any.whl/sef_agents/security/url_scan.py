"""URL/Endpoint Scanner.

Scans files for URLs and API endpoints that could indicate
external data transmission or cloud service connections.
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


# Patterns to detect URLs and endpoints
URL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("HTTP/HTTPS URL", re.compile(r'https?://[^\s\'"<>)}\]]+', re.IGNORECASE)),
    ("WebSocket URL", re.compile(r'wss?://[^\s\'"<>)}\]]+', re.IGNORECASE)),
    ("FTP URL", re.compile(r'ftp://[^\s\'"<>)}\]]+', re.IGNORECASE)),
]

# URLs that are safe and expected (documentation, localhost, etc.)
WHITELIST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"https?://localhost", re.IGNORECASE),
    re.compile(r"https?://127\.0\.0\.1", re.IGNORECASE),
    re.compile(r"https?://0\.0\.0\.0", re.IGNORECASE),
    re.compile(r"https?://example\.com", re.IGNORECASE),
    re.compile(r"https?://example\.org", re.IGNORECASE),
    # Documentation and reference links
    re.compile(r"https?://modelcontextprotocol\.io", re.IGNORECASE),
    re.compile(r"https?://github\.com", re.IGNORECASE),
    re.compile(r"https?://ghcr\.io", re.IGNORECASE),
    re.compile(r"https?://files\.pythonhosted\.org", re.IGNORECASE),
    re.compile(r"https?://pypi\.org", re.IGNORECASE),
    re.compile(r"https?://docs\.pytest\.org", re.IGNORECASE),
    # Schema references (not actual URLs called at runtime)
    re.compile(r"https?://json-schema\.org", re.IGNORECASE),
    re.compile(r"https?://www\.w3\.org", re.IGNORECASE),
    re.compile(r"https?://docs\.astral\.sh", re.IGNORECASE),
    re.compile(r"https?://blog\.crewai\.com", re.IGNORECASE),
    re.compile(r"https?://api\.example\.com", re.IGNORECASE),
    re.compile(r"https?://astral\.sh", re.IGNORECASE),
    re.compile(r"https?://api\.stripe\.com", re.IGNORECASE),
    re.compile(r"https?://stripe\.com", re.IGNORECASE),
    re.compile(r"https?://boto3\.amazonaws\.com", re.IGNORECASE),
    # Common Badges and Libraries
    re.compile(r"https?://img\.shields\.io", re.IGNORECASE),
    re.compile(r"https?://www\.structlog\.org", re.IGNORECASE),
    # FastMCP Cloud schema references (not actual URLs called at runtime)
    re.compile(r"https?://gofastmcp\.com", re.IGNORECASE),
]


@dataclass
class URLScanResult:
    """Result of URL scan."""

    passed: bool
    files_scanned: int
    external_urls: list[dict[str, str]] = field(default_factory=list)
    whitelisted_urls: list[dict[str, str]] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """One-line summary for CLI output."""
        if self.passed:
            return f"0 external URLs found in {self.files_scanned} files"
        return f"{len(self.external_urls)} external URLs found"


def _is_whitelisted(url: str) -> bool:
    """Check if URL matches any whitelist pattern."""
    # Skip regex pattern fragments (contain backslashes or regex metacharacters)
    if "\\" in url or "[^" in url or "\\s" in url:
        return True
    return any(pattern.search(url) for pattern in WHITELIST_PATTERNS)


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
    # Skip lock files (they contain many package URLs)
    if file_path.name in {"uv.lock", "poetry.lock", "package-lock.json"}:
        return False
    # Skip generated JSON reports (bandit, pip-audit)
    if file_path.name in {"bandit-report.json", "pip-audit-report.json"}:
        return False
    # User defined ignores
    if "GAP_ANALYSIS.md" in file_path.name:
        return False
    if "docs/misc" in str(file_path):
        return False
    return True


def _process_file_urls(
    file_path: Path,
    directory: Path,
    external_urls: list[dict[str, str]],
    whitelisted_urls: list[dict[str, str]],
) -> None:
    """Process a single file for URLs."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return

    relative_path = str(file_path.relative_to(directory))

    for pattern_name, pattern in URL_PATTERNS:
        for match in pattern.finditer(content):
            url = match.group(0)
            # Clean up trailing punctuation
            url = url.rstrip(".,;:\"')")

            url_info = {
                "file": relative_path,
                "url": url,
                "type": pattern_name,
            }

            if _is_whitelisted(url):
                whitelisted_urls.append(url_info)
            else:
                external_urls.append(url_info)
                logger.info(
                    "external_url_found",
                    file=relative_path,
                    url=url,
                )


def scan_urls(
    directory: Path,
    include_extensions: set[str] | None = None,
) -> URLScanResult:
    """
    Scan files for external URLs and endpoints.

    Args:
        directory: Root directory to scan
        include_extensions: File extensions to scan (default: .py, .md, .txt, .json)

    Returns:
        URLScanResult with pass/fail status and found URLs
    """
    include_extensions = include_extensions or {".py", ".md", ".txt", ".json", ".toml"}
    external_urls: list[dict[str, str]] = []
    whitelisted_urls: list[dict[str, str]] = []
    files_scanned = 0

    for file_path in directory.rglob("*"):
        if not _should_scan_file(file_path, include_extensions):
            continue

        files_scanned += 1
        _process_file_urls(file_path, directory, external_urls, whitelisted_urls)

    passed = len(external_urls) == 0

    logger.info(
        "url_scan_complete",
        passed=passed,
        files_scanned=files_scanned,
        external_count=len(external_urls),
        whitelisted_count=len(whitelisted_urls),
    )

    return URLScanResult(
        passed=passed,
        files_scanned=files_scanned,
        external_urls=external_urls,
        whitelisted_urls=whitelisted_urls,
    )
