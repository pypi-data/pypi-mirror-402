# Technical Debt Registry

**Project:** [Project Name]
**Last Updated:** YYYY-MM-DD
**Last Modified By:** [git user email]
**Owner:** [Team/Person]

---

## ⛔ CRITICAL GUARDRAIL

> **DO NOT FIX DEBT DURING FEATURE WORK**
>
> Debt items in this registry are **logged only**. Fixing debt requires:
> 1. Explicit approval from PM/Tech Lead
> 2. A separate story (e.g., `DEBT-015`) with its own estimate
> 3. Dedicated sprint allocation
>
> **If you encounter debt during feature work:**
> - ✅ Log it here with status `Open`
> - ✅ Continue with your assigned feature
> - ❌ DO NOT attempt to fix it in the same PR
>
> **Violation = 🛑 HALT + Escalation to User**

---

## Summary

| Severity | Count | Oldest |
|----------|-------|--------|
| 🔴 Critical | 0 | - |
| 🟠 High | 0 | - |
| 🟡 Medium | 0 | - |
| 🟢 Low | 0 | - |

---

## Debt Items

| ID | Location | Type | Severity | Linked Story | Status | Logged By | Date | Last Modified By |
|----|----------|------|----------|--------------|--------|-----------|------|------------------|
| DEBT-001 | `src/example.py:45` | No type hints | 🟡 Medium | STORY-042 | Open | [email] | 2024-12-22 | [email] |

---

## Debt Types

| Type | Description | Detection |
|------|-------------|-----------|
| `no-types` | Missing type hints on functions | Manual / Scanner |
| `bare-except` | Generic exception handling | Scanner |
| `no-tests` | Module lacks test coverage | Scanner |
| `no-docs` | Missing docstrings | Scanner |
| `complexity` | Cognitive complexity > 15 | Scanner |
| `duplication` | Repeated code blocks | Manual |
| `deprecated` | Using deprecated APIs | Scanner |
| `todo-fixme` | Unresolved TODO/FIXME comments | Scanner |
| `hardcoded` | Hardcoded values that should be config | Manual |
| `legacy-pattern` | Outdated architectural patterns | Manual |

---

## Severity Definitions

| Severity | Criteria | SLA |
|----------|----------|-----|
| 🔴 **Critical** | Security risk, data loss, blocks deployment | Fix before merge |
| 🟠 **High** | Performance impact, maintainability blocker, violates DRY | Fix within current sprint |
| 🟡 **Medium** | Code smell, testability concern, industry best practice violation | Fix within 2 sprints |
| 🟢 **Low** | Style preference, minor optimization | Fix when touching file |

> **Note:** All severity levels represent production concerns. "Low" does not mean "acceptable" - it means lower priority, not ignorable.

---

## Status Values

| Status | Meaning | Can Fix? |
|--------|---------|----------|
| `Open` | Identified, not yet addressed | ❌ No (needs approval) |
| `Approved` | PM/Tech Lead approved for fixing | ✅ Yes (with dedicated story) |
| `In Progress` | Actively being fixed in dedicated story | ✅ Yes |
| `Blocked` | Cannot fix due to dependency | ❌ No |
| `Resolved` | Fixed, awaiting verification | - |
| `Closed` | Verified fixed | - |
| `Wont Fix` | Accepted as-is with justification | ❌ No |

### Status Transition Rules

```
Open ──► Approved ──► In Progress ──► Resolved ──► Closed
  │                        │
  │                        └──► Blocked ──► (back to Approved when unblocked)
  │
  └──► Wont Fix (requires justification)
```

**⚠️ IMPORTANT:** Only `Approved` or `In Progress` items may be worked on.

---

## Logging Protocol

### When to Log (by Agent)

| Agent | When | Action |
|------|------|--------|
| **Discovery** | Phase 1: Initial scan | Log all detected debt |
| **Developer** | Phase 4: Implementation | Log debt encountered but out of scope |
| **PR Reviewer** | Phase 5: Review | Log debt found OR reject PR |

### How to Log

1. Assign next `DEBT-XXX` ID
2. Record exact location (`file:line`)
3. Classify type from table above
4. Assess severity
5. Link to current story if applicable
6. Set status to `Open`

---

## Archived Items

*Move resolved items here for historical reference*

| ID | Location | Type | Resolution | Resolved By | Date |
|----|----------|------|------------|-------------|------|
