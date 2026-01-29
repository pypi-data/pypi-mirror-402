"""Browser Tools for SEF Agents.

This package provides browser automation capabilities for frontend E2E testing
using Playwright MCP. It includes:

- playwright_mcp_client: Client wrapper for Playwright MCP tools
- execution_logger: Audit trail logging for test execution
- evidence_verifier: Verify screenshots, logs, and timestamps
- screenshot_utils: Screenshot capture and management
- test_executor: Execute conceptual tests via browser tools
- report_generator: Generate test reports with evidence
"""

from sef_agents.tools.browser.evidence_verifier import (
    EvidenceVerifier,
    VerificationResult,
)
from sef_agents.tools.browser.execution_logger import (
    ExecutionLogEntry,
    ExecutionLogger,
)
from sef_agents.tools.browser.screenshot_utils import (
    get_screenshot_dir,
    get_screenshot_path,
    save_screenshot,
    verify_screenshot_content,
)
from sef_agents.tools.browser.test_executor import (
    BrowserTestExecutor,
    ExecutionResult,
    StepResult,
)

__all__ = [
    # Evidence verification
    "EvidenceVerifier",
    "VerificationResult",
    # Execution logging
    "ExecutionLogEntry",
    "ExecutionLogger",
    # Screenshot utilities
    "get_screenshot_dir",
    "get_screenshot_path",
    "save_screenshot",
    "verify_screenshot_content",
    # Test execution
    "BrowserTestExecutor",
    "ExecutionResult",
    "StepResult",
]
