"""Code Quality Scanner - AST-based pe_rules enforcement.

Scans Python files for code quality violations using Abstract Syntax Trees.
Detects: bare exceptions, import organization, logging issues, docstring gaps.

**Note:** This scanner is Python-only (uses native AST module).
For TypeScript/JavaScript/Java, code quality issues are detected via
debt_scanner using regex patterns defined in language YAML configs.

Usage:
    from sef_agents.tools.code_quality_scanner import scan_code_quality
    result = scan_code_quality("/path/to/project")

Dependencies:
    - Python ast module (stdlib)
    - structlog for logging

Multi-Language Support:
    - Python: This scanner (AST-based, native)
    - TypeScript/JavaScript/Java: debt_scanner (regex-based, config-driven)
    - All languages: Unified via health_scanner
"""

import ast
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import structlog

from sef_agents.tools.report_utils import write_report
from sef_agents.utils.ignore_matcher import is_intentionally_ignored

logger = structlog.get_logger(__name__)


class Severity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Owner(str, Enum):
    """Agent responsible for fixing the issue."""

    DEVELOPER = "developer"
    ARCHITECT = "architect"
    PR_REVIEWER = "pr_reviewer"
    DOCS_CURATOR = "docs_curator"


@dataclass
class QualityIssue:
    """Single code quality finding."""

    file: str
    line: int
    rule: str
    message: str
    severity: Severity
    owner: Owner
    suggestion: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file,
            "line": self.line,
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity.value,
            "owner": self.owner.value,
            "suggestion": self.suggestion,
        }


