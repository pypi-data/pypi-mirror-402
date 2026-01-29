# Documentation Standards (Curator Protocol)

## 1. Principles
- **Code Speaks**: Explain *why*, not *what*.
- **Bus Factor**: Write for the 3 AM debugger.
- **Token Economy**: Omit articles (a/an/the). Fragments OK. **Applies to inline comments only, not docstrings.**

## 2. Comments (Inline)
- **Token Economy**: Omit articles (a/an/the). Fragments OK.
- REQUIRED: Hidden truths (TODO, FIXME, HACK, NOTE, PERF).
- FORBIDDEN: Code-echoing (`i++ # increment i`).

## 3. Docstrings (Strict)
### Rules
- Summary: 1-line what/why.
- Args/Returns/Raises: Mandatory for all non-trivial funcs.
- Side Effects: Mandatory if I/O or global state change.

### Formatting
- Python: Google style (full sentences with articles, imperative mood).
- TS/JS: JSDoc.
- Java: Javadoc.

### Token Economy Scope
- **Token economy does NOT apply to docstrings.**
- Docstrings must follow industry-standard format (Google style) with full sentences and articles for tooling compatibility.
- Token economy applies only to inline comments for brevity.

### AI-Generated Docstring Guidelines (MANDATORY FOR 98% AI-GENERATED CODEBASE)
**CRITICAL: Since 98% of code/documentation is AI-generated, these rules are ENFORCED at generation time.**

**FORBIDDEN Patterns (Token Waste - Auto-flagged by `validate_compliance`):**
- ❌ "This function is designed to..." → ✅ "Processes..."
- ❌ "It is important to note that..." → ✅ Omit
- ❌ "Please note that..." → ✅ Omit
- ❌ "In order to..." → ✅ "To..."
- ❌ "It should be noted that..." → ✅ Omit
- ❌ "As you can see..." → ✅ Omit
- ❌ "The purpose of this function is to..." → ✅ Omit
- ❌ "This function is responsible for..." → ✅ Omit
- ❌ Excessive adjectives: "extremely", "very", "highly", "significantly"
- ❌ Hedging: "might", "could", "possibly", "potentially", "probably"
- ❌ Redundant phrases: "in other words", "that is to say"

**REQUIRED:**
- Direct, imperative statements (Google style)
- One-line summary (≤80 chars)
- Args/Returns/Raises: One sentence per item
- No redundant phrases or meta-commentary
- Full sentences with articles (Google style compliance)

**Enforcement:**
- `validate_compliance` tool automatically flags violations
- PR review blocks fluff violations
- Developer agent prompt includes these rules

**Example:**
```python
# ❌ Bad (AI fluff - will be flagged)
"""This function is designed to process user data.
It is important to note that this function might potentially
return None in some cases. Please note that the function
is extremely efficient and highly optimized."""

# ✅ Good (Concise, Google style, passes validation)
"""Process user data.

Args:
    user_id: Unique identifier for the user.

Returns:
    Processed user data or None if user not found.
"""
```

## 4. Module Headers
- Purpose: 1 sentence.
- Usage: ≤3 lines copy-pasteable example.
- Dependencies: Env vars, services, DB.

## 5. Signal-to-Noise Score
- A (>80%): Exemplary.
- D (<40%): Debt. Block PR.

## 6. Enforcement
- Discovery: CODE_MAP, TECH_DEBT.
- Architect: ADRs.
- Developer: Code/Docstrings.
- Reviewer: Block for documentation debt.

## 7. Project Documentation (On-Demand Reference)

**When user explicitly requests help with project-level documentation**, use these industry standards:

### README.md

**Required Sections (in order):**
1. **Title** - Project name as H1
2. **Badges** - Build status, language version, license (if applicable)
3. **Tagline** - One-line value proposition (bold)
4. **Description** - 2-3 sentences explaining what the project does
5. **Table of Contents** - Required if README exceeds 200 lines
6. **What This Does** - Clear explanation of purpose and target audience
7. **Features** - Organized by category (tables preferred for clarity)
8. **Security** - If applicable, security guarantees/audit info
9. **Installation** - Prerequisites and setup steps
10. **Configuration** - How to configure/connect (with examples)
11. **Local Development** - For contributors (if open to contributions)
12. **Quick Start** - Step-by-step getting started guide
13. **Contributing** - Link to CONTRIBUTING.md (do not duplicate content)
14. **About** - Context, framework, standards used
15. **License** - License type

**Formatting Guidelines:**
- Use tables for features/tools lists (improves scanability)
- Code blocks for all commands/examples
- Horizontal rules (`---`) to separate major sections
- Keep language clear and concise (industry standard, not Curator Protocol)
- Include troubleshooting table if common issues exist
- **Version History**: Link to release notes/changelog (adapt to environment):
  - GitHub: Link to Releases page
  - GitLab: Link to Releases or tags
  - Internal/Enterprise: Link to version docs, JIRA releases, or omit if not applicable
  - Do NOT create CHANGELOG.md (use platform-native release tracking)

**Badges:**
- Build/CI status (if CI configured)
- Language version (e.g., Python 3.13+)
- License (if open source)
- Keep badges minimal (2-3 max recommended)

### CONTRIBUTING.md
- **Sections**: Development setup, code standards, PR process, testing requirements
- **PR Template**: Include checklist (type of change, testing, compliance)
- **Code Standards**: Reference Curator Protocol for code docs

### ADR (Architecture Decision Record)
- **Template**: Use `docs/templates/ADR.md` if available, or:
  - Status: Proposed | Accepted | Deprecated
  - Context: Why decision needed
  - Decision: What was chosen
  - Consequences: Trade-offs, risks, mitigations
- **Format**: Curator-style (context-focused, minimal fluff)
- **Location**: `docs/adr/ADR-XXX.md` or `docs/ADR-XXX.md`

**Note**: These are reference standards for when explicitly requested. Not enforced automatically.
