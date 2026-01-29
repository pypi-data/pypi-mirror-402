# Regression Risk Protocol (Architect)

## MANDATORY: Regression Analysis
Before approving any design, you MUST assess regression risk.

## Risk Identification Checklist
- [ ] Does change touch shared utilities?
- [ ] Does change modify database schema?
- [ ] Does change affect API contracts?
- [ ] Does change alter authentication/authorization?
- [ ] Does change impact >3 modules?
- [ ] Does change modify core business logic?

## Risk Classification
| Risk Level | Criteria | Action |
|:---|:---|:---|
| **LOW** | Isolated change, <3 files, no shared deps | ✅ Proceed |
| **MEDIUM** | Touches shared module, requires test updates | ⚠️ Flag, require test plan |
| **HIGH** | Schema change, API contract, auth, core logic | 🛑 Escalate |

## High-Risk Indicators
- Database migrations (schema changes)
- Breaking API changes
- Authentication/authorization modifications
- Shared library changes
- Configuration changes affecting multiple services
- Changes to critical business logic

## Escalation Protocol
| Condition | Level | Action |
|:---|:---|:---|
| Low risk | - | ✅ Proceed with design |
| Medium risk identified | L1 | Notify PM, document in design, require test plan |
| High risk, scope unclear | L2 | PM + Architect session to clarify scope |
| High risk, user approval needed | L3 | 🛑 HALT → User must approve before proceeding |

## Mitigation Requirements
For MEDIUM/HIGH risk changes:
- [ ] Rollback plan documented
- [ ] Feature flag available (if applicable)
- [ ] Integration tests cover affected paths
- [ ] Monitoring/alerting in place
- [ ] Stakeholders notified

## Output Format
```markdown
## Regression Analysis

### Risk Assessment
| Area | Impact | Risk | Mitigation |
|:---|:---|:---|:---|
| Database | Schema migration | HIGH | Rollback script required |
| API | New endpoint only | LOW | - |
| Auth | No change | - | - |
| Shared Utils | Modified helper | MEDIUM | Update dependent tests |

### Affected Modules
- `src/core/utils.py` → used by 5 modules
- `src/api/v1/routes.py` → public API

### Test Coverage Required
- [ ] Unit tests for changed functions
- [ ] Integration tests for affected paths
- [ ] E2E test for critical flow

### Verdict
- ✅ **LOW RISK**: Proceed with implementation
- ⚠️ **MEDIUM RISK**: Proceed with test plan attached
- 🛑 **HIGH RISK**: HALT - User approval required

[Reasoning for verdict]
```

## Status Indicators
- ✅ Low risk, proceed
- ⚠️ Medium risk, proceed with caution
- 🛑 High risk, HALT for approval
