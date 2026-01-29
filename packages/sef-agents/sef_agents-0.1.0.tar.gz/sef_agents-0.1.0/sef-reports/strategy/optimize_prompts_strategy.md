# Strategy Decision Matrix: OPTIMIZE-PROMPTS-001

**Date:** 2025-12-30
**Author:** Distinguished Solution Strategist
**Status:** Draft

## Problem Statement
**Core Problem**: SEF Agent prompts (e.g., `pr_reviewer` at 11k+ tokens) are bloated, redundant, and hard to read.
**Impact**: "Lost in the Middle" bias causes agents to ignore buried instructions; high latency/cost; fragmented logic.
**Constraints**: Maintain functional parity; adhere to SEF Laconic standard.
**Success Metric**: `pr_reviewer` < 5k tokens; 0 duplicated instructions; Grade 8-10 readability.

## Options Evaluated

### Option A: Contextual Modularization
**Description**: Dynamically load rule files based on task context (e.g., only load `frontend_patterns.md` if `.js/tsx` files are modified).
**Pros**:
- Drastic token reduction for specific tasks.
- Higher focus for the LLM.
**Cons**:
- Requires metadata/file-extension logic in prompt generators.
**Effort**: Medium
**Risk**: Low
**Time to Value**: 1 week

### Option B: Hyper-Compression (Curator Protocol)
**Description**: Refactor all `.md` rules into atomic, laconic fragments. Remove all "You are a..." boilerplate and meta-instructions from rule files.
**Pros**:
- Universal reduction in prompt size.
- Improved readability/signal-to-noise.
**Cons**:
- Time-consuming manual refactor.
**Effort**: Medium
**Risk**: Low
**Time to Value**: 1 week

### Option C: Decomposed Agent Graph
**Description**: Split large agents into specialized sub-agents (Frontend/Backend/Security) coordinated by a Scrum Master.
**Pros**:
- Maximum isolation and focus.
**Cons**:
- Increases system complexity and execution time.
**Effort**: High
**Risk**: Medium
**Time to Value**: 3 weeks

## Trade-off Analysis

| Criteria | Weight | Opt A | Opt B | Opt C |
|----------|--------|-------|-------|-------|
| Token Efficiency | 30% | 9 | 7 | 8 |
| Implementation Speed | 20% | 8 | 7 | 4 |
| Maintainability | 20% | 7 | 9 | 5 |
| Reliability | 20% | 8 | 9 | 6 |
| Cost | 10% | 9 | 8 | 5 |
| **Total** | 100% | **8.2** | **8.0** | **5.9** |

## Recommendation

**Best Bet**: **Hybrid of Option A & B**.

**Rationale**: Immediate gains from Option B (fixing the 11k token `pr_reviewer` duplication) followed by Option A's dynamic loading will ensure long-term scalability without the architectural overhead of Option C.

**Next Steps**:
1. **Deduplicate**: Fix the accidental repetition in `frontend_patterns.md`.
2. **Compress**: Rewrite `core_protocol.md` and `patterns` files using Fragment-only style.
3. **Modularize**: Update `start_agent.py` to accept dynamic rule filters.

## Appendix
- Duplication found in `frontend_patterns.md` (lines 173+ repeat line 5+).
- `backend_patterns.md` follows an "Instruction Manual" style rather than "Rule Fragment" style.
