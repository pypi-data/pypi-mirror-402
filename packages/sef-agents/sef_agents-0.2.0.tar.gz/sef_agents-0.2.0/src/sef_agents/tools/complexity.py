"""Complexity Scanner - Multi-language complexity analysis.

Supports Python (AST-based) and TypeScript/JavaScript/Java (AST or regex-based).
Uses ConfigLoader to load language-specific thresholds.
Calculates LOC, cyclomatic/cognitive complexity, function/class counts.
Implements dual-threshold system: function-level + file-level.
"""

import ast
import fnmatch
import re
from pathlib import Path

import structlog

from sef_agents.core.config_loader import ConfigLoader
from sef_agents.core.language_detector import LanguageDetector

logger = structlog.get_logger(__name__)


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for Python complexity analysis."""

    def __init__(self):
        """Initialize visitor."""
        self.complexity = 0
        self.functions = 0
        self.classes = 0

    def visit_FunctionDef(self, node) -> None:
        """Count function and base complexity."""
        self.functions += 1
        self.complexity += 1  # Base complexity
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node) -> None:
        """Count async function."""
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node) -> None:
        """Count class."""
        self.classes += 1
        self.generic_visit(node)

    def visit_If(self, node) -> None:
        """Count if statement."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node) -> None:
        """Count for loop."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node) -> None:
        """Count async for loop."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node) -> None:
        """Count while loop."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_Try(self, node) -> None:
        """Count try block."""
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node) -> None:
        """Count exception handler."""
        self.complexity += 1
        self.generic_visit(node)


def _analyze_python_ast(content: str) -> dict:
    """Analyze Python file using AST.

    Args:
        content: File content.

    Returns:
        Dict with complexity metrics.
    """
    tree = ast.parse(content)
    visitor = ComplexityVisitor()
    visitor.visit(tree)

    return {
        "complexity": visitor.complexity,
        "functions": visitor.functions,
        "classes": visitor.classes,
    }


def _analyze_regex_based(content: str, language: str) -> dict:
    """Analyze file using regex patterns (TypeScript/JavaScript/Java).

    Args:
        content: File content.
        language: Language name.

    Returns:
        Dict with complexity metrics.
    """
    complexity = 0
    functions = 0
    classes = 0

    # Count functions/methods
    if language in ("typescript", "javascript"):
        # Function patterns: function name(), arrow functions, async functions
        function_patterns = [
            r"\bfunction\s+\w+\s*\(",
            r"\bconst\s+\w+\s*=\s*(async\s+)?\([^)]*\)\s*=>",
            r"\bconst\s+\w+\s*=\s*(async\s+)?function",
            r"\bexport\s+(async\s+)?function",
            r"\bexport\s+const\s+\w+\s*=\s*(async\s+)?\([^)]*\)\s*=>",
        ]
        for pattern in function_patterns:
            functions += len(re.findall(pattern, content, re.MULTILINE))

        # Class patterns
        class_pattern = r"\b(class|interface|type)\s+\w+"
        classes = len(re.findall(class_pattern, content, re.MULTILINE))

    elif language == "java":
        # Method patterns: public/private/protected returnType methodName(
        method_pattern = r"\b(public|private|protected|static)\s+.*?\s+\w+\s*\("
        functions = len(re.findall(method_pattern, content, re.MULTILINE))

        # Class patterns
        class_pattern = r"\b(public\s+)?(abstract\s+)?(final\s+)?class\s+\w+"
        classes = len(re.findall(class_pattern, content, re.MULTILINE))

    # Count complexity contributors (if, for, while, switch, catch, ternary)
    complexity_patterns = [
        r"\bif\s*\(",
        r"\bfor\s*\(",
        r"\bwhile\s*\(",
        r"\bswitch\s*\(",
        r"\bcatch\s*\(",
        r"\?\s*.*\s*:",
    ]
    for pattern in complexity_patterns:
        complexity += len(re.findall(pattern, content, re.MULTILINE))

    # Base complexity = number of functions
    complexity += functions

    return {
        "complexity": complexity,
        "functions": functions,
        "classes": classes,
    }


def analyze_file(file_path: Path, config_loader: ConfigLoader | None = None) -> dict:
    """Analyze file for complexity metrics.

    Supports Python (AST), TypeScript, JavaScript, Java (regex).
    Uses ConfigLoader to get language-specific thresholds.

    Args:
        file_path: Path to file.
        config_loader: Optional ConfigLoader instance. Creates default if None.

    Returns:
        Dict with loc, complexity, functions, classes, thresholds, error.
    """
    if config_loader is None:
        config_loader = ConfigLoader()

    try:
        if config_loader is None:
            config_loader = ConfigLoader()

        # Detect language first
        detector = LanguageDetector()
        lang_info = detector.detect(file_path)

        if lang_info.language == "unknown":
            # Can't check exclusions without language, proceed with basic analysis
            content = file_path.read_text(encoding="utf-8")
            loc = len(content.splitlines())
            return {
                "loc": loc,
                "complexity": 0,
                "functions": 0,
                "classes": 0,
                "error": f"Unknown language for file: {file_path}",
            }

        # Load config to check exclusions (before reading file content)
        try:
            config = config_loader.load(lang_info.language, lang_info.framework)
        except FileNotFoundError:
            logger.warning(
                "config_not_found",
                language=lang_info.language,
                file=str(file_path),
            )
            from sef_agents.core.config_loader import LanguageConfig, Thresholds

            config = LanguageConfig(
                language=lang_info.language, thresholds=Thresholds()
            )

        # Check skip_analysis exclusions (before reading file)
        if config.exclusions and "skip_analysis" in config.exclusions:
            file_str = str(file_path)
            file_name = file_path.name
            for pattern in config.exclusions["skip_analysis"]:
                # Check both full path and filename
                if fnmatch.fnmatch(file_str, pattern) or fnmatch.fnmatch(
                    file_name, pattern
                ):
                    logger.debug(
                        "file_excluded_from_analysis",
                        file=str(file_path),
                        pattern=pattern,
                    )
                    return {
                        "loc": 0,
                        "complexity": 0,
                        "functions": 0,
                        "classes": 0,
                        "error": None,
                        "excluded": True,
                        "exclusion_reason": f"Matches skip pattern: {pattern}",
                    }

        # Read file content after exclusion check
        content = file_path.read_text(encoding="utf-8")
        loc = len(content.splitlines())

        # Get thresholds
        thresholds = config.thresholds

        # Analyze based on language and parser type
        if lang_info.language == "python":
            metrics = _analyze_python_ast(content)
            per_function = None  # Python doesn't track per-function yet
        elif lang_info.language in ("typescript", "javascript"):
            # Use AST parser if configured, else regex fallback
            if config.parser == "ast":
                from sef_agents.tools.complexity_ast import analyze_typescript_ast

                ast_result = analyze_typescript_ast(file_path, content)
                if ast_result.error:
                    logger.warning(
                        "ast_fallback_to_regex",
                        error=ast_result.error,
                        file=str(file_path),
                    )
                    metrics = _analyze_regex_based(content, lang_info.language)
                    per_function = None
                else:
                    # Convert AST result to metrics format
                    metrics = {
                        "complexity": ast_result.file_complexity,
                        "functions": len(ast_result.functions),
                        "classes": ast_result.classes,
                    }
                    per_function = [
                        {"name": f.name, "complexity": f.complexity, "line": f.line}
                        for f in ast_result.functions
                    ]
            else:
                metrics = _analyze_regex_based(content, lang_info.language)
                per_function = None
        elif lang_info.language == "java":
            metrics = _analyze_regex_based(content, lang_info.language)
            per_function = None
        else:
            return {
                "loc": loc,
                "complexity": 0,
                "functions": 0,
                "classes": 0,
                "error": f"Unsupported language: {lang_info.language}",
            }

        # Check exclusions for file-level complexity
        skip_file_complexity = False
        if config.exclusions and "file_complexity" in config.exclusions:
            for pattern in config.exclusions["file_complexity"]:
                if fnmatch.fnmatch(file_path.name, pattern):
                    skip_file_complexity = True
                    logger.debug(
                        "file_excluded_from_complexity",
                        file=str(file_path),
                        pattern=pattern,
                    )
                    break

        return {
            "loc": loc,
            "complexity": metrics["complexity"],
            "functions": metrics["functions"],
            "classes": metrics["classes"],
            "per_function": per_function,  # List of {name, complexity, line} if available
            "thresholds": {
                "complexity": thresholds.complexity,  # Legacy
                "function_complexity_warn": thresholds.function_complexity_warn,
                "function_complexity_block": thresholds.function_complexity_block,
                "file_complexity_warn": thresholds.file_complexity_warn,
                "file_complexity_block": thresholds.file_complexity_block,
                "file_length": thresholds.file_length,
            },
            "skip_file_complexity": skip_file_complexity,
            "error": None,
        }
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}
    except Exception as e:
        logger.error("analyze_file_failed", error=str(e))
        raise


def scan_complexity_tool(files: str) -> str:
    """Scan files for complexity metrics (LOC, Cognitive/Cyclomatic).

    Uses dual-threshold system:
    - Function-level: Warn 15, Block 25 (cognitive complexity)
    - File-level: Warn 80, Block 150 (aggregate)

    Automatically excludes:
    - Autogenerated files (*.generated.ts, *.auto.ts)
    - Hidden directories (.*/)
    - Coverage/build directories (coverage/, dist/, build/)
    - Vendor directories (node_modules/, vendor/, third-party/)

    Usage: scan_complexity("file1.py,file2.ts")
    """
    file_list = [f.strip() for f in files.split(",") if f.strip()]
    report = ["🔍 **Code Complexity Scan**\n"]

    for fname in file_list:
        p = Path(fname)
        if not p.exists():
            report.append(f"❌ `{fname}`: File not found")
            continue

        metrics = analyze_file(p)

        # Skip excluded files silently (autogenerated, vendor, etc.)
        if metrics.get("excluded"):
            continue

        if metrics.get("error"):
            report.append(f"❌ `{fname}`: Parse Error: {metrics['error']}")
            continue

        thresholds = metrics.get("thresholds", {})
        skip_file = metrics.get("skip_file_complexity", False)

        # File-level checks
        loc_status = (
            "🔴" if metrics["loc"] > thresholds.get("file_length", 500) else "🟢"
        )
        file_comp = metrics["complexity"]

        report.append(f"### `{p.name}`")
        report.append(
            f"- LOC: {metrics['loc']} {loc_status} (Limit: {thresholds.get('file_length', 500)})"
        )
        report.append(f"- Functions: {metrics['functions']}")
        report.append(f"- Classes: {metrics['classes']}")

        # File-level complexity (if not excluded)
        if not skip_file:
            file_warn = thresholds.get("file_complexity_warn", 80)
            file_block = thresholds.get("file_complexity_block", 150)

            if file_comp >= file_block:
                file_status = "🔴 BLOCKER"
                report.append(
                    f"- File Complexity: {file_comp} {file_status} (Block: {file_block}, Warn: {file_warn})"
                )
            elif file_comp >= file_warn:
                file_status = "🟡 WARNING"
                report.append(
                    f"- File Complexity: {file_comp} {file_status} (Block: {file_block}, Warn: {file_warn})"
                )
            else:
                file_status = "🟢 OK"
                report.append(
                    f"- File Complexity: {file_comp} {file_status} (Block: {file_block}, Warn: {file_warn})"
                )
        else:
            report.append(f"- File Complexity: {file_comp} ⚪ EXCLUDED")

        # Per-function complexity (if available)
        per_function = metrics.get("per_function")
        if per_function:
            func_warn = thresholds.get("function_complexity_warn", 15)
            func_block = thresholds.get("function_complexity_block", 25)

            violations = [f for f in per_function if f["complexity"] >= func_warn]

            if violations:
                report.append("")
                report.append("**Function-Level Violations:**")
                for func in violations:
                    if func["complexity"] >= func_block:
                        status = "🔴 BLOCKER"
                    else:
                        status = "🟡 WARNING"
                    report.append(
                        f"- `{func['name']}` (line {func['line']}): "
                        f"{func['complexity']} {status} (Block: {func_block}, Warn: {func_warn})"
                    )

        report.append("")

    return "\n".join(report)
