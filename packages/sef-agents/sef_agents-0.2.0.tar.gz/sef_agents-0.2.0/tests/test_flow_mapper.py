"""Tests for flow_mapper module."""

import tempfile
from pathlib import Path

import pytest

from sef_agents.tools.flow_mapper import (
    Flow,
    FlowMap,
    FlowStep,
    generate_flow,
    parse_req_file_for_flow,
    scan_requirements_for_flows,
)


@pytest.fixture
def sample_req_with_flow() -> str:
    """Sample REQ.md content with flow context."""
    return """# Requirement: [STORY-001] Payment Validation

**Status:** In Progress
**Priority:** P1

---

## Flow Context

| Field | Value |
|-------|-------|
| **Business Process** | Order Processing |
| **Flow** | checkout_flow |
| **Flow Step** | payment_validation |
| **Upstream Step** | shipping_selection |
| **Downstream Step** | order_creation |

---

## User Story

**As a** customer
**I want** my payment validated
**So that** I can complete checkout
"""


@pytest.fixture
def sample_req_without_flow() -> str:
    """Sample REQ.md content without flow context."""
    return """# Requirement: [STORY-002] User Settings

**Status:** Draft
**Priority:** P2

---

## User Story

**As a** user
**I want** to change settings
**So that** I can customize my experience
"""


@pytest.fixture
def req_directory_with_flows(
    sample_req_with_flow: str,
    sample_req_without_flow: str,
) -> Path:
    """Create temp directory with REQ.md files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        req_dir = Path(tmpdir) / "requirements"
        req_dir.mkdir()

        # Story with flow context
        (req_dir / "STORY-001-REQ.md").write_text(sample_req_with_flow)

        # Story without flow context
        (req_dir / "STORY-002-REQ.md").write_text(sample_req_without_flow)

        # Another story in same flow
        (req_dir / "STORY-003-REQ.md").write_text(
            """# Requirement: [STORY-003] Order Creation

**Status:** Draft
**Priority:** P1

---

## Flow Context

| Field | Value |
|-------|-------|
| **Business Process** | Order Processing |
| **Flow** | checkout_flow |
| **Flow Step** | order_creation |
| **Upstream Step** | payment_validation |
| **Downstream Step** | confirmation |

---

## User Story

