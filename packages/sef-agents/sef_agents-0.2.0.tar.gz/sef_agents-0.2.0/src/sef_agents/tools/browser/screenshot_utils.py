"""Screenshot utilities for browser testing.

Provides functions to capture, save, and verify screenshots
from Playwright MCP browser tools.
"""

from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# PNG file signature (first 8 bytes)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def get_screenshot_dir(story_id: str, base_dir: Path | None = None) -> Path:
    """Get screenshot directory for a story.

    Args:
        story_id: Story identifier.
        base_dir: Base directory. Defaults to project root.

    Returns:
        Path to screenshot directory.
    """
    if base_dir is None:
        from sef_agents.session import SessionManager

        session = SessionManager.get()
        base_dir = session.project_root or Path.cwd()

    return base_dir / "sef-reports" / "qa_lead" / "screenshots" / story_id


def get_screenshot_path(
    story_id: str,
    test_id: str,
    step_number: int,
    base_dir: Path | None = None,
) -> Path:
    """Get screenshot path for a specific test step.

    Args:
        story_id: Story identifier.
        test_id: Test case identifier.
        step_number: Step number (1-indexed).
        base_dir: Base directory. Defaults to project root.

    Returns:
        Path for the screenshot file.
    """
    screenshot_dir = get_screenshot_dir(story_id, base_dir)
    return screenshot_dir / f"{test_id}_step{step_number}.png"


def ensure_screenshot_dir(story_id: str, base_dir: Path | None = None) -> Path:
    """Ensure screenshot directory exists.

    Args:
        story_id: Story identifier.
        base_dir: Base directory.

    Returns:
        Path to created/existing directory.
    """
    screenshot_dir = get_screenshot_dir(story_id, base_dir)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir


def save_screenshot(content: bytes, path: Path) -> bool:
    """Save screenshot content to file.

    Args:
        content: Screenshot bytes (PNG format).
        path: Path to save file.

    Returns:
        True if saved successfully.

    Raises:
        ValueError: If content is empty or invalid PNG.
    """
    if not content:
        raise ValueError("Screenshot content is empty")

    # Verify PNG signature
    if not content.startswith(PNG_SIGNATURE):
        raise ValueError("Invalid PNG format: signature mismatch")

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    path.write_bytes(content)

    logger.info("screenshot_saved", path=str(path), size=len(content))
    return True


def verify_screenshot_exists(path: Path) -> tuple[bool, str]:
    """Verify screenshot file exists and is valid.

    Args:
        path: Path to screenshot file.

    Returns:
        Tuple of (valid, error_message).
    """
    if not path.exists():
        return False, f"File does not exist: {path}"

    if path.stat().st_size == 0:
        return False, f"File is empty: {path}"

    # Read first 8 bytes to verify PNG signature
    with open(path, "rb") as f:
        header = f.read(8)

    if header != PNG_SIGNATURE:
        return False, f"Invalid PNG signature: {path}"

    return True, ""


def verify_screenshot_content(path: Path) -> tuple[bool, str]:
    """Verify screenshot has actual content (not all black/white).

    Uses basic pixel sampling to detect uniform images.

    Args:
        path: Path to screenshot file.

    Returns:
        Tuple of (valid, error_message).
    """
    # First verify file exists and is valid PNG
    valid, error = verify_screenshot_exists(path)
    if not valid:
        return False, error

    try:
        # Read PNG file and check for content
        # Use simple byte analysis instead of PIL to avoid dependency
        content = path.read_bytes()

        # Skip PNG header and check for data variation
        # A truly uniform image will have very repetitive data
        data_section = content[100 : min(1000, len(content))]

        if len(data_section) < 100:
            return False, "Screenshot too small to verify"

        # Count unique bytes in sample
        unique_bytes = len(set(data_section))

        # Very uniform images have few unique byte values
        if unique_bytes < 5:
            return False, "Screenshot appears to be uniform (all black/white)"

        return True, ""

    except Exception as e:
        logger.error("screenshot_verification_failed", path=str(path), error=str(e))
        raise


def get_screenshot_mtime(path: Path) -> float:
    """Get screenshot file modification time.

    Args:
        path: Path to screenshot file.

    Returns:
        Modification time as timestamp.

    Raises:
        FileNotFoundError: If file doesn't exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Screenshot not found: {path}")

    return path.stat().st_mtime
