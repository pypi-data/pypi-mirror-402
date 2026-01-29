"""Configuration Loader for SEF Agents.

Loads language-specific and framework-specific configurations for
debt scanning, pattern detection, and compliance checking.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# Default config directory
CONFIG_ROOT = Path(__file__).parent.parent / "config"


@dataclass
class DebtPattern:
    """Technical debt pattern definition.

    Attributes:
        name: Pattern identifier.
        description: Human-readable description.
        severity: critical, high, medium, low.
        pattern: Regex pattern (if regex-based).
        ast_node: AST node type (if AST-based).
        condition: Additional condition for AST matching.
        suggestion: Fix suggestion.
    """

    name: str
    description: str
    severity: str = "medium"
    pattern: str | None = None
    ast_node: str | None = None
    condition: str | None = None
    suggestion: str = ""


@dataclass
class NamingRules:
    """Naming convention rules.

    Attributes:
        generic_names: Names considered too generic.
        conventions: Naming conventions (snake_case, camelCase, etc.).
    """

    generic_names: list[str] = field(default_factory=list)
    conventions: dict[str, str] = field(default_factory=dict)


@dataclass
class Thresholds:
    """Code quality thresholds.

    Attributes:
        complexity: Max cyclomatic complexity (legacy, use function_complexity_block).
        function_complexity_warn: Per-function cognitive complexity warning threshold.
        function_complexity_block: Per-function cognitive complexity blocker threshold.
        file_complexity_warn: Aggregate file complexity warning threshold.
        file_complexity_block: Aggregate file complexity blocker threshold.
        function_length: Max function lines.
        nesting_depth: Max nesting levels.
        file_length: Max file lines.
        comment_ratio: Max comment-to-code ratio.
        class_ratio: Max class-to-function ratio.
    """

    complexity: int = 15  # Legacy fallback
    function_complexity_warn: int | None = None
    function_complexity_block: int | None = None
    file_complexity_warn: int | None = None
    file_complexity_block: int | None = None
    function_length: int = 100
    nesting_depth: int = 4
    file_length: int = 500
    comment_ratio: float = 0.4
    class_ratio: float = 0.5

    def __post_init__(self):
        """Set defaults for dual thresholds if not provided."""
        if self.function_complexity_warn is None:
            self.function_complexity_warn = 15
        if self.function_complexity_block is None:
            self.function_complexity_block = 25
        if self.file_complexity_warn is None:
            self.file_complexity_warn = 80
        if self.file_complexity_block is None:
            self.file_complexity_block = 150


@dataclass
class LanguageConfig:
    """Complete language configuration.

    Attributes:
        language: Language name.
        extensions: File extensions.
        framework: Framework name (if applicable).
        debt_patterns: Debt detection patterns.
        deprecated_imports: Deprecated import mappings.
        naming: Naming rules.
        thresholds: Quality thresholds.
        anti_patterns: AI anti-pattern rules.
        parser: Parser type (ast, regex, tree-sitter).
    """

    language: str
    extensions: list[str] = field(default_factory=list)
    framework: str | None = None
    debt_patterns: list[DebtPattern] = field(default_factory=list)
    deprecated_imports: dict[str, str] = field(default_factory=dict)
    naming: NamingRules = field(default_factory=NamingRules)
    thresholds: Thresholds = field(default_factory=Thresholds)
    anti_patterns: dict[str, Any] = field(default_factory=dict)
    parser: str = "regex"
    exclusions: dict[str, list[str]] = field(default_factory=dict)

    def merge_framework(self, framework_config: "LanguageConfig") -> "LanguageConfig":
        """Merge framework-specific config on top of base config.

        Args:
            framework_config: Framework configuration to merge.

        Returns:
            New merged configuration.
        """
        # Deep merge patterns
        merged_patterns = self.debt_patterns.copy()
        pattern_names = {p.name for p in merged_patterns}
        for pattern in framework_config.debt_patterns:
            if pattern.name not in pattern_names:
                merged_patterns.append(pattern)

        # Merge deprecated imports
        merged_deprecated = {
            **self.deprecated_imports,
            **framework_config.deprecated_imports,
        }

        # Merge naming rules
        merged_naming = NamingRules(
            generic_names=list(
                set(self.naming.generic_names + framework_config.naming.generic_names)
            ),
            conventions={
                **self.naming.conventions,
                **framework_config.naming.conventions,
            },
        )

        # Use framework thresholds if specified, else base
        merged_thresholds = Thresholds(
            complexity=framework_config.thresholds.complexity
            or self.thresholds.complexity,
            function_length=framework_config.thresholds.function_length
            or self.thresholds.function_length,
            nesting_depth=framework_config.thresholds.nesting_depth
            or self.thresholds.nesting_depth,
            file_length=framework_config.thresholds.file_length
            or self.thresholds.file_length,
            comment_ratio=framework_config.thresholds.comment_ratio
            or self.thresholds.comment_ratio,
            class_ratio=framework_config.thresholds.class_ratio
            or self.thresholds.class_ratio,
        )

        # Merge anti-patterns
        merged_anti = {**self.anti_patterns, **framework_config.anti_patterns}

        return LanguageConfig(
            language=self.language,
            extensions=self.extensions,
            framework=framework_config.framework,
            debt_patterns=merged_patterns,
            deprecated_imports=merged_deprecated,
            naming=merged_naming,
            thresholds=merged_thresholds,
            anti_patterns=merged_anti,
            parser=self.parser,
        )


class ConfigLoader:
    """Loads and caches language/framework configurations.

    Attributes:
        config_root: Root directory for config files.
        _cache: Cached configurations.
    """

    def __init__(self, config_root: Path | None = None) -> None:
        """Initialize config loader.

        Args:
            config_root: Config directory. Defaults to src/sef_agents/config.
        """
        self.config_root = config_root or CONFIG_ROOT
        self._cache: dict[str, LanguageConfig] = {}

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load YAML file.

        Args:
            path: Path to YAML file.

        Returns:
            Parsed YAML content.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        if not path.exists():
            raise FileNotFoundError(f"Config not found: {path}")

        try:
            import yaml

            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except ImportError:
            logger.error("yaml_not_installed", msg="Install PyYAML: pip install pyyaml")
            raise

    def _parse_config(self, data: dict[str, Any]) -> LanguageConfig:
        """Parse raw config dict into LanguageConfig.

        Args:
            data: Raw config dictionary.

        Returns:
            Parsed LanguageConfig.
        """
        # Parse debt patterns
        patterns = []
        for name, pattern_data in data.get("debt_patterns", {}).items():
            if isinstance(pattern_data, dict):
                patterns.append(
                    DebtPattern(
                        name=name,
                        description=pattern_data.get("description", ""),
                        severity=pattern_data.get("severity", "medium"),
                        pattern=pattern_data.get("pattern"),
                        ast_node=pattern_data.get("ast_node"),
                        condition=pattern_data.get("condition"),
                        suggestion=pattern_data.get("suggestion", ""),
                    )
                )

        # Parse naming rules
        naming_data = data.get("naming", {})
        naming = NamingRules(
            generic_names=naming_data.get("generic_names", []),
            conventions=naming_data.get("conventions", {}),
        )

        # Parse thresholds
        thresh_data = data.get("thresholds", {})
        thresholds = Thresholds(
            complexity=thresh_data.get("complexity", 15),
            function_complexity_warn=thresh_data.get("function_complexity_warn"),
            function_complexity_block=thresh_data.get("function_complexity_block"),
            file_complexity_warn=thresh_data.get("file_complexity_warn"),
            file_complexity_block=thresh_data.get("file_complexity_block"),
            function_length=thresh_data.get("function_length", 100),
            nesting_depth=thresh_data.get("nesting_depth", 4),
            file_length=thresh_data.get("file_length", 500),
            comment_ratio=thresh_data.get("comment_ratio", 0.4),
            class_ratio=thresh_data.get("class_ratio", 0.5),
        )

        return LanguageConfig(
            language=data.get("language", "unknown"),
            extensions=data.get("extensions", []),
            framework=data.get("framework"),
            debt_patterns=patterns,
            deprecated_imports=data.get("deprecated_imports", {}),
            naming=naming,
            thresholds=thresholds,
            anti_patterns=data.get("anti_patterns", {}),
            parser=data.get("parser", "regex"),
            exclusions=data.get("exclusions", {}),
        )

    def load_language(self, language: str) -> LanguageConfig:
        """Load configuration for a language.

        Args:
            language: Language name (python, typescript, javascript, java).

        Returns:
            LanguageConfig for the language.

        Raises:
            FileNotFoundError: If config file not found.
        """
        cache_key = language

        if cache_key in self._cache:
            return self._cache[cache_key]

        config_path = self.config_root / "languages" / f"{language}.yaml"
        data = self._load_yaml(config_path)
        config = self._parse_config(data)

        self._cache[cache_key] = config
        logger.debug("config_loaded", language=language)

        return config

    def load_framework(self, framework: str) -> LanguageConfig:
        """Load configuration for a framework.

        Args:
            framework: Framework name (react, angular, spring_boot).

        Returns:
            LanguageConfig for the framework.

        Raises:
            FileNotFoundError: If config file not found.
        """
        config_path = self.config_root / "frameworks" / f"{framework}.yaml"
        data = self._load_yaml(config_path)
        return self._parse_config(data)

    def load(self, language: str, framework: str | None = None) -> LanguageConfig:
        """Load configuration for language with optional framework overlay.

        Args:
            language: Language name.
            framework: Optional framework name.

        Returns:
            Merged LanguageConfig.
        """
        cache_key = f"{language}/{framework}" if framework else language

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Load base language config
        base_config = self.load_language(language)

        # Merge framework config if specified
        if framework:
            try:
                framework_config = self.load_framework(framework)
                merged = base_config.merge_framework(framework_config)
                self._cache[cache_key] = merged
                return merged
            except FileNotFoundError:
                logger.warning(
                    "framework_config_not_found",
                    framework=framework,
                    using="base_language_config",
                )

        return base_config

    def get_available_languages(self) -> list[str]:
        """Get list of available language configs.

        Returns:
            List of language names.
        """
        lang_dir = self.config_root / "languages"
        if not lang_dir.exists():
            return []

        return [p.stem for p in lang_dir.glob("*.yaml")]

    def get_available_frameworks(self) -> list[str]:
        """Get list of available framework configs.

        Returns:
            List of framework names.
        """
        fw_dir = self.config_root / "frameworks"
        if not fw_dir.exists():
            return []

        return [p.stem for p in fw_dir.glob("*.yaml")]


# Singleton instance
_default_loader: ConfigLoader | None = None


def get_config_loader() -> ConfigLoader:
    """Get default ConfigLoader instance.

    Returns:
        Singleton ConfigLoader.
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = ConfigLoader()
    return _default_loader


def load_config(language: str, framework: str | None = None) -> LanguageConfig:
    """Load configuration (convenience function).

    Args:
        language: Language name.
        framework: Optional framework name.

    Returns:
        LanguageConfig.
    """
    return get_config_loader().load(language, framework)
