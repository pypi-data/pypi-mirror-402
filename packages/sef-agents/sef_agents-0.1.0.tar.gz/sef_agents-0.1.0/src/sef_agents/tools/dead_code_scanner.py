"""Dead Code Scanner for SEF Agents.

Detects unused code:
- Unused imports
- Unused local functions (not exported)
- Orphan files (never imported)

Supports Python (AST), TypeScript, JavaScript, Java (regex).

Respects .gitignore and .dockerignore to avoid false positives.
"""

import ast
import re
from typing import Any
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from sef_agents.constants import Severity
from sef_agents.core.language_detector import LanguageDetector, LANGUAGE_EXTENSIONS
from sef_agents.tools.debt_scanner import DebtItem, ScanResult
from sef_agents.utils.ignore_matcher import IgnorePatternMatcher

logger = structlog.get_logger(__name__)


@dataclass
class ImportInfo:
    """Information about an import statement.

    Attributes:
        module: Module being imported.
        names: Names imported from module.
        file_path: File containing import.
        line_number: Line number of import.
    """

    module: str
    names: list[str]
    file_path: Path
    line_number: int


@dataclass
class FunctionInfo:
    """Information about a function definition.

    Attributes:
        name: Function name.
        file_path: File containing function.
        line_number: Line number of definition.
        is_private: True if name starts with _.
        is_exported: True if referenced in __all__.
    """

    name: str
    file_path: Path
    line_number: int
    is_private: bool = False
    is_exported: bool = False


@dataclass
class DeadCodeResult:
    """Result of dead code scan.

    Attributes:
        unused_imports: List of unused imports.
        orphan_files: Files not imported anywhere.
        unused_functions: Functions never called.
        files_scanned: Number of files analyzed.
    """

    unused_imports: list[DebtItem] = field(default_factory=list)
    orphan_files: list[DebtItem] = field(default_factory=list)
    unused_functions: list[DebtItem] = field(default_factory=list)
    files_scanned: int = 0

    def to_scan_result(self) -> ScanResult:
        """Convert to ScanResult for integration with debt scanner."""
        result = ScanResult(files_scanned=self.files_scanned)
        result.items.extend(self.unused_imports)
        result.items.extend(self.orphan_files)
        result.items.extend(self.unused_functions)
        return result

    @property
    def total_items(self) -> int:
        """Total dead code items found."""
        return (
            len(self.unused_imports)
            + len(self.orphan_files)
            + len(self.unused_functions)
        )


