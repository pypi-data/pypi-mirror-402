"""External Dependency Detector for SEF Agents.

Scans Python codebases to auto-detect external dependencies:
- Environment variable references (API URLs, endpoints)
- Known third-party API client libraries
- Hardcoded URL literals
- Config file endpoint definitions

Never touches .env files (security).
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# Known external API client libraries
KNOWN_API_CLIENTS: dict[str, str] = {
    "stripe": "Stripe Payment API",
    "boto3": "AWS Services",
    "botocore": "AWS Services",
    "twilio": "Twilio Communication API",
    "sendgrid": "SendGrid Email API",
    "slack_sdk": "Slack API",
    "google.cloud": "Google Cloud Services",
    "azure": "Azure Services",
    "requests_oauthlib": "OAuth Provider",
    "httpx": "HTTP Client (external calls)",
    "aiohttp": "Async HTTP Client (external calls)",
    "requests": "HTTP Client (external calls)",
    "urllib3": "HTTP Client (external calls)",
    "redis": "Redis Database",
    "pymongo": "MongoDB",
    "psycopg2": "PostgreSQL",
    "mysql": "MySQL",
    "elasticsearch": "Elasticsearch",
    "kafka": "Apache Kafka",
    "pika": "RabbitMQ",
    "celery": "Celery Task Queue",
}

# Patterns for env var extraction
ENV_VAR_PATTERNS: list[str] = [
    r'os\.getenv\(["\']([A-Z_]+(?:URL|API|ENDPOINT|HOST|SERVICE)[A-Z_]*)["\']',
    r'os\.environ\[["\']([A-Z_]+(?:URL|API|ENDPOINT|HOST|SERVICE)[A-Z_]*)["\']',
    r'os\.environ\.get\(["\']([A-Z_]+(?:URL|API|ENDPOINT|HOST|SERVICE)[A-Z_]*)["\']',
]

# URL pattern
URL_PATTERN = re.compile(
    r'["\']'
    r'(https?://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s"\']*)'
    r'["\']'
)


@dataclass
class ExternalDependency:
    """Represents a detected external dependency."""

    name: str
    dep_type: str  # 'env_var', 'api_client', 'url', 'config'
    source_file: str
    line_number: int | None = None
    description: str = ""

    def to_dict(self) -> dict[str, str | int | None]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.dep_type,
            "file": self.source_file,
            "line": self.line_number,
            "description": self.description,
        }


@dataclass
class ScanResult:
    """Result of external dependency scan."""

    dependencies: list[ExternalDependency] = field(default_factory=list)
    files_scanned: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def env_vars(self) -> list[ExternalDependency]:
        """Get environment variable dependencies."""
        return [d for d in self.dependencies if d.dep_type == "env_var"]

    @property
    def api_clients(self) -> list[ExternalDependency]:
        """Get API client dependencies."""
        return [d for d in self.dependencies if d.dep_type == "api_client"]

    @property
    def urls(self) -> list[ExternalDependency]:
        """Get URL dependencies."""
        return [d for d in self.dependencies if d.dep_type == "url"]


def _scan_file_for_env_vars(file_path: Path, content: str) -> list[ExternalDependency]:
    """Scan file content for environment variable references.

    Args:
        file_path: Path to the file being scanned.
        content: File content.

    Returns:
        List of detected env var dependencies.
    """
    deps: list[ExternalDependency] = []
    seen: set[str] = set()

    for pattern in ENV_VAR_PATTERNS:
        for match in re.finditer(pattern, content):
            var_name = match.group(1)
            if var_name not in seen:
                seen.add(var_name)
                # Find line number
                line_num = content[: match.start()].count("\n") + 1
                deps.append(
                    ExternalDependency(
                        name=var_name,
                        dep_type="env_var",
                        source_file=str(file_path),
                        line_number=line_num,
                        description="Environment variable for external endpoint",
                    )
                )

    return deps


def _scan_file_for_api_clients(
    file_path: Path, content: str
) -> list[ExternalDependency]:
    """Scan file for known API client library imports.

    Args:
        file_path: Path to the file being scanned.
        content: File content.

    Returns:
        List of detected API client dependencies.
    """
    deps: list[ExternalDependency] = []
    seen: set[str] = set()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return deps

    for node in ast.walk(tree):
        module_name: str | None = None

        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split(".")[0]

        if module_name and module_name in KNOWN_API_CLIENTS:
            if module_name not in seen:
                seen.add(module_name)
                deps.append(
                    ExternalDependency(
                        name=module_name,
                        dep_type="api_client",
                        source_file=str(file_path),
                        line_number=node.lineno if hasattr(node, "lineno") else None,
                        description=KNOWN_API_CLIENTS[module_name],
                    )
                )

    return deps


def _scan_file_for_urls(file_path: Path, content: str) -> list[ExternalDependency]:
    """Scan file for hardcoded external URLs.

    Args:
        file_path: Path to the file being scanned.
        content: File content.

    Returns:
        List of detected URL dependencies.
    """
    deps: list[ExternalDependency] = []
    seen: set[str] = set()

    for match in URL_PATTERN.finditer(content):
        url = match.group(1)
        # Extract domain
        domain_match = re.search(r"https?://([^/]+)", url)
        domain = domain_match.group(1) if domain_match else url

        if domain not in seen:
            seen.add(domain)
            line_num = content[: match.start()].count("\n") + 1
            deps.append(
                ExternalDependency(
                    name=domain,
                    dep_type="url",
                    source_file=str(file_path),
                    line_number=line_num,
                    description=f"External URL: {url[:50]}...",
                )
            )

    return deps


def scan_directory(directory: str | Path) -> ScanResult:
    """Scan a directory for external dependencies.

    Args:
        directory: Path to directory to scan.

    Returns:
        ScanResult with all detected dependencies.
    """
    result = ScanResult()
    dir_path = Path(directory)

    if not dir_path.exists():
        result.errors.append(f"Directory not found: {directory}")
        return result

    # Find all Python files, excluding common non-code directories
    exclude_dirs = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".tox",
        "dist",
        "build",
    }

    for py_file in dir_path.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            result.files_scanned += 1

            # Scan for all dependency types
            result.dependencies.extend(_scan_file_for_env_vars(py_file, content))
            result.dependencies.extend(_scan_file_for_api_clients(py_file, content))
            result.dependencies.extend(_scan_file_for_urls(py_file, content))

        except (OSError, UnicodeDecodeError) as e:
            result.errors.append(f"Error reading {py_file}: {e}")
            logger.warning("file_read_error", file=str(py_file), error=str(e))

    logger.info(
        "scan_complete",
        files_scanned=result.files_scanned,
        dependencies_found=len(result.dependencies),
    )

    return result


def generate_codemap_section(result: ScanResult) -> str:
    """Generate CODE_MAP.md External Dependencies section.

    Args:
        result: Scan result with dependencies.

    Returns:
        Markdown formatted section.
    """
    output = """## External Dependencies
