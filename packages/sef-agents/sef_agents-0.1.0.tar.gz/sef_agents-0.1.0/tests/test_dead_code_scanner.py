"""Tests for dead code scanner module."""

import tempfile
from pathlib import Path


from sef_agents.tools.dead_code_scanner import (
    DeadCodeScanner,
    UnusedImportDetector,
    scan_dead_code,
)
from sef_agents.utils.ignore_matcher import (
    IgnorePatternMatcher,
    is_intentionally_ignored,
)


class TestIgnorePatternMatcher:
    """Tests for IgnorePatternMatcher."""

    def test_empty_matcher_ignores_nothing(self) -> None:
        """Empty matcher should not ignore any files."""
        matcher = IgnorePatternMatcher()
        assert not matcher.is_ignored(Path("test.py"))
        assert not matcher.is_ignored(Path("src/main.py"))

    def test_simple_pattern(self) -> None:
        """Test simple glob patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create .gitignore
            gitignore = tmp_path / ".gitignore"
            gitignore.write_text("*.pyc\n__pycache__/\n")

            matcher = IgnorePatternMatcher.from_file(gitignore, tmp_path)

            assert matcher.is_ignored(Path("test.pyc"))
            assert matcher.is_ignored(Path("src/test.pyc"))
            assert matcher.is_ignored(Path("__pycache__"), is_dir=True)
            assert not matcher.is_ignored(Path("test.py"))

    def test_negation_pattern(self) -> None:
        """Test negation patterns (!)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            gitignore = tmp_path / ".gitignore"
            gitignore.write_text("*.log\n!important.log\n")

            matcher = IgnorePatternMatcher.from_file(gitignore, tmp_path)

            assert matcher.is_ignored(Path("debug.log"))
            assert not matcher.is_ignored(Path("important.log"))

    def test_directory_only_pattern(self) -> None:
        """Test directory-only patterns (ending with /)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            gitignore = tmp_path / ".gitignore"
            gitignore.write_text("build/\n")

            matcher = IgnorePatternMatcher.from_file(gitignore, tmp_path)

            assert matcher.is_ignored(Path("build"), is_dir=True)
            assert not matcher.is_ignored(Path("build"))  # File named build

    def test_doublestar_pattern(self) -> None:
        """Test ** pattern matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            gitignore = tmp_path / ".gitignore"
            gitignore.write_text("**/test_*.py\n")

            matcher = IgnorePatternMatcher.from_file(gitignore, tmp_path)

            assert matcher.is_ignored(Path("test_main.py"))
            assert matcher.is_ignored(Path("src/test_main.py"))
            assert matcher.is_ignored(Path("src/deep/nested/test_main.py"))
            assert not matcher.is_ignored(Path("main.py"))

    def test_from_directory_loads_multiple_files(self) -> None:
        """Test loading from both .gitignore and .dockerignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / ".gitignore").write_text("*.pyc\n")
            (tmp_path / ".dockerignore").write_text("*.log\n")

            matcher = IgnorePatternMatcher.from_directory(tmp_path)

            assert matcher.is_ignored(Path("test.pyc"))
            assert matcher.is_ignored(Path("debug.log"))
            assert not matcher.is_ignored(Path("main.py"))

    def test_filter_paths(self) -> None:
        """Test filtering list of paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            gitignore = tmp_path / ".gitignore"
            gitignore.write_text("*.pyc\n")

            # Create actual files for is_dir check
            (tmp_path / "main.py").write_text("")
            (tmp_path / "test.pyc").write_text("")

            matcher = IgnorePatternMatcher.from_file(gitignore, tmp_path)

            paths = [tmp_path / "main.py", tmp_path / "test.pyc"]
            filtered = matcher.filter_paths(paths)

            assert len(filtered) == 1
            assert filtered[0].name == "main.py"


class TestUnusedImportDetector:
    """Tests for UnusedImportDetector."""

    def test_detects_unused_import(self) -> None:
        """Test detection of unused import."""
        import ast

        code = """
import os
import sys

print(sys.version)
"""
        tree = ast.parse(code)
        detector = UnusedImportDetector()
        detector.visit(tree)
        unused = detector.get_unused_imports()

        assert "os" in unused
        assert "sys" not in unused

    def test_detects_unused_from_import(self) -> None:
        """Test detection of unused from...import."""
        import ast

        code = """
from pathlib import Path, PurePath
from typing import List

x: List[Path] = []
"""
        tree = ast.parse(code)
        detector = UnusedImportDetector()
        detector.visit(tree)
        unused = detector.get_unused_imports()

        assert "PurePath" in unused
        assert "Path" not in unused
        assert "List" not in unused

    def test_handles_aliased_imports(self) -> None:
        """Test handling of aliased imports."""
        import ast

        code = """
import numpy as np
import pandas as pd

df = pd.DataFrame()
"""
        tree = ast.parse(code)
        detector = UnusedImportDetector()
        detector.visit(tree)
        unused = detector.get_unused_imports()

        assert "np" in unused
        assert "pd" not in unused

    def test_handles_attribute_access(self) -> None:
        """Test that module.attribute counts as usage."""
        import ast

        code = """
import os

path = os.path.join("a", "b")
"""
        tree = ast.parse(code)
        detector = UnusedImportDetector()
        detector.visit(tree)
        unused = detector.get_unused_imports()

        assert "os" not in unused

    def test_skips_type_checking_imports(self) -> None:
        """Test that TYPE_CHECKING imports are skipped."""
        import ast

        code = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mymodule import MyClass
