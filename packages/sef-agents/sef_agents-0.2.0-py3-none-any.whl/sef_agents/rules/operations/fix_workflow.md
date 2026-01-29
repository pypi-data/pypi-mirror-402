# Default Fix Workflow Protocol

## MANDATORY FLOW FOR FIXES (NON-NEGOTIABLE)

**When user asks to fix something, follow this exact sequence:**

### Flow 1: Unknown Root Cause (Default)
1. **Forensic Engineer** verifies the claim
   - Performs RCA (Root Cause Analysis)
   - Identifies root cause
   - Documents current implementation
2. **Strategist** recommends solution
   - Reviews forensic findings
   - Recommends production-grade, industry best practice solution
   - Provides trade-off analysis
3. **Present to User**:
   - Current implementation summary
   - Root cause analysis
   - Strategist's recommendation
   - **WAIT for user approval** before proceeding
4. **Developer** implements (after approval)
   - Implements approved solution
   - Follows implementation protocol

### Flow 2: Known Root Cause (Direct Fix)
**If root cause is already known and verified:**
- **Developer** can pick up task directly
- Still requires: Current implementation summary + proposed fix
- **WAIT for user approval** before implementing

## Rules

### Before Any Fix
1. **MANDATORY**: Perform RCA (Root Cause Analysis)
2. **MANDATORY**: Document current implementation
3. **MANDATORY**: Get strategist recommendation (unless root cause is trivial)
4. **MANDATORY**: Present findings to user
5. **MANDATORY**: Wait for user approval before implementing

### Agent Responsibilities

**Forensic Engineer:**
- Verify the claim/problem
- Identify root cause (5 Whys)
- Document current implementation state
- Hand off to Strategist with findings

**Strategist:**
- Review forensic findings
- Recommend production-grade solution
- Provide industry best practice approach
- Present trade-off analysis
- Hand off to Developer with recommendation

**Developer:**
- Review forensic findings and strategist recommendation
- Present summary to user (current state + recommendation)
- Wait for approval
- Implement approved solution
- **Write regression test for fix** (see `development/implementation.md` Section 2.1)
- Execute tests: `pytest --cov-fail-under=85`
- Mark artifacts: `tests_written`, `tests_verified`

## Output Format (Before Implementation)

```markdown
## Root Cause Analysis
**Problem**: [User's reported issue]
**Root Cause**: [Identified root cause]
**Current Implementation**: [Summary of current code/approach]

## Recommended Solution
**Strategy**: [Strategist's recommendation]
**Rationale**: [Why this is the best approach]
**Trade-offs**: [Key considerations]

## Approval Required
Please review and approve before implementation proceeds.
```

## Forbidden Actions

❌ **DO NOT** implement fixes without RCA
❌ **DO NOT** skip strategist recommendation for non-trivial fixes
❌ **DO NOT** implement without user approval
❌ **DO NOT** assume root cause without verification
