"""Tests for debt_scanner module."""

import tempfile
from pathlib import Path

import pytest

from sef_agents.tools.debt_scanner import (
    DebtItem,
    ScanResult,
    _compute_file_hash,
    _load_cache,
    _load_checkpoint,
    _save_cache,
    _save_checkpoint,
    FileCacheEntry,
    generate_debt_report,
    get_cached_debt_count,
    scan_debt_tool,
    scan_directory,
    scan_file,
    ScanCheckpoint,
)


@pytest.fixture
def sample_python_file() -> Path:
    """Create sample Python file with debt patterns."""
    content = '''"""Sample module with debt patterns."""

def function_without_types(x, y):
    """Function missing type hints."""
    return x + y


def function_without_docstring(x: int) -> int:
    return x * 2


class UndocumentedClass:
    pass


def complex_function(data: list) -> int:
    """Function with high complexity exceeding threshold of 15."""
    result = 0
    for item in data:
        if item > 0:
            if item % 2 == 0:
                for i in range(item):
                    if i > 10:
                        result += i
                    elif i > 8:
                        result += i * 2
                    elif i > 6:
                        result += i * 3
                    elif i > 4:
                        result += i * 4
                    elif i > 2:
                        result += i * 5
                    else:
                        result += 1
            elif item % 3 == 0:
                for j in range(item):
                    if j > 5:
                        result -= j
                    elif j > 3:
                        result -= j * 2
                    else:
                        result -= 1
            else:
                result -= item
        elif item < -10:
            result = -100
        elif item < -5:
            result = -50
        else:
            result = 0
    return result


def function_with_bare_except():
    """Function with bare except."""
    try:
        x = 1 / 0
    except:
        pass


def function_with_broad_except():
    """Function with broad except."""
    try:
        x = 1 / 0
    except Exception:
        pass


# TODO: Fix this later
# FIXME: Critical bug here
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)


@pytest.fixture
def sample_directory(sample_python_file: Path) -> Path:
    """Create directory with Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)

        # Copy sample file
        dest = dir_path / "sample.py"
        dest.write_text(sample_python_file.read_text())

        # Create clean file
        clean = dir_path / "clean.py"
        clean.write_text('''"""Clean module."""


def clean_function(x: int, y: int) -> int:
    """Add two numbers.

    Args:
        x: First number.
        y: Second number.

    Returns:
        Sum of x and y.
    """
    return x + y
