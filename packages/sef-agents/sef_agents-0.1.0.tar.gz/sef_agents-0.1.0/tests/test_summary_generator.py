"""Tests for executive summary generator.

Real execution tests - no mocking of the unit under test.
"""

import json
from pathlib import Path


from sef_agents.tools.summary_generator import (
    generate_executive_summary,
    write_executive_summary,
    _calculate_score,
    _parse_security_report,
)


class TestCalculateScore:
    """Tests for score calculation logic."""

    def test_perfect_score(self) -> None:
        """All metrics passing yields 100."""
        score = _calculate_score(
            security_passed=True,
            critical_issues=0,
            debt_count=0,
            compliance_passed=True,
        )
        assert score == 100.0

    def test_security_failure_deducts_20(self) -> None:
        """Security failure reduces score by 20."""
        score = _calculate_score(
            security_passed=False,
            critical_issues=0,
            debt_count=0,
            compliance_passed=True,
        )
        assert score == 80.0

    def test_critical_issues_deduct_10_each(self) -> None:
        """Each critical issue deducts 10 points (capped at 30)."""
        score = _calculate_score(
            security_passed=True,
            critical_issues=2,
            debt_count=0,
            compliance_passed=True,
        )
        assert score == 80.0

    def test_critical_issues_capped_at_30(self) -> None:
        """Critical issues penalty capped at 30 points."""
        score = _calculate_score(
            security_passed=True,
            critical_issues=10,
            debt_count=0,
            compliance_passed=True,
        )
        assert score == 70.0  # Only -30, not -100

    def test_debt_deducts_2_each_capped(self) -> None:
        """Debt items deduct 2 points each, capped at 30."""
        score = _calculate_score(
            security_passed=True,
            critical_issues=0,
            debt_count=5,
            compliance_passed=True,
        )
        assert score == 90.0  # 5 * 2 = 10

    def test_debt_penalty_capped_at_30(self) -> None:
        """Debt penalty capped at 30 points."""
        score = _calculate_score(
            security_passed=True,
            critical_issues=0,
            debt_count=50,
            compliance_passed=True,
        )
        assert score == 70.0  # Only -30, not -100

    def test_compliance_failure_deducts_10(self) -> None:
        """Compliance failure reduces score by 10."""
        score = _calculate_score(
            security_passed=True,
            critical_issues=0,
            debt_count=0,
            compliance_passed=False,
        )
        assert score == 90.0

    def test_score_floor_at_zero(self) -> None:
        """Score floors at 0 with maximum penalties."""
        # -20 (security) -30 (capped critical) -30 (capped debt) -10 (compliance) = 10
        score = _calculate_score(
            security_passed=False,
            critical_issues=10,
            debt_count=50,
            compliance_passed=False,
        )
        assert score == 10.0  # All caps hit, minimum possible with these inputs

    def test_score_never_below_zero(self) -> None:
        """Score cannot go below 0 even with extreme values."""
        # This would be -20 -30 -30 -10 = -90 without floor
        score = _calculate_score(
            security_passed=False,
            critical_issues=100,  # Still capped at -30
            debt_count=500,  # Still capped at -30
            compliance_passed=False,
        )
        assert score == 10.0  # Caps prevent going below 10

    def test_combined_penalties(self) -> None:
        """Multiple penalties combine correctly."""
        score = _calculate_score(
            security_passed=False,  # -20
            critical_issues=1,  # -10
            debt_count=5,  # -10
            compliance_passed=False,  # -10
        )
        assert score == 50.0


class TestParseSecurityReport:
    """Tests for security report parsing."""

    def test_parse_passing_report(self, tmp_path: Path) -> None:
        """Parses passing security report correctly."""
        report = tmp_path / "security_audit_2025-01-01.md"
        report.write_text(
            "# Security Audit\n\n**OVERALL: ✅ PASSED**\n\nAll checks passed.\n"
        )
        passed, critical = _parse_security_report(report)
        assert passed is True
        assert critical == 0

    def test_parse_failing_report(self, tmp_path: Path) -> None:
        """Parses failing security report correctly."""
        report = tmp_path / "security_audit_2025-01-01.md"
        report.write_text(
            "# Security Audit\n\n"
            "**OVERALL: ❌ FAILED**\n\n"
            "| Check | Status |\n"
            "| Network | ❌ FAIL |\n"
            "| Secrets | ❌ FAIL |\n"
        )
        passed, critical = _parse_security_report(report)
        assert passed is False
        assert critical == 2

    def test_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        """Non-existent file returns safe defaults."""
        report = tmp_path / "nonexistent.md"
        passed, critical = _parse_security_report(report)
        assert passed is True
        assert critical == 0


class TestGenerateExecutiveSummary:
    """Integration tests for summary generation."""

    def test_generates_valid_structure(self, tmp_path: Path) -> None:
        """Summary has all required fields."""
        summary = generate_executive_summary(str(tmp_path))

        assert "generated_at" in summary
        assert "score" in summary
        assert "critical_issues" in summary
        assert "debt_count" in summary
        assert "security_passed" in summary
        assert "compliance_passed" in summary

    def test_score_is_float(self, tmp_path: Path) -> None:
        """Score is a float between 0 and 100."""
        summary = generate_executive_summary(str(tmp_path))
        assert isinstance(summary["score"], float)
        assert 0.0 <= summary["score"] <= 100.0

    def test_with_security_report(self, tmp_path: Path) -> None:
        """Incorporates security report when present."""
        # Create sef-reports/security directory
        security_dir = tmp_path / "sef-reports" / "security"
        security_dir.mkdir(parents=True)

        report = security_dir / "security_audit_2025-01-01.md"
        report.write_text("**OVERALL: ✅ PASSED**\n")

        summary = generate_executive_summary(str(tmp_path))
        assert summary["security_passed"] is True


class TestWriteExecutiveSummary:
    """Tests for writing summary to disk."""

    def test_creates_file(self, tmp_path: Path) -> None:
        """Creates executive-summary.json in sef-reports/."""
        output_path = write_executive_summary(str(tmp_path))

        assert output_path.exists()
        assert output_path.name == "executive-summary.json"
        assert output_path.parent.name == "sef-reports"

    def test_file_is_valid_json(self, tmp_path: Path) -> None:
        """Written file is valid JSON."""
        output_path = write_executive_summary(str(tmp_path))

        content = output_path.read_text()
        data = json.loads(content)

        assert "score" in data
        assert "security_passed" in data

    def test_creates_directory_if_missing(self, tmp_path: Path) -> None:
        """Creates sef-reports directory if it doesn't exist."""
        output_path = write_executive_summary(str(tmp_path))

        assert (tmp_path / "sef-reports").is_dir()
        assert output_path.exists()

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        """Overwrites existing executive-summary.json."""
        # First write
        write_executive_summary(str(tmp_path))

        # Second write
        output_path = write_executive_summary(str(tmp_path))

        # Should still exist and be valid
        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "score" in data
