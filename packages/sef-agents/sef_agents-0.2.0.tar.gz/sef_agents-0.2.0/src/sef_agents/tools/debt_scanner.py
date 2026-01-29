"""Technical Debt Scanner for SEF Agents.

Multi-language debt scanner supporting:
- Python, TypeScript, JavaScript, Java
- React, Angular, Spring Boot frameworks

Uses configurable YAML rules for extensibility.
Supports incremental scanning and checkpoint-based resume.
"""

import ast
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from sef_agents.constants import Severity
from sef_agents.core.config_loader import ConfigLoader, LanguageConfig
from sef_agents.core.language_detector import LanguageDetector, LanguageInfo
from sef_agents.utils.git_utils import get_changed_files, is_git_repo

logger = structlog.get_logger(__name__)

# Cache and checkpoint file names
CACHE_FILE = "debt_cache.json"
CHECKPOINT_FILE = "debt_checkpoint.json"


@dataclass
class DebtItem:
    """Represents a technical debt item.

    Attributes:
        debt_id: Unique identifier.
        location: File path and line number.
        debt_type: Category of debt.
        severity: Severity level.
        description: Detailed description.
        line_number: Line number in file.
        language: Source language.
    """

    debt_id: str
    location: str
    debt_type: str
    severity: str
    description: str
    line_number: int | None = None
    language: str = "python"

    def to_dict(self) -> dict[str, str | int | None]:
        """Convert to dictionary."""
        return {
            "id": self.debt_id,
            "location": self.location,
            "type": self.debt_type,
            "severity": self.severity,
            "description": self.description,
            "line": self.line_number,
            "language": self.language,
        }

    def to_markdown_row(self) -> str:
        """Format as TECH_DEBT.md table row."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return (
            f"| {self.debt_id} | `{self.location}` | {self.debt_type} | "
            f"{self.severity} | - | Open | Scanner | {today} |"
        )


@dataclass
class ScanResult:
    """Result of debt scan.

    Attributes:
        items: List of debt items found.
        files_scanned: Number of files scanned.
        errors: List of errors encountered.
        languages: Languages detected.
    """

    items: list[DebtItem] = field(default_factory=list)
    files_scanned: int = 0
    errors: list[str] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)

    @property
    def by_type(self) -> dict[str, list[DebtItem]]:
        """Group items by debt type."""
        grouped: dict[str, list[DebtItem]] = {}
        for item in self.items:
            if item.debt_type not in grouped:
                grouped[item.debt_type] = []
            grouped[item.debt_type].append(item)
        return grouped

    @property
    def by_severity(self) -> dict[str, int]:
        """Count items by severity."""
        counts: dict[str, int] = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 0,
            Severity.MEDIUM: 0,
            Severity.LOW: 0,
        }
        for item in self.items:
            if item.severity in counts:
                counts[item.severity] += 1
        return counts


@dataclass
class FileCacheEntry:
    """Cached scan result for a single file.

    Attributes:
        file_hash: MD5 hash of file content.
        items: Debt items found in file.
        scanned_at: Timestamp of scan.
    """

    file_hash: str
    items: list[dict[str, Any]]
    scanned_at: str


@dataclass
class ScanCheckpoint:
    """Checkpoint for resumable scanning.

    Attributes:
        files_to_scan: List of files to scan.
        current_index: Current file index.
        completed_files: Files already scanned.
        started_at: Scan start time.
    """

    files_to_scan: list[str]
    current_index: int
    completed_files: list[str]
    started_at: str


def _get_sef_dir(base_dir: Path) -> Path:
    """Get SEF cache directory path for the scanned directory.

    For debt scanning, cache is stored in the scanned directory itself,
    not the project root. This allows independent caching per directory.

    Args:
        base_dir: Directory being scanned.

    Returns:
        Path to .sef_cache directory within base_dir.
    """
    from sef_agents.utils.git_utils import SEF_CACHE_DIR

    sef_dir = base_dir / SEF_CACHE_DIR
    sef_dir.mkdir(parents=True, exist_ok=True)
    return sef_dir


def _compute_file_hash(file_path: Path) -> str:
    """Compute MD5 hash of file content."""
    try:
        content = file_path.read_bytes()
        return hashlib.md5(content, usedforsecurity=False).hexdigest()
    except OSError:
        return ""


def _load_cache(base_dir: Path) -> dict[str, FileCacheEntry]:
    """Load debt cache from disk.

    Args:
        base_dir: Project root directory.

    Returns:
        Dictionary mapping file paths to cache entries.
    """
    cache_path = _get_sef_dir(base_dir) / CACHE_FILE
    if not cache_path.exists():
        return {}

    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return {
            path: FileCacheEntry(
                file_hash=entry["file_hash"],
                items=entry["items"],
                scanned_at=entry["scanned_at"],
            )
            for path, entry in data.items()
        }
    except (json.JSONDecodeError, KeyError, OSError) as e:
        logger.warning("cache_load_failed", error=str(e))
        return {}


def _save_cache(base_dir: Path, cache: dict[str, FileCacheEntry]) -> None:
    """Save debt cache to disk.

    Args:
        base_dir: Project root directory.
        cache: Cache dictionary to save.
    """
    cache_path = _get_sef_dir(base_dir) / CACHE_FILE
    data = {
        path: {
            "file_hash": entry.file_hash,
            "items": entry.items,
            "scanned_at": entry.scanned_at,
        }
        for path, entry in cache.items()
    }
    try:
        cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as e:
        logger.warning("cache_save_failed", error=str(e))


def _load_checkpoint(base_dir: Path) -> ScanCheckpoint | None:
    """Load scan checkpoint from disk.

    Args:
        base_dir: Project root directory.

    Returns:
        Checkpoint if exists, None otherwise.
    """
    checkpoint_path = _get_sef_dir(base_dir) / CHECKPOINT_FILE
    if not checkpoint_path.exists():
        return None

    try:
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        return ScanCheckpoint(
            files_to_scan=data["files_to_scan"],
            current_index=data["current_index"],
            completed_files=data["completed_files"],
            started_at=data["started_at"],
        )
    except (json.JSONDecodeError, KeyError, OSError) as e:
        logger.warning("checkpoint_load_failed", error=str(e))
        return None


def _save_checkpoint(base_dir: Path, checkpoint: ScanCheckpoint) -> None:
    """Save scan checkpoint to disk (called after each file).

    Args:
        base_dir: Project root directory.
        checkpoint: Checkpoint to save.
    """
    checkpoint_path = _get_sef_dir(base_dir) / CHECKPOINT_FILE
    data = {
        "files_to_scan": checkpoint.files_to_scan,
        "current_index": checkpoint.current_index,
        "completed_files": checkpoint.completed_files,
        "started_at": checkpoint.started_at,
    }
    try:
        checkpoint_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as e:
        logger.warning("checkpoint_save_failed", error=str(e))


def _clear_checkpoint(base_dir: Path) -> None:
    """Remove checkpoint file after successful scan completion."""
    checkpoint_path = _get_sef_dir(base_dir) / CHECKPOINT_FILE
    try:
        if checkpoint_path.exists():
            checkpoint_path.unlink()
    except OSError:
        pass


def get_cached_debt_count(base_dir: Path) -> int | None:
    """Get debt count from cache without scanning.

    Args:
        base_dir: Project root directory.

    Returns:
        Total debt items in cache, or None if no cache exists.
    """
    cache = _load_cache(base_dir)
    if not cache:
        return None
    return sum(len(entry.items) for entry in cache.values())


class MultiLanguageScanner:
    """Multi-language debt scanner using configurable rules.

    Attributes:
        config_loader: Configuration loader instance.
        language_detector: Language detector instance.
        project_root: Project root directory.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize scanner.

        Args:
            project_root: Project root for framework detection.
        """
        self.config_loader = ConfigLoader()
        self.project_root = project_root or Path.cwd()
        self.language_detector = LanguageDetector(self.project_root)
        self._debt_counter = 0

    def _next_debt_id(self) -> str:
        """Generate next debt ID."""
        self._debt_counter += 1
        return f"DEBT-{self._debt_counter:03d}"

    def _severity_emoji(self, severity: str) -> str:
        """Convert severity string to emoji format."""
        return Severity.from_string(severity)

    def scan_file(self, file_path: Path) -> list[DebtItem]:
        """Scan a file for debt patterns.

        Args:
            file_path: Path to file.

        Returns:
            List of debt items found.
        """
        # Detect language and framework
        lang_info = self.language_detector.detect(file_path)

        if lang_info.language == "unknown":
            return []

        # Load configuration
        try:
            config = self.config_loader.load(lang_info.language, lang_info.framework)
        except FileNotFoundError:
            logger.warning(
                "config_not_found",
                language=lang_info.language,
                framework=lang_info.framework,
            )
            return []

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("file_read_error", file=str(file_path), error=str(e))
            return []

        # Scan based on parser type
        if config.parser == "ast" and lang_info.language == "python":
            return self._scan_python_ast(file_path, content, config, lang_info)
        return self._scan_regex(file_path, content, config, lang_info)

    def _scan_python_ast(
        self,
        file_path: Path,
        content: str,
        config: LanguageConfig,
        lang_info: LanguageInfo,
    ) -> list[DebtItem]:
        """Scan Python file using AST.

        Args:
            file_path: Path to file.
            content: File content.
            config: Language configuration.
            lang_info: Detected language info.

        Returns:
            List of debt items.
        """
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning("syntax_error", file=str(file_path), error=str(e))
            return []

        scanner = PythonASTScanner(
            str(file_path),
            content,
            config,
            self._next_debt_id,
        )
        scanner.visit(tree)
        scanner.scan_todos()
        scanner.scan_deprecated_imports(tree)

        return scanner.items

    def _scan_regex(
        self,
        file_path: Path,
        content: str,
        config: LanguageConfig,
        lang_info: LanguageInfo,
    ) -> list[DebtItem]:
        """Scan file using regex patterns from config.

        Args:
            file_path: Path to file.
            content: File content.
            config: Language configuration.
            lang_info: Detected language info.

        Returns:
            List of debt items.
        """
        items: list[DebtItem] = []
        lines = content.splitlines()

        for pattern_def in config.debt_patterns:
            if not pattern_def.pattern:
                continue

            try:
                regex = re.compile(pattern_def.pattern)
            except re.error as e:
                logger.warning(
                    "invalid_pattern",
                    pattern=pattern_def.name,
                    error=str(e),
                )
                continue

            # Scan each line
            for i, line in enumerate(lines, start=1):
                if regex.search(line):
                    location = f"{file_path}:{i}"
                    items.append(
                        DebtItem(
                            debt_id=self._next_debt_id(),
                            location=location,
                            debt_type=pattern_def.name,
                            severity=self._severity_emoji(pattern_def.severity),
                            description=pattern_def.description,
                            line_number=i,
                            language=str(lang_info),
                        )
                    )

        # Check deprecated imports
        for deprecated, suggestion in config.deprecated_imports.items():
            if deprecated in content:
                for i, line in enumerate(lines, start=1):
                    if deprecated in line and ("import" in line or "from" in line):
                        items.append(
                            DebtItem(
                                debt_id=self._next_debt_id(),
                                location=f"{file_path}:{i}",
                                debt_type="deprecated",
                                severity=Severity.HIGH,
                                description=f"Deprecated `{deprecated}`: {suggestion}",
                                line_number=i,
                                language=str(lang_info),
                            )
                        )
                        break

        return items


class PythonASTScanner(ast.NodeVisitor):
    """AST visitor for Python debt patterns.

    Attributes:
        file_path: Path to file.
        content: File content.
        config: Language configuration.
        items: Collected debt items.
    """

    def __init__(
        self,
        file_path: str,
        content: str,
        config: LanguageConfig,
        id_generator: Any,
    ) -> None:
        """Initialize scanner.

        Args:
            file_path: Path to file.
            content: File content.
            config: Language configuration.
            id_generator: Function to generate debt IDs.
        """
        self.file_path = file_path
        self.content = content
        self.config = config
        self.lines = content.splitlines()
        self.items: list[DebtItem] = []
        self._next_id = id_generator

    def _add_item(
        self,
        debt_type: str,
        severity: str,
        description: str,
        line_number: int | None = None,
    ) -> None:
        """Add a debt item."""
        location = self.file_path
        if line_number:
            location = f"{self.file_path}:{line_number}"

        self.items.append(
            DebtItem(
                debt_id=self._next_id(),
                location=location,
                debt_type=debt_type,
                severity=severity,
                description=description,
                line_number=line_number,
                language="python",
            )
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function definitions."""
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function definitions."""
        self._check_function(node)
        self.generic_visit(node)

    def _check_type_hints(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_private: bool
    ) -> None:
        """Check for missing type hints."""
        if is_private:
            return

        has_return_type = node.returns is not None
        if not has_return_type:
            self._add_item(
                "no-types",
                Severity.MEDIUM,
                f"Function `{node.name}` missing return type hint",
                node.lineno,
            )

        total_args = len(node.args.args)
        args_with_types = sum(1 for arg in node.args.args if arg.annotation is not None)

        if total_args > 0 and args_with_types < total_args:
            missing = total_args - args_with_types
            self._add_item(
                "no-types",
                Severity.MEDIUM,
                f"Function `{node.name}` missing {missing} arg type hints",
                node.lineno,
            )

    def _check_docstring(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_private: bool
    ) -> None:
        """Check for missing docstring."""
        if not is_private and not ast.get_docstring(node):
            self._add_item(
                "no-docs",
                Severity.LOW,
                f"Function `{node.name}` missing docstring",
                node.lineno,
            )

    def _check_complexity_metric(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, thresholds: Any
    ) -> None:
        """Check cyclomatic complexity."""
        complexity = self._estimate_complexity(node)
        if complexity > thresholds.complexity:
            self._add_item(
                "complexity",
                Severity.HIGH,
                f"`{node.name}` complexity {complexity} > {thresholds.complexity}",
                node.lineno,
            )

    def _check_function_length_metric(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, thresholds: Any
    ) -> None:
        """Check function length."""
        if hasattr(node, "end_lineno") and node.end_lineno:
            func_length = node.end_lineno - node.lineno
            if func_length > thresholds.function_length:
                self._add_item(
                    "long-function",
                    Severity.MEDIUM,
                    f"`{node.name}` is {func_length} lines (max {thresholds.function_length})",
                    node.lineno,
                )

    def _check_nesting_depth_metric(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, thresholds: Any
    ) -> None:
        """Check nesting depth."""
        max_depth = self._max_nesting_depth(node)
        if max_depth > thresholds.nesting_depth:
            self._add_item(
                "deep-nesting",
                Severity.MEDIUM,
                f"`{node.name}` nesting depth {max_depth} > {thresholds.nesting_depth}",
                node.lineno,
            )

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check function for debt patterns."""
        is_private = node.name.startswith("_")
        thresholds = self.config.thresholds

        self._check_type_hints(node, is_private)
        self._check_docstring(node, is_private)
        self._check_complexity_metric(node, thresholds)
        self._check_function_length_metric(node, thresholds)
        self._check_nesting_depth_metric(node, thresholds)

    def _estimate_complexity(self, node: ast.AST) -> int:
        """Estimate cyclomatic complexity."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(
                child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)
            ):
                complexity += 1
        return complexity

    def _max_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        max_depth = current_depth
        nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try)

        for child in ast.iter_child_nodes(node):
            if isinstance(child, nesting_nodes):
                child_depth = self._max_nesting_depth(child, current_depth + 1)
            else:
                child_depth = self._max_nesting_depth(child, current_depth)
            max_depth = max(max_depth, child_depth)

        return max_depth

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Check exception handlers."""
        if node.type is None:
            self._add_item(
                "bare-except",
                Severity.CRITICAL,
                "Bare `except:` clause - catches all exceptions",
                node.lineno,
            )
        elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
            self._add_item(
                "bare-except",
                Severity.HIGH,
                "`except Exception:` - too broad",
                node.lineno,
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check class definitions."""
        if not ast.get_docstring(node):
            self._add_item(
                "no-docs",
                Severity.LOW,
                f"Class `{node.name}` missing docstring",
                node.lineno,
            )
        self.generic_visit(node)

    def scan_todos(self) -> None:
        """Scan for TODO/FIXME comments."""
        todo_pattern = re.compile(
            r"#\s*(TODO|FIXME|XXX|HACK|BUG)[\s:]+(.+)", re.IGNORECASE
        )
        for i, line in enumerate(self.lines, start=1):
            match = todo_pattern.search(line)
            if match:
                tag = match.group(1).upper()
                message = match.group(2).strip()[:50]
                severity = Severity.HIGH if tag in ("FIXME", "BUG") else Severity.MEDIUM
                self._add_item(
                    "todo-fixme",
                    severity,
                    f"{tag}: {message}",
                    i,
                )

    def scan_deprecated_imports(self, tree: ast.AST) -> None:
        """Scan for deprecated imports."""
        deprecated = self.config.deprecated_imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if module in deprecated:
                        self._add_item(
                            "deprecated",
                            Severity.HIGH,
                            f"Deprecated `{module}`: {deprecated[module]}",
                            node.lineno,
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                module = node.module.split(".")[0]
                if module in deprecated:
                    self._add_item(
                        "deprecated",
                        Severity.HIGH,
                        f"Deprecated `{module}`: {deprecated[module]}",
                        node.lineno,
                    )


def scan_file(file_path: Path) -> list[DebtItem]:
    """Scan a single file for debt patterns.

    Args:
        file_path: Path to file.

    Returns:
        List of debt items found.
    """
    scanner = MultiLanguageScanner(file_path.parent)
    return scanner.scan_file(file_path)


# Common directories to skip
SKIP_DIRECTORIES = frozenset(
    {
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
    }
)

# Supported extensions
SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".java"}


def _should_skip_path(path: Path) -> bool:
    """Check if path should be skipped."""
    return any(excluded in path.parts for excluded in SKIP_DIRECTORIES)


def _get_files_to_scan(
    dir_path: Path,
    extensions: set[str],
    incremental: bool,
    cache: dict[str, FileCacheEntry],
) -> list[Path]:
    """Determine which files need to be scanned.

    Args:
        dir_path: Root directory to scan.
        extensions: Set of supported file extensions.
        incremental: Whether to use incremental scanning.
        cache: Existing cache.

    Returns:
        List of paths to scan.
    """
    if incremental and is_git_repo(dir_path) and cache:
        changed_files = get_changed_files(dir_path, extensions)
        changed_set = {str(dir_path / f) for f in changed_files}

        files_to_scan = []
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in extensions:
                continue
            if _should_skip_path(file_path):
                continue

            str_path = str(file_path)
            if str_path in changed_set:
                files_to_scan.append(file_path)
            elif str_path in cache:
                current_hash = _compute_file_hash(file_path)
                if current_hash != cache[str_path].file_hash:
                    files_to_scan.append(file_path)
            else:
                files_to_scan.append(file_path)

        logger.info(
            "incremental_scan",
            changed_files=len(files_to_scan),
            cached_files=len(cache),
        )
        return files_to_scan

    # Full scan
    return [
        f
        for f in dir_path.rglob("*")
        if f.is_file() and f.suffix in extensions and not _should_skip_path(f)
    ]


def scan_directory(directory: str | Path, incremental: bool = True) -> ScanResult:
    """Scan directory for technical debt with incremental and checkpoint support.

    Args:
        directory: Path to directory.
        incremental: If True, only scan changed files (uses git + cache).

    Returns:
        ScanResult with all debt items.
    """
    result = ScanResult()
    dir_path = Path(directory).resolve()

    if not dir_path.exists():
        result.errors.append(f"Directory not found: {directory}")
        return result

    scanner = MultiLanguageScanner(dir_path)

    # Excluded directories (unused)

    # Supported extensions
    extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".java"}

    # Load cache
    cache = _load_cache(dir_path)

    # Check for existing checkpoint (resume interrupted scan)
    checkpoint = _load_checkpoint(dir_path)
    if checkpoint:
        logger.info(
            "resuming_scan",
            from_index=checkpoint.current_index,
            total_files=len(checkpoint.files_to_scan),
        )
        files_to_scan = [Path(f) for f in checkpoint.files_to_scan]
        start_index = checkpoint.current_index
    else:
        files_to_scan = _get_files_to_scan(dir_path, extensions, incremental, cache)
        start_index = 0

        checkpoint = ScanCheckpoint(
            files_to_scan=[str(f) for f in files_to_scan],
            current_index=0,
            completed_files=[],
            started_at=datetime.now(timezone.utc).isoformat(),
        )

    # Scan files with checkpoint after each
    for i in range(start_index, len(files_to_scan)):
        file_path = (
            files_to_scan[i]
            if isinstance(files_to_scan[i], Path)
            else Path(files_to_scan[i])
        )

        if not file_path.exists():
            continue

        result.files_scanned += 1

        # Track language
        lang_info = scanner.language_detector.detect(file_path)
        lang_key = str(lang_info)
        result.languages[lang_key] = result.languages.get(lang_key, 0) + 1

        # Scan file
        items = scanner.scan_file(file_path)
        result.items.extend(items)

        str_path = str(file_path)
        cache[str_path] = FileCacheEntry(
            file_hash=_compute_file_hash(file_path),
            items=[item.to_dict() for item in items],
            scanned_at=datetime.now(timezone.utc).isoformat(),
        )

        checkpoint.current_index = i + 1
        checkpoint.completed_files.append(str_path)
        _save_checkpoint(dir_path, checkpoint)

    # Merge cached results for unchanged files
    if incremental and cache:
        scanned_paths = {str(f) for f in files_to_scan}
        for path, entry in cache.items():
            if path not in scanned_paths:
                for item_dict in entry.items:
                    result.items.append(
                        DebtItem(
                            debt_id=item_dict.get("id", "DEBT-???"),
                            location=item_dict.get("location", path),
                            debt_type=item_dict.get("type", "unknown"),
                            severity=item_dict.get("severity", Severity.MEDIUM),
                            description=item_dict.get("description", ""),
                            line_number=item_dict.get("line"),
                            language=item_dict.get("language", "unknown"),
                        )
                    )
                # Count cached file
                result.files_scanned += 1

    # Save final cache and clear checkpoint
    _save_cache(dir_path, cache)
    _clear_checkpoint(dir_path)

    logger.info(
        "debt_scan_complete",
        files_scanned=result.files_scanned,
        items_found=len(result.items),
        languages=result.languages,
        incremental=incremental,
    )

    return result


def generate_debt_report(directory: str) -> str:
    """Generate technical debt report.

    Args:
        directory: Path to scan.

    Returns:
        Markdown formatted report.
    """
    result = scan_directory(directory)

    if result.errors:
        return f"Errors: {result.errors}"

    output = f"""# Technical Debt Scan Report

*Auto-generated by debt_scanner.py (multi-language)*
*Scanned: {result.files_scanned} files*
*Found: {len(result.items)} items*

## Languages Detected

| Language | Files |
|----------|-------|
"""
    for lang, count in sorted(result.languages.items()):
        output += f"| {lang} | {count} |\n"

    output += "\n## Summary by Severity\n\n"
    output += "| Severity | Count |\n"
    output += "|----------|-------|\n"
    for severity, count in result.by_severity.items():
        output += f"| {severity} | {count} |\n"

    output += "\n## Items by Type\n\n"

    for debt_type, items in result.by_type.items():
        output += f"### {debt_type} ({len(items)})\n\n"
        output += "| ID | Location | Severity | Description |\n"
        output += "|----|----------|----------|-------------|\n"
        for item in items:
            loc = item.location
            desc = (
                item.description[:50]
                if len(item.description) > 50
                else item.description
            )
            output += f"| {item.debt_id} | `{loc}` | {item.severity} | {desc} |\n"
        output += "\n"

    return output


def append_to_tech_debt_md(directory: str, tech_debt_path: str) -> str:
    """Scan and append new items to TECH_DEBT.md.

    Args:
        directory: Path to scan.
        tech_debt_path: Path to TECH_DEBT.md file.

    Returns:
        Status message.
    """
    result = scan_directory(directory)

    if result.errors:
        return f"Errors: {result.errors}"

    if not result.items:
        return "No debt items found."

    # Generate new rows
    new_rows = "\n".join(item.to_markdown_row() for item in result.items)

    # Read existing file
    debt_file = Path(tech_debt_path)
    if not debt_file.exists():
        return f"TECH_DEBT.md not found at {tech_debt_path}"

    try:
        content = debt_file.read_text(encoding="utf-8")
        marker = "| DEBT-001"
        if marker in content:
            content += "\n" + new_rows
        else:
            example = "| DEBT-001 | `src/example.py:45` | No type hints "
            example += "| 🟡 Medium | STORY-042 | Open | Discovery | 2024-12-22 |"
            content = content.replace(example, new_rows)

        debt_file.write_text(content, encoding="utf-8")
        return f"Appended {len(result.items)} items to {tech_debt_path}"

    except OSError as e:
        return f"Failed to update TECH_DEBT.md: {e}"


# Tool functions for MCP integration


def scan_debt_tool(directory: str, summary: bool = False) -> str:
    """Scan directory for technical debt.

    Multi-language support: Python, TypeScript, JavaScript, Java.
    Framework support: React, Angular, Spring Boot.

    Args:
        directory: Path to scan.
        summary: If True, return quick summary. If False, return full report.

    Returns:
        Formatted debt report or summary.
    """
    if not summary:
        return generate_debt_report(directory)

    # Summary mode
    result = scan_directory(directory)

    if result.errors:
        return f"❌ Errors: {', '.join(result.errors)}"

    if not result.items:
        return f"✅ No technical debt found in {result.files_scanned} files."

    lines = [
        f"📋 **Debt Summary** ({result.files_scanned} files scanned)\n",
    ]

    # Languages
    if result.languages:
        lines.append("| Language | Files |")
        lines.append("|----------|-------|")
        for lang, count in sorted(result.languages.items()):
            lines.append(f"| {lang} | {count} |")
        lines.append("")

    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for severity, count in result.by_severity.items():
        if count > 0:
            lines.append(f"| {severity} | {count} |")

    lines.append("")
    lines.append("| Type | Count |")
    lines.append("|------|-------|")
    for debt_type, items in result.by_type.items():
        lines.append(f"| {debt_type} | {len(items)} |")

    lines.append(f"\n**Total:** {len(result.items)} items")
    lines.append("\nRun `scan_debt(directory, summary=False)` for full report.")

    return "\n".join(lines)
