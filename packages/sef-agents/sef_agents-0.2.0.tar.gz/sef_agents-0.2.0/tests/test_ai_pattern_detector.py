"""Tests for AI Anti-Pattern Detector.

Real execution tests - no mocking of the code under test.
Each test creates actual files and runs the detector against them.
"""

from pathlib import Path

import pytest

from sef_agents.tools.ai_pattern_detector import (
    AIPatternDetector,
    PatternFinding,
    detect_ai_patterns_tool,
)


class TestPatternFinding:
    """Tests for PatternFinding dataclass."""

    def test_create_finding(self) -> None:
        """Test PatternFinding creation with all fields."""
        finding = PatternFinding(
            pattern_id="test_pattern",
            severity="HIGH",
            line=42,
            message="Test message",
            suggestion="Test suggestion",
        )
        assert finding.pattern_id == "test_pattern"
        assert finding.severity == "HIGH"
        assert finding.line == 42
        assert finding.message == "Test message"
        assert finding.suggestion == "Test suggestion"


class TestAIPatternDetector:
    """Tests for AIPatternDetector class."""

    def test_file_not_found(self) -> None:
        """Test error handling for missing file."""
        detector = AIPatternDetector()
        with pytest.raises(FileNotFoundError):
            detector.detect_patterns(Path("/nonexistent/file.py"))

    def test_javascript_file_supported(self, tmp_path: Path) -> None:
        """Test that JavaScript files are now supported."""
        js_file = tmp_path / "test.js"
        js_file.write_text("const userCount = 10;")

        detector = AIPatternDetector()
        # Should not raise - JS is now supported
        findings = detector.detect_patterns(js_file)
        assert isinstance(findings, list)

    def test_syntax_error_handling(self, tmp_path: Path) -> None:
        """Test graceful handling of syntax errors."""
        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def broken(\n")

        detector = AIPatternDetector()
        findings = detector.detect_patterns(bad_file)

        assert len(findings) == 1
        assert findings[0].pattern_id == "syntax_error"
        assert findings[0].severity == "HIGH"

    def test_clean_file_no_findings(self, tmp_path: Path) -> None:
        """Test that clean code produces no findings."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text('''"""Clean module."""


def calculate_total_price(unit_price: float, quantity: int) -> float:
    """Calculate total price from unit price and quantity."""
    return unit_price * quantity


def format_currency(amount: float) -> str:
    """Format amount as USD currency string."""
    return f"${amount:.2f}"
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(clean_file)

        # Should have no high-severity issues
        high_findings = [f for f in findings if f.severity == "HIGH"]
        assert len(high_findings) == 0


class TestOverAbstraction:
    """Tests for over-abstraction detection."""

    def test_detects_too_many_classes(self, tmp_path: Path) -> None:
        """Test detection of high class-to-function ratio."""
        over_abstracted = tmp_path / "over_abstracted.py"
        over_abstracted.write_text('''"""Over-abstracted module."""


class Handler:
    """Handler class."""

    def handle(self) -> None:
        """Handle something."""
        pass


class Manager:
    """Manager class."""

    def manage(self) -> None:
        """Manage something."""
        pass


class Processor:
    """Processor class."""

    def process(self) -> None:
        """Process something."""
        pass
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(over_abstracted)

        over_abstraction = [f for f in findings if f.pattern_id == "over_abstraction"]
        assert len(over_abstraction) == 1
        assert "ratio" in over_abstraction[0].message.lower()

    def test_balanced_code_no_finding(self, tmp_path: Path) -> None:
        """Test that balanced class/function ratio passes."""
        balanced = tmp_path / "balanced.py"
        balanced.write_text('''"""Balanced module."""


class UserService:
    """User service."""

    def get_user(self, user_id: int) -> dict:
        """Get user by ID."""
        return {}

    def create_user(self, name: str) -> dict:
        """Create new user."""
        return {}

    def update_user(self, user_id: int, data: dict) -> dict:
        """Update user."""
        return {}


def validate_email(email: str) -> bool:
    """Validate email format."""
    return "@" in email


def hash_password(password: str) -> str:
    """Hash a password."""
    return password
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(balanced)

        over_abstraction = [f for f in findings if f.pattern_id == "over_abstraction"]
        assert len(over_abstraction) == 0


class TestUnusedParams:
    """Tests for unused parameter detection."""

    def test_detects_unused_param(self, tmp_path: Path) -> None:
        """Test detection of unused function parameters."""
        unused_param = tmp_path / "unused_param.py"
        unused_param.write_text('''"""Module with unused params."""


def process_data(data: list, unused_flag: bool) -> int:
    """Process data, ignoring flag."""
    return len(data)
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(unused_param)

        unused = [f for f in findings if f.pattern_id == "unused_params"]
        assert len(unused) == 1
        assert "unused_flag" in unused[0].message

    def test_underscore_prefix_ignored(self, tmp_path: Path) -> None:
        """Test that underscore-prefixed params are ignored."""
        underscore = tmp_path / "underscore.py"
        underscore.write_text('''"""Module with intentionally unused params."""


def callback(event: dict, _context: dict) -> None:
    """Handle event, context unused by design."""
    print(event)
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(underscore)

        unused = [f for f in findings if f.pattern_id == "unused_params"]
        # Should not flag _context
        assert all("_context" not in f.message for f in unused)

    def test_self_cls_not_flagged(self, tmp_path: Path) -> None:
        """Test that self and cls are never flagged."""
        method_file = tmp_path / "methods.py"
        method_file.write_text('''"""Module with class methods."""


class Example:
    """Example class."""

    def instance_method(self) -> None:
        """Instance method that doesn't use self explicitly."""
        print("hello")

    @classmethod
    def class_method(cls) -> None:
        """Class method that doesn't use cls explicitly."""
        print("world")
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(method_file)

        unused = [f for f in findings if f.pattern_id == "unused_params"]
        assert all("self" not in f.message for f in unused)
        assert all("cls" not in f.message for f in unused)


class TestGenericNaming:
    """Tests for generic naming detection."""

    def test_detects_generic_variable(self, tmp_path: Path) -> None:
        """Test detection of generic variable names."""
        generic = tmp_path / "generic.py"
        generic.write_text('''"""Module with generic names."""


def process() -> dict:
    """Process something."""
    data = {}
    result = []
    temp = 0
    return data
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(generic)

        generic_findings = [f for f in findings if f.pattern_id == "generic_naming"]
        names_found = [f.message for f in generic_findings]

        assert any("data" in msg for msg in names_found)
        assert any("result" in msg for msg in names_found)
        assert any("temp" in msg for msg in names_found)

    def test_descriptive_names_pass(self, tmp_path: Path) -> None:
        """Test that descriptive names pass."""
        descriptive = tmp_path / "descriptive.py"
        descriptive.write_text('''"""Module with descriptive names."""


def calculate_order_total(order_items: list, tax_rate: float) -> float:
    """Calculate order total with tax."""
    subtotal = sum(item["price"] for item in order_items)
    tax_amount = subtotal * tax_rate
    return subtotal + tax_amount
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(descriptive)

        generic_findings = [f for f in findings if f.pattern_id == "generic_naming"]
        # Should have minimal generic name findings
        assert len(generic_findings) <= 1  # 'item' might be flagged in comprehension


class TestVerboseComments:
    """Tests for verbose comment detection."""

    def test_detects_excessive_comments(self, tmp_path: Path) -> None:
        """Test detection of high comment-to-code ratio."""
        verbose = tmp_path / "verbose.py"
        verbose.write_text('''"""Module with too many comments."""

# This is a comment
# Another comment
# Yet another comment
# More comments
# Even more comments
x = 1
# Comment after code
# And another
y = 2
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(verbose)

        verbose_findings = [f for f in findings if f.pattern_id == "verbose_comments"]
        assert len(verbose_findings) == 1
        assert "ratio" in verbose_findings[0].message.lower()

    def test_reasonable_comments_pass(self, tmp_path: Path) -> None:
        """Test that reasonable comment ratio passes."""
        reasonable = tmp_path / "reasonable.py"
        reasonable.write_text('''"""Module with reasonable comments."""


def connect_database(host: str, port: int) -> object:
    """Connect to database."""
    # Validate connection params
    if not host:
        raise ValueError("Host required")

    connection = create_connection(host, port)
    return connection


def create_connection(host: str, port: int) -> object:
    """Create database connection."""
    return {"host": host, "port": port}
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(reasonable)

        verbose_findings = [f for f in findings if f.pattern_id == "verbose_comments"]
        assert len(verbose_findings) == 0


class TestCopyPasteDetection:
    """Tests for copy-paste code block detection."""

    def test_detects_duplicate_blocks(self, tmp_path: Path) -> None:
        """Test detection of copy-pasted code blocks."""
        duplicate = tmp_path / "duplicate.py"
        # Create EXACTLY identical blocks (same code, different function names)
        duplicate.write_text('''"""Module with duplicated code."""

x = 1
y = 2
z = 3
a = 4
b = 5

x = 1
y = 2
z = 3
a = 4
b = 5
''')

        # Use config with smaller block size
        config = {
            "enabled_patterns": ["copy_paste_blocks"],
            "thresholds": {
                "min_block_size": 4,
                "similarity_threshold": 0.85,
            },
            "severity_weights": {"copy_paste_blocks": "HIGH"},
        }

        detector = AIPatternDetector(config)
        findings = detector.detect_patterns(duplicate)

        copy_paste = [f for f in findings if f.pattern_id == "copy_paste_blocks"]
        # Should detect the identical blocks
        assert len(copy_paste) >= 1

    def test_unique_blocks_pass(self, tmp_path: Path) -> None:
        """Test that unique code blocks pass."""
        unique = tmp_path / "unique.py"
        unique.write_text('''"""Module with unique code."""


def calculate_sum(numbers: list) -> int:
    """Sum all numbers."""
    total = 0
    for num in numbers:
        total += num
    return total


def find_maximum(values: list) -> int:
    """Find maximum value."""
    if not values:
        return 0
    max_val = values[0]
    for val in values[1:]:
        if val > max_val:
            max_val = val
    return max_val
''')

        detector = AIPatternDetector()
        findings = detector.detect_patterns(unique)

        copy_paste = [f for f in findings if f.pattern_id == "copy_paste_blocks"]
        # Unique logic should not trigger
        assert len(copy_paste) == 0


class TestCustomConfig:
    """Tests for custom configuration."""

    def test_disable_pattern(self, tmp_path: Path) -> None:
        """Test that disabled patterns are not checked."""
        generic = tmp_path / "generic.py"
        generic.write_text('''"""Module with generic names."""


def process() -> dict:
    """Process something."""
    data = {}
    return data
''')

        config = {
            "enabled_patterns": ["over_abstraction"],  # Only this one
            "thresholds": {"class_to_function_ratio": 0.5},
            "generic_names": ["data"],
            "severity_weights": {"over_abstraction": "MEDIUM"},
        }

        detector = AIPatternDetector(config)
        findings = detector.detect_patterns(generic)

        # Should not find generic_naming since it's disabled
        generic_findings = [f for f in findings if f.pattern_id == "generic_naming"]
        assert len(generic_findings) == 0

    def test_custom_threshold(self, tmp_path: Path) -> None:
        """Test that custom thresholds are applied."""
        classes = tmp_path / "classes.py"
        classes.write_text('''"""Module with classes."""


class A:
    """Class A."""
    def method_a(self) -> None:
        """Method A."""
        pass


class B:
    """Class B."""
    def method_b(self) -> None:
        """Method B."""
        pass
''')

        # Strict threshold - should trigger
        strict_config = {
            "enabled_patterns": ["over_abstraction"],
            "thresholds": {"class_to_function_ratio": 0.3},
            "severity_weights": {"over_abstraction": "HIGH"},
        }

        detector = AIPatternDetector(strict_config)
        findings = detector.detect_patterns(classes)
        assert len([f for f in findings if f.pattern_id == "over_abstraction"]) == 1

        # Lenient threshold - should pass
        lenient_config = {
            "enabled_patterns": ["over_abstraction"],
            "thresholds": {"class_to_function_ratio": 2.0},
            "severity_weights": {"over_abstraction": "HIGH"},
        }

        detector = AIPatternDetector(lenient_config)
        findings = detector.detect_patterns(classes)
        assert len([f for f in findings if f.pattern_id == "over_abstraction"]) == 0


class TestDetectAIPatternsTool:
    """Tests for the main tool function."""

    def test_tool_returns_report(self, tmp_path: Path, monkeypatch) -> None:
        """Test that tool returns formatted report."""
        from sef_agents.session import SessionManager

        monkeypatch.chdir(tmp_path)
        SessionManager.get().active_agent = "developer"  # Required by tool guard

        test_file = tmp_path / "test.py"
        test_file.write_text('''"""Test module."""


def example() -> None:
    """Example function."""
    pass
''')

        result = detect_ai_patterns_tool(str(test_file))

        assert "Analysis complete" in result or "No AI anti-patterns" in result

    def test_tool_file_not_found(self, tmp_path: Path, monkeypatch) -> None:
        """Test tool error handling for missing file."""
        from sef_agents.session import SessionManager

        monkeypatch.chdir(tmp_path)
        SessionManager.get().active_agent = "developer"  # Required by tool guard

        result = detect_ai_patterns_tool("/nonexistent/path.py")
        assert "Error" in result
        assert "not found" in result.lower()

    def test_tool_javascript_support(self, tmp_path: Path, monkeypatch) -> None:
        """Test tool works with JavaScript files."""
        # Ensure report is written to tmp_path, not project root
        monkeypatch.chdir(tmp_path)

        # We need an active agent for the tool to work (it checks SessionManager)
        # Note: Depending on implementation, valid_agent check might be needed.
        # Looking at other tests, they set active_agent.
        from sef_agents.session import SessionManager

        SessionManager.get().active_agent = "developer"

        js_file = tmp_path / "test.js"
        js_file.write_text("const userCount = 10;")

        result = detect_ai_patterns_tool(str(js_file))
        # JS is now supported - should not error
        assert "Error" not in result or "not found" not in result.lower()

    def test_tool_with_findings(self, tmp_path: Path, monkeypatch) -> None:
        """Test tool report includes findings."""
        from sef_agents.session import SessionManager

        monkeypatch.chdir(tmp_path)
        SessionManager.get().active_agent = "developer"  # Required by tool guard

        problematic = tmp_path / "problematic.py"
        problematic.write_text('''"""Problematic module."""


def process(data: list, unused: str) -> dict:
    """Process data."""
    result = {}
    temp = 0
    return result
''')

        result = detect_ai_patterns_tool(str(problematic))

        # Should contain findings in table format
        assert "Severity" in result or "issues" in result.lower()
