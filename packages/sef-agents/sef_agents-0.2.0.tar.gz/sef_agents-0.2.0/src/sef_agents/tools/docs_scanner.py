"""Documentation Quality Scanner for SEF Agents.

Scans code for documentation anti-patterns based on the Curator Protocol.
Detects code-echoing comments, missing docstrings, incomplete contracts.

Usage:
    from sef_agents.tools.docs_scanner import scan_docs
    report = scan_docs(Path("/path/to/project"))

Dependencies:
    - structlog for logging
    - pathlib for file operations
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from sef_agents.constants import Severity, Status
from sef_agents.tools.report_utils import write_report

logger = structlog.get_logger(__name__)

# Code-echoing patterns (comments that restate the code)
CODE_ECHO_PATTERNS: list[tuple[str, str]] = [
    (r"#\s*increment\s+\w+", "Redundant 'increment' comment"),
    (r"#\s*decrement\s+\w+", "Redundant 'decrement' comment"),
    (r"#\s*return\s+(true|false|none|null)", "Redundant return comment"),
    (r"#\s*set\s+\w+\s*(to|=)", "Redundant assignment comment"),
    (r"#\s*get\s+\w+", "Redundant getter comment"),
    (r"#\s*call\s+\w+", "Redundant call comment"),
    (r"#\s*create\s+(new\s+)?\w+", "Redundant instantiation comment"),
    (r"#\s*initialize", "Redundant init comment"),
    (r"#\s*constructor", "Redundant constructor comment"),
    (r"#\s*loop\s+(through|over)", "Redundant loop comment"),
    (r"#\s*iterate", "Redundant iteration comment"),
    (r"#\s*check\s+if", "Redundant conditional comment"),
    (r"#\s*import\s+\w+", "Redundant import comment"),
    (r"//\s*increment\s+\w+", "Redundant 'increment' comment"),
    (r"//\s*return\s+(true|false|null)", "Redundant return comment"),
    (r"//\s*get\s+\w+", "Redundant getter comment"),
    (r"/\*\*?\s*constructor\s*\*/", "Redundant constructor comment"),
]

# Placeholder docstring patterns
PLACEHOLDER_PATTERNS: list[tuple[str, str]] = [
    (r'"""TODO"""', "Placeholder TODO docstring"),
    (r"'''TODO'''", "Placeholder TODO docstring"),
    (r'""""""', "Empty docstring"),
    (r"''''''", "Empty docstring"),
    (r'"""[.]{3}"""', "Ellipsis placeholder docstring"),
    (r"/\*\*\s*TODO\s*\*/", "Placeholder TODO Javadoc"),
    (r"/\*\*\s*\*/", "Empty Javadoc"),
]

# File extensions by language
LANGUAGE_EXTENSIONS: dict[str, list[str]] = {
    "python": [".py"],
    "typescript": [".ts", ".tsx"],
    "javascript": [".js", ".jsx"],
    "java": [".java"],
    "yaml": [".yaml", ".yml"],
    "markdown": [".md"],
}


@dataclass
class DocIssue:
    """Single documentation issue.

    Attributes:
        file_path: Path to file with issue.
        line: Line number (1-indexed).
        issue_type: Category of issue.
        severity: Issue severity.
        message: Human-readable description.
        suggestion: Recommended fix.
    """

    file_path: str
    line: int
    issue_type: str
    severity: str
    message: str
    suggestion: str

    def to_dict(self) -> dict[str, str | int]:
        """Convert to dictionary."""
        return {
            "file": self.file_path,
            "line": self.line,
            "type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class DocScanResult:
    """Result of documentation scan.

    Attributes:
        files_scanned: Number of files analyzed.
        issues: List of documentation issues found.
        languages: Languages detected.
    """

    files_scanned: int = 0
    issues: list[DocIssue] = field(default_factory=list)
    languages: set[str] = field(default_factory=set)

    @property
    def by_severity(self) -> dict[str, int]:
        """Count issues by severity."""
        counts = {
            Severity.HIGH: 0,
            Severity.MEDIUM: 0,
            Severity.LOW: 0,
        }
        for issue in self.issues:
            if issue.severity in counts:
                counts[issue.severity] += 1
        return counts

    @property
    def by_type(self) -> dict[str, int]:
        """Count issues by type."""
        counts: dict[str, int] = {}
        for issue in self.issues:
            counts[issue.issue_type] = counts.get(issue.issue_type, 0) + 1
        return counts


class DocScanner:
    """Documentation quality scanner.

    Scans Python, TypeScript, Java, YAML, and Markdown files for
    documentation anti-patterns.
    """

    def __init__(self) -> None:
        """Initialize scanner with compiled patterns."""
        self._code_echo_patterns = [
            (re.compile(p, re.IGNORECASE), msg) for p, msg in CODE_ECHO_PATTERNS
        ]
        self._placeholder_patterns = [
            (re.compile(p, re.IGNORECASE), msg) for p, msg in PLACEHOLDER_PATTERNS
        ]

    def scan_directory(self, directory: Path) -> DocScanResult:
        """Scan directory for documentation issues.

        Args:
            directory: Root directory to scan.

        Returns:
            DocScanResult with all issues found.
        """
        result = DocScanResult()

        for ext_list in LANGUAGE_EXTENSIONS.values():
            for ext in ext_list:
                for file_path in directory.rglob(f"*{ext}"):
                    if self._should_skip(file_path):
                        continue
                    self._scan_file(file_path, result)

        return result

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = {
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        }
        return any(part in skip_dirs for part in file_path.parts)

    def _scan_file(self, file_path: Path, result: DocScanResult) -> None:
        """Scan single file for issues."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("file_read_error", path=str(file_path), error=str(e))
            return

        result.files_scanned += 1
        suffix = file_path.suffix.lower()

        # Detect language
        for lang, exts in LANGUAGE_EXTENSIONS.items():
            if suffix in exts:
                result.languages.add(lang)
                break

        # Universal checks (all languages)
        self._check_code_echo(file_path, content, result)
        self._check_placeholders(file_path, content, result)

        # Language-specific checks
        if suffix == ".py":
            self._scan_python(file_path, content, result)
        elif suffix in (".ts", ".tsx", ".js", ".jsx"):
            self._scan_typescript(file_path, content, result)
        elif suffix == ".java":
            self._scan_java(file_path, content, result)
        elif suffix in (".yaml", ".yml"):
            self._scan_yaml(file_path, content, result)
        elif suffix == ".md":
            self._scan_markdown(file_path, content, result)

    def _check_code_echo(
        self, file_path: Path, content: str, result: DocScanResult
    ) -> None:
        """Check for code-echoing comments."""
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, message in self._code_echo_patterns:
                if pattern.search(line):
                    result.issues.append(
                        DocIssue(
                            file_path=str(file_path),
                            line=i,
                            issue_type="code-echo",
                            severity=Severity.MEDIUM,
                            message=message,
                            suggestion="Remove or explain WHY, not WHAT.",
                        )
                    )
                    break  # One issue per line

    def _check_placeholders(
        self, file_path: Path, content: str, result: DocScanResult
    ) -> None:
        """Check for placeholder docstrings."""
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, message in self._placeholder_patterns:
                if pattern.search(line):
                    result.issues.append(
                        DocIssue(
                            file_path=str(file_path),
                            line=i,
                            issue_type="placeholder",
                            severity=Severity.HIGH,
                            message=message,
                            suggestion="Replace with proper docstring or remove.",
                        )
                    )
                    break

    def _scan_python(
        self, file_path: Path, content: str, result: DocScanResult
    ) -> None:
        """Scan Python file for documentation issues."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        # Check module docstring
        if not ast.get_docstring(tree):
            result.issues.append(
                DocIssue(
                    file_path=str(file_path),
                    line=1,
                    issue_type="missing-module-doc",
                    severity=Severity.MEDIUM,
                    message="Missing module docstring",
                    suggestion="Add module docstring with Purpose, Usage, Dependencies.",
                )
            )

        # Check functions and classes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_python_function(file_path, node, result)
            elif isinstance(node, ast.ClassDef):
                self._check_python_class(file_path, node, result)

    def _check_python_function(
        self,
        file_path: Path,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        result: DocScanResult,
    ) -> None:
        """Check Python function documentation."""
        # Skip private/dunder methods for docstring requirement
        if node.name.startswith("_") and not node.name.startswith("__"):
            return

        docstring = ast.get_docstring(node)

        # Check for missing docstring on public functions
        if not docstring and not node.name.startswith("_"):
            # Skip simple one-liners
            if len(node.body) > 1 or not isinstance(node.body[0], ast.Return):
                result.issues.append(
                    DocIssue(
                        file_path=str(file_path),
                        line=node.lineno,
                        issue_type="missing-docstring",
                        severity=Severity.MEDIUM,
                        message=f"Function `{node.name}` missing docstring",
                        suggestion="Add docstring with Args, Returns, Raises.",
                    )
                )
            return

        if not docstring:
            return

        # Check docstring completeness
        has_args = bool(node.args.args) and not all(
            arg.arg == "self" for arg in node.args.args
        )
        has_return = any(isinstance(n, ast.Return) and n.value for n in ast.walk(node))

        if has_args and "Args:" not in docstring and "Parameters:" not in docstring:
            result.issues.append(
                DocIssue(
                    file_path=str(file_path),
                    line=node.lineno,
                    issue_type="incomplete-docstring",
                    severity=Severity.LOW,
                    message=f"`{node.name}` docstring missing Args section",
                    suggestion="Document function parameters.",
                )
            )

        if has_return and "Returns:" not in docstring and "Return:" not in docstring:
            result.issues.append(
                DocIssue(
                    file_path=str(file_path),
                    line=node.lineno,
                    issue_type="incomplete-docstring",
                    severity=Severity.LOW,
                    message=f"`{node.name}` docstring missing Returns section",
                    suggestion="Document return value.",
                )
            )

    def _check_python_class(
        self, file_path: Path, node: ast.ClassDef, result: DocScanResult
    ) -> None:
        """Check Python class documentation."""
        docstring = ast.get_docstring(node)

        if not docstring:
            result.issues.append(
                DocIssue(
                    file_path=str(file_path),
                    line=node.lineno,
                    issue_type="missing-docstring",
                    severity=Severity.MEDIUM,
                    message=f"Class `{node.name}` missing docstring",
                    suggestion="Add docstring with purpose and Attributes.",
                )
            )

    def _scan_typescript(
        self, file_path: Path, content: str, result: DocScanResult
    ) -> None:
        """Scan TypeScript/JavaScript for documentation issues."""
        lines = content.split("\n")

        # Check for exported functions without JSDoc
        func_pattern = re.compile(
            r"^export\s+(async\s+)?function\s+(\w+)|"
            r"^export\s+const\s+(\w+)\s*=\s*(async\s+)?\("
        )

        for i, line in enumerate(lines):
            if func_pattern.match(line.strip()):
                has_jsdoc = False
                for j in range(i - 1, max(0, i - 5), -1):
                    prev_line = lines[j].strip()
                    if prev_line.endswith("*/"):
                        has_jsdoc = True
                        break
                    if prev_line and not prev_line.startswith("//"):
                        break

                if not has_jsdoc:
                    func_match = func_pattern.match(line.strip())
                    func_name = func_match.group(2) or func_match.group(3)
                    result.issues.append(
                        DocIssue(
                            file_path=str(file_path),
                            line=i + 1,
                            issue_type="missing-jsdoc",
                            severity=Severity.MEDIUM,
                            message=f"Exported function `{func_name}` missing JSDoc",
                            suggestion="Add JSDoc with @param, @returns, @throws.",
                        )
                    )

    def _scan_java(self, file_path: Path, content: str, result: DocScanResult) -> None:
        """Scan Java for documentation issues."""
        lines = content.split("\n")

        # Check for public methods without Javadoc
        method_pattern = re.compile(r"^\s*public\s+(?!class)(\w+)\s+(\w+)\s*\(")

        for i, line in enumerate(lines):
            method_match = method_pattern.match(line)
            if method_match:
                # Check for preceding Javadoc
                has_javadoc = False
                for j in range(i - 1, max(0, i - 10), -1):
                    prev_line = lines[j].strip()
                    if prev_line.endswith("*/"):
                        has_javadoc = True
                        break
                    if prev_line and not prev_line.startswith("*"):
                        break

                if not has_javadoc:
                    method_name = method_match.group(2)
                    result.issues.append(
                        DocIssue(
                            file_path=str(file_path),
                            line=i + 1,
                            issue_type="missing-javadoc",
                            severity=Severity.MEDIUM,
                            message=f"Public method `{method_name}` missing Javadoc",
                            suggestion="Add Javadoc with @param, @return, @throws.",
                        )
                    )

    def _scan_yaml(self, file_path: Path, content: str, result: DocScanResult) -> None:
        """Scan YAML for documentation issues."""
        lines = content.split("\n")

        # Check for file header comment
        if lines and not lines[0].strip().startswith("#"):
            result.issues.append(
                DocIssue(
                    file_path=str(file_path),
                    line=1,
                    issue_type="missing-header",
                    severity=Severity.LOW,
                    message="YAML file missing header comment",
                    suggestion="Add comment explaining config purpose.",
                )
            )

    def _scan_markdown(
        self, file_path: Path, content: str, result: DocScanResult
    ) -> None:
        """Scan Markdown for documentation issues."""
        lines = content.split("\n")

        # Check for H1 header
        has_h1 = any(line.strip().startswith("# ") for line in lines[:10])
        if not has_h1:
            result.issues.append(
                DocIssue(
                    file_path=str(file_path),
                    line=1,
                    issue_type="missing-h1",
                    severity=Severity.LOW,
                    message="Markdown file missing H1 title",
                    suggestion="Add # Title at start of file.",
                )
            )


def scan_docs(directory: Path) -> DocScanResult:
    """Scan directory for documentation issues.

    Args:
        directory: Root directory to scan.

    Returns:
        DocScanResult with all issues found.
    """
    scanner = DocScanner()
    return scanner.scan_directory(directory)


def generate_docs_report(result: DocScanResult, directory: Path) -> str:
    """Generate markdown report from scan result.

    Args:
        result: Scan result to format.
        directory: Scanned directory (for report header).

    Returns:
        Formatted markdown report.
    """
    lines = [
        "# Documentation Quality Report",
        "",
        f"**Directory:** `{directory}`",
        f"**Files Scanned:** {result.files_scanned}",
        f"**Languages:** {', '.join(sorted(result.languages)) or 'None detected'}",
        "",
        "## Summary",
        "",
        "| Severity | Count |",
        "|----------|-------|",
    ]

    for severity, count in result.by_severity.items():
        lines.append(f"| {severity} | {count} |")

    lines.extend(
        [
            "",
            f"**Total Issues:** {len(result.issues)}",
            "",
        ]
    )

    if not result.issues:
        lines.append(f"{Status.SUCCESS} **No documentation issues found.**")
        return "\n".join(lines)

    # Group by type
    lines.extend(["## Issues by Type", ""])

    for issue_type, count in sorted(result.by_type.items()):
        lines.append(f"### {issue_type} ({count})")
        lines.append("")
        lines.append("| File | Line | Message | Suggestion |")
        lines.append("|------|------|---------|------------|")

        type_issues = [i for i in result.issues if i.issue_type == issue_type]
        for issue in type_issues[:50]:  # Limit per type
            file_short = Path(issue.file_path).name
            lines.append(
                f"| `{file_short}` | {issue.line} | {issue.message} | {issue.suggestion} |"
            )

        if len(type_issues) > 50:
            lines.append(f"| ... | ... | *{len(type_issues) - 50} more* | ... |")

        lines.append("")

    return "\n".join(lines)


def validate_docs_tool(directory: str) -> str:
    """MCP tool: Scan documentation quality.

    Scans Python, TypeScript, Java, YAML, and Markdown files
    for documentation anti-patterns.

    Args:
        directory: Path to directory to scan.

    Returns:
        Summary of documentation issues.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return f"{Status.ERROR} Directory not found: {directory}"

    result = scan_docs(dir_path)
    report_content = generate_docs_report(result, dir_path)

    # Save report
    report_path = write_report(
        agent="docs_curator",
        report_name="docs_quality",
        content=report_content,
        title="Documentation Quality Report",
    )

    if not result.issues:
        return f"{Status.SUCCESS} No documentation issues found in {result.files_scanned} files."

    by_sev = result.by_severity
    return (
        f"{Status.WARNING} Found {len(result.issues)} documentation issues:\n"
        f"  {Severity.HIGH_ICON} High: {by_sev.get(Severity.HIGH, 0)}\n"
        f"  {Severity.MEDIUM_ICON} Medium: {by_sev.get(Severity.MEDIUM, 0)}\n"
        f"  {Severity.LOW_ICON} Low: {by_sev.get(Severity.LOW, 0)}\n\n"
        f"Report: {report_path}"
    )
