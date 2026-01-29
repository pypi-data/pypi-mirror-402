"""Network Import Scanner.

Scans Python files for forbidden network library imports that could
indicate external data transmission capabilities.
"""

import ast
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


# Libraries that enable network communication
FORBIDDEN_IMPORTS: set[str] = {
    # HTTP clients
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "urllib3",
    "urllib.request",
    "http.client",
    # Low-level networking
    "socket",
    "socketserver",
    "asyncio.open_connection",
    # Other protocols
    "ftplib",
    "smtplib",
    "telnetlib",
    "websocket",
    "websockets",
    "grpc",
    # Cloud SDKs
    "boto3",
    "google.cloud",
    "azure",
}


@dataclass
class NetworkScanResult:
    """Result of network import scan."""

    passed: bool
    files_scanned: int
    violations: list[dict[str, str]] = field(default_factory=list)
    forbidden_imports_checked: set[str] = field(default_factory=set)

    @property
    def summary(self) -> str:
        """One-line summary for CLI output."""
        if self.passed:
            return f"0 network libraries found in {self.files_scanned} files"
        return f"{len(self.violations)} network imports found"


def _extract_imports(file_path: Path) -> list[str]:
    """Extract all import names from a Python file using AST."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as e:
        logger.warning("failed_to_parse", file=str(file_path), error=str(e))
        return []

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
                # Also add full import path for submodules
                for alias in node.names:
                    imports.append(f"{node.module}.{alias.name}")

    return imports


def scan_network_imports(
    directory: Path,
    forbidden: set[str] | None = None,
) -> NetworkScanResult:
    """
    Scan all Python files in directory for forbidden network imports.

    Args:
        directory: Root directory to scan
        forbidden: Optional custom set of forbidden imports

    Returns:
        NetworkScanResult with pass/fail status and violations
    """
    forbidden = forbidden or FORBIDDEN_IMPORTS
    violations: list[dict[str, str]] = []
    files_scanned = 0

    # Find all Python files
    py_files = list(directory.rglob("*.py"))

    for py_file in py_files:
        if _should_skip(py_file):
            continue

        files_scanned += 1
        imports = _extract_imports(py_file)

        for imp in imports:
            imp_parts = imp.split(".")
            for i in range(len(imp_parts)):
                check_module = ".".join(imp_parts[: i + 1])
                if check_module in forbidden:
                    violations.append(
                        {
                            "file": str(py_file.relative_to(directory)),
                            "import": imp,
                            "matched": check_module,
                        }
                    )
                    logger.info(
                        "network_import_found",
                        file=str(py_file),
                        import_name=imp,
                    )
                    break

    passed = len(violations) == 0

    logger.info(
        "network_scan_complete",
        passed=passed,
        files_scanned=files_scanned,
        violations_count=len(violations),
    )

    return NetworkScanResult(
        passed=passed,
        files_scanned=files_scanned,
        violations=violations,
        forbidden_imports_checked=forbidden,
    )
