"""Tests for Configuration Loader.

Real execution tests - no mocking of code under test.
"""

import pytest

from sef_agents.core.config_loader import (
    ConfigLoader,
    DebtPattern,
    LanguageConfig,
    NamingRules,
    Thresholds,
    get_config_loader,
    load_config,
)


class TestDebtPattern:
    """Tests for DebtPattern dataclass."""

    def test_create_pattern(self) -> None:
        """Test DebtPattern creation."""
        pattern = DebtPattern(
            name="todo_fixme",
            description="TODO comments",
            severity="medium",
            pattern=r"#\s*TODO",
            suggestion="Address the TODO",
        )

        assert pattern.name == "todo_fixme"
        assert pattern.severity == "medium"


class TestLanguageConfig:
    """Tests for LanguageConfig dataclass."""

    def test_create_config(self) -> None:
        """Test LanguageConfig creation."""
        config = LanguageConfig(
            language="python",
            extensions=[".py"],
            parser="ast",
        )

        assert config.language == "python"
        assert ".py" in config.extensions

    def test_merge_framework(self) -> None:
        """Test merging framework config into base config."""
        base = LanguageConfig(
            language="typescript",
            extensions=[".ts"],
            debt_patterns=[
                DebtPattern(name="any_type", description="Using any", severity="high")
            ],
            deprecated_imports={"tslint": "Use ESLint"},
            naming=NamingRules(generic_names=["data", "result"]),
            thresholds=Thresholds(complexity=15),
        )

        framework = LanguageConfig(
            language="typescript",
            framework="react",
            debt_patterns=[
                DebtPattern(
                    name="missing_key", description="Missing key prop", severity="high"
                )
            ],
            deprecated_imports={"enzyme": "Use React Testing Library"},
            naming=NamingRules(generic_names=["handler", "callback"]),
            thresholds=Thresholds(complexity=12),
        )

        merged = base.merge_framework(framework)

        # Framework should be set
        assert merged.framework == "react"

        # Patterns should be combined
        pattern_names = [p.name for p in merged.debt_patterns]
        assert "any_type" in pattern_names
        assert "missing_key" in pattern_names

        # Deprecated imports merged
        assert "tslint" in merged.deprecated_imports
        assert "enzyme" in merged.deprecated_imports

        # Naming rules merged
        assert "data" in merged.naming.generic_names
        assert "handler" in merged.naming.generic_names

        # Framework thresholds override
        assert merged.thresholds.complexity == 12


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_load_python_config(self) -> None:
        """Test loading Python configuration."""
        loader = ConfigLoader()
        config = loader.load_language("python")

        assert config.language == "python"
        assert ".py" in config.extensions
        assert config.parser == "ast"
        assert len(config.debt_patterns) > 0
        assert "distutils" in config.deprecated_imports

    def test_load_typescript_config(self) -> None:
        """Test loading TypeScript configuration."""
        loader = ConfigLoader()
        config = loader.load_language("typescript")

        assert config.language == "typescript"
        assert ".ts" in config.extensions
        assert len(config.debt_patterns) > 0

    def test_load_javascript_config(self) -> None:
        """Test loading JavaScript configuration."""
        loader = ConfigLoader()
        config = loader.load_language("javascript")

        assert config.language == "javascript"
        assert ".js" in config.extensions

    def test_load_java_config(self) -> None:
        """Test loading Java configuration."""
        loader = ConfigLoader()
        config = loader.load_language("java")

        assert config.language == "java"
        assert ".java" in config.extensions

    def test_load_react_framework(self) -> None:
        """Test loading React framework config."""
        loader = ConfigLoader()
        config = loader.load_framework("react")

        assert config.framework == "react"
        pattern_names = [p.name for p in config.debt_patterns]
        assert "missing_key_prop" in pattern_names

    def test_load_angular_framework(self) -> None:
        """Test loading Angular framework config."""
        loader = ConfigLoader()
        config = loader.load_framework("angular")

        assert config.framework == "angular"
        pattern_names = [p.name for p in config.debt_patterns]
        assert "subscribe_without_unsubscribe" in pattern_names

    def test_load_spring_boot_framework(self) -> None:
        """Test loading Spring Boot framework config."""
        loader = ConfigLoader()
        config = loader.load_framework("spring_boot")

        assert config.framework == "spring_boot"
        pattern_names = [p.name for p in config.debt_patterns]
        assert "field_injection" in pattern_names

    def test_load_merged_config(self) -> None:
        """Test loading language with framework overlay."""
        loader = ConfigLoader()
        config = loader.load("typescript", "react")

        assert config.language == "typescript"
        assert config.framework == "react"

        # Should have both base and framework patterns
        pattern_names = [p.name for p in config.debt_patterns]
        assert "any_type" in pattern_names  # From TypeScript
        assert "missing_key_prop" in pattern_names  # From React

    def test_load_nonexistent_language(self) -> None:
        """Test loading non-existent language config."""
        loader = ConfigLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_language("cobol")

    def test_load_with_missing_framework(self) -> None:
        """Test loading with non-existent framework falls back to base."""
        loader = ConfigLoader()
        config = loader.load("python", "nonexistent_framework")

        # Should return base config without error
        assert config.language == "python"
        assert config.framework is None

    def test_config_caching(self) -> None:
        """Test that configs are cached."""
        loader = ConfigLoader()

        config1 = loader.load_language("python")
        config2 = loader.load_language("python")

        # Should be same object (cached)
        assert config1 is config2

    def test_get_available_languages(self) -> None:
        """Test listing available languages."""
        loader = ConfigLoader()
        languages = loader.get_available_languages()

        assert "python" in languages
        assert "typescript" in languages
        assert "javascript" in languages
        assert "java" in languages

    def test_get_available_frameworks(self) -> None:
        """Test listing available frameworks."""
        loader = ConfigLoader()
        frameworks = loader.get_available_frameworks()

        assert "react" in frameworks
        assert "angular" in frameworks
        assert "spring_boot" in frameworks


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_config_loader(self) -> None:
        """Test singleton config loader."""
        loader1 = get_config_loader()
        loader2 = get_config_loader()

        assert loader1 is loader2

    def test_load_config_function(self) -> None:
        """Test load_config convenience function."""
        config = load_config("python")

        assert config.language == "python"

    def test_load_config_with_framework(self) -> None:
        """Test load_config with framework."""
        config = load_config("java", "spring_boot")

        assert config.language == "java"
        assert config.framework == "spring_boot"


