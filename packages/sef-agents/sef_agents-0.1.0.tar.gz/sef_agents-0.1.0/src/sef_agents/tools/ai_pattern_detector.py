"""AI Anti-Pattern Detector for SEF.

Multi-language detection of AI-generated code anti-patterns.
Supports: Python, TypeScript, JavaScript, Java.
Frameworks: React, Angular, Spring Boot.

Patterns detected:
- Over-abstraction (excessive class/function ratio)
- Unused parameters in functions
- Generic naming (data, result, temp, handler, etc.)
- Verbose/redundant comments
- Copy-paste similarity between code blocks
"""

import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from sef_agents.core.config_loader import ConfigLoader, LanguageConfig
from sef_agents.core.language_detector import LanguageDetector, LanguageInfo

logger = structlog.get_logger(__name__)


@dataclass
class PatternFinding:
    """Represents a detected anti-pattern.

    Attributes:
        pattern_id: Unique identifier for the pattern type.
        severity: LOW, MEDIUM, or HIGH.
        line: Line number where pattern was detected.
        message: Human-readable description.
        suggestion: Recommended fix.
        language: Source language.
    """

    pattern_id: str
    severity: str
    line: int
    message: str
    suggestion: str
    language: str = "python"


# Default fallback configuration
DEFAULT_CONFIG: dict[str, Any] = {
    "enabled_patterns": [
        "over_abstraction",
        "unused_params",
        "generic_naming",
        "verbose_comments",
        "copy_paste_blocks",
    ],
    "thresholds": {
        "class_to_function_ratio": 0.5,
        "comment_to_code_ratio": 0.4,
        "similarity_threshold": 0.85,
        "min_block_size": 5,
    },
    "generic_names": [
        "data",
        "result",
        "temp",
        "tmp",
        "handler",
        "manager",
        "helper",
        "utils",
        "misc",
        "stuff",
        "thing",
        "obj",
        "val",
        "var",
        "foo",
        "bar",
        "baz",
        "x",
        "y",
        "z",
        "item",
        "elem",
        "info",
    ],
    "severity_weights": {
        "over_abstraction": "MEDIUM",
        "unused_params": "LOW",
        "generic_naming": "LOW",
        "verbose_comments": "LOW",
        "copy_paste_blocks": "HIGH",
    },
}