@dataclass
class ScanResult:
    """Aggregated scan results."""

    issues: list[QualityIssue] = field(default_factory=list)
    files_scanned: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        """Count critical issues."""
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Count high severity issues."""
        return sum(1 for i in self.issues if i.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        """Count medium severity issues."""
        return sum(1 for i in self.issues if i.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        """Count low severity issues."""
        return sum(1 for i in self.issues if i.severity == Severity.LOW)

    def by_owner(self) -> dict[str, list[QualityIssue]]:
        """Group issues by owner agent."""
        grouped: dict[str, list[QualityIssue]] = {}
        for issue in self.issues:
            owner = issue.owner.value
            if owner not in grouped:
                grouped[owner] = []
            grouped[owner].append(issue)
        return grouped


class CodeQualityAnalyzer(ast.NodeVisitor):
    """AST visitor that detects code quality violations."""

    def __init__(self, file_path: str, source: str) -> None:
        """Initialize analyzer.

        Args:
            file_path: Path to source file being analyzed.
            source: Source code content.
        """
        self.file_path = file_path
        self.source = source
        self.lines = source.splitlines()
        self.issues: list[QualityIssue] = []
        self._in_function = False
        self._current_function: str | None = None
        self._imports: list[tuple[int, str, str]] = []  # (line, type, name)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Detect bare except and except Exception."""
        if node.type is None:
            self.issues.append(
                QualityIssue(
                    file=self.file_path,
                    line=node.lineno,
                    rule="E001",
                    message="Bare except clause",
                    severity=Severity.CRITICAL,
                    owner=Owner.DEVELOPER,
                    suggestion="Use specific exception: except ValueError, TypeError",
                )
            )
        elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
            # Check if it re-raises
            has_reraise = any(
                isinstance(stmt, ast.Raise) and stmt.exc is None
                for stmt in ast.walk(node)
            )
            if not has_reraise:
                self.issues.append(
                    QualityIssue(
                        file=self.file_path,
                        line=node.lineno,
                        rule="E002",
                        message="except Exception without re-raise",
                        severity=Severity.CRITICAL,
                        owner=Owner.DEVELOPER,
                        suggestion="Use specific exception or add 'raise' to re-raise",
                    )
                )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function for type hints and docstrings."""
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function for type hints and docstrings."""
        self._check_function(node)
        self.generic_visit(node)

    def _check_return_type(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        is_private: bool,
        is_dunder: bool,
    ) -> None:
        """Check for return type hints."""
        if not is_dunder and node.returns is None and not is_private:
            self.issues.append(
                QualityIssue(
                    file=self.file_path,
                    line=node.lineno,
                    rule="T001",
                    message=f"Missing return type hint: {node.name}",
                    severity=Severity.HIGH,
                    owner=Owner.DEVELOPER,
                    suggestion=f"Add return type: def {node.name}(...) -> ReturnType:",
                )
            )

    def _check_docstring_quality(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        is_private: bool,
        is_dunder: bool,
    ) -> None:
        """Check docstring quality."""
        if is_private or is_dunder:
            return

        docstring = ast.get_docstring(node)
        if docstring is None:
            self.issues.append(
                QualityIssue(
                    file=self.file_path,
                    line=node.lineno,
                    rule="D001",
                    message=f"Missing docstring: {node.name}",
                    severity=Severity.MEDIUM,
                    owner=Owner.DEVELOPER,
                    suggestion="Add docstring with Args, Returns, Raises sections",
                )
            )
        elif docstring.strip() in ("TODO", "..."):
            self.issues.append(
                QualityIssue(
                    file=self.file_path,
                    line=node.lineno,
                    rule="D002",
                    message=f"Empty/placeholder docstring: {node.name}",
                    severity=Severity.HIGH,
                    owner=Owner.DEVELOPER,
                    suggestion="Replace placeholder with actual documentation",
                )
            )
        elif node.args.args and "Args:" not in docstring:
            self.issues.append(
                QualityIssue(
                    file=self.file_path,
                    line=node.lineno,
                    rule="D003",
                    message=f"Docstring missing Args section: {node.name}",
                    severity=Severity.MEDIUM,
                    owner=Owner.DEVELOPER,
                    suggestion="Add Args: section documenting parameters",
                )
            )

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check function for quality issues.

        Args:
            node: Function definition AST node.
        """
        # Skip private/dunder methods for some checks
        is_private = node.name.startswith("_")
        is_dunder = node.name.startswith("__") and node.name.endswith("__")

        self._check_return_type(node, is_private, is_dunder)
        self._check_docstring_quality(node, is_private, is_dunder)

    def visit_Import(self, node: ast.Import) -> None:
        """Track import statements."""
        for alias in node.names:
            self._imports.append((node.lineno, "import", alias.name))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from imports."""
        module = node.module or ""
        for alias in node.names:
            self._imports.append((node.lineno, "from", module))
        self.generic_visit(node)

    def _check_logging_call(self, node: ast.Call) -> None:
        """Check for logging.* usage."""
        if not isinstance(node.func, ast.Attribute):
            return

        if isinstance(node.func.value, ast.Name):
            if node.func.value.id == "logging":
                self.issues.append(
                    QualityIssue(
                        file=self.file_path,
                        line=node.lineno,
                        rule="L002",
                        message="stdlib logging used instead of structlog",
                        severity=Severity.MEDIUM,
                        owner=Owner.DEVELOPER,
                        suggestion="Use structlog: import structlog; logger = structlog.get_logger()",
                    )
                )

        # Check for f-strings in logger calls
        if node.func.attr in ("info", "debug", "warning", "error", "critical"):
            if node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.JoinedStr):
                    self.issues.append(
                        QualityIssue(
                            file=self.file_path,
                            line=node.lineno,
                            rule="L003",
                            message="f-string in logger call",
                            severity=Severity.MEDIUM,
                            owner=Owner.DEVELOPER,
                            suggestion='Use lazy formatting: logger.info("msg %s", var) or structured: logger.info("msg", var=var)',
                        )
                    )

    def visit_Call(self, node: ast.Call) -> None:
        """Detect print() and logging misuse."""
        # Check for print()
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.issues.append(
                QualityIssue(
                    file=self.file_path,
                    line=node.lineno,
                    rule="L001",
                    message="print() statement found",
                    severity=Severity.HIGH,
                    owner=Owner.DEVELOPER,
                    suggestion="Use structlog: logger.info('message', key=value)",
                )
            )

        self._check_logging_call(node)
        self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> None:
        """Check module-level issues."""
        # Check module docstring
        docstring = ast.get_docstring(node)
        if docstring is None:
            self.issues.append(
                QualityIssue(
                    file=self.file_path,
                    line=1,
                    rule="D004",
                    message="Missing module docstring",
                    severity=Severity.MEDIUM,
                    owner=Owner.DOCS_CURATOR,
                    suggestion="Add module docstring at top of file",
                )
            )
        self.generic_visit(node)

    def check_import_order(self) -> None:
        """Verify import organization: stdlib → third-party → local."""
        if not self._imports:
            return

        # Standard library modules (common ones)
        stdlib = {
            "abc",
            "ast",
            "asyncio",
            "collections",
            "contextlib",
            "copy",
            "dataclasses",
            "datetime",
            "enum",
            "functools",
            "hashlib",
            "io",
            "itertools",
            "json",
            "logging",
            "math",
            "os",
            "pathlib",
            "pickle",
            "random",
            "re",
            "shutil",
            "socket",
            "sqlite3",
            "string",
            "subprocess",
            "sys",
            "tempfile",
            "threading",
            "time",
            "traceback",
            "typing",
            "unittest",
            "urllib",
            "uuid",
            "warnings",
            "xml",
        }

        current_section = 0  # 0=stdlib, 1=third-party, 2=local
        for line, _, name in self._imports:
            root_module = name.split(".")[0]

            if root_module in stdlib:
                section = 0
            elif root_module.startswith("sef_agents"):
                section = 2
            else:
                section = 1  # third-party

            if section < current_section:
                self.issues.append(
                    QualityIssue(
                        file=self.file_path,
                        line=line,
                        rule="I001",
                        message=f"Import order violation: {name}",
                        severity=Severity.MEDIUM,
                        owner=Owner.DEVELOPER,
                        suggestion="Order imports: stdlib → third-party → local",
                    )
                )
            current_section = max(current_section, section)