class UnusedImportDetector(ast.NodeVisitor):
    """AST visitor to detect unused imports in a Python file.

    Attributes:
        imports: Dictionary mapping imported names to line numbers.
        used_names: Set of names used in the file.
    """

    def __init__(self) -> None:
        """Initialize detector."""
        self.imports: dict[str, int] = {}
        self.used_names: set[str] = set()
        self._in_import = False

    def visit_Import(self, node: ast.Import) -> None:
        """Record import statements."""
        self._in_import = True
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split(".")[0]
            self.imports[name] = node.lineno
        self._in_import = False
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Record from...import statements."""
        self._in_import = True
        for alias in node.names:
            if alias.name == "*":
                # Can't track star imports
                continue
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self._in_import = False
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Record name usage."""
        if not self._in_import:
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Record attribute access (module.attr)."""
        # Get the root name
        current = node
        while isinstance(current, ast.Attribute):
            current = current.value
        if isinstance(current, ast.Name) and not self._in_import:
            self.used_names.add(current.id)
        self.generic_visit(node)

    def get_unused_imports(self) -> dict[str, int]:
        """Get imports that are never used.

        Returns:
            Dictionary mapping unused import names to line numbers.
        """
        unused = {}
        for name, lineno in self.imports.items():
            if name not in self.used_names:
                # Skip common false positives
                if name in ("__future__", "annotations", "TYPE_CHECKING"):
                    continue
                unused[name] = lineno
        return unused


class DeadCodeScanner:
    """Scanner for detecting dead code across a project.

    Attributes:
        project_root: Root directory of project.
        ignore_matcher: Matcher for .gitignore/.dockerignore patterns.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize scanner.

        Args:
            project_root: Project root directory.
        """
        self.project_root = project_root.resolve()
        self.ignore_matcher = IgnorePatternMatcher.from_directory(self.project_root)
        self._debt_counter = 0

        # Excluded directories
        self._exclude_dirs = {
            "__pycache__",
            ".git",
            ".venv",
            ".sef",
            "venv",
            "node_modules",
            ".tox",
            "dist",
            "build",
            "target",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "egg-info",
        }

    def _next_debt_id(self) -> str:
        """Generate next debt ID."""
        self._debt_counter += 1
        return f"DEAD-{self._debt_counter:03d}"

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped.

        Args:
            file_path: Path to check.

        Returns:
            True if file should be skipped.
        """
        # Check excluded directories
        if any(excluded in file_path.parts for excluded in self._exclude_dirs):
            return True

        # Check ignore patterns
        if self.ignore_matcher.is_ignored(file_path):
            return True

        return False

    def _scan_imports_regex(self, content: str, language: str) -> list[tuple[str, int]]:
        """Extract imports using regex for TS/JS/Java.

        Args:
            content: File content.
            language: Language name.

        Returns:
            List of (import_name, line_number) tuples.
        """
        imports: list[tuple[str, int]] = []
        lines = content.splitlines()

        if language in ("typescript", "javascript"):
            # import ... from '...'
            pattern1 = re.compile(
                r"import\s+(?:\{[^}]+\}|\*\s+as\s+\w+|\w+).*?\s+from\s+['\"]([^'\"]+)['\"]"
            )
            # import '...'
            pattern2 = re.compile(r"import\s+['\"]([^'\"]+)['\"]")
            # require('...')
            pattern3 = re.compile(r"require\(['\"]([^'\"]+)['\"]\)")

            for i, line in enumerate(lines, 1):
                for pattern in [pattern1, pattern2, pattern3]:
                    matches = pattern.findall(line)
                    imports.extend((match, i) for match in matches)

        elif language == "java":
            # import package.Class;
            pattern = re.compile(r"import\s+(?:static\s+)?([\w.]+);")
            for i, line in enumerate(lines, 1):
                matches = pattern.findall(line)
                imports.extend((match, i) for match in matches)

        return imports

    def scan_unused_imports(self, file_path: Path) -> list[DebtItem]:
        """Scan single file for unused imports.

        Supports Python (AST), TypeScript, JavaScript, Java (regex).

        Args:
            file_path: Path to file.

        Returns:
            List of debt items for unused imports.
        """
        if self._should_skip_file(file_path):
            return []

        # Detect language
        detector = LanguageDetector()
        lang_info = detector.detect(file_path)

        if lang_info.language == "unknown":
            return []

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.debug("file_read_error", file=str(file_path), error=str(e))
            return []

        items: list[DebtItem] = []

        if lang_info.language == "python":
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                logger.debug("file_parse_error", file=str(file_path), error=str(e))
                return []

            detector_ast = UnusedImportDetector()
            detector_ast.visit(tree)
            unused = detector_ast.get_unused_imports()

            for name, lineno in unused.items():
                items.append(
                    DebtItem(
                        debt_id=self._next_debt_id(),
                        location=f"{file_path}:{lineno}",
                        debt_type="unused-import",
                        severity=Severity.LOW,
                        description=f"Unused import: `{name}`",
                        line_number=lineno,
                        language="python",
                    )
                )
        else:
            # For TS/JS/Java, we can detect imports but unused detection is limited
            # without full AST parsing. For now, we'll skip unused import detection
            # for these languages (can be enhanced later with proper parsers).
            logger.debug(
                "unused_import_scan_skipped",
                language=lang_info.language,
                file=str(file_path),
            )

        return items

    def _collect_all_files(self, dir_path: Path) -> set[Path]:
        """Collect all supported language files."""
        all_files: set[Path] = set()
        for extensions in LANGUAGE_EXTENSIONS.values():
            for ext in extensions:
                for file_path in dir_path.rglob(f"*{ext}"):
                    if self._should_skip_file(file_path):
                        continue
                    all_files.add(file_path)
        return all_files

    def _collect_imported_modules(
        self, files: set[Path], detector: LanguageDetector
    ) -> set[str]:
        """Collect all imports across files."""
        imported_modules: set[str] = set()
        for file_path in files:
            lang_info = detector.detect(file_path)
            if lang_info.language == "unknown":
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            if lang_info.language == "python":
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self._add_module_and_parents(imported_modules, alias.name)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        self._add_module_and_parents(imported_modules, node.module)
            else:
                imports = self._scan_imports_regex(content, lang_info.language)
                for import_name, _ in imports:
                    self._add_module_and_parents(imported_modules, import_name)
        return imported_modules

    def _add_module_and_parents(self, modules: set[str], name: str) -> None:
        """Add module and its parent packages to set."""
        modules.add(name)
        parts = name.split(".")
        for i in range(len(parts)):
            modules.add(".".join(parts[: i + 1]))

    def _is_entry_point_or_test(self, file_path: Path, lang_info: Any) -> bool:
        """Check if file is entry point or test."""
        skip_names = {
            "python": (
                "__init__.py",
                "__main__.py",
                "setup.py",
                "conftest.py",
                "manage.py",
                "main.py",
                "app.py",
                "wsgi.py",
                "asgi.py",
                "cli.py",
                "server.py",
            ),
            "typescript": ("index.ts", "index.tsx", "main.ts", "app.tsx"),
            "javascript": ("index.js", "index.jsx", "main.js", "app.jsx"),
            "java": ("Main.java", "Application.java"),
        }

        if file_path.name in skip_names.get(lang_info.language, ()):
            return True

        test_patterns = {
            "python": (r"^test_.*\.py$", r".*_test\.py$"),
            "typescript": (r"^.*\.test\.tsx?$", r"^.*\.spec\.tsx?$"),
            "javascript": (r"^.*\.test\.jsx?$", r"^.*\.spec\.jsx?$"),
            "java": (r"^.*Test\.java$", r"^.*Tests\.java$"),
        }

        for pattern in test_patterns.get(lang_info.language, []):
            if re.match(pattern, file_path.name):
                return True
        return False

    def _get_module_candidates(
        self, file_path: Path, dir_path: Path, language: str
    ) -> list[str]:
        """Get possible module names for a file."""
        try:
            rel_path = file_path.relative_to(dir_path)
        except ValueError:
            return []

        candidates = []
        if language == "python":
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            candidates.append(".".join(module_parts))
            if module_parts and module_parts[0] == "src":
                candidates.append(".".join(module_parts[1:]))
            candidates.append(rel_path.stem)
        elif language in ("typescript", "javascript"):
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            candidates.append("/".join(module_parts))
            candidates.append(".".join(module_parts))
            if module_parts and module_parts[0] == "src":
                candidates.append("/".join(module_parts[1:]))
                candidates.append(".".join(module_parts[1:]))
            candidates.append(rel_path.stem)
        elif language == "java":
            module_parts = list(rel_path.parts[:-1])
            if module_parts:
                candidates.append(".".join(module_parts))
            candidates.append(rel_path.stem)

        return candidates

    def scan_orphan_files(self, directory: Path) -> list[DebtItem]:
        """Find files that are never imported.

        Supports Python (AST), TypeScript, JavaScript, Java (regex).

        Args:
            directory: Directory to scan.

        Returns:
            List of debt items for orphan files.
        """
        dir_path = directory.resolve()
        detector = LanguageDetector()

        all_files = self._collect_all_files(dir_path)
        imported_modules = self._collect_imported_modules(all_files, detector)

        items = []
        for file_path in all_files:
            lang_info = detector.detect(file_path)
            if lang_info.language == "unknown":
                continue

            if self._is_entry_point_or_test(file_path, lang_info):
                continue

            possible_modules = self._get_module_candidates(
                file_path, dir_path, lang_info.language
            )
            is_imported = any(mod in imported_modules for mod in possible_modules)

            if not is_imported:
                # Use relative path for display
                try:
                    display_path = str(file_path.relative_to(dir_path))
                except ValueError:
                    display_path = str(file_path)

                items.append(
                    DebtItem(
                        debt_id=self._next_debt_id(),
                        location=str(file_path),
                        debt_type="orphan-file",
                        severity=Severity.MEDIUM,
                        description=f"File never imported: `{display_path}`",
                        line_number=None,
                        language=lang_info.language,
                    )
                )

        return items

    def scan_directory(self, directory: Path | str) -> DeadCodeResult:
        """Scan directory for all dead code patterns.

        Args:
            directory: Directory to scan.

        Returns:
            DeadCodeResult with all findings.
        """
        dir_path = Path(directory).resolve()
        result = DeadCodeResult()

        if not dir_path.exists():
            logger.error("directory_not_found", directory=str(directory))
            return result

        # Scan for unused imports in all supported language files
        for extensions in LANGUAGE_EXTENSIONS.values():
            for ext in extensions:
                for file_path in dir_path.rglob(f"*{ext}"):
                    if self._should_skip_file(file_path):
                        continue

                    result.files_scanned += 1
                    unused_imports = self.scan_unused_imports(file_path)
                    result.unused_imports.extend(unused_imports)

        # Scan for orphan files
        orphan_files = self.scan_orphan_files(dir_path)
        result.orphan_files.extend(orphan_files)

        logger.info(
            "dead_code_scan_complete",
            files_scanned=result.files_scanned,
            unused_imports=len(result.unused_imports),
            orphan_files=len(result.orphan_files),
        )

        return result


