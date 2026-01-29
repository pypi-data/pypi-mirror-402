# QA Validation of Intent (SEF)

## Core Principle
In the Synchronous Engineering Framework (SEF), QA "shifts left" completely. Instead of validating code after it's written, **QA validates the intent (Acceptance Criteria) BEFORE development begins.**

## Workflow
1.  **Requirement Review**:
    -   Product Owner / BA drafts User Story + AC.
    -   QA Lead reviews the AC.

2.  **Validation Checkpoints**:
    -   [ ] Is the AC specific and testable?
    -   [ ] Are negative scenarios/edge cases covered?
    -   [ ] Are performance/security implications conditioned?
    -   [ ] Does it align with existing system behavior (check `CODE_MAP.md`)?

3.  **Approval Gate**:
    -   QA must explicitly "Approve" the AC.
    -   Development DOES NOT START until this approval is granted.

## Instruction for Agents
When acting as **QA / Tester**:
-   If presented with a raw requirement, critique the AC heavily.
-   Demand specific examples.
-   Do not ask for code implementation yet.
