"""Tests for Language Detector.

Real execution tests - no mocking of code under test.
"""

import json
from pathlib import Path


from sef_agents.core.language_detector import (
    LanguageDetector,
    LanguageInfo,
    detect_language,
    get_supported_frameworks,
    get_supported_languages,
)


class TestLanguageInfo:
    """Tests for LanguageInfo dataclass."""

    def test_create_language_info(self) -> None:
        """Test LanguageInfo creation."""
        info = LanguageInfo(
            language="python",
            framework="django",
            extensions=[".py"],
            confidence=1.0,
        )

        assert info.language == "python"
        assert info.framework == "django"
        assert str(info) == "python/django"

    def test_language_only(self) -> None:
        """Test LanguageInfo without framework."""
        info = LanguageInfo(language="java")

        assert info.framework is None
        assert str(info) == "java"


class TestLanguageDetector:
    """Tests for LanguageDetector class."""

    def test_detect_python(self, tmp_path: Path) -> None:
        """Test Python detection."""
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')")

        detector = LanguageDetector()
        info = detector.detect(py_file)

        assert info.language == "python"
        assert info.confidence == 1.0

    def test_detect_typescript(self, tmp_path: Path) -> None:
        """Test TypeScript detection."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("const x: number = 1;")

        detector = LanguageDetector()
        info = detector.detect(ts_file)

        assert info.language == "typescript"

    def test_detect_tsx(self, tmp_path: Path) -> None:
        """Test TSX detection."""
        tsx_file = tmp_path / "component.tsx"
        tsx_file.write_text("export const App = () => <div>Hello</div>;")

        detector = LanguageDetector()
        info = detector.detect(tsx_file)

        assert info.language == "typescript"

    def test_detect_javascript(self, tmp_path: Path) -> None:
        """Test JavaScript detection."""
        js_file = tmp_path / "test.js"
        js_file.write_text("const x = 1;")

        detector = LanguageDetector()
        info = detector.detect(js_file)

        assert info.language == "javascript"

    def test_detect_java(self, tmp_path: Path) -> None:
        """Test Java detection."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("public class Test {}")

        detector = LanguageDetector()
        info = detector.detect(java_file)

        assert info.language == "java"

    def test_detect_unknown(self, tmp_path: Path) -> None:
        """Test unknown file type."""
        unknown_file = tmp_path / "test.xyz"
        unknown_file.write_text("unknown content")

        detector = LanguageDetector()
        info = detector.detect(unknown_file)

        assert info.language == "unknown"
        assert info.confidence == 0.0


class TestFrameworkDetection:
    """Tests for framework detection."""

    def test_detect_react_from_import(self, tmp_path: Path) -> None:
        """Test React detection from import statement."""
        tsx_file = tmp_path / "App.tsx"
        tsx_file.write_text("""
import React from 'react';
export const App = () => <div>Hello</div>;
""")

        detector = LanguageDetector(project_root=tmp_path)
        info = detector.detect(tsx_file)

        assert info.language == "typescript"
        assert info.framework == "react"

    def test_detect_angular_from_import(self, tmp_path: Path) -> None:
        """Test Angular detection from import statement."""
        ts_file = tmp_path / "app.component.ts"
        ts_file.write_text("""
import { Component } from '@angular/core';
@Component({ selector: 'app-root' })
export class AppComponent {}
""")

        detector = LanguageDetector(project_root=tmp_path)
        info = detector.detect(ts_file)

        assert info.language == "typescript"
        assert info.framework == "angular"

    def test_detect_spring_boot_from_import(self, tmp_path: Path) -> None:
        """Test Spring Boot detection from import statement."""
        java_file = tmp_path / "Application.java"
        java_file.write_text("""
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
""")

        detector = LanguageDetector(project_root=tmp_path)
        info = detector.detect(java_file)

        assert info.language == "java"
        assert info.framework == "spring_boot"

    def test_detect_react_from_package_json(self, tmp_path: Path) -> None:
        """Test React detection from package.json."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps({"dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}})
        )

        ts_file = tmp_path / "App.tsx"
        ts_file.write_text("export const App = () => <div>Hello</div>;")

        detector = LanguageDetector(project_root=tmp_path)
        info = detector.detect(ts_file)

        assert info.framework == "react"

    def test_detect_angular_from_angular_json(self, tmp_path: Path) -> None:
        """Test Angular detection from angular.json."""
        angular_json = tmp_path / "angular.json"
        angular_json.write_text(json.dumps({"projects": {}}))

        ts_file = tmp_path / "app.ts"
        ts_file.write_text("const x = 1;")

        detector = LanguageDetector(project_root=tmp_path)
        # Force project detection
        framework = detector.detect_framework_from_project()

        assert framework == "angular"


class TestDirectoryScan:
    """Tests for directory scanning."""

    def test_detect_directory(self, tmp_path: Path) -> None:
        """Test language distribution in directory."""
        # Create files
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def util(): pass")
        (tmp_path / "app.ts").write_text("const x = 1;")

        detector = LanguageDetector(project_root=tmp_path)
        counts = detector.detect_directory(tmp_path)

        assert counts.get("python", 0) == 2
        assert counts.get("typescript", 0) == 1

    def test_excludes_node_modules(self, tmp_path: Path) -> None:
        """Test that node_modules is excluded."""
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "lib.js").write_text("const x = 1;")

        (tmp_path / "app.js").write_text("const y = 2;")

        detector = LanguageDetector(project_root=tmp_path)
        counts = detector.detect_directory(tmp_path)

        assert counts.get("javascript", 0) == 1


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_detect_language_function(self, tmp_path: Path) -> None:
        """Test detect_language function."""
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1")

        result = detect_language(str(py_file))

        assert result == "python"

    def test_get_supported_languages(self) -> None:
        """Test get_supported_languages function."""
        languages = get_supported_languages()

        assert "python" in languages
        assert "typescript" in languages
        assert "javascript" in languages
        assert "java" in languages

    def test_get_supported_frameworks(self) -> None:
        """Test get_supported_frameworks function."""
        frameworks = get_supported_frameworks()

        assert "react" in frameworks
        assert "angular" in frameworks
        assert "spring_boot" in frameworks
