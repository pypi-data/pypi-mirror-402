# Requirement: [STORY-XXX] [Title]

> ⚠️ **DEPRECATED:** Use `docs/requirements/STORY-XXX.md` (one file per story) for merge safety.
> Copy from `docs/requirements/STORY-000-template.md`

**Status:** Draft | QA Approved | In Development | In Review | Done
**Priority:** P1 | P2 | P3
**Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD
**Last Modified By:** [git user email]

---

## Ownership

| Agent | Owner |
|------|-------|
| **Primary Owner** | [Name] |
| **Secondary Owner(s)** | [Name1, Name2] |
| **Current Assignee** | [Name] |

---

## Dependencies

### Story Dependencies

| Dependency | Story ID | Status | Type |
|------------|----------|--------|------|
| Depends On | STORY-001 | Done | Must complete first |
| Depends On | STORY-002 | In Progress | Provides API |
| Blocks | STORY-005 | Draft | Waiting on this story |

### External Dependencies

| System | Owner | Contract | Notes |
|--------|-------|----------|-------|
| [External System] | [Owner if known] | [Contract path if exists] | [Version/notes] |

---

## Flow Context

| Field | Value |
|-------|-------|
| **Business Process** | [Process Name] |
| **Flow** | [Flow Name, e.g., `checkout_flow`] |
| **Flow Step** | [Step Name, e.g., `payment_validation`] |
| **Upstream Step** | [Previous step in flow] |
| **Downstream Step** | [Next step in flow] |

---

## User Story

**As a** [persona]
**I want** [capability]
**So that** [benefit]

---

## Acceptance Criteria

### AC-1: [Criterion Title]
**Given** [precondition]
**When** [action]
**Then** [expected result]

- [ ] Testable: Yes
- [ ] Automatable: Yes
- [ ] Edge cases identified: Yes

### AC-2: [Criterion Title]
**Given** [precondition]
**When** [action]
**Then** [expected result]

---

## Edge Cases

| # | Scenario | Expected Behavior | AC Reference |
|---|----------|-------------------|--------------|
| 1 | [Edge case description] | [Behavior] | AC-1 |
| 2 | [Edge case description] | [Behavior] | AC-2 |

---

## Impact Analysis

### Code Impact
| File/Module | Change Type | Risk |
|-------------|-------------|------|
| `src/services/payment.py` | Modify | Medium |
| `src/api/checkout.py` | Modify | Low |
| `tests/test_payment.py` | Add | Low |

### Regression Risk
| Area | Risk Level | Mitigation |
|------|------------|------------|
| Payment processing | Medium | Add integration test |
| User session | Low | Existing tests cover |

---

## Technical Notes

*Architect/Developer notes on implementation approach*

---

## QA Sign-off

| Check | Status | Reviewer | Date |
|-------|--------|----------|------|
| AC Testable | ⬜ | | |
| AC Complete | ⬜ | | |
| Edge Cases Covered | ⬜ | | |
| Flow Continuity Verified | ⬜ | | |

**QA Lead Approval:** ⬜ Pending | ✅ Approved | ❌ Rejected

---

## History

| Date | Change | By |
|------|--------|-----|
| YYYY-MM-DD | Created | [Name] |
