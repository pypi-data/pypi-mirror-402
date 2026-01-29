import pytest
from pathlib import Path
import sys

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from sef_agents.prompts import start_agent


def test_structural_prompt_anchors():
    """Verify XML-like anchors are present in STRUCTURAL mode."""
    start_agent.PROMPT_STRATEGY = "STRUCTURAL"
    prompt = start_agent.get_developer_prompt()

    assert "<IDENTITY>" in prompt
    assert "</IDENTITY>" in prompt
    assert "<CONTEXT>" in prompt
    assert "<ACTIVE_RULES>" in prompt
    assert "<CRITICAL_CONSTRAINTS>" in prompt
    assert "</CRITICAL_CONSTRAINTS>" in prompt


def test_structural_prioritization():
    """Verify critical constraints are at the end in STRUCTURAL mode."""
    start_agent.PROMPT_STRATEGY = "STRUCTURAL"
    prompt = start_agent.get_developer_prompt()

    critical_idx = prompt.find("<CRITICAL_CONSTRAINTS>")
    rules_idx = prompt.find("<ACTIVE_RULES>")

    assert critical_idx > rules_idx, (
        "Critical constraints must follow active rules for recency bias."
    )


def test_legacy_fallback():
    """Verify legacy prompt structure is preserved."""
    start_agent.PROMPT_STRATEGY = "LEGACY"
    prompt = start_agent.get_developer_prompt()

    assert "# IDENTITY:" in prompt
    assert "# SYSTEM PROTOCOL (NON-NEGOTIABLE)" in prompt
    assert "<IDENTITY>" not in prompt


def test_domain_sharpening_python():
    """Verify TS rules are filtered out when in a Python environment."""
    start_agent.PROMPT_STRATEGY = "STRUCTURAL"

    # Mock _detect_tech_stack to simulate Python environment
    original_detect = start_agent._detect_tech_stack
    start_agent._detect_tech_stack = lambda: ["frontend"]

    try:
        # Load developer prompt which includes both patterns
        start_agent.get_developer_prompt()
        # In developer prompt, architecture/frontend_patterns.md would be excluded if it was there
        # But core_protocol.md is always there.
        # Note: wrap_prompt_structural filters lines based on RelPath in rules_content
        # Let's check if a rule with 'frontend' in name is missing if we explicitly add it
        rules = start_agent.load_rules(
            ["architecture/frontend_patterns.md", "architecture/backend_patterns.md"]
        )
        filtered_rules = start_agent.wrap_prompt_structural("Test", "Mission", rules)

        assert "RULE: architecture/backend_patterns.md" in filtered_rules
        assert "RULE: architecture/frontend_patterns.md" not in filtered_rules
    finally:
        start_agent._detect_tech_stack = original_detect


if __name__ == "__main__":
    pytest.main([__file__])