''')

        yield dir_path


class TestDebtItem:
    """Tests for DebtItem dataclass."""

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        item = DebtItem(
            debt_id="DEBT-001",
            location="src/file.py:10",
            debt_type="no-types",
            severity="🟡 Medium",
            description="Missing type hints",
            line_number=10,
        )
        d = item.to_dict()

        assert d["id"] == "DEBT-001"
        assert d["type"] == "no-types"
        assert d["line"] == 10

    def test_to_markdown_row(self) -> None:
        """Test markdown row generation."""
        item = DebtItem(
            debt_id="DEBT-001",
            location="src/file.py:10",
            debt_type="no-types",
            severity="🟡 Medium",
            description="Missing type hints",
        )
        row = item.to_markdown_row()

        assert "DEBT-001" in row
        assert "no-types" in row
        assert "Open" in row


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_by_type(self) -> None:
        """Test grouping by type."""
        result = ScanResult(
            items=[
                DebtItem("D1", "f.py", "no-types", "🟡 Medium", "desc"),
                DebtItem("D2", "f.py", "no-types", "🟡 Medium", "desc"),
                DebtItem("D3", "f.py", "bare-except", "🔴 Critical", "desc"),
            ]
        )
        grouped = result.by_type

        assert len(grouped["no-types"]) == 2
        assert len(grouped["bare-except"]) == 1

    def test_by_severity(self) -> None:
        """Test counting by severity."""
        result = ScanResult(
            items=[
                DebtItem("D1", "f.py", "no-types", "🟡 Medium", "desc"),
                DebtItem("D2", "f.py", "bare-except", "🔴 Critical", "desc"),
            ]
        )
        counts = result.by_severity

        assert counts["🟡 Medium"] == 1
        assert counts["🔴 Critical"] == 1


class TestDebtScanner:
    """Tests for debt scanner AST visitor."""

    def test_detects_missing_types(self, sample_python_file: Path) -> None:
        """Test detection of missing type hints."""
        items = scan_file(sample_python_file)
        type_items = [i for i in items if i.debt_type == "no-types"]

        assert len(type_items) > 0

    def test_detects_missing_docstrings(self, sample_python_file: Path) -> None:
        """Test detection of missing docstrings."""
        items = scan_file(sample_python_file)
        doc_items = [i for i in items if i.debt_type == "no-docs"]

        assert len(doc_items) > 0

    def test_detects_bare_except(self, sample_python_file: Path) -> None:
        """Test detection of bare except clauses."""
        items = scan_file(sample_python_file)
        except_items = [i for i in items if i.debt_type == "bare-except"]

        # Should find both bare except: and except Exception:
        assert len(except_items) >= 2

    def test_detects_todos(self, sample_python_file: Path) -> None:
        """Test detection of TODO/FIXME comments."""
        items = scan_file(sample_python_file)
        todo_items = [i for i in items if i.debt_type == "todo-fixme"]

        assert len(todo_items) >= 2

    def test_detects_complexity(self, sample_python_file: Path) -> None:
        """Test detection of high complexity."""
        items = scan_file(sample_python_file)
        complexity_items = [i for i in items if i.debt_type == "complexity"]

        # complex_function should be detected
        assert len(complexity_items) >= 1


class TestScanFile:
    """Tests for scan_file function."""

    def test_scan_valid_file(self, sample_python_file: Path) -> None:
        """Test scanning valid Python file."""
        items = scan_file(sample_python_file)
        assert len(items) > 0

    def test_scan_nonexistent_file(self) -> None:
        """Test scanning nonexistent file."""
        items = scan_file(Path("/nonexistent/file.py"))
        assert items == []

    def test_scan_syntax_error(self) -> None:
        """Test scanning file with syntax error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken(:\n    pass")
            f.flush()
            items = scan_file(Path(f.name))
            assert items == []


class TestScanDirectory:
    """Tests for scan_directory function."""

    def test_scan_directory(self, sample_directory: Path) -> None:
        """Test scanning directory."""
        result = scan_directory(sample_directory)

        assert result.files_scanned == 2
        assert len(result.items) > 0

    def test_scan_nonexistent_directory(self) -> None:
        """Test scanning nonexistent directory."""
        result = scan_directory("/nonexistent/path")
        assert len(result.errors) > 0

    def test_excludes_pycache(self) -> None:
        """Test that __pycache__ is excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pycache = Path(tmpdir) / "__pycache__"
            pycache.mkdir()
            (pycache / "module.py").write_text("x = 1")

            result = scan_directory(tmpdir)
            assert result.files_scanned == 0


class TestGenerateDebtReport:
    """Tests for generate_debt_report function."""

    def test_report_generation(self, sample_directory: Path) -> None:
        """Test report generation."""
        report = generate_debt_report(str(sample_directory))

        assert "Technical Debt Scan Report" in report
        assert "Summary" in report
        assert "Severity" in report

    def test_report_nonexistent_directory(self) -> None:
        """Test report for nonexistent directory."""
        report = generate_debt_report("/nonexistent/path")
        assert "Errors" in report


class TestDeprecatedImports:
    """Tests for deprecated import detection."""

    def test_detects_deprecated_import(self, tmp_path: Path) -> None:
        """Test detection of deprecated imports."""
        deprecated_file = tmp_path / "deprecated.py"
        deprecated_file.write_text('''"""Module with deprecated import."""