class AIPatternDetector:
    """Multi-language AI anti-pattern detector.

    Attributes:
        config: Configuration dictionary for pattern detection.
        findings: List of detected pattern findings.
        language_detector: Language detection utility.
        config_loader: Configuration loader for language rules.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> None:
        """Initialize detector.

        Args:
            config: Optional configuration override. Uses lang config if None.
            project_root: Project root for framework detection.
        """
        self.custom_config = config
        self.findings: list[PatternFinding] = []
        self._code_blocks: list[tuple[int, str]] = []
        self.language_detector = LanguageDetector(project_root or Path.cwd())
        self.config_loader = ConfigLoader()

    def _get_config(self, lang_config: LanguageConfig | None) -> dict[str, Any]:
        """Get effective configuration.

        Args:
            lang_config: Language configuration if available.

        Returns:
            Configuration dictionary.
        """
        if self.custom_config:
            return self.custom_config

        if lang_config and lang_config.anti_patterns:
            # Merge language config with defaults
            merged = DEFAULT_CONFIG.copy()
            merged["generic_names"] = list(
                set(merged["generic_names"]) | set(lang_config.naming.generic_names)
            )
            for key, value in lang_config.anti_patterns.items():
                if isinstance(value, dict) and "threshold" in value:
                    merged["thresholds"][f"{key}_threshold"] = value["threshold"]
            return merged

        return DEFAULT_CONFIG

    def detect_patterns(self, file_path: Path) -> list[PatternFinding]:
        """Run all enabled pattern detectors on a file.

        Args:
            file_path: Path to file to analyze.

        Returns:
            List of PatternFinding objects for detected issues.

        Raises:
            FileNotFoundError: If file_path does not exist.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.findings = []
        self._code_blocks = []

        # Detect language
        lang_info = self.language_detector.detect(file_path)

        if lang_info.language == "unknown":
            logger.warning("unsupported_language", file=str(file_path))
            return []

        # Load language config
        lang_config: LanguageConfig | None = None
        try:
            lang_config = self.config_loader.load(
                lang_info.language, lang_info.framework
            )
        except FileNotFoundError:
            logger.debug(
                "lang_config_not_found",
                language=lang_info.language,
                using="default_config",
            )

        config = self._get_config(lang_config)

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
        except UnicodeDecodeError as e:
            logger.warning("unicode_decode_error", file=str(file_path), error=str(e))
            return []

        # Choose detection strategy based on language
        if lang_info.language == "python":
            return self._detect_python(file_path, content, lines, config, lang_info)
        return self._detect_regex_based(file_path, lines, config, lang_info)

    def _detect_python(
        self,
        file_path: Path,
        content: str,
        lines: list[str],
        config: dict[str, Any],
        lang_info: LanguageInfo,
    ) -> list[PatternFinding]:
        """Detect patterns in Python using AST.

        Args:
            file_path: Path to file.
            content: File content.
            lines: File lines.
            config: Configuration.
            lang_info: Language info.

        Returns:
            List of findings.
        """
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning("syntax_error", file=str(file_path), error=str(e))
            return [
                PatternFinding(
                    pattern_id="syntax_error",
                    severity="HIGH",
                    line=e.lineno or 1,
                    message=f"Syntax error: {e.msg}",
                    suggestion="Fix syntax before pattern analysis",
                    language=str(lang_info),
                )
            ]

        enabled = config.get("enabled_patterns", [])

        if "over_abstraction" in enabled:
            self._detect_over_abstraction(tree, config, lang_info)

        if "unused_params" in enabled:
            self._detect_unused_params_python(tree, config, lang_info)

        if "generic_naming" in enabled:
            self._detect_generic_naming_python(tree, config, lang_info)

        if "verbose_comments" in enabled:
            self._detect_verbose_comments(lines, config, lang_info)

        if "copy_paste_blocks" in enabled:
            self._detect_copy_paste(lines, config, lang_info)

        logger.info(
            "pattern_detection_complete",
            file=str(file_path),
            language=str(lang_info),
            findings_count=len(self.findings),
        )

        return self.findings

    def _detect_regex_based(
        self,
        file_path: Path,
        lines: list[str],
        config: dict[str, Any],
        lang_info: LanguageInfo,
    ) -> list[PatternFinding]:
        """Detect patterns using regex for non-Python languages.

        Args:
            file_path: Path to file.
            lines: File lines.
            config: Configuration.
            lang_info: Language info.

        Returns:
            List of findings.
        """
        enabled = config.get("enabled_patterns", [])

        if "generic_naming" in enabled:
            self._detect_generic_naming_regex(lines, config, lang_info)

        if "verbose_comments" in enabled:
            self._detect_verbose_comments(lines, config, lang_info)

        if "copy_paste_blocks" in enabled:
            self._detect_copy_paste(lines, config, lang_info)

        logger.info(
            "pattern_detection_complete",
            file=str(file_path),
            language=str(lang_info),
            findings_count=len(self.findings),
        )

        return self.findings

    def _detect_over_abstraction(
        self,
        tree: ast.AST,
        config: dict[str, Any],
        lang_info: LanguageInfo,
    ) -> None:
        """Detect excessive class-to-function ratio."""
        class_count = 0
        function_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                function_count += 1

        if function_count == 0:
            return

        ratio = class_count / function_count
        threshold = config["thresholds"].get("class_to_function_ratio", 0.5)

        if ratio > threshold:
            self.findings.append(
                PatternFinding(
                    pattern_id="over_abstraction",
                    severity=config["severity_weights"]["over_abstraction"],
                    line=1,
                    message=f"High class-to-function ratio: {ratio:.2f} (threshold: {threshold})",
                    suggestion="Consider if all classes are necessary.",
                    language=str(lang_info),
                )
            )

    def _detect_unused_params_python(
        self,
        tree: ast.AST,
        config: dict[str, Any],
        lang_info: LanguageInfo,
    ) -> None:
        """Detect unused parameters in Python functions."""
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue

            if not node.body:
                continue

            param_names: set[str] = set()
            for arg in node.args.args:
                if arg.arg not in ("self", "cls"):
                    param_names.add(arg.arg)
            for arg in node.args.kwonlyargs:
                param_names.add(arg.arg)

            if not param_names:
                continue

            used_names: set[str] = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Name):
                    used_names.add(child.id)

            unused = param_names - used_names

            for param in unused:
                if param.startswith("_"):
                    continue

                self.findings.append(
                    PatternFinding(
                        pattern_id="unused_params",
                        severity=config["severity_weights"]["unused_params"],
                        line=node.lineno,
                        message=f"Unused parameter '{param}' in '{node.name}'",
                        suggestion=f"Remove '{param}' or prefix with underscore.",
                        language=str(lang_info),
                    )
                )

    def _detect_generic_naming_python(
        self,
        tree: ast.AST,
        config: dict[str, Any],
        lang_info: LanguageInfo,
    ) -> None:
        """Detect generic naming in Python code."""
        generic_names = set(config.get("generic_names", []))

        for node in ast.walk(tree):
            name: str | None = None
            node_type: str = ""

            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                name = node.name
                node_type = "function"
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                name = node.id
                node_type = "variable"

            if name and name.lower() in generic_names:
                if len(name) == 1 and node_type == "variable":
                    continue

                self.findings.append(
                    PatternFinding(
                        pattern_id="generic_naming",
                        severity=config["severity_weights"]["generic_naming"],
                        line=getattr(node, "lineno", 1),
                        message=f"Generic {node_type} name: '{name}'",
                        suggestion="Use a more descriptive name.",
                        language=str(lang_info),
                    )
                )

    def _detect_generic_naming_regex(
        self,
        lines: list[str],
        config: dict[str, Any],
        lang_info: LanguageInfo,
    ) -> None:
        """Detect generic naming using regex for JS/TS/Java."""
        generic_names = set(config.get("generic_names", []))

        # Patterns for variable/function declarations by language
        patterns = {
            "typescript": [
                r"(?:const|let|var)\s+(\w+)\s*[=:]",
                r"function\s+(\w+)\s*\(",
            ],
            "javascript": [
                r"(?:const|let|var)\s+(\w+)\s*=",
                r"function\s+(\w+)\s*\(",
            ],
            "java": [
                r"(?:public|private|protected)?\s*\w+\s+(\w+)\s*[=;]",
                r"(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(",
            ],
        }

        lang_patterns = patterns.get(lang_info.language, [])

        for i, line in enumerate(lines, start=1):
            for pattern in lang_patterns:
                for match in re.finditer(pattern, line):
                    name = match.group(1)
                    if name and name.lower() in generic_names:
                        self.findings.append(
                            PatternFinding(
                                pattern_id="generic_naming",
                                severity=config["severity_weights"]["generic_naming"],
                                line=i,
                                message=f"Generic name: '{name}'",
                                suggestion="Use a more descriptive name.",
                                language=str(lang_info),
                            )
                        )

    def _detect_verbose_comments(
        self,
        lines: list[str],
        config: dict[str, Any],
        lang_info: LanguageInfo,
    ) -> None:
        """Detect excessive comments."""
        comment_lines = 0
        code_lines = 0

        # Comment patterns by language
        single_comment = {
            "python": "#",
            "typescript": "//",
            "javascript": "//",
            "java": "//",
        }
        comment_char = single_comment.get(lang_info.language, "#")

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(comment_char):
                comment_lines += 1
            elif not stripped.startswith(('"""', "'''", "/*", "*")):
                code_lines += 1

        if code_lines == 0:
            return

        ratio = comment_lines / code_lines
        threshold = config["thresholds"].get("comment_to_code_ratio", 0.4)

        if ratio > threshold:
            self.findings.append(
                PatternFinding(
                    pattern_id="verbose_comments",
                    severity=config["severity_weights"]["verbose_comments"],
                    line=1,
                    message=f"High comment-to-code ratio: {ratio:.2f}",
                    suggestion="Remove redundant comments.",
                    language=str(lang_info),
                )
            )

    def _detect_copy_paste(
        self,
        lines: list[str],
        config: dict[str, Any],
        lang_info: LanguageInfo,
    ) -> None:
        """Detect copy-paste code blocks."""
        min_block = config["thresholds"].get("min_block_size", 5)

        # Extract non-empty, non-comment lines
        comment_char = "#" if lang_info.language == "python" else "//"
        code_lines: list[tuple[int, str]] = []

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith(comment_char):
                # Normalize identifiers
                normalized = re.sub(r"[a-zA-Z_][a-zA-Z0-9_]*", "X", stripped)
                code_lines.append((idx + 1, normalized))

        if len(code_lines) < min_block * 2:
            return

        blocks: list[tuple[int, str]] = []

        for i in range(len(code_lines) - min_block + 1):
            block_content = "\n".join(line for _, line in code_lines[i : i + min_block])
            block_hash = hashlib.md5(
                block_content.encode(), usedforsecurity=False
            ).hexdigest()
            start_line = code_lines[i][0]
            blocks.append((start_line, block_hash))

        # Find duplicates
        seen_hashes: dict[str, int] = {}
        reported_lines: set[int] = set()

        for start_line, block_hash in blocks:
            if block_hash in seen_hashes:
                original_line = seen_hashes[block_hash]
                if abs(start_line - original_line) < min_block:
                    continue
                if start_line in reported_lines:
                    continue

                self.findings.append(
                    PatternFinding(
                        pattern_id="copy_paste_blocks",
                        severity=config["severity_weights"]["copy_paste_blocks"],
                        line=start_line,
                        message=f"Potential copy-paste from line {original_line}",
                        suggestion="Extract duplicated logic into a reusable function.",
                        language=str(lang_info),
                    )
                )
                reported_lines.add(start_line)
            else:
                seen_hashes[block_hash] = start_line


