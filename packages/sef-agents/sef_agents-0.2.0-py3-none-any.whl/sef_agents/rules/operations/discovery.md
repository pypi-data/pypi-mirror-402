# Discovery Protocol

## 1. Mandatory Sequence

| Step | Action | Output |
|------|--------|--------|
| 1 | **Scan** | Traverse directory, detect project type |
| 2 | **Codemaps** | Generate `codemap/` with per-package maps |
| 3 | **Features** | Infer `FEATURES.md` from codemaps |
| 4 | **Agents** | Generate `AGENTS.md` with SEF protocol |
| 5 | **Architecture** | Generate `docs/ARCHITECTURE.md`, `docs/EXTERNAL_DEPS.md` |
| 6 | **Debt** | Scan for TODO/FIXME/orphans → `docs/TECH_DEBT.md` |
| 7 | **Context Graph** | Populate `sef-reports/context_graph.json` |
| 8 | **Audit** | Run `audit_discovery()` to verify all artifacts |
| 9 | **Handoff** | Return control with context |

## 2. Artifact Locations

| Artifact | Location | Update Strategy |
|----------|----------|-----------------|
| `CODE_MAP.md` (meta) | `codemap/CODE_MAP.md` | Merge (SEF:MANUAL/SEF:AUTO) |
| Package codemaps | `codemap/<package>.md` | Merge |
| `FEATURES.md` | Root | Regenerate |
| `AGENTS.md` | Root | Regenerate |
| `ARCHITECTURE.md` | `docs/` | Preserve (relocate from root if needed) |
| `EXTERNAL_DEPS.md` | `docs/` | Preserve (relocate from root if needed) |
| `TECH_DEBT.md` | `docs/` | Regenerate |
| `context_graph.json` | `sef-reports/` | Regenerate |

## 3. Tools

| Tool | Purpose |
|------|---------|
| `generate_codemaps(dir)` | Centralized codemap generation |
| `generate_features_file(dir)` | Infer features from codemaps |
| `generate_agents_file(dir)` | Create AGENTS.md with SEF protocol |
| `scan_health(dir)` | Health scan + TECH_DEBT.md + context graph |
| `audit_discovery(dir)` | Post-completion verification |

## 4. Merge Strategy

Use section markers for update behavior:

```markdown
## Purpose
<!-- SEF:MANUAL -->
[User-editable content preserved on update]

## Directory Structure
<!-- SEF:AUTO -->
[Auto-regenerated on each discovery run]
```

## 5. Hygiene Checks

- **Patterns**: Ensure `*_cache/`, `__pycache__/`, `.DS_Store`, `node_modules/`, `dist/` are ignored.
- **Action**: If `.gitignore` missing patterns, append them.
- **Relocation**: Move misplaced artifacts (root → docs/).

## 6. Report Routing

**No `unknown/` directory allowed in sef-reports/.**

Valid agents for report routing:
- `developer`, `architect`, `qa_lead`, `security_owner`
- `docs_curator`, `platform_engineer`, `pr_reviewer`
- `tester`, `product_manager`, `strategist`, `forensic_engineer`

Invalid agents fallback to `platform_engineer`.

## 7. Context Graph Population

**Mandatory for brownfield projects:**

1. Run `populate_context_graph(directory, levels="L1,L2")`
2. Graph populated with file nodes, pattern nodes, decision nodes
3. Outcome: `sef-reports/context_graph.json` for dashboard

## 8. Discovery Audit

**Run `audit_discovery()` after completion to verify:**

| Check | Pass Condition |
|-------|----------------|
| Artifact existence | All required files present |
| Placement validation | No misplaced files, no `unknown/` |
| Content validation | Required sections present |
| Curator compliance | Documentation follows standards |

If audit fails, remediation steps provided.

## 9. Report Output

- **Status**: ✅ Success, ⚠️ Partial, ❌ Failed, 🛑 HALT
- **Escalation**: HALT for inaccessible dirs or detected secrets
- **Audit**: Required before handoff
