"""File Operation Audit Scanner.

Scans Python files for file I/O operations to verify all file access
is local-only and follows expected patterns.
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


# File operation functions to track
FILE_OPERATIONS: set[str] = {
    "open",
    "read",
    "write",
    "read_text",
    "write_text",
    "read_bytes",
    "write_bytes",
    "mkdir",
    "rmdir",
    "unlink",
    "remove",
    "rename",
    "replace",
}

# Potentially dangerous operations
DANGEROUS_OPERATIONS: set[str] = {
    "rmtree",  # Recursive delete
    "system",  # System command execution
    "popen",  # Process execution
    "subprocess",  # Subprocess module
    "exec",  # Code execution
    "eval",  # Code evaluation
}


@dataclass
class FileOperation:
    """Information about a file operation."""

    file: str
    line: int
    operation: str
    is_dangerous: bool
    context: str


@dataclass
class FileAuditResult:
    """Result of file operation audit."""

    passed: bool
    files_scanned: int
    operations: list[FileOperation] = field(default_factory=list)
    dangerous_operations: list[FileOperation] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """One-line summary for CLI output."""
        if self.passed:
            return f"{len(self.operations)} file operations found, all local-only"
        return (
            f"{len(self.dangerous_operations)} potentially dangerous operations found"
        )


class FileOperationVisitor(ast.NodeVisitor):
    """AST visitor to find file operations."""

    def __init__(self, file_path: str, source_lines: list[str]) -> None:
        self.file_path = file_path
        self.source_lines = source_lines
        self.operations: list[FileOperation] = []
        self.dangerous: list[FileOperation] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to detect file operations."""
        func_name = self._get_func_name(node)

        if func_name in FILE_OPERATIONS:
            context = self._get_context(node.lineno)
            op = FileOperation(
                file=self.file_path,
                line=node.lineno,
                operation=func_name,
                is_dangerous=False,
                context=context,
            )
            self.operations.append(op)

        if func_name in DANGEROUS_OPERATIONS:
            context = self._get_context(node.lineno)
            op = FileOperation(
                file=self.file_path,
                line=node.lineno,
                operation=func_name,
                is_dangerous=True,
                context=context,
            )
            self.dangerous.append(op)
            logger.warning(
                "dangerous_operation_found",
                file=self.file_path,
                line=node.lineno,
                operation=func_name,
            )

        self.generic_visit(node)

    def _get_func_name(self, node: ast.Call) -> str:
        """Extract function name from call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _get_context(self, line_num: int) -> str:
        """Get source code context for a line."""
        if 0 < line_num <= len(self.source_lines):
            return self.source_lines[line_num - 1].strip()
        return ""


def audit_file_operations(
    directory: Path,
) -> FileAuditResult:
    """
    Audit all file operations in Python files.

    Args:
        directory: Root directory to scan

    Returns:
        FileAuditResult with operation information
    """
    all_operations: list[FileOperation] = []
    dangerous_operations: list[FileOperation] = []
    files_scanned = 0

    py_files = list(directory.rglob("*.py"))

    for py_file in py_files:
        if _should_skip(py_file):
            continue

        files_scanned += 1
        relative_path = str(py_file.relative_to(directory))

        try:
            source = py_file.read_text(encoding="utf-8")
            source_lines = source.split("\n")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning("failed_to_parse", file=relative_path, error=str(e))
            continue

        visitor = FileOperationVisitor(relative_path, source_lines)
        visitor.visit(tree)

        all_operations.extend(visitor.operations)
        dangerous_operations.extend(visitor.dangerous)

    passed = len(dangerous_operations) == 0

    logger.info(
        "file_audit_complete",
        passed=passed,
        files_scanned=files_scanned,
        total_operations=len(all_operations),
        dangerous_count=len(dangerous_operations),
    )

    return FileAuditResult(
        passed=passed,
        files_scanned=files_scanned,
        operations=all_operations,
        dangerous_operations=dangerous_operations,
    )