import distutils
from optparse import OptionParser
''')
        items = scan_file(deprecated_file)
        deprecated_items = [i for i in items if i.debt_type == "deprecated"]

        assert len(deprecated_items) >= 2

    def test_ignores_valid_imports(self, tmp_path: Path) -> None:
        """Test that valid imports are not flagged."""
        valid_file = tmp_path / "valid.py"
        valid_file.write_text('''"""Module with valid imports."""

import os
import sys
from pathlib import Path
''')
        items = scan_file(valid_file)
        deprecated_items = [i for i in items if i.debt_type == "deprecated"]

        assert len(deprecated_items) == 0


class TestLongFunctions:
    """Tests for long function detection."""

    def test_detects_long_function(self, tmp_path: Path) -> None:
        """Test detection of overly long functions."""
        long_file = tmp_path / "long_func.py"
        # Create function with 150+ lines
        lines = [
            '"""Module with long function."""',
            "",
            "def very_long_function() -> None:",
            '    """Long function."""',
        ]
        for i in range(120):
            lines.append(f"    x_{i} = {i}")
        lines.append("    return None")
        long_file.write_text("\n".join(lines))

        items = scan_file(long_file)
        long_items = [i for i in items if i.debt_type == "long-function"]

        assert len(long_items) >= 1


class TestDeepNesting:
    """Tests for deep nesting detection."""

    def test_detects_deep_nesting(self, tmp_path: Path) -> None:
        """Test detection of deeply nested code."""
        nested_file = tmp_path / "nested.py"
        nested_file.write_text('''"""Module with deep nesting."""


def deeply_nested(data: list) -> int:
    """Function with deep nesting."""
    result = 0
    for item in data:
        if item > 0:
            for i in range(item):
                if i > 5:
                    for j in range(i):
                        if j > 2:
                            result += j
    return result
''')
        items = scan_file(nested_file)
        nesting_items = [i for i in items if i.debt_type == "deep-nesting"]

        assert len(nesting_items) >= 1


class TestToolFunctions:
    """Tests for MCP tool functions."""

    def test_scan_debt_tool(self, sample_directory: Path) -> None:
        """Test scan_debt_tool function."""
        result = scan_debt_tool(str(sample_directory))

        assert "Technical Debt Scan Report" in result
        assert "Summary" in result

    def test_scan_debt_summary_tool(self, sample_directory: Path) -> None:
        """Test scan_debt_summary_tool function."""
        result = scan_debt_tool(str(sample_directory), summary=True)

        assert "Debt Summary" in result
        assert "Severity" in result
        assert "Total" in result

    def test_scan_debt_summary_tool_empty(self, tmp_path: Path) -> None:
        """Test summary tool with no debt."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text('''"""Clean module."""


def clean_func(x: int) -> int:
    """Return x doubled."""
    return x * 2
