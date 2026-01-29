#!/bin/bash
# demo_security_scan.sh - Run this in front of enterprise customers
#
# This script demonstrates the SEF Agents security audit capabilities.
# It shows that SEF Agents contains no network calls, secrets, or vulnerabilities.

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "          SEF-AGENTS SECURITY AUDIT DEMONSTRATION"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "📁 Step 1: Show codebase size (small, auditable)"
echo "─────────────────────────────────────────────────"
find src -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 || echo "Counting lines..."
echo ""

echo "🔍 Step 2: Run security scan"
echo "─────────────────────────────────────────────────"
uv run python -m sef_agents.security_scan
echo ""

echo "📄 Step 3: View the report"
echo "─────────────────────────────────────────────────"
REPORT=$(ls -t sef-reports/security/security_audit_*.md 2>/dev/null | head -1)
if [ -n "$REPORT" ]; then
    head -80 "$REPORT"
    echo ""
    echo "... (truncated - full report at $REPORT)"
else
    echo "No report found. Run the security scan first."
fi
echo ""

echo "🔬 Step 4: Manual verification (optional)"
echo "─────────────────────────────────────────────────"
echo "You can verify the results yourself:"
echo ""
echo "  # Check for network imports:"
echo '  grep -r "import requests\|import httpx\|import urllib" src/'
echo ""
echo "  # Check for hardcoded secrets:"
echo '  grep -r "api_key\|password\|secret" src/ --include="*.py"'
echo ""

echo "✅ Demo complete!"
echo "   Full report saved to: sef-reports/security/"
