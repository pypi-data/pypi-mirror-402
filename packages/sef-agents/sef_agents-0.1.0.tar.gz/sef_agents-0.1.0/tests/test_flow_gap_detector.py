"""Tests for flow_gap_detector module."""

import tempfile
from pathlib import Path

import pytest

from sef_agents.tools.flow_gap_detector import (
    FlowDefinition,
    Gap,
    GapReport,
    detect_flow_gaps,
    detect_gaps,
    parse_flows_md,
)


@pytest.fixture
def sample_flows_md() -> str:
    """Sample FLOWS.md content."""
    return """# Business Flows Registry

## Flow: checkout_flow

**Process:** Order Processing

### Steps

| Step | Name | Description | Story ID | Status |
|------|------|-------------|----------|--------|
| 1 | cart_review | User reviews cart | STORY-001 | Done |
| 2 | payment_validation | Validate payment | STORY-002 | In Progress |
| 3 | order_creation | Create order | STORY-003 | Draft |
| 4 | confirmation | Show confirmation | - | Not Started |

## Flow: user_registration

**Process:** User Onboarding

### Steps

| Step | Name | Description | Story ID | Status |
|------|------|-------------|----------|--------|
| 1 | form_input | User enters details | STORY-010 | Done |
| 2 | email_verification | Verify email | STORY-011 | In Progress |
"""


@pytest.fixture
def flows_file(sample_flows_md: str) -> Path:
    """Create temp FLOWS.md file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_flows_md)
        return Path(f.name)


@pytest.fixture
def req_directory_matching() -> Path:
    """Create temp directory with matching REQ.md files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        req_dir = Path(tmpdir)

        # STORY-001: Done, in flow
        (req_dir / "STORY-001-REQ.md").write_text(
            """# Requirement: [STORY-001] Cart Review

**Status:** Done

## Flow Context

| Field | Value |
|-------|-------|
| **Business Process** | Order Processing |
| **Flow** | checkout_flow |
| **Flow Step** | cart_review |
| **Upstream Step** | - |
| **Downstream Step** | payment_validation |
"""
        )

        # STORY-002: In Progress, in flow
        (req_dir / "STORY-002-REQ.md").write_text(
            """# Requirement: [STORY-002] Payment Validation

**Status:** In Progress

## Flow Context

| Field | Value |
|-------|-------|
| **Business Process** | Order Processing |
| **Flow** | checkout_flow |
| **Flow Step** | payment_validation |
| **Upstream Step** | cart_review |
| **Downstream Step** | order_creation |
"""
        )

        yield req_dir


@pytest.fixture
def req_directory_with_gaps() -> Path:
    """Create temp directory with missing/mismatched REQ.md files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        req_dir = Path(tmpdir)

        # STORY-001: Done, matches
        (req_dir / "STORY-001-REQ.md").write_text(
            """# Requirement: [STORY-001] Cart Review

**Status:** Done

## Flow Context

| Field | Value |
|-------|-------|
| **Flow** | checkout_flow |
| **Flow Step** | cart_review |
"""
        )

        # STORY-002: Status mismatch (Draft vs In Progress expected)
        (req_dir / "STORY-002-REQ.md").write_text(
            """# Requirement: [STORY-002] Payment Validation

**Status:** Draft

## Flow Context

| Field | Value |
|-------|-------|
| **Flow** | checkout_flow |
| **Flow Step** | payment_validation |
"""
        )

        # STORY-999: Orphan flow step (not in FLOWS.md)
        (req_dir / "STORY-999-REQ.md").write_text(
            """# Requirement: [STORY-999] Unknown Step

**Status:** Draft

## Flow Context