"""
        tree = ast.parse(code)
        detector = UnusedImportDetector()
        detector.visit(tree)
        unused = detector.get_unused_imports()

        # TYPE_CHECKING should be excluded from unused
        assert "TYPE_CHECKING" not in unused


class TestDeadCodeScanner:
    """Tests for DeadCodeScanner."""

    def test_scans_unused_imports_in_file(self) -> None:
        """Test scanning single file for unused imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create Python file with unused import
            py_file = tmp_path / "test.py"
            py_file.write_text("import os\nimport sys\nprint(sys.version)\n")

            scanner = DeadCodeScanner(tmp_path)
            items = scanner.scan_unused_imports(py_file)

            assert len(items) == 1
            assert items[0].debt_type == "unused-import"
            assert "os" in items[0].description

    def test_skips_excluded_directories(self) -> None:
        """Test that excluded directories are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create file in excluded directory
            pycache = tmp_path / "__pycache__"
            pycache.mkdir()
            (pycache / "test.py").write_text("import os\n")

            scanner = DeadCodeScanner(tmp_path)
            items = scanner.scan_unused_imports(pycache / "test.py")

            assert len(items) == 0

    def test_skips_gitignored_files(self) -> None:
        """Test that .gitignore patterns are respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create .gitignore
            (tmp_path / ".gitignore").write_text("generated/\n")

            # Create file in ignored directory
            generated = tmp_path / "generated"
            generated.mkdir()
            (generated / "test.py").write_text("import os\n")

            scanner = DeadCodeScanner(tmp_path)
            items = scanner.scan_unused_imports(generated / "test.py")

            assert len(items) == 0

    def test_scan_orphan_files(self) -> None:
        """Test detection of orphan files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create main file that imports utils
            (tmp_path / "main.py").write_text("from utils import helper\n")

            # Create utils (imported)
            (tmp_path / "utils.py").write_text("def helper(): pass\n")

            # Create orphan file (never imported)
            (tmp_path / "orphan.py").write_text("def unused(): pass\n")

            # Create __init__.py (should be excluded)
            (tmp_path / "__init__.py").write_text("")

            scanner = DeadCodeScanner(tmp_path)
            items = scanner.scan_orphan_files(tmp_path)

            # Should find orphan.py but not __init__.py
            orphan_files = [i.location for i in items]
            assert any("orphan.py" in loc for loc in orphan_files)
            assert not any("__init__.py" in loc for loc in orphan_files)
            assert not any("main.py" in loc for loc in orphan_files)

    def test_scan_directory_full(self) -> None:
        """Test full directory scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create files with issues
            (tmp_path / "main.py").write_text(
                "import os\nimport sys\nprint(sys.version)\n"
            )
            (tmp_path / "orphan.py").write_text("def unused(): pass\n")

            scanner = DeadCodeScanner(tmp_path)
            result = scanner.scan_directory(tmp_path)

            assert result.files_scanned >= 2
            assert len(result.unused_imports) >= 1
            assert len(result.orphan_files) >= 1


class TestScanDeadCodeTools:
    """Tests for MCP tool functions."""

    def test_scan_dead_code_empty_dir(self) -> None:
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scan_dead_code(tmpdir)
            assert "No dead code found" in result

    def test_scan_dead_code_with_issues(self) -> None:
        """Test scanning directory with dead code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / "test.py").write_text(
                "import os\nimport sys\nprint(sys.version)\n"
            )

            result = scan_dead_code(tmpdir)

            assert "Dead Code Scan Report" in result
            assert "Unused Imports" in result

    def test_scan_dead_code_summary(self) -> None:
        """Test summary function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / "test.py").write_text("import os\n")

            result = scan_dead_code(tmpdir, summary=True)

            assert "Dead Code Summary" in result or "No dead code found" in result


class TestIsIntentionallyIgnored:
    """Tests for convenience function."""

    def test_returns_false_for_unignored_file(self) -> None:
        """Test that unignored files return False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # No .gitignore
            test_file = tmp_path / "test.py"
            test_file.write_text("")

            assert not is_intentionally_ignored(test_file, tmp_path)

    def test_returns_true_for_ignored_file(self) -> None:
        """Test that ignored files return True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / ".gitignore").write_text("*.log\n")
            test_file = tmp_path / "debug.log"
            test_file.write_text("")

            assert is_intentionally_ignored(test_file, tmp_path)
