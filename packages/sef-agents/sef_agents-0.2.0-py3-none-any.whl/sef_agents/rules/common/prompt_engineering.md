# Prompt Engineering Protocol (Curator)

## Purpose
Agents creating AI/LLM prompts during application builds MUST follow this structural approach with self-contained quality rules.

## Mandatory Format: Structural

Prompts MUST use structured formats (XML, YAML, or strict Markdown sections). Natural language prose is FORBIDDEN.

### Approved Formats

**Option 1: XML (Recommended for Complex Prompts)**
```xml
<role>Senior Backend Engineer</role>

<task>
  <primary>Implement user authentication</primary>
  <constraints>
    - Use bcrypt for hashing
    - Session timeout: 30 minutes
    - Max login attempts: 3
  </constraints>
</task>

<context>
  <codebase>FastAPI application</codebase>
  <dependencies>SQLAlchemy, Redis</dependencies>
</context>

<output_format>
  <code_style>PEP 8</code_style>
  <test_coverage>≥85%</test_coverage>
  <deliverables>
    1. auth.py implementation
    2. Unit tests
    3. Migration script
  </deliverables>
</output_format>
```

**Option 2: YAML (Recommended for Configuration)**
```yaml
role: Senior Backend Engineer

task:
  primary: Implement user authentication
  constraints:
    - Use bcrypt for hashing
    - Session timeout: 30 minutes
    - Max login attempts: 3

context:
  codebase: FastAPI application
  dependencies:
    - SQLAlchemy
    - Redis

output_format:
  code_style: PEP 8
  test_coverage: "≥85%"
  deliverables:
    - auth.py implementation
    - Unit tests
    - Migration script
```

**Option 3: Strict Markdown Sections**
```markdown
# Role
Senior Backend Engineer

# Task
## Primary
Implement user authentication

## Constraints
- Use bcrypt for hashing
- Session timeout: 30 minutes
- Max login attempts: 3

# Context
- Codebase: FastAPI application
- Dependencies: SQLAlchemy, Redis

# Output Format
- Code Style: PEP 8
- Test Coverage: ≥85%
- Deliverables:
  1. auth.py implementation
  2. Unit tests
  3. Migration script
```

---

## Quality Rules (Self-Contained, No Runtime Tools Required)

### 1. Position Rules (Primacy/Recency)

**Objective**: Critical instructions at start/end, context in middle.

**Rules**:
- **Top 20%**: Role definition + primary task directive
- **Middle 60%**: Context, examples, background, edge cases
- **Bottom 20%**: Output format, validation checklist, deliverables

**Structural Enforcement**:
- XML/YAML: Structure inherently enforces position
- Markdown: Use `# Role`, `# Task` (top), `# Output Format` (bottom)

**Self-Check**:
- [ ] Primary directive in first section?
- [ ] Context/examples NOT in first section?
- [ ] Output requirements in last section?

---

### 2. Readability Rules

**Objective**: Simple, scannable, grade level ≤ 8.

**Rules**:
- **Sentence length**: ≤ 15 words (avg)
- **Active voice only**: "Service scales" NOT "Scaling is handled by"
- **Simple vocabulary**: Avoid jargon without definition
- **No nested clauses**: Break into multiple sentences

**Forbidden Patterns**:
- ❌ "The system, which was designed to handle high traffic, should be implemented using..."
- ✅ "Implement the system. It must handle high traffic."

**Self-Check**:
- [ ] Sentences ≤ 15 words?
- [ ] Active voice throughout?
- [ ] Jargon defined or avoided?

---

### 3. Efficiency Rules (Token Budget)

**Objective**: 70%+ actionable words, zero filler.

**Eliminate Filler**:
- ❌ "please", "try to", "you should", "it would be nice if"
- ✅ Use imperatives: "Generate", "Implement", "Validate"

**Before/After**:
- ❌ "You should try to implement authentication using bcrypt if possible."
- ✅ "Implement authentication. Use bcrypt for hashing."

**Self-Check**:
- [ ] No hedging words? (try, should, could, might, probably)
- [ ] Imperatives used? (Generate, Validate, Ensure)
- [ ] Every word adds value?

