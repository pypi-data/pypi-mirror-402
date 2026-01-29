#!/usr/bin/env python3
"""Validate Python version matches project requirements.

Pre-build check to ensure Python version compatibility.
Exits with code 1 if version mismatch detected.
"""

import sys
from pathlib import Path
from packaging.requirements import Requirement
from packaging.version import InvalidVersion


def get_required_python_version() -> str:
    """Extract required Python version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"❌ pyproject.toml not found at {pyproject_path}", file=sys.stderr)
        sys.exit(1)

    content = pyproject_path.read_text(encoding="utf-8")
    for line in content.split("\n"):
        if line.strip().startswith("requires-python"):
            # Extract version specifier: ">=3.13" or ">=3.13,<3.14"
            version_spec = line.split("=", 1)[1].strip().strip('"').strip("'")
            return version_spec

    print("❌ requires-python not found in pyproject.toml", file=sys.stderr)
    sys.exit(1)


def get_current_python_version() -> tuple[int, int, int]:
    """Get current Python version as tuple."""
    return sys.version_info[:3]


def check_version_compatibility(
    required_spec: str, current_version: tuple[int, int, int]
) -> bool:
    """Check if current Python version satisfies requirement."""
    try:
        # Parse requirement specifier (e.g., ">=3.13")
        req = Requirement(f"python{required_spec}")
        current_str = f"{current_version[0]}.{current_version[1]}.{current_version[2]}"

        # Check if current version satisfies requirement
        return req.specifier.contains(current_str, prereleases=True)
    except (InvalidVersion, ValueError) as e:
        print(f"❌ Error parsing version: {e}", file=sys.stderr)
        return False


def main() -> None:
    """Main validation logic."""
    required_spec = get_required_python_version()
    current_version = get_current_python_version()
    current_str = f"{current_version[0]}.{current_version[1]}.{current_version[2]}"

    print("🔍 Checking Python version compatibility...")
    print(f"   Required: Python {required_spec}")
    print(f"   Current:  Python {current_str}")

    if check_version_compatibility(required_spec, current_version):
        print(f"✅ Python version {current_str} satisfies requirement {required_spec}")
        sys.exit(0)
    else:
        print(
            f"❌ Python version {current_str} does NOT satisfy requirement {required_spec}",
            file=sys.stderr,
        )
        print(
            f"   Please use Python version that matches: {required_spec}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
