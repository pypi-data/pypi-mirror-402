"""Capability Detection for SEF Workflow.

Detects available tools (Playwright, etc.) and story type classification
for appropriate testing strategy selection.
"""

import re
from pathlib import Path

import structlog

from sef_agents.constants import (
    BACKEND_KEYWORDS,
    FRONTEND_KEYWORDS,
    StoryType,
)

logger = structlog.get_logger(__name__)


class CapabilityDetector:
    """Detects tool capabilities and story type.

    Attributes:
        project_root: Root directory for file scanning.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize capability detector.

        Args:
            project_root: Project root for file scanning.
        """
        self.project_root = project_root or Path(".")

    def detect_browser_tools(self) -> bool:
        """Detect if browser/Playwright MCP tools are available.

        Checks for MCP browser tools availability via:
        1. Check sef-agents browser tools module
        2. Fall back to file-based indicators

        Returns:
            True if browser tools are available.
        """
        # Primary: Check sef-agents browser tools module
        try:
            from sef_agents.tools.browser.playwright_mcp_client import (
                check_browser_tools_available,
            )

            if check_browser_tools_available():
                logger.info("browser_tools_detected", source="playwright_mcp_client")
                return True
        except ImportError:
            logger.debug("playwright_mcp_client not available, using fallback")

        # Fallback: Check for file-based indicators
        indicators = [
            self.project_root / "playwright.config.ts",
            self.project_root / "playwright.config.js",
            self.project_root / "e2e",
            self.project_root / "tests" / "e2e",
        ]

        for indicator in indicators:
            if indicator.exists():
                logger.info("browser_tools_detected", indicator=str(indicator))
                return True

        # Check package.json for playwright
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                content = package_json.read_text()
                if "playwright" in content.lower():
                    logger.info("browser_tools_detected", source="package.json")
                    return True
            except OSError:
                pass

        # Check pyproject.toml for playwright
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text()
                if "playwright" in content.lower():
                    logger.info("browser_tools_detected", source="pyproject.toml")
                    return True
            except OSError:
                pass

        logger.info("browser_tools_not_detected")
        return False

    def classify_story_type(self, requirements_content: str) -> str:
        """Classify story type from requirements content.

        Args:
            requirements_content: Full text of requirements file.

        Returns:
            StoryType value (backend, frontend, fullstack, unknown).
        """
        content_lower = requirements_content.lower()

        frontend_score = sum(1 for kw in FRONTEND_KEYWORDS if kw in content_lower)
        backend_score = sum(1 for kw in BACKEND_KEYWORDS if kw in content_lower)

        logger.info(
            "story_type_classification",
            frontend_score=frontend_score,
            backend_score=backend_score,
        )

        if frontend_score > 0 and backend_score > 0:
            return StoryType.FULLSTACK.value
        elif frontend_score > 0:
            return StoryType.FRONTEND.value
        elif backend_score > 0:
            return StoryType.BACKEND.value
        else:
            return StoryType.UNKNOWN.value

    def classify_from_file(self, requirements_path: Path) -> str:
        """Classify story type from requirements file.

        Args:
            requirements_path: Path to requirements markdown file.

        Returns:
            StoryType value.
        """
        if not requirements_path.exists():
            logger.warning("requirements_file_not_found", path=str(requirements_path))
            return StoryType.UNKNOWN.value

        try:
            content = requirements_path.read_text()
            return self.classify_story_type(content)
        except OSError as e:
            logger.error("requirements_read_failed", error=str(e))
            return StoryType.UNKNOWN.value

    def find_requirements_file(self, story_id: str) -> Path | None:
        """Find requirements file for a story.

        Args:
            story_id: Story identifier.

        Returns:
            Path to requirements file if found.
        """
        # Check common locations
        patterns = [
            f"docs/requirements/REQ-{story_id}.md",
            f"docs/requirements/{story_id}.md",
            f"requirements/{story_id}.md",
            "docs/requirements/REQ-*.md",  # Glob pattern
        ]

        for pattern in patterns:
            if "*" in pattern:
                matches = list(self.project_root.glob(pattern))
                if matches:
                    for match in matches:
                        if story_id.lower() in match.name.lower():
                            return match
                    return matches[0]
            else:
                path = self.project_root / pattern
                if path.exists():
                    return path

        return None

    def check_capabilities(
        self,
        story_id: str,
        story_type: str | None = None,
    ) -> dict:
        """Check all capabilities for a story.

        Args:
            story_id: Story identifier.
            story_type: Optional pre-classified story type.

        Returns:
            Dict with capability check results.
        """
        # Detect story type if not provided
        if not story_type or story_type == StoryType.UNKNOWN.value:
            req_file = self.find_requirements_file(story_id)
            if req_file:
                story_type = self.classify_from_file(req_file)
            else:
                story_type = StoryType.UNKNOWN.value

        # Detect available tools
        browser_available = self.detect_browser_tools()

        # Determine required capabilities
        requires_browser = story_type in (
            StoryType.FRONTEND.value,
            StoryType.FULLSTACK.value,
        )

        # Build capability status
        capabilities = {
            "browser_tools": browser_available,
            "git_tools": True,  # Always assume available
            "file_tools": True,  # Always available in MCP
        }

        # Check for capability gaps
        gaps = []
        if requires_browser and not browser_available:
            gaps.append(
                {
                    "capability": "browser_tools",
                    "required": True,
                    "available": False,
                    "reason": "Frontend story requires Playwright for E2E tests",
                }
            )

        return {
            "story_id": story_id,
            "story_type": story_type,
            "requires_browser": requires_browser,
            "browser_available": browser_available,
            "capabilities": capabilities,
            "gaps": gaps,
            "all_met": len(gaps) == 0,
        }

    def format_capability_report(self, check_result: dict) -> str:
        """Format capability check as user-friendly report.

        Args:
            check_result: Result from check_capabilities().

        Returns:
            Formatted string report.
        """
        lines = [
            f"📋 Capability Check: {check_result['story_id']}",
            "",
            f"Story Type: {check_result['story_type']}",
            "",
            "| Capability | Required | Available |",
            "|------------|----------|-----------|",
        ]

        caps = check_result["capabilities"]
        requires_browser = check_result["requires_browser"]

        lines.append(
            f"| Browser/Playwright | "
            f"{'✅ Yes' if requires_browser else '➖ No'} | "
            f"{'✅ Yes' if caps['browser_tools'] else '❌ No'} |"
        )
        lines.append("| Git Tools | ✅ Yes | ✅ Yes |")
        lines.append("| File Tools | ✅ Yes | ✅ Yes |")

        if check_result["gaps"]:
            lines.append("")
            lines.append("⚠️ WARNING: Capability gaps detected.")
            lines.append("")
            lines.append("Options:")
            lines.append("1. Enable Playwright MCP in Cursor settings (recommended)")
            lines.append("2. Run manual E2E tests, document in ui_test_report.md")
            lines.append("3. Log to TECH_DEBT.md as 'E2E_PENDING' and continue")
            lines.append("")
            lines.append("Select option (1/2/3):")
        else:
            lines.append("")
            lines.append("✅ All required capabilities available.")

        return "\n".join(lines)


def detect_story_type_from_diff(diff_content: str) -> str:
    """Classify story type from git diff content.

    Useful for developer to detect frontend work mid-implementation.

    Args:
        diff_content: Git diff output.

    Returns:
        StoryType value.
    """
    # Check file extensions in diff
    frontend_extensions = {".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss"}
    backend_extensions = {".py", ".java", ".go", ".rs", ".sql"}

    frontend_files = 0
    backend_files = 0

    # Parse diff for file paths
    file_pattern = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)
    matches = file_pattern.findall(diff_content)

    for filepath in matches:
        ext = Path(filepath).suffix.lower()
        if ext in frontend_extensions:
            frontend_files += 1
        elif ext in backend_extensions:
            backend_files += 1

    if frontend_files > 0 and backend_files > 0:
        return StoryType.FULLSTACK.value
    elif frontend_files > 0:
        return StoryType.FRONTEND.value
    elif backend_files > 0:
        return StoryType.BACKEND.value

    return StoryType.UNKNOWN.value