---

### 4. Ambiguity Rules

**Objective**: Zero vague terms. Quantify everything.

**Forbidden Vague Terms**:
- ❌ "some", "stuff", "things", "appropriate", "reasonable", "fast", "scalable", "user-friendly"

**Quantify**:
- ❌ "The API should be fast."
- ✅ "API response time: < 200ms (p95)."

- ❌ "Handle a reasonable number of users."
- ✅ "Support 10,000 concurrent users."

**Self-Check**:
- [ ] No vague terms? (some, stuff, appropriate, reasonable)
- [ ] Performance metrics quantified? (ms, RPS, MB)
- [ ] Scope defined? (exact counts, limits, thresholds)

---

### 5. Negation Rules

**Objective**: Prefer positive constraints. If negation needed, provide alternative.

**Pattern**:
- ❌ "Do not use global variables."
- ✅ "Use dependency injection for state management."

- ❌ "Avoid blocking I/O."
- ✅ "Use async/await for I/O operations."

**If Negation Required**:
- ✅ "Do not use MD5 for hashing. Use bcrypt or Argon2."

**Self-Check**:
- [ ] Positive constraints preferred?
- [ ] Negations paired with alternatives?
- [ ] "Do not X" replaced with "Use Y"?

---

### 6. Redundancy Rules

**Objective**: One instruction per concept. No repetition.

**Rules**:
- **Single source of truth**: Define once, reference elsewhere
- **No paraphrasing**: Don't restate in different words
- **Use references**: "See Context section" NOT re-explaining

**Before/After**:
- ❌
  ```
  Use bcrypt for password hashing.
  ...
  Passwords must be hashed with bcrypt.
  ```
- ✅
  ```
  Use bcrypt for password hashing.
  ...
  Verify password hashing (see Constraints).
  ```

**Self-Check**:
- [ ] Each concept stated once?
- [ ] No paraphrasing?
- [ ] References used for repetition?

---

### 7. Contradiction Rules

**Objective**: Zero conflicting directives.

**Rules**:
- **Review for conflicts** before finalizing
- **Explicit precedence**: If conflict possible, state priority
- **Mutual exclusivity**: Flag incompatible requirements

**Pattern**:
- ❌
  ```
  Use synchronous database calls.
  ...
  Ensure non-blocking I/O.
  ```
- ✅
  ```
  Use async database calls (asyncpg) for non-blocking I/O.
  ```

**If Precedence Needed**:
- ✅ "Prefer performance over readability. If conflict, optimize for < 100ms response time."

**Self-Check**:
- [ ] No conflicting constraints?
- [ ] Precedence rules stated if needed?
- [ ] Mutual exclusivity resolved?

---

## Validation Checklist (Agents MUST Complete)

Before finalizing any prompt:

- [ ] **Format**: Structural (XML/YAML/Markdown sections)?
- [ ] **Position**: Critical instructions at top/bottom?
- [ ] **Readability**: Sentences ≤ 15 words, active voice?
- [ ] **Efficiency**: No filler words (try, should, please)?
- [ ] **Ambiguity**: Vague terms eliminated, metrics quantified?
- [ ] **Negation**: Positive constraints preferred, alternatives provided?
- [ ] **Redundancy**: Each concept stated once?
- [ ] **Contradiction**: No conflicting directives?

---

## Agent Responsibilities

| Agent | Prompt Creation Scenario | Protocol Application |
|:------|:------------------------|:---------------------|
| **Product Manager** | Defining AI feature requirements | Use YAML for structured AC |
| **Architect** | Designing AI system prompts | Use XML for complex multi-section prompts |
| **Developer** | Implementing prompt templates in code | Use Markdown for inline documentation |

---

## Escalation

| Issue | Action |
|:------|:-------|
| Prompt exceeds 2000 tokens | L1 → Architect (redesign for conciseness) |
| Ambiguity unavoidable | L2 → Product Manager (clarify requirements) |
| Conflicting constraints | L3 → HALT (user decision required) |