class TestConfigContent:
    """Tests for specific config content."""

    def test_python_has_required_patterns(self) -> None:
        """Test Python config has expected debt patterns."""
        loader = ConfigLoader()
        config = loader.load_language("python")

        pattern_names = [p.name for p in config.debt_patterns]

        assert "todo_fixme" in pattern_names
        assert "bare_except" in pattern_names
        assert "missing_type_hints" in pattern_names
        assert "high_complexity" in pattern_names

    def test_python_thresholds(self) -> None:
        """Test Python config has reasonable thresholds."""
        loader = ConfigLoader()
        config = loader.load_language("python")

        assert config.thresholds.complexity == 12
        assert config.thresholds.function_length == 50
        assert config.thresholds.nesting_depth == 3

    def test_typescript_any_type_pattern(self) -> None:
        """Test TypeScript has any_type pattern."""
        loader = ConfigLoader()
        config = loader.load_language("typescript")

        pattern_names = [p.name for p in config.debt_patterns]
        assert "any_type" in pattern_names

    def test_java_deprecated_imports(self) -> None:
        """Test Java has deprecated imports."""
        loader = ConfigLoader()
        config = loader.load_language("java")

        assert "java.util.Date" in config.deprecated_imports
        assert "java.util.Vector" in config.deprecated_imports

    def test_react_specific_patterns(self) -> None:
        """Test React has framework-specific patterns."""
        loader = ConfigLoader()
        config = loader.load_framework("react")

        pattern_names = [p.name for p in config.debt_patterns]
        assert "missing_key_prop" in pattern_names
        assert "state_mutation" in pattern_names
        assert "deprecated_lifecycle" in pattern_names