**As a** customer
**I want** my order created
**So that** I receive confirmation
"""
        )

        yield req_dir


class TestFlowStep:
    """Tests for FlowStep dataclass."""

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        step = FlowStep(
            step_name="payment_validation",
            story_id="STORY-001",
            status="In Progress",
            upstream="shipping_selection",
            downstream="order_creation",
            file_path="/path/to/req.md",
        )
        result = step.to_dict()

        assert result["step_name"] == "payment_validation"
        assert result["story_id"] == "STORY-001"
        assert result["status"] == "In Progress"
        assert result["upstream"] == "shipping_selection"
        assert result["downstream"] == "order_creation"


class TestFlow:
    """Tests for Flow class."""

    def test_add_step(self) -> None:
        """Test adding steps to flow."""
        flow = Flow(name="checkout_flow", process="Order Processing")
        step = FlowStep(
            step_name="payment_validation",
            story_id="STORY-001",
            status="In Progress",
            upstream="",
            downstream="",
            file_path="",
        )
        flow.add_step(step)

        assert "payment_validation" in flow.steps
        assert flow.steps["payment_validation"].story_id == "STORY-001"

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        flow = Flow(name="checkout_flow", process="Order Processing")
        result = flow.to_dict()

        assert result["name"] == "checkout_flow"
        assert result["process"] == "Order Processing"
        assert result["steps"] == {}


class TestFlowMap:
    """Tests for FlowMap class."""

    def test_get_or_create_flow_new(self) -> None:
        """Test creating new flow."""
        flow_map = FlowMap()
        flow = flow_map.get_or_create_flow("checkout_flow", "Order Processing")

        assert flow.name == "checkout_flow"
        assert flow.process == "Order Processing"
        assert "checkout_flow" in flow_map.flows

    def test_get_or_create_flow_existing(self) -> None:
        """Test getting existing flow."""
        flow_map = FlowMap()
        flow1 = flow_map.get_or_create_flow("checkout_flow", "Order Processing")
        flow2 = flow_map.get_or_create_flow("checkout_flow")

        assert flow1 is flow2
        assert len(flow_map.flows) == 1

    def test_to_mermaid_empty(self) -> None:
        """Test Mermaid generation with empty flows."""
        flow_map = FlowMap()
        mermaid = flow_map.to_mermaid()

        assert "graph LR" in mermaid

    def test_to_mermaid_with_steps(self) -> None:
        """Test Mermaid generation with steps."""
        flow_map = FlowMap()
        flow = flow_map.get_or_create_flow("checkout_flow")
        flow.add_step(
            FlowStep(
                step_name="payment",
                story_id="STORY-001",
                status="Done",
                upstream="",
                downstream="confirmation",
                file_path="",
            )
        )

        mermaid = flow_map.to_mermaid()

        assert "subgraph checkout_flow" in mermaid
        assert "payment" in mermaid
        assert "STORY-001" in mermaid

    def test_to_summary(self) -> None:
        """Test summary generation."""
        flow_map = FlowMap()
        flow = flow_map.get_or_create_flow("checkout_flow", "Order Processing")
        flow.add_step(
            FlowStep(
                step_name="payment",
                story_id="STORY-001",
                status="Done",
                upstream="",
                downstream="",
                file_path="",
            )
        )

        summary = flow_map.to_summary()

        assert "## Flow: checkout_flow" in summary
        assert "Order Processing" in summary
        assert "STORY-001" in summary


class TestParseReqFileForFlow:
    """Tests for parse_req_file_for_flow function."""

    def test_parse_with_flow_context(self, req_directory_with_flows: Path) -> None:
        """Test parsing file with flow context."""
        req_file = req_directory_with_flows / "STORY-001-REQ.md"
        step, flow_name, story_id = parse_req_file_for_flow(req_file)

        assert step is not None
        assert flow_name == "checkout_flow"
        assert story_id == "STORY-001"
        assert step.step_name == "payment_validation"
        assert step.upstream == "shipping_selection"
        assert step.downstream == "order_creation"

    def test_parse_without_flow_context(self, req_directory_with_flows: Path) -> None:
        """Test parsing file without flow context."""
        req_file = req_directory_with_flows / "STORY-002-REQ.md"
        step, flow_name, story_id = parse_req_file_for_flow(req_file)

        assert step is None
        assert flow_name == ""
        assert story_id == "STORY-002"

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing nonexistent file."""
        step, flow_name, story_id = parse_req_file_for_flow(Path("/nonexistent.md"))

        assert step is None
        assert flow_name == ""
        assert story_id == ""


class TestScanRequirementsForFlows:
    """Tests for scan_requirements_for_flows function."""

    def test_scan_directory(self, req_directory_with_flows: Path) -> None:
        """Test scanning requirements directory."""
        flow_map = scan_requirements_for_flows(req_directory_with_flows)

        assert len(flow_map.flows) == 1
        assert "checkout_flow" in flow_map.flows
        assert len(flow_map.flows["checkout_flow"].steps) == 2
        assert len(flow_map.orphan_stories) == 1

    def test_scan_nonexistent_directory(self) -> None:
        """Test scanning nonexistent directory."""
        flow_map = scan_requirements_for_flows("/nonexistent/path")

        assert len(flow_map.errors) > 0

    def test_scan_empty_directory(self) -> None:
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flow_map = scan_requirements_for_flows(tmpdir)

            assert len(flow_map.flows) == 0
            assert len(flow_map.orphan_stories) == 0


class TestGenerateFlowDiagram:
    """Tests for generate_flow_diagram function."""

    def test_generate_artifact(self, req_directory_with_flows: Path) -> None:
        """Test generating flow diagram artifact."""
        result = generate_flow(str(req_directory_with_flows))

        assert "Generated:" in result
        assert "1 flows" in result
        assert "2 steps" in result

        # Check artifact was created
        artifact = req_directory_with_flows / "FLOW_DIAGRAM.md"
        assert artifact.exists()

        content = artifact.read_text()
        assert "```mermaid" in content
        assert "checkout_flow" in content

    def test_generate_no_flows(self) -> None:
        """Test generating with no flows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_flow(tmpdir)
            assert "No flows found" in result


class TestGetFlowSummary:
    """Tests for get_flow_summary function."""

    def test_summary(self, req_directory_with_flows: Path) -> None:
        """Test getting flow summary."""
        summary = generate_flow(str(req_directory_with_flows), output="summary")

        assert "checkout_flow" in summary
        assert "STORY-001" in summary
        assert "Orphan Stories" in summary
