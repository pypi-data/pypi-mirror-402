"""Flow Mapper for SEF Agents.

Scans REQ.md files, extracts flow context fields,
and generates Mermaid diagrams for E2E flow visualization.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# Regex patterns for flow context extraction
STORY_ID_PATTERN = re.compile(r"#\s*Requirement:\s*\[([A-Z]+-\d+)\]")
STATUS_PATTERN = re.compile(r"\*\*Status:\*\*\s*(\w+(?:\s+\w+)?)")
FLOW_PATTERN = re.compile(r"\|\s*\*\*Flow\*\*\s*\|\s*([^|]+)\s*\|")
FLOW_STEP_PATTERN = re.compile(r"\|\s*\*\*Flow Step\*\*\s*\|\s*([^|]+)\s*\|")
UPSTREAM_PATTERN = re.compile(r"\|\s*\*\*Upstream Step\*\*\s*\|\s*([^|]+)\s*\|")
DOWNSTREAM_PATTERN = re.compile(r"\|\s*\*\*Downstream Step\*\*\s*\|\s*([^|]+)\s*\|")
PROCESS_PATTERN = re.compile(r"\|\s*\*\*Business Process\*\*\s*\|\s*([^|]+)\s*\|")


@dataclass
class FlowStep:
    """Represents a step in a flow derived from a story."""

    step_name: str
    story_id: str
    status: str
    upstream: str
    downstream: str
    file_path: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            "step_name": self.step_name,
            "story_id": self.story_id,
            "status": self.status,
            "upstream": self.upstream,
            "downstream": self.downstream,
            "file_path": self.file_path,
        }


@dataclass
class Flow:
    """Represents a business flow with its steps."""

    name: str
    process: str = ""
    steps: dict[str, FlowStep] = field(default_factory=dict)

    def add_step(self, step: FlowStep) -> None:
        """Add a step to the flow."""
        self.steps[step.step_name] = step

    def to_dict(self) -> dict[str, str | dict[str, dict[str, str]]]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "process": self.process,
            "steps": {name: step.to_dict() for name, step in self.steps.items()},
        }


@dataclass
class FlowMap:
    """Collection of all flows extracted from requirements."""

    flows: dict[str, Flow] = field(default_factory=dict)
    orphan_stories: list[dict[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def get_or_create_flow(self, flow_name: str, process: str = "") -> Flow:
        """Get existing flow or create new one."""
        if flow_name not in self.flows:
            self.flows[flow_name] = Flow(name=flow_name, process=process)
        elif process and not self.flows[flow_name].process:
            self.flows[flow_name].process = process
        return self.flows[flow_name]

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram for all flows."""
        lines = ["graph LR"]

        for flow in self.flows.values():
            if not flow.steps:
                continue

            lines.append(f"    subgraph {flow.name}")

            # Build edges from upstream/downstream
            for step in flow.steps.values():
                step_id = _sanitize_id(step.step_name)
                style = _get_status_style(step.status)

                label = f"{step.step_name}<br/>{step.story_id}"
                lines.append(f"        {step_id}[{label}]{style}")

                if step.downstream and step.downstream.strip() not in ("-", "", "N/A"):
                    downstream_id = _sanitize_id(step.downstream.strip())
                    lines.append(f"        {step_id} --> {downstream_id}")

            lines.append("    end")

        return "\n".join(lines)

    def to_summary(self) -> str:
        """Generate text summary of flows."""
        lines = ["# Flow Map Summary", ""]

        if not self.flows:
            lines.append("No flows found in requirements.")
            return "\n".join(lines)

        for flow in self.flows.values():
            lines.append(f"## Flow: {flow.name}")
            if flow.process:
                lines.append(f"**Process:** {flow.process}")
            lines.append("")

            if flow.steps:
                lines.append("| Step | Story | Status |")
                lines.append("|------|-------|--------|")
                for step in flow.steps.values():
                    lines.append(
                        f"| {step.step_name} | {step.story_id} | {step.status} |"
                    )
            else:
                lines.append("*No steps defined*")

            lines.append("")

        if self.orphan_stories:
            lines.append("## Orphan Stories (No Flow Context)")
            lines.append("")
            for orphan in self.orphan_stories:
                lines.append(f"- {orphan['story_id']}: {orphan['file']}")
            lines.append("")

        return "\n".join(lines)


