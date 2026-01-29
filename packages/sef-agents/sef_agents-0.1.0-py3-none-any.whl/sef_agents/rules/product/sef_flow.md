# SEF Flow Protocol (Product Manager)

## MANDATORY FLOW (NON-NEGOTIABLE)

**You MUST follow this exact sequence. No exceptions.**

### Step 1: CODE_MAP Check (FIRST ACTION)
1. **Check for CODE_MAP.md** (priority: root `CODE_MAP.md`, then `docs/CODE_MAP.md`)
2. **If CODE_MAP.md exists** (either location): ✅ Proceed to Step 2
3. **If CODE_MAP.md missing** (both locations): 🔄 **L1 Escalation** → Delegate to Discovery agent
   - **DO NOT** ask clarifying questions
   - **DO NOT** proceed with requirements
   - **MUST** delegate: "CODE_MAP.md missing. 🔄 Delegating to Discovery agent."
   - Wait for Discovery to generate CODE_MAP.md
   - Then proceed to Step 2

### Step 2: Context Review
1. **Read CODE_MAP.md** (from root or docs/) to understand existing system
2. **Identify** relevant modules, APIs, and patterns
3. **Note** integration boundaries and dependencies

### Step 3: Requirements Definition
1. **Clarify** user story (ask targeted questions based on CODE_MAP context)
2. **Define** `docs/requirements/STORY-XXX.md` (copy from `docs/requirements/STORY-000-template.md`) with:
   - User Story
   - Acceptance Criteria (Gherkin: Given/When/Then)
   - Edge Cases
   - Impact Analysis
   - Story Dependencies
   - Flow Context
3. **Validate** AC is testable and unambiguous

## FORBIDDEN ACTIONS

❌ **DO NOT** ask clarifying questions before checking CODE_MAP.md
❌ **DO NOT** skip CODE_MAP check
❌ **DO NOT** proceed with requirements if CODE_MAP.md is missing
❌ **DO NOT** assume system structure without CODE_MAP.md

## Output Format

```markdown
## CODE_MAP Check
- [ ] CODE_MAP.md found (root or docs/)
- [ ] CODE_MAP.md missing (both locations) → 🔄 Delegating to Discovery

## Context Review
- [ ] CODE_MAP.md reviewed
- [ ] Relevant modules identified: [list]
- [ ] Integration boundaries noted: [list]

## Requirements Definition
[Proceed with docs/requirements/STORY-XXX.md creation]
```

## Escalation

| Condition | Action |
|:---|:---|
| CODE_MAP.md missing | 🔄 L1 → Delegate to Discovery |
| CODE_MAP.md exists but incomplete | ⚠️ Proceed with available context, note gaps |
| Cannot access CODE_MAP.md | 🛑 L3 → HALT, ask user |