*Auto-detected by external_detector.py*

"""

    if not result.dependencies:
        output += "No external dependencies detected.\n"
        return output

    # Group by type
    if result.env_vars:
        output += "### Environment Variables (External Endpoints)\n\n"
        output += "| Variable | File | Line | Notes |\n"
        output += "|----------|------|------|-------|\n"
        for dep in result.env_vars:
            output += f"| `{dep.name}` | `{Path(dep.source_file).name}` | {dep.line_number or '-'} | {dep.description} |\n"
        output += "\n"

    if result.api_clients:
        output += "### External API Clients\n\n"
        output += "| Library | Service | File | Line |\n"
        output += "|---------|---------|------|------|\n"
        for dep in result.api_clients:
            output += f"| `{dep.name}` | {dep.description} | `{Path(dep.source_file).name}` | {dep.line_number or '-'} |\n"
        output += "\n"

    if result.urls:
        output += "### Hardcoded External URLs\n\n"
        output += "| Domain | File | Line | Notes |\n"
        output += "|--------|------|------|-------|\n"
        for dep in result.urls:
            output += f"| `{dep.name}` | `{Path(dep.source_file).name}` | {dep.line_number or '-'} | ⚠️ Consider using env var |\n"
        output += "\n"

    return output


def scan_and_report(directory: str) -> str:
    """Scan directory and return formatted report.

    Args:
        directory: Path to scan.

    Returns:
        Status message with summary.
    """
    result = scan_directory(directory)

    if result.errors:
        return f"Scan completed with errors: {result.errors}"

    summary = (
        f"Scanned {result.files_scanned} files. "
        f"Found: {len(result.env_vars)} env vars, "
        f"{len(result.api_clients)} API clients, "
        f"{len(result.urls)} URLs."
    )

    return summary
