"""Evidence verifier for browser test results.

Verifies all test evidence (screenshots, logs, timestamps)
to ensure test results are not hallucinated.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from sef_agents.tools.browser.execution_logger import ExecutionLogger
from sef_agents.tools.browser.screenshot_utils import (
    get_screenshot_dir,
    get_screenshot_mtime,
    verify_screenshot_content,
    verify_screenshot_exists,
)

logger = structlog.get_logger(__name__)


@dataclass
class VerificationResult:
    """Result of evidence verification.

    Attributes:
        valid: Whether all evidence is valid.
        issues: List of issues found.
        screenshot_count: Number of screenshots verified.
        log_entry_count: Number of log entries verified.
        warnings: Non-critical issues.
    """

    valid: bool
    issues: list[str] = field(default_factory=list)
    screenshot_count: int = 0
    log_entry_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "issues": self.issues,
            "screenshot_count": self.screenshot_count,
            "log_entry_count": self.log_entry_count,
            "warnings": self.warnings,
        }


class EvidenceVerifier:
    """Verify test execution evidence.

    Ensures test results are backed by real evidence:
    - Screenshots exist and are valid
    - Execution log exists and is consistent
    - Timestamps are sequential and realistic
    """

    def __init__(self, story_id: str, base_dir: Path | None = None):
        """Initialize evidence verifier.

        Args:
            story_id: Story identifier.
            base_dir: Base directory for evidence files.
        """
        self.story_id = story_id

        if base_dir is None:
            from sef_agents.session import SessionManager

            session = SessionManager.get()
            base_dir = session.project_root or Path.cwd()

        self.base_dir = base_dir
        self.execution_logger = ExecutionLogger(story_id, base_dir)
        self.screenshot_dir = get_screenshot_dir(story_id, base_dir)

    def verify_screenshot(self, path: Path) -> tuple[bool, str]:
        """Verify a single screenshot file.

        Args:
            path: Path to screenshot file.

        Returns:
            Tuple of (valid, error_message).
        """
        # First check existence
        valid, error = verify_screenshot_exists(path)
        if not valid:
            return False, error

        # Then check content
        valid, error = verify_screenshot_content(path)
        if not valid:
            return False, error

        return True, ""

    def verify_all_screenshots(self) -> tuple[bool, list[str], int]:
        """Verify all screenshots in the screenshot directory.

        Returns:
            Tuple of (all_valid, issues, count).
        """
        issues = []
        count = 0

        if not self.screenshot_dir.exists():
            return False, ["Screenshot directory does not exist"], 0

        screenshots = list(self.screenshot_dir.glob("*.png"))

        if not screenshots:
            return False, ["No screenshots found"], 0

        for screenshot in screenshots:
            valid, error = self.verify_screenshot(screenshot)
            if valid:
                count += 1
            else:
                issues.append(error)

        return len(issues) == 0, issues, count

    def verify_log_integrity(self) -> tuple[bool, list[str]]:
        """Verify execution log is valid.

        Returns:
            Tuple of (valid, issues).
        """
        return self.execution_logger.verify_log_integrity()

    def verify_timestamp_consistency(self) -> tuple[bool, list[str]]:
        """Verify timestamps are consistent.

        Checks:
        - Log timestamps are sequential
        - Log timestamps are realistic (not too fast/slow)
        - Screenshot mtimes are close to log timestamps

        Returns:
            Tuple of (valid, issues).
        """
        issues = []
        entries = self.execution_logger.read_log()

        if not entries:
            return False, ["No log entries to verify"]

        prev_timestamp = None

        for entry in entries:
            try:
                timestamp = datetime.fromisoformat(entry.timestamp)

                # Check sequential
                if prev_timestamp:
                    if timestamp < prev_timestamp:
                        issues.append(
                            f"Timestamp not sequential: {entry.test_id} step {entry.step_number}"
                        )

                    # Check realistic duration (between 50ms and 5 min)
                    duration = (timestamp - prev_timestamp).total_seconds()
                    if duration < 0.05:
                        issues.append(
                            f"Suspiciously fast execution: {duration:.3f}s for {entry.test_id} step {entry.step_number}"
                        )
                    elif duration > 300:
                        issues.append(
                            f"Suspiciously slow execution: {duration:.1f}s for {entry.test_id} step {entry.step_number}"
                        )

                # Check screenshot timestamp if available
                if entry.screenshot_path:
                    screenshot_path = Path(entry.screenshot_path)
                    if screenshot_path.exists():
                        try:
                            mtime = get_screenshot_mtime(screenshot_path)
                            screenshot_time = datetime.fromtimestamp(mtime)
                            time_diff = abs(
                                (timestamp - screenshot_time).total_seconds()
                            )

                            if time_diff > 10:  # More than 10 seconds difference
                                issues.append(
                                    f"Screenshot mtime mismatch: {time_diff:.1f}s diff for {entry.test_id} step {entry.step_number}"
                                )
                        except FileNotFoundError:
                            pass  # Already caught by screenshot verification

                prev_timestamp = timestamp

            except ValueError as e:
                issues.append(f"Invalid timestamp: {entry.timestamp} - {e}")

        return len(issues) == 0, issues

    def verify_log_screenshot_consistency(self) -> tuple[bool, list[str]]:
        """Verify log entries have corresponding screenshots.

        Returns:
            Tuple of (valid, issues).
        """
        issues = []
        entries = self.execution_logger.read_log()

        for entry in entries:
            if entry.screenshot_path:
                screenshot = Path(entry.screenshot_path)
                if not screenshot.exists():
                    issues.append(
                        f"Screenshot missing: {entry.screenshot_path} for {entry.test_id} step {entry.step_number}"
                    )
                elif screenshot.stat().st_size != entry.screenshot_size:
                    issues.append(
                        f"Screenshot size mismatch: {entry.test_id} step {entry.step_number}"
                    )

        return len(issues) == 0, issues

    def cross_validate(self) -> VerificationResult:
        """Cross-validate all evidence sources.

        Performs comprehensive verification:
        1. Verify all screenshots exist and are valid
        2. Verify execution log integrity
        3. Verify timestamp consistency
        4. Verify log-screenshot consistency

        Returns:
            VerificationResult with all findings.
        """
        all_issues = []
        warnings = []

        # 1. Verify screenshots
        screenshots_valid, screenshot_issues, screenshot_count = (
            self.verify_all_screenshots()
        )
        if not screenshots_valid:
            all_issues.extend(screenshot_issues)

        # 2. Verify log integrity
        log_valid, log_issues = self.verify_log_integrity()
        if not log_valid:
            all_issues.extend(log_issues)

        log_entry_count = self.execution_logger.get_entry_count()

        # 3. Verify timestamp consistency
        timestamp_valid, timestamp_issues = self.verify_timestamp_consistency()
        if not timestamp_valid:
            # Timestamp issues are warnings, not critical
            warnings.extend(timestamp_issues)

        # 4. Verify log-screenshot consistency
        consistency_valid, consistency_issues = self.verify_log_screenshot_consistency()
        if not consistency_valid:
            all_issues.extend(consistency_issues)

        valid = len(all_issues) == 0

        result = VerificationResult(
            valid=valid,
            issues=all_issues,
            screenshot_count=screenshot_count,
            log_entry_count=log_entry_count,
            warnings=warnings,
        )

        logger.info(
            "evidence_verification_complete",
            valid=valid,
            screenshot_count=screenshot_count,
            log_entry_count=log_entry_count,
            issue_count=len(all_issues),
            warning_count=len(warnings),
        )

        return result


def verify_test_evidence(
    story_id: str, base_dir: Path | None = None
) -> VerificationResult:
    """Verify all test evidence for a story.

    Args:
        story_id: Story identifier.
        base_dir: Base directory for evidence files.

    Returns:
        VerificationResult with all findings.
    """
    verifier = EvidenceVerifier(story_id, base_dir)
    return verifier.cross_validate()
