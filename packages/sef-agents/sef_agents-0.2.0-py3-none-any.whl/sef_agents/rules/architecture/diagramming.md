# Architecture Diagramming Standards

## Purpose
Visualize system structure and data flow using Mermaid diagrams that are version-controllable.

## Standard: Mermaid.js (Single Source)

### IDE Setup (One-time)
| IDE | Setup |
|-----|-------|
| VS Code | Install "Markdown Preview Mermaid Support" extension |
| JetBrains | Settings → Plugins → Search "Mermaid" → Install |
| GitHub/GitLab | Auto-renders (no setup) |

### React Dashboard
Use `react-markdown` + `mermaid` library for rendering.

---

## Templates: USE ONLY PRE-VALIDATED

**Reference:** `mermaid_templates.md`

| Template | Use For | Diagram Type |
|----------|---------|--------------|
| Template 1 | System overview | `flowchart TB` |
| Template 2 | Module dependencies | `flowchart LR` |
| Template 3 | Request lifecycle | `sequenceDiagram` |
| Template 4 | Class relationships | `classDiagram` |
| Template 5 | Data pipelines | `flowchart LR` |
| Template 6 | External integrations | `flowchart TB` |

**Do NOT freestyle Mermaid.** Fill placeholders in templates only.

---

## Syntax Rules (MANDATORY)

### Node IDs
✅ `UserSvc`, `DB1`, `API` (alphanumeric)
❌ `user-svc`, `user_svc`, `user svc`

### Labels with Special Characters
✅ `A["Label (parens)"]` (quoted)
❌ `A[Label (breaks)]`

### Arrows
| Diagram | Solid | Dashed | Labeled |
|---------|-------|--------|---------|
| Flowchart | `-->` | `-.->` | `-->\|text\|` |
| Sequence | `->>` | `-->>` | `->>` + `: text` |
| Class | `-->` | `..>` | N/A |

### Size Limits
- Max 10 nodes per diagram
- Max 15 edges per diagram
- Split larger diagrams

---

## Validation Checklist

Before ANY Mermaid diagram:

- [ ] Template from `mermaid_templates.md`
- [ ] Node IDs alphanumeric only
- [ ] Special char labels quoted
- [ ] Correct arrow syntax
- [ ] ≤ 10 nodes, ≤ 15 edges

**If ANY fails → use TABLE instead.**

---

## Fallback: Tables

When uncertain, tables have zero syntax risk:

```markdown
| Component | Depends On | Relationship |
|-----------|------------|--------------|
| API | Service | Calls |
| Service | Database | Queries |
```

---

## Required Diagrams by Artifact

| Artifact | Required Diagrams |
|----------|-------------------|
| CODE_MAP.md | System Context, Module Dependencies |
| ARCHITECTURE.md | Request Flow, Component Overview |
| EXTERNAL_DEPS.md | Integration Map |

---

## Rules
- Keep diagrams simple (max 10 nodes)
- Use subgraphs for grouping
- Update diagrams in same commit as code changes
- Validate syntax before committing