def analyze_file(file_path: Path) -> list[QualityIssue]:
    """Analyze single Python file for quality issues.

    Args:
        file_path: Path to Python file.

    Returns:
        List of quality issues found.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("file_read_error", file=str(file_path), error=str(e))
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        logger.warning("syntax_error", file=str(file_path), error=str(e))
        return []

    analyzer = CodeQualityAnalyzer(str(file_path), source)
    analyzer.visit(tree)
    analyzer.check_import_order()

    return analyzer.issues


def scan_directory(directory: str | Path) -> ScanResult:
    """Scan directory for code quality issues.

    Args:
        directory: Path to directory to scan.

    Returns:
        ScanResult with all findings.
    """
    result = ScanResult()
    dir_path = Path(directory)

    if not dir_path.exists():
        result.errors.append(f"Directory not found: {directory}")
        return result

    # Find all Python files
    python_files = list(dir_path.rglob("*.py"))

    for file_path in python_files:
        # Skip ignored paths
        if is_intentionally_ignored(file_path, dir_path):
            continue

        result.files_scanned += 1
        issues = analyze_file(file_path)
        result.issues.extend(issues)

    # Sort by severity (critical first)
    severity_order = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
    }
    result.issues.sort(key=lambda x: (severity_order[x.severity], x.file, x.line))

    logger.info(
        "scan_complete",
        files_scanned=result.files_scanned,
        issues_found=len(result.issues),
        critical=result.critical_count,
    )

    return result


def format_report(result: ScanResult, directory: str) -> str:
    """Format scan result as Markdown report.

    Args:
        result: Scan result to format.
        directory: Directory that was scanned.

    Returns:
        Markdown formatted report.
    """
    lines = [
        "# Code Quality Report",
        "",
        f"**Directory:** `{directory}`",
        f"**Files Scanned:** {result.files_scanned}",
        "",
        "## Summary",
        "",
        "| Severity | Count | Status |",
        "|----------|-------|--------|",
        f"| Critical | {result.critical_count} | {'🛑 Block' if result.critical_count > 0 else '✅'} |",
        f"| High | {result.high_count} | {'⚠️ Fix soon' if result.high_count > 0 else '✅'} |",
        f"| Medium | {result.medium_count} | {'📋 Backlog' if result.medium_count > 0 else '✅'} |",
        f"| Low | {result.low_count} | {'ℹ️ Info' if result.low_count > 0 else '✅'} |",
        "",
    ]

    # Critical issues
    critical = [i for i in result.issues if i.severity == Severity.CRITICAL]
    if critical:
        lines.extend(
            [
                "## Critical Issues (Action Required)",
                "",
                "| File | Line | Rule | Message |",
                "|------|------|------|---------|",
            ]
        )
        for issue in critical:
            lines.append(
                f"| `{issue.file}` | {issue.line} | {issue.rule} | {issue.message} |"
            )
        lines.append("")

    # High priority
    high = [i for i in result.issues if i.severity == Severity.HIGH]
    if high:
        lines.extend(
            [
                "## High Priority",
                "",
                "| File | Line | Rule | Message |",
                "|------|------|------|---------|",
            ]
        )
        for issue in high[:20]:  # Limit to 20
            lines.append(
                f"| `{issue.file}` | {issue.line} | {issue.rule} | {issue.message} |"
            )
        if len(high) > 20:
            lines.append(f"| ... | ... | ... | *({len(high) - 20} more)* |")
        lines.append("")

    # By owner
    by_owner = result.by_owner()
    if by_owner:
        lines.append("## By Owner")
        lines.append("")
        for owner, issues in sorted(by_owner.items()):
            lines.append(f"### {owner} ({len(issues)} issues)")
            lines.append("")
            for issue in issues[:10]:
                lines.append(f"- [ ] `{issue.file}:{issue.line}` - {issue.message}")
            if len(issues) > 10:
                lines.append(f"- *... and {len(issues) - 10} more*")
            lines.append("")

    # Errors
    if result.errors:
        lines.extend(["## Errors", ""])
        for error in result.errors:
            lines.append(f"- {error}")
        lines.append("")

    return "\n".join(lines)


def scan_code_quality(directory: str) -> str:
    """MCP tool: Scan directory for code quality issues.

    Performs AST-based analysis for pe_rules compliance:
    - Exception handling (bare except, except Exception)
    - Type hints on functions
    - Docstring completeness
    - Import organization
    - Logging best practices

    Args:
        directory: Path to directory to scan.

    Returns:
        Status message with path to generated report.
    """
    result = scan_directory(directory)
    report_content = format_report(result, directory)

    # Write report
    try:
        report_path = write_report(
            agent="platform_engineer",
            report_name="code_quality",
            content=report_content,
            title="Code Quality Report",
        )
        status = "🛑 CRITICAL" if result.critical_count > 0 else "✅ PASS"
        return (
            f"{status} Code quality scan complete.\n\n"
            f"**Files:** {result.files_scanned} | "
            f"**Critical:** {result.critical_count} | "
            f"**High:** {result.high_count} | "
            f"**Medium:** {result.medium_count}\n\n"
            f"Report: `{report_path}`"
        )
    except OSError as e:
        return f"Scan complete but failed to save report: {e}\n\n{report_content}"
