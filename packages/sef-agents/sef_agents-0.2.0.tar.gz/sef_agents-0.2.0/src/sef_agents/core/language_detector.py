"""Language Detection for SEF Agents.

Detects programming language and framework from file extensions and content.
Used to load appropriate configuration for debt scanning and pattern detection.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LanguageInfo:
    """Information about detected language and framework.

    Attributes:
        language: Primary language (python, typescript, javascript, java).
        framework: Detected framework (react, angular, spring_boot) or None.
        extensions: File extensions for this language.
        confidence: Detection confidence (0.0-1.0).
    """

    language: str
    framework: str | None = None
    extensions: list[str] = field(default_factory=list)
    confidence: float = 1.0

    def __str__(self) -> str:
        """Return string representation."""
        if self.framework:
            return f"{self.language}/{self.framework}"
        return self.language


# Language definitions
LANGUAGE_EXTENSIONS: dict[str, list[str]] = {
    "python": [".py", ".pyw", ".pyi"],
    "typescript": [".ts", ".tsx", ".mts", ".cts"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "java": [".java"],
}

# Framework detection patterns (file content or project structure)
FRAMEWORK_PATTERNS: dict[str, dict[str, Any]] = {
    "react": {
        "languages": ["typescript", "javascript"],
        "imports": [
            r"from\s+['\"]react['\"]",
            r"import\s+.*\s+from\s+['\"]react['\"]",
            r"require\(['\"]react['\"]\)",
        ],
        "files": ["package.json"],
        "package_deps": ["react", "react-dom"],
    },
    "angular": {
        "languages": ["typescript"],
        "imports": [
            r"from\s+['\"]@angular/",
            r"import\s+.*\s+from\s+['\"]@angular/",
        ],
        "files": ["angular.json", "package.json"],
        "package_deps": ["@angular/core"],
        "decorators": ["@Component", "@NgModule", "@Injectable"],
    },
    "spring_boot": {
        "languages": ["java"],
        "imports": [
            r"import\s+org\.springframework\.",
            r"import\s+org\.springframework\.boot\.",
        ],
        "files": ["pom.xml", "build.gradle"],
        "annotations": [
            "@SpringBootApplication",
            "@RestController",
            "@Service",
            "@Repository",
        ],
    },
}


class LanguageDetector:
    """Detects programming language and framework from files.

    Attributes:
        project_root: Root directory of the project.
        _framework_cache: Cached framework detection results.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize language detector.

        Args:
            project_root: Project root for framework detection. Defaults to cwd.
        """
        self.project_root = project_root or Path.cwd()
        self._framework_cache: dict[str, str | None] = {}

    def detect_from_extension(self, file_path: Path | str) -> str | None:
        """Detect language from file extension.

        Args:
            file_path: Path to file.

        Returns:
            Language name or None if unknown.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        for language, extensions in LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                return language

        return None

    def detect_framework_from_content(
        self,
        content: str,
        language: str,
    ) -> str | None:
        """Detect framework from file content.

        Args:
            content: File content.
            language: Detected language.

        Returns:
            Framework name or None.
        """
        for framework, patterns in FRAMEWORK_PATTERNS.items():
            if language not in patterns.get("languages", []):
                continue

            # Check import patterns
            for pattern in patterns.get("imports", []):
                if re.search(pattern, content):
                    logger.debug(
                        "framework_detected_from_import",
                        framework=framework,
                        pattern=pattern,
                    )
                    return framework

            # Check decorators/annotations
            for decorator in patterns.get("decorators", []) + patterns.get(
                "annotations", []
            ):
                if decorator in content:
                    logger.debug(
                        "framework_detected_from_decorator",
                        framework=framework,
                        decorator=decorator,
                    )
                    return framework

        return None

    def _check_package_json_deps(
        self, file_path: Path, deps_to_check: list[str]
    ) -> bool:
        """Check if package.json contains specific dependencies."""
        try:
            pkg = json.loads(file_path.read_text())
            deps = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {}),
            }
            for dep in deps_to_check:
                if dep in deps:
                    return True
        except (json.JSONDecodeError, OSError):
            pass
        return False

    def _check_framework_match(self, framework: str, patterns: dict[str, Any]) -> bool:
        """Check if project matches framework patterns."""
        for filename in patterns.get("files", []):
            file_path = self.project_root / filename
            if not file_path.exists():
                continue

            # For package.json, check dependencies
            if filename == "package.json":
                if self._check_package_json_deps(
                    file_path, patterns.get("package_deps", [])
                ):
                    return True
            # For pom.xml/build.gradle, presence is enough
            elif filename in ("pom.xml", "build.gradle", "angular.json"):
                if filename == "angular.json":
                    return True
                elif framework == "spring_boot":
                    try:
                        build_content = file_path.read_text()
                        if "spring-boot" in build_content.lower():
                            return True
                    except OSError:
                        pass
        return False

    def detect_framework_from_project(self) -> str | None:
        """Detect framework from project structure.

        Returns:
            Framework name or None.
        """
        # Check cache
        cache_key = str(self.project_root)
        if cache_key in self._framework_cache:
            return self._framework_cache[cache_key]

        detected: str | None = None

        for framework, patterns in FRAMEWORK_PATTERNS.items():
            if self._check_framework_match(framework, patterns):
                detected = framework
                break

        self._framework_cache[cache_key] = detected
        return detected

    def detect(self, file_path: Path | str) -> LanguageInfo:
        """Detect language and framework for a file.

        Args:
            file_path: Path to file.

        Returns:
            LanguageInfo with detected language and framework.
        """
        path = Path(file_path)

        # Detect language from extension
        language = self.detect_from_extension(path)

        if not language:
            logger.debug("unknown_language", file=str(path))
            return LanguageInfo(
                language="unknown",
                confidence=0.0,
            )

        # Detect framework from project structure first (cached)
        framework = self.detect_framework_from_project()

        # If no framework from project, try from file content
        if not framework and path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                framework = self.detect_framework_from_content(content, language)
            except (OSError, UnicodeDecodeError):
                pass

        # Validate framework matches language
        if framework:
            expected_langs = FRAMEWORK_PATTERNS.get(framework, {}).get("languages", [])
            if language not in expected_langs:
                framework = None

        return LanguageInfo(
            language=language,
            framework=framework,
            extensions=LANGUAGE_EXTENSIONS.get(language, []),
            confidence=1.0 if language != "unknown" else 0.0,
        )

    def detect_directory(self, directory: Path | str) -> dict[str, int]:
        """Detect language distribution in a directory.

        Args:
            directory: Directory to scan.

        Returns:
            Dict mapping language to file count.
        """
        dir_path = Path(directory)
        counts: dict[str, int] = {}

        if not dir_path.exists():
            return counts

        exclude_dirs = {
            "__pycache__",
            "node_modules",
            ".git",
            ".venv",
            "venv",
            "dist",
            "build",
            "target",
        }

        for ext_list in LANGUAGE_EXTENSIONS.values():
            for ext in ext_list:
                for file_path in dir_path.rglob(f"*{ext}"):
                    if any(excluded in file_path.parts for excluded in exclude_dirs):
                        continue

                    info = self.detect(file_path)
                    lang_key = str(info)
                    counts[lang_key] = counts.get(lang_key, 0) + 1

        return counts


def detect_language(file_path: str) -> str:
    """Detect language for a file (convenience function).

    Args:
        file_path: Path to file.

    Returns:
        Language string (e.g., "python", "typescript/react").
    """
    detector = LanguageDetector()
    info = detector.detect(file_path)
    return str(info)


def get_supported_languages() -> list[str]:
    """Get list of supported languages.

    Returns:
        List of language names.
    """
    return list(LANGUAGE_EXTENSIONS.keys())


def get_supported_frameworks() -> list[str]:
    """Get list of supported frameworks.

    Returns:
        List of framework names.
    """
    return list(FRAMEWORK_PATTERNS.keys())
