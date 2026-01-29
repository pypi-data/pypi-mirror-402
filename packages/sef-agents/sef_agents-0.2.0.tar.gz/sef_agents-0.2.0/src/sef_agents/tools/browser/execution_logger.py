"""Execution logger for browser test audit trail.

Logs all MCP tool calls with timestamps, arguments, responses,
and screenshot paths for complete audit trail.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ExecutionLogEntry:
    """Single execution log entry.

    Attributes:
        timestamp: ISO8601 timestamp of execution.
        test_id: Test case identifier.
        step_number: Step number within test case.
        tool_name: Name of MCP tool called.
        tool_args: Arguments passed to tool.
        response: Response from tool.
        screenshot_path: Path to captured screenshot.
        screenshot_size: Size of screenshot file in bytes.
        duration_ms: Execution duration in milliseconds.
        status: Step status (PASS/FAIL).
        error: Error message if failed.
    """

    timestamp: str
    test_id: str
    step_number: int
    tool_name: str
    tool_args: dict = field(default_factory=dict)
    response: dict = field(default_factory=dict)
    screenshot_path: str | None = None
    screenshot_size: int = 0
    duration_ms: int = 0
    status: str = "PASS"
    error: str | None = None

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionLogEntry":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


def get_log_path(story_id: str, base_dir: Path | None = None) -> Path:
    """Get execution log path for a story.

    Args:
        story_id: Story identifier.
        base_dir: Base directory. Defaults to project root.

    Returns:
        Path to log file.
    """
    if base_dir is None:
        from sef_agents.session import SessionManager

        session = SessionManager.get()
        base_dir = session.project_root or Path.cwd()

    return base_dir / "sef-reports" / "qa_lead" / f"test_execution_log_{story_id}.jsonl"


class ExecutionLogger:
    """Log all test execution for audit trail.

    Writes JSONL format with one entry per line.
    """

    def __init__(self, story_id: str, base_dir: Path | None = None):
        """Initialize execution logger.

        Args:
            story_id: Story identifier.
            base_dir: Base directory for log files.
        """
        self.story_id = story_id
        self.log_file = get_log_path(story_id, base_dir)
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_execution(self, entry: ExecutionLogEntry) -> None:
        """Append execution entry to log file.

        Args:
            entry: Execution log entry to append.
        """
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")

        logger.info(
            "execution_logged",
            test_id=entry.test_id,
            step=entry.step_number,
            tool=entry.tool_name,
            status=entry.status,
        )

    def log_step(
        self,
        test_id: str,
        step_number: int,
        tool_name: str,
        tool_args: dict,
        response: dict,
        screenshot_path: Path | None = None,
        duration_ms: int = 0,
        status: str = "PASS",
        error: str | None = None,
    ) -> ExecutionLogEntry:
        """Log a test step execution.

        Args:
            test_id: Test case identifier.
            step_number: Step number.
            tool_name: MCP tool name.
            tool_args: Tool arguments.
            response: Tool response.
            screenshot_path: Path to screenshot.
            duration_ms: Execution duration.
            status: Step status.
            error: Error message if failed.

        Returns:
            The logged entry.
        """
        screenshot_size = 0
        screenshot_str = None

        if screenshot_path and screenshot_path.exists():
            screenshot_size = screenshot_path.stat().st_size
            screenshot_str = str(screenshot_path)

        entry = ExecutionLogEntry(
            timestamp=datetime.now().isoformat(),
            test_id=test_id,
            step_number=step_number,
            tool_name=tool_name,
            tool_args=tool_args,
            response=response,
            screenshot_path=screenshot_str,
            screenshot_size=screenshot_size,
            duration_ms=duration_ms,
            status=status,
            error=error,
        )

        self.log_execution(entry)
        return entry

    def read_log(self) -> list[ExecutionLogEntry]:
        """Read all entries from log file.

        Returns:
            List of log entries.
        """
        if not self.log_file.exists():
            return []

        entries = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(ExecutionLogEntry.from_json(line))
                    except json.JSONDecodeError as e:
                        logger.warning("invalid_log_entry", line=line, error=str(e))

        return entries

    def clear_log(self) -> None:
        """Clear the log file."""
        if self.log_file.exists():
            self.log_file.unlink()
        self._ensure_log_dir()

    def verify_log_integrity(self) -> tuple[bool, list[str]]:
        """Verify log file integrity.

        Checks:
        - Log file exists
        - All entries are valid JSON
        - Timestamps are sequential
        - No gaps in step numbers per test

        Returns:
            Tuple of (valid, list of issues).
        """
        issues = []

        if not self.log_file.exists():
            return False, ["Log file does not exist"]

        entries = self.read_log()

        if not entries:
            return False, ["Log file is empty"]

        # Check timestamps are sequential
        prev_timestamp = None
        for entry in entries:
            try:
                timestamp = datetime.fromisoformat(entry.timestamp)
                if prev_timestamp and timestamp < prev_timestamp:
                    issues.append(
                        f"Timestamp not sequential: {entry.timestamp} < {prev_timestamp.isoformat()}"
                    )
                prev_timestamp = timestamp
            except ValueError:
                issues.append(f"Invalid timestamp format: {entry.timestamp}")

        # Check step numbers per test
        test_steps: dict[str, list[int]] = {}
        for entry in entries:
            if entry.test_id not in test_steps:
                test_steps[entry.test_id] = []
            test_steps[entry.test_id].append(entry.step_number)

        for test_id, steps in test_steps.items():
            expected = list(range(1, len(steps) + 1))
            if sorted(steps) != expected:
                issues.append(f"Step numbers not sequential for {test_id}: {steps}")

        return len(issues) == 0, issues

    def get_entry_count(self) -> int:
        """Get number of entries in log.

        Returns:
            Number of log entries.
        """
        return len(self.read_log())
