# Synchronous Engineering Flow

## Core Principle
**Eliminate Handoffs.** The goal is single-phase delivery where development, testing, and documentation happen in parallel, facilitated by AI augmentation.

## The Process

### Traditional vs. SEF
-   ❌ **Traditional**: Dev writes code -> Handoff to QA -> QA finds bugs -> Handoff to Dev -> Fix...
-   ✅ **SEF**: Dev + AI write Code + Tests + Docs simultaneously. QA validated the AC upfront.

### Definition of Done (SEF)
A task is NOT done when "code is written". It is done when:
1.  [ ] Code implements the QA-approved AC.
2.  [ ] AI-generated structural tests pass.
3.  [ ] `CODE_MAP.md` is updated (structural changes reflected).
4.  [ ] Documentation is current.
5.  [ ] Architecture diagrams are updated.

**There is no "Ready for QA" column.** Verification happens continuously.

## Scrum Master Agent
-   Identify and destroy queues.
-   Ensure `CODE_MAP.md` is treated as a first-class citizen.
-   Block stories that lack QA-approved AC.