def detect_ai_patterns_tool(file_path: str, config_path: str | None = None) -> str:
    """Detect AI anti-patterns in a source file.

    Multi-language support: Python, TypeScript, JavaScript, Java.
    Framework support: React, Angular, Spring Boot.

    Patterns detected:
    - Over-abstraction (too many classes)
    - Unused parameters
    - Generic naming (data, result, temp, etc.)
    - Verbose comments
    - Copy-paste code blocks

    Args:
        file_path: Path to the file to analyze.
        config_path: Optional path to config override.

    Returns:
        Markdown-formatted report of findings.
    """
    from sef_agents.constants import Status
    from sef_agents.session import SessionManager
    from sef_agents.tools.context_tools import _format_available_agents_numbered
    from sef_agents.tools.report_utils import write_report

    # Enforce agent activation requirement
    active_agent = SessionManager.get().active_agent
    if not active_agent:
        agents_output = _format_available_agents_numbered()
        return (
            f"{Status.ERROR} No SEF Agent is active.\n\n"
            "**AI pattern detection requires an active agent for proper context.**\n\n"
            f"{agents_output}\n\n"
            "Activate an agent first: `set_active_agent(agent_name)` or `set_active_agent(number)`"
        )

    p = Path(file_path)

    # Load custom config if provided
    config: dict[str, Any] | None = None
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            try:
                import yaml

                config = yaml.safe_load(config_file.read_text())
                logger.info("config_loaded", path=config_path)
            except ImportError:
                logger.warning("yaml_not_installed", using="default_config")
            except (OSError, ValueError) as e:
                logger.warning(
                    "config_load_failed", error=str(e), using="default_config"
                )

    detector = AIPatternDetector(config)

    try:
        findings = detector.detect_patterns(p)
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"

    # Generate report
    report_lines: list[str] = []

    if not findings:
        report_lines.append("✅ No AI anti-patterns detected.\n")
    else:
        high = [f for f in findings if f.severity == "HIGH"]
        medium = [f for f in findings if f.severity == "MEDIUM"]
        low = [f for f in findings if f.severity == "LOW"]

        report_lines.append(f"Found {len(findings)} potential issues:\n")
        report_lines.append(f"- 🔴 HIGH: {len(high)}")
        report_lines.append(f"- 🟡 MEDIUM: {len(medium)}")
        report_lines.append(f"- 🟢 LOW: {len(low)}\n")

        report_lines.append("| Severity | Line | Pattern | Message | Suggestion |")
        report_lines.append("|----------|------|---------|---------|------------|")

        for finding in sorted(findings, key=lambda f: (f.severity != "HIGH", f.line)):
            icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(
                finding.severity, "⚪"
            )
            report_lines.append(
                f"| {icon} {finding.severity} | {finding.line} | "
                f"`{finding.pattern_id}` | {finding.message} | {finding.suggestion} |"
            )

    report_content = "\n".join(report_lines)

    # active_agent already validated above, safe to use
    # Fallback to platform_engineer if agent is "unknown" or None
    agent = (
        active_agent
        if active_agent and active_agent != "unknown"
        else "platform_engineer"
    )
    report_name = f"ai_patterns_{p.stem}"
    title = f"AI Pattern Analysis: {p.name}"

    try:
        report_path = write_report(agent, report_name, report_content, title=title)
        return f"Analysis complete. Report: `{report_path}`\n\n{report_content}"
    except OSError as e:
        return f"Analysis complete (report save failed: {e}):\n\n{report_content}"