def _sanitize_id(name: str) -> str:
    """Convert step name to valid Mermaid node ID."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())


def _get_status_style(status: str) -> str:
    """Get Mermaid style class based on status."""
    status_lower = status.lower()
    if status_lower == "done":
        return ":::done"
    if status_lower in ("in progress", "in development"):
        return ":::inprogress"
    if status_lower == "draft":
        return ":::draft"
    return ""


def _extract_field(pattern: re.Pattern[str], content: str) -> str:
    """Extract field value using regex pattern."""
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""


def parse_req_file_for_flow(file_path: Path) -> tuple[FlowStep | None, str, str]:
    """Parse a REQ.md file for flow context.

    Args:
        file_path: Path to REQ.md file.

    Returns:
        Tuple of (FlowStep or None, flow_name, story_id).
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("req_file_read_error", file=str(file_path), error=str(e))
        return None, "", ""

    # Extract story ID
    story_id = _extract_field(STORY_ID_PATTERN, content)
    if not story_id:
        return None, "", ""

    # Extract flow context
    flow_name = _extract_field(FLOW_PATTERN, content)
    if not flow_name or flow_name in ("-", "N/A", "[Flow Name"):
        # No flow context
        return None, "", story_id

    flow_step = _extract_field(FLOW_STEP_PATTERN, content)
    if not flow_step or flow_step in ("-", "N/A", "[Step Name"):
        return None, flow_name, story_id

    status = _extract_field(STATUS_PATTERN, content) or "Draft"
    upstream = _extract_field(UPSTREAM_PATTERN, content)
    downstream = _extract_field(DOWNSTREAM_PATTERN, content)

    step = FlowStep(
        step_name=flow_step,
        story_id=story_id,
        status=status,
        upstream=upstream,
        downstream=downstream,
        file_path=str(file_path),
    )

    return step, flow_name, story_id


def scan_requirements_for_flows(directory: str | Path) -> FlowMap:
    """Scan requirements directory and build flow map.

    Args:
        directory: Path to requirements directory.

    Returns:
        FlowMap with all flows and steps.
    """
    flow_map = FlowMap()
    dir_path = Path(directory)

    if not dir_path.exists():
        flow_map.errors.append(f"Directory not found: {directory}")
        return flow_map

    # Find all REQ.md and story files
    req_files = list(dir_path.rglob("*REQ*.md")) + list(dir_path.rglob("STORY-*.md"))
    req_files = list(set(req_files))

    for req_file in req_files:
        step, flow_name, story_id = parse_req_file_for_flow(req_file)

        if step and flow_name:
            # Extract process from file
            try:
                content = req_file.read_text(encoding="utf-8")
                process = _extract_field(PROCESS_PATTERN, content)
            except OSError:
                process = ""

            flow = flow_map.get_or_create_flow(flow_name, process)
            flow.add_step(step)
        elif story_id and not flow_name:
            # Story without flow context
            flow_map.orphan_stories.append(
                {
                    "story_id": story_id,
                    "file": str(req_file),
                }
            )

    logger.info(
        "flow_scan_complete",
        files_scanned=len(req_files),
        flows_found=len(flow_map.flows),
        orphan_stories=len(flow_map.orphan_stories),
    )

    return flow_map


def generate_flow(directory: str, output: str = "diagram") -> str:
    """Generate flow diagram or summary from requirements.

    Args:
        directory: Path to requirements directory.
        output: Output type - "diagram" (full with mermaid), "summary" (text only).

    Returns:
        Markdown with Mermaid diagram and summary, or text summary only.
    """
    flow_map = scan_requirements_for_flows(directory)

    if flow_map.errors:
        return f"Errors: {flow_map.errors}"

    # Summary mode
    if output == "summary":
        return flow_map.to_summary()

    # Diagram mode (default)
    if not flow_map.flows:
        return (
            f"No flows found in {directory}. Ensure stories have Flow Context sections."
        )

    mermaid = flow_map.to_mermaid()
    summary = flow_map.to_summary()

    result = f"""# Flow Diagram

*Auto-generated by flow_mapper.py*

## Visual Flow

```mermaid
{mermaid}
```

## Style Legend

- Default: Draft
- `:::done`: Completed
- `:::inprogress`: In Progress

---

{summary}
"""

    # Write artifact
    output_path = Path(directory) / "FLOW_DIAGRAM.md"
    try:
        output_path.write_text(result, encoding="utf-8")
        flows_count = len(flow_map.flows)
        steps_count = sum(len(f.steps) for f in flow_map.flows.values())
        return f"Generated: `{output_path}` ({flows_count} flows, {steps_count} steps)"
    except OSError as e:
        return f"Failed to write artifact: {e}"