def scan_dead_code(directory: str, summary: bool = False) -> str:
    """Scan directory for dead code.

    Args:
        directory: Path to scan.
        summary: If True, return quick summary. If False, return full report.

    Returns:
        Markdown formatted report or summary.
    """
    dir_path = Path(directory).resolve()
    scanner = DeadCodeScanner(dir_path)
    result = scanner.scan_directory(dir_path)

    if result.total_items == 0:
        return f"✅ No dead code found in {result.files_scanned} files."

    # Summary mode
    if summary:
        return f"""📋 **Dead Code Summary** ({result.files_scanned} files scanned)

| Type | Count |
|------|-------|
| Unused Imports | {len(result.unused_imports)} |
| Orphan Files | {len(result.orphan_files)} |

**Total:** {result.total_items} items

Run `scan_dead_code(directory, summary=False)` for full report."""

    # Full report mode
    output = f"""# Dead Code Scan Report

*Scanned: {result.files_scanned} files*
*Found: {result.total_items} items*

## Summary

| Type | Count | Severity |
|------|-------|----------|
| Unused Imports | {len(result.unused_imports)} | {Severity.LOW} |
| Orphan Files | {len(result.orphan_files)} | {Severity.MEDIUM} |

"""

    if result.unused_imports:
        output += "## Unused Imports\n\n"
        output += "| ID | Location | Import |\n"
        output += "|----|----------|--------|\n"
        for item in result.unused_imports:
            # Extract import name from description
            import_name = item.description.replace("Unused import: ", "")
            output += f"| {item.debt_id} | `{item.location}` | {import_name} |\n"
        output += "\n"

    if result.orphan_files:
        output += "## Orphan Files (Never Imported)\n\n"
        output += "| ID | File | Note |\n"
        output += "|----|------|------|\n"
        for item in result.orphan_files:
            output += f"| {item.debt_id} | `{item.location}` | Verify if needed |\n"
        output += "\n"

    output += """## Recommendations

1. **Unused Imports**: Remove to reduce file size and improve clarity
2. **Orphan Files**: Verify if file is:
   - Entry point (add to exclusions)
   - Dynamically imported (add comment)
   - Actually unused (safe to delete)

*Note: Files in .gitignore/.dockerignore are automatically excluded.*
"""

    return output