''')
        result = scan_debt_tool(str(tmp_path), summary=True)

        assert "No technical debt found" in result or "Debt Summary" in result


class TestFileHash:
    """Tests for file hash computation."""

    def test_compute_hash(self, tmp_path: Path) -> None:
        """Test hash computation for file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")

        hash1 = _compute_file_hash(test_file)
        assert len(hash1) == 32  # MD5 hex length

    def test_hash_changes_with_content(self, tmp_path: Path) -> None:
        """Test hash changes when content changes."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")
        hash1 = _compute_file_hash(test_file)

        test_file.write_text("x = 2")
        hash2 = _compute_file_hash(test_file)

        assert hash1 != hash2

    def test_hash_nonexistent_file(self, tmp_path: Path) -> None:
        """Test hash of nonexistent file returns empty string."""
        result = _compute_file_hash(tmp_path / "nonexistent.py")
        assert result == ""


class TestCacheManagement:
    """Tests for cache loading and saving."""

    def test_save_and_load_cache(self, tmp_path: Path) -> None:
        """Test saving and loading cache."""
        cache = {
            "file1.py": FileCacheEntry(
                file_hash="abc123",
                items=[{"id": "DEBT-001", "type": "no-types"}],
                scanned_at="2025-01-01T00:00:00",
            )
        }

        _save_cache(tmp_path, cache)
        loaded = _load_cache(tmp_path)

        assert "file1.py" in loaded
        assert loaded["file1.py"].file_hash == "abc123"
        assert len(loaded["file1.py"].items) == 1

    def test_load_missing_cache(self, tmp_path: Path) -> None:
        """Test loading nonexistent cache returns empty dict."""
        result = _load_cache(tmp_path)
        assert result == {}

    def test_get_cached_debt_count(self, tmp_path: Path) -> None:
        """Test getting debt count from cache."""
        cache = {
            "file1.py": FileCacheEntry(
                file_hash="abc",
                items=[{"id": "D1"}, {"id": "D2"}],
                scanned_at="2025-01-01",
            ),
            "file2.py": FileCacheEntry(
                file_hash="def",
                items=[{"id": "D3"}],
                scanned_at="2025-01-01",
            ),
        }
        _save_cache(tmp_path, cache)

        count = get_cached_debt_count(tmp_path)
        assert count == 3

    def test_get_cached_debt_count_no_cache(self, tmp_path: Path) -> None:
        """Test debt count with no cache returns None."""
        count = get_cached_debt_count(tmp_path)
        assert count is None


class TestCheckpointManagement:
    """Tests for checkpoint loading and saving."""

    def test_save_and_load_checkpoint(self, tmp_path: Path) -> None:
        """Test saving and loading checkpoint."""
        checkpoint = ScanCheckpoint(
            files_to_scan=["file1.py", "file2.py", "file3.py"],
            current_index=1,
            completed_files=["file1.py"],
            started_at="2025-01-01T00:00:00",
        )

        _save_checkpoint(tmp_path, checkpoint)
        loaded = _load_checkpoint(tmp_path)

        assert loaded is not None
        assert loaded.current_index == 1
        assert len(loaded.files_to_scan) == 3
        assert loaded.completed_files == ["file1.py"]

    def test_load_missing_checkpoint(self, tmp_path: Path) -> None:
        """Test loading nonexistent checkpoint returns None."""
        result = _load_checkpoint(tmp_path)
        assert result is None


class TestIncrementalScanning:
    """Tests for incremental scanning with cache."""

    def test_scan_creates_cache(self, tmp_path: Path) -> None:
        """Test that scanning creates cache file."""
        test_file = tmp_path / "test.py"
        test_file.write_text('"""Test."""\nx = 1')

        scan_directory(tmp_path, incremental=True)

        cache_file = tmp_path / ".sef_cache" / "debt_cache.json"
        assert cache_file.exists()

    def test_scan_uses_cache_for_unchanged(self, tmp_path: Path) -> None:
        """Test that unchanged files use cached results."""
        test_file = tmp_path / "test.py"
        test_file.write_text('"""Test."""\n\ndef func(x):\n    return x')

        # First scan
        result1 = scan_directory(tmp_path, incremental=True)
        items_count1 = len(result1.items)

        # Second scan (no changes)
        result2 = scan_directory(tmp_path, incremental=True)

        # Should have same results from cache
        assert len(result2.items) == items_count1

    def test_scan_clears_checkpoint_on_completion(self, tmp_path: Path) -> None:
        """Test checkpoint is cleared after successful scan."""
        test_file = tmp_path / "test.py"
        test_file.write_text('"""Test."""\nx = 1')

        scan_directory(tmp_path, incremental=True)

        checkpoint_file = tmp_path / ".sef_cache" / "debt_checkpoint.json"
        assert not checkpoint_file.exists()

    def test_full_scan_mode(self, tmp_path: Path) -> None:
        """Test full scan ignores cache."""
        test_file = tmp_path / "test.py"
        test_file.write_text('"""Test."""\nx = 1')

        result = scan_directory(tmp_path, incremental=False)

        assert result.files_scanned >= 1
