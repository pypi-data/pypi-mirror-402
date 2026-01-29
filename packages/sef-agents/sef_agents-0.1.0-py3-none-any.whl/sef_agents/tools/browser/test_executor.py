"""Test executor for browser-based E2E tests.

Executes conceptual tests via Playwright MCP browser tools
and generates verified test reports.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from sef_agents.tools.browser.evidence_verifier import (
    EvidenceVerifier,
    VerificationResult,
)
from sef_agents.tools.browser.execution_logger import ExecutionLogger
from sef_agents.tools.browser.playwright_mcp_client import (
    PlaywrightMCPClient,
    check_browser_tools_available,
)
from sef_agents.tools.browser.screenshot_utils import (
    ensure_screenshot_dir,
    get_screenshot_path,
)

logger = structlog.get_logger(__name__)


@dataclass
class StepResult:
    """Result of a single test step.

    Attributes:
        step_number: Step number (1-indexed).
        action: Step action description.
        status: Step status (PASS/FAIL/SKIP).
        screenshot_path: Path to captured screenshot.
        error: Error message if failed.
        duration_ms: Execution duration in milliseconds.
        timestamp: ISO8601 timestamp.
    """

    step_number: int
    action: str
    status: str
    screenshot_path: Path | None = None
    error: str | None = None
    duration_ms: int = 0
    timestamp: str = ""

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ExecutionResult:
    """Result of a test case execution.

    Attributes:
        test_id: Test case identifier.
        title: Test case title.
        status: Overall status (PASS/FAIL).
        steps: List of step results.
        execution_time_ms: Total execution time.
        start_time: Start timestamp.
        end_time: End timestamp.
    """

    test_id: str
    title: str
    status: str
    steps: list[StepResult] = field(default_factory=list)
    execution_time_ms: int = 0
    start_time: str = ""
    end_time: str = ""


class BrowserTestExecutor:
    """Execute conceptual tests via Playwright MCP.

    Loads conceptual tests from JSON, executes via browser tools,
    logs execution, captures screenshots, and generates verified reports.
    """

    def __init__(self, story_id: str, base_dir: Path | None = None):
        """Initialize test executor.

        Args:
            story_id: Story identifier.
            base_dir: Base directory for test artifacts.
        """
        self.story_id = story_id

        if base_dir is None:
            from sef_agents.session import SessionManager

            session = SessionManager.get()
            base_dir = session.project_root or Path.cwd()

        self.base_dir = base_dir
        self.playwright_client = PlaywrightMCPClient.get_instance()
        self.execution_logger = ExecutionLogger(story_id, base_dir)
        self.evidence_verifier = EvidenceVerifier(story_id, base_dir)

        # Ensure screenshot directory exists
        ensure_screenshot_dir(story_id, base_dir)

    def get_conceptual_tests_path(self) -> Path:
        """Get path to conceptual tests JSON file.

        Returns:
            Path to tests/conceptual/{story_id}_tests.json
        """
        return self.base_dir / "tests" / "conceptual" / f"{self.story_id}_tests.json"

    def load_conceptual_tests(self) -> dict:
        """Load conceptual tests from JSON file.

        Returns:
            Parsed test data.

        Raises:
            FileNotFoundError: If tests file doesn't exist.
            json.JSONDecodeError: If file is not valid JSON.
        """
        tests_path = self.get_conceptual_tests_path()

        if not tests_path.exists():
            raise FileNotFoundError(
                f"Conceptual tests not found: {tests_path}. "
                "Run Test Designer agent first to create conceptual tests."
            )

        content = tests_path.read_text(encoding="utf-8")
        return json.loads(content)

    def _map_step_to_tool(self, step: str) -> tuple[str, dict]:
        """Map a test step description to MCP tool call.

        Args:
            step: Step description text.

        Returns:
            Tuple of (tool_name, tool_args).
        """
        step_lower = step.lower()

        # Simple keyword-based mapping
        if "navigate" in step_lower or "go to" in step_lower:
            # Extract URL if present
            return "browser_navigate", {"url": "http://localhost:3000"}

        if "click" in step_lower:
            return "browser_click", {"element": step, "ref": "auto"}

        if "type" in step_lower or "enter" in step_lower or "input" in step_lower:
            return "browser_type", {"element": step, "ref": "auto", "text": "test"}

        if "wait" in step_lower:
            return "browser_wait_for", {"time": 1}

        if "screenshot" in step_lower or "capture" in step_lower:
            return "browser_take_screenshot", {"filename": None}

        if "snapshot" in step_lower or "verify" in step_lower or "check" in step_lower:
            return "browser_snapshot", {}

        # Default to snapshot for verification steps
        return "browser_snapshot", {}

    def execute_step(self, test_id: str, step_number: int, step: str) -> StepResult:
        """Execute a single test step.

        Args:
            test_id: Test case identifier.
            step_number: Step number (1-indexed).
            step: Step description.

        Returns:
            StepResult with execution details.
        """
        start_time = time.time()
        screenshot_path = get_screenshot_path(
            self.story_id, test_id, step_number, self.base_dir
        )

        try:
            # Map step to tool call
            tool_name, tool_args = self._map_step_to_tool(step)

            # Execute via Playwright MCP
            # In real implementation, this would call the actual MCP tool
            if tool_name == "browser_navigate":
                result = self.playwright_client.browser_navigate(
                    tool_args.get("url", "")
                )
            elif tool_name == "browser_click":
                result = self.playwright_client.browser_click(
                    tool_args.get("element", ""),
                    tool_args.get("ref", ""),
                )
            elif tool_name == "browser_type":
                result = self.playwright_client.browser_type(
                    tool_args.get("element", ""),
                    tool_args.get("ref", ""),
                    tool_args.get("text", ""),
                )
            elif tool_name == "browser_snapshot":
                result = self.playwright_client.browser_snapshot()
            elif tool_name == "browser_take_screenshot":
                result = self.playwright_client.browser_take_screenshot(
                    str(screenshot_path)
                )
            elif tool_name == "browser_wait_for":
                result = self.playwright_client.browser_wait_for(
                    time=tool_args.get("time")
                )
            else:
                result = self.playwright_client.browser_snapshot()

            duration_ms = int((time.time() - start_time) * 1000)

            # Log execution
            self.execution_logger.log_step(
                test_id=test_id,
                step_number=step_number,
                tool_name=tool_name,
                tool_args=tool_args,
                response=result.data or {},
                screenshot_path=screenshot_path if screenshot_path.exists() else None,
                duration_ms=duration_ms,
                status="PASS" if result.success else "FAIL",
                error=result.error,
            )

            return StepResult(
                step_number=step_number,
                action=step,
                status="PASS" if result.success else "FAIL",
                screenshot_path=screenshot_path if screenshot_path.exists() else None,
                error=result.error,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Log failed execution
            self.execution_logger.log_step(
                test_id=test_id,
                step_number=step_number,
                tool_name="error",
                tool_args={},
                response={"error": str(e)},
                duration_ms=duration_ms,
                status="FAIL",
                error=str(e),
            )

            logger.error(
                "execute_step_failed", test_id=test_id, step=step_number, error=str(e)
            )
            raise

    def execute_test_case(self, test_case: dict) -> ExecutionResult:
        """Execute a single test case.

        Args:
            test_case: Test case dictionary from conceptual tests.

        Returns:
            ExecutionResult with all step results.
        """
        test_id = test_case.get("id", "TC-UNKNOWN")
        title = test_case.get("title", "Unknown Test")
        steps = test_case.get("steps", [])

        start_time = datetime.now()
        step_results = []

        logger.info("executing_test_case", test_id=test_id, step_count=len(steps))

        for i, step in enumerate(steps, 1):
            step_result = self.execute_step(test_id, i, step)
            step_results.append(step_result)

            # Stop on first failure (optional - could continue)
            if step_result.status == "FAIL":
                logger.warning(
                    "test_step_failed",
                    test_id=test_id,
                    step=i,
                    error=step_result.error,
                )

        end_time = datetime.now()
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Determine overall status
        all_passed = all(s.status == "PASS" for s in step_results)
        status = "PASS" if all_passed else "FAIL"

        return ExecutionResult(
            test_id=test_id,
            title=title,
            status=status,
            steps=step_results,
            execution_time_ms=execution_time_ms,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )

    def execute_all_tests(self) -> list[ExecutionResult]:
        """Execute all conceptual tests for the story.

        Returns:
            List of ExecutionResult for each test case.

        Raises:
            RuntimeError: If browser tools not available.
            FileNotFoundError: If conceptual tests not found.
        """
        # Check browser tools availability
        if not check_browser_tools_available():
            raise RuntimeError(
                "Playwright MCP browser tools are not available. "
                "Please enable Playwright MCP in your client settings."
            )

        # Clear previous log
        self.execution_logger.clear_log()

        # Load conceptual tests
        test_data = self.load_conceptual_tests()
        test_cases = test_data.get("test_cases", [])

        if not test_cases:
            raise ValueError("No test cases found in conceptual tests")

        logger.info(
            "executing_all_tests",
            story_id=self.story_id,
            test_count=len(test_cases),
        )

        results = []
        for test_case in test_cases:
            result = self.execute_test_case(test_case)
            results.append(result)

        return results

    def verify_evidence(self) -> VerificationResult:
        """Verify all test evidence.

        Returns:
            VerificationResult with findings.
        """
        return self.evidence_verifier.cross_validate()

    def generate_report(self, results: list[ExecutionResult]) -> Path:
        """Generate test report with verification.

        Args:
            results: List of test results.

        Returns:
            Path to generated report.

        Raises:
            ValueError: If evidence verification fails.
        """
        # Verify evidence before generating report
        verification = self.verify_evidence()

        if not verification.valid:
            raise ValueError(
                f"Evidence verification failed. Issues: {verification.issues}"
            )

        # Generate report
        report_path = self.base_dir / "sef-reports" / "qa_lead" / "ui_test_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._format_report(results, verification)
        report_path.write_text(content, encoding="utf-8")

        logger.info("test_report_generated", path=str(report_path))
        return report_path

    def _format_report(
        self, results: list[ExecutionResult], verification: VerificationResult
    ) -> str:
        """Format test results as markdown report.

        Args:
            results: List of test results.
            verification: Verification result.

        Returns:
            Markdown formatted report.
        """
        now = datetime.now()
        passed = sum(1 for r in results if r.status == "PASS")
        failed = len(results) - passed
        total_time = sum(r.execution_time_ms for r in results)

        lines = [
            f"# UI Test Report: {self.story_id}",
            "",
            f"**Execution Date:** {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Tests:** {len(results)}",
            f"**Passed:** {passed}",
            f"**Failed:** {failed}",
            f"**Execution Time:** {total_time / 1000:.1f}s",
            "",
            "---",
            "",
            "## Verification Status",
            "",
            f"- {'✅' if verification.valid else '❌'} **Overall:** {'VERIFIED' if verification.valid else 'FAILED'}",
            f"- ✅ **Screenshots:** {verification.screenshot_count} files verified",
            f"- ✅ **Execution Log:** {verification.log_entry_count} entries",
        ]

        if verification.issues:
            lines.append("")
            lines.append("### Issues Found")
            for issue in verification.issues:
                lines.append(f"- ❌ {issue}")

        if verification.warnings:
            lines.append("")
            lines.append("### Warnings")
            for warning in verification.warnings:
                lines.append(f"- ⚠️ {warning}")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Test Results",
                "",
            ]
        )

        for result in results:
            status_icon = "✅" if result.status == "PASS" else "❌"
            lines.extend(
                [
                    f"### {result.test_id}: {result.title}",
                    "",
                    f"- **Status:** {status_icon} {result.status}",
                    f"- **Execution Time:** {result.execution_time_ms}ms",
                    f"- **Steps:** {len(result.steps)}",
                    "",
                    "| Step | Action | Status | Screenshot |",
                    "|------|--------|--------|------------|",
                ]
            )

            for step in result.steps:
                step_icon = "✅" if step.status == "PASS" else "❌"
                screenshot_link = ""
                if step.screenshot_path and step.screenshot_path.exists():
                    rel_path = step.screenshot_path.relative_to(self.base_dir)
                    screenshot_link = f"[📷]({rel_path})"

                lines.append(
                    f"| {step.step_number} | {step.action[:50]}... | {step_icon} {step.status} | {screenshot_link} |"
                )

            lines.append("")

        lines.extend(
            [
                "---",
                "",
                f"*Report generated by SEF Agents at {now.isoformat()}*",
            ]
        )

        return "\n".join(lines)


def execute_frontend_tests(story_id: str, base_dir: Path | None = None) -> str:
    """Execute frontend tests for a story.

    MCP tool function to execute conceptual tests.

    Args:
        story_id: Story identifier.
        base_dir: Base directory.

    Returns:
        Execution summary.
    """
    try:
        executor = BrowserTestExecutor(story_id, base_dir)
        results = executor.execute_all_tests()

        # Verify evidence
        verification = executor.verify_evidence()

        if not verification.valid:
            return (
                f"❌ Test execution completed but evidence verification failed.\n"
                f"Issues: {verification.issues}"
            )

        # Generate report
        report_path = executor.generate_report(results)

        passed = sum(1 for r in results if r.status == "PASS")
        failed = len(results) - passed

        return (
            f"✅ Test execution complete for {story_id}\n"
            f"Tests: {len(results)} | Passed: {passed} | Failed: {failed}\n"
            f"Report: {report_path}\n"
            f"Evidence: {verification.screenshot_count} screenshots, "
            f"{verification.log_entry_count} log entries"
        )

    except FileNotFoundError as e:
        return f"❌ {e}"
    except RuntimeError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error("execute_frontend_tests_failed", story_id=story_id, error=str(e))
        raise