| Field | Value |
|-------|-------|
| **Flow** | checkout_flow |
| **Flow Step** | unknown_step |
"""
        )

        yield req_dir


class TestFlowDefinition:
    """Tests for FlowDefinition dataclass."""

    def test_add_step(self) -> None:
        """Test adding step to flow definition."""
        flow = FlowDefinition(name="checkout_flow", process="Order Processing")
        flow.add_step(1, "cart_review", "Review cart", "STORY-001", "Done")

        assert "cart_review" in flow.steps
        assert flow.steps["cart_review"]["story_id"] == "STORY-001"
        assert flow.steps["cart_review"]["order"] == "1"


class TestGap:
    """Tests for Gap dataclass."""

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        gap = Gap(
            gap_type="missing_story",
            severity="high",
            flow="checkout_flow",
            step="confirmation",
            description="No linked story",
        )
        result = gap.to_dict()

        assert result["type"] == "missing_story"
        assert result["severity"] == "high"
        assert result["flow"] == "checkout_flow"


class TestGapReport:
    """Tests for GapReport class."""

    def test_add_gap(self) -> None:
        """Test adding gaps to report."""
        report = GapReport()
        report.add_gap(
            Gap(
                gap_type="missing_story",
                severity="high",
                flow="checkout_flow",
                step="confirmation",
                description="No linked story",
            )
        )

        assert len(report.gaps) == 1
        assert report.high_severity_count == 1

    def test_severity_counts(self) -> None:
        """Test severity counting."""
        report = GapReport()
        report.add_gap(Gap("missing_story", "high", "f", "s", "d"))
        report.add_gap(Gap("orphan_step", "medium", "f", "s", "d"))
        report.add_gap(Gap("status_mismatch", "low", "f", "s", "d"))
        report.add_gap(Gap("missing_story", "high", "f", "s2", "d"))

        assert report.high_severity_count == 2
        assert report.medium_severity_count == 1
        assert report.low_severity_count == 1

    def test_to_markdown_no_gaps(self) -> None:
        """Test markdown generation with no gaps."""
        report = GapReport(flows_checked=2, steps_checked=5)
        markdown = report.to_markdown()

        assert "No gaps detected" in markdown
        assert "Flows checked: 2" in markdown

    def test_to_markdown_with_gaps(self) -> None:
        """Test markdown generation with gaps."""
        report = GapReport()
        report.add_gap(Gap("missing_story", "high", "checkout", "confirm", "No story"))
        markdown = report.to_markdown()

        assert "High Severity Gaps" in markdown
        assert "checkout" in markdown
        assert "confirm" in markdown


class TestParseFlowsMd:
    """Tests for parse_flows_md function."""

    def test_parse_valid_file(self, flows_file: Path) -> None:
        """Test parsing valid FLOWS.md file."""
        flows = parse_flows_md(flows_file)

        assert len(flows) == 2
        assert "checkout_flow" in flows
        assert "user_registration" in flows

        checkout = flows["checkout_flow"]
        assert checkout.process == "Order Processing"
        assert len(checkout.steps) == 4
        assert "cart_review" in checkout.steps
        assert checkout.steps["cart_review"]["story_id"] == "STORY-001"

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing nonexistent file."""
        flows = parse_flows_md(Path("/nonexistent.md"))
        assert len(flows) == 0


class TestDetectGaps:
    """Tests for detect_gaps function."""

    def test_no_gaps_when_matching(
        self,
        flows_file: Path,
        req_directory_matching: Path,
    ) -> None:
        """Test no gaps when flows and stories match."""
        report = detect_gaps(flows_file, req_directory_matching)

        # Should have some gaps due to missing stories (STORY-003, confirmation)
        # but cart_review and payment_validation should match
        matching_gaps = [
            g
            for g in report.gaps
            if g.step in ("cart_review", "payment_validation")
            and g.gap_type not in ("missing_story", "missing_implementation")
        ]
        assert len(matching_gaps) == 0

    def test_detects_missing_story(
        self,
        flows_file: Path,
        req_directory_matching: Path,
    ) -> None:
        """Test detecting missing story (no story_id in FLOWS.md)."""
        report = detect_gaps(flows_file, req_directory_matching)

        missing_story_gaps = [g for g in report.gaps if g.gap_type == "missing_story"]
        assert len(missing_story_gaps) == 1
        assert missing_story_gaps[0].step == "confirmation"

    def test_detects_status_mismatch(
        self,
        flows_file: Path,
        req_directory_with_gaps: Path,
    ) -> None:
        """Test detecting status mismatch."""
        report = detect_gaps(flows_file, req_directory_with_gaps)

        status_gaps = [g for g in report.gaps if g.gap_type == "status_mismatch"]
        assert len(status_gaps) >= 1

        payment_gap = next(
            (g for g in status_gaps if g.step == "payment_validation"), None
        )
        assert payment_gap is not None
        assert "Draft" in payment_gap.description

    def test_detects_orphan_step(
        self,
        flows_file: Path,
        req_directory_with_gaps: Path,
    ) -> None:
        """Test detecting orphan step (in story but not in FLOWS.md)."""
        report = detect_gaps(flows_file, req_directory_with_gaps)

        orphan_gaps = [g for g in report.gaps if g.gap_type == "orphan_step"]
        assert len(orphan_gaps) >= 1

        unknown_gap = next((g for g in orphan_gaps if g.step == "unknown_step"), None)
        assert unknown_gap is not None

    def test_handles_missing_flows_file(
        self,
        req_directory_matching: Path,
    ) -> None:
        """Test handling missing FLOWS.md file."""
        report = detect_gaps("/nonexistent/FLOWS.md", req_directory_matching)

        assert len(report.gaps) == 1
        assert report.gaps[0].gap_type == "config_error"


class TestDetectFlowGaps:
    """Tests for detect_flow_gaps function."""

    def test_generates_report(
        self,
        flows_file: Path,
        req_directory_matching: Path,
    ) -> None:
        """Test generating gap report."""
        result = detect_flow_gaps(str(flows_file), str(req_directory_matching))

        assert "Generated:" in result
        assert "Flow Gap Analysis Report" in result


class TestGetGapSummary:
    """Tests for get_gap_summary function."""

    def test_summary_with_gaps(
        self,
        flows_file: Path,
        req_directory_with_gaps: Path,
    ) -> None:
        """Test summary with gaps."""
        summary = detect_flow_gaps(
            str(flows_file), str(req_directory_with_gaps), summary=True
        )

        assert "gaps found" in summary

    def test_summary_no_gaps(self) -> None:
        """Test summary when flows file missing (error gap)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = detect_flow_gaps("/nonexistent.md", tmpdir, summary=True)
            assert "gaps found" in summary or "No flow gaps" in summary
