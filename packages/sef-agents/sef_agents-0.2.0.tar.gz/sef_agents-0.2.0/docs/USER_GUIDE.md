# SEF-Agents User Guide

How to use sef-agents for different project scenarios.

**Note:** Users interact via natural language. The AI assistant translates requests to MCP tool calls automatically.

---

## Table of Contents

- [Summary: For Business Users](#summary-for-business-users)
- [How It Works](#how-it-works)
- [Greenfield Projects](#greenfield-projects)
- [Brownfield Projects](#brownfield-projects)
- [Common Scenarios](#common-scenarios)
- [Edge Cases](#edge-cases)
- [Troubleshooting](#troubleshooting)

---

## Summary: For Business Users

**What is SEF-Agents?**

SEF-Agents is an **Engineering Operating System** that transforms AI coding assistants into enterprise-grade engineering partners. It provides the Synchronous Engineering Framework—a complete workflow accelerator with specialized agents, quality enforcement, and workflow orchestration for the entire software development lifecycle.

**How to Use It:**

1. **Activate SEF-Agents** first:
   - Type: "activate sef"
   - The AI will show available agents and ask which one to use

2. **Tell the AI what you need** in plain language:
   - Example: "Set agent to product manager. Create requirements for user login feature"
   - Example: "Set agent to forensic engineer. Investigate why payment fails"

3. **The system assigns specialized roles** automatically:
   - **Product Manager**: Writes clear requirements
   - **QA Lead**: Validates requirements are testable
   - **Architect**: Designs the solution
   - **Developer**: Writes production-ready code
   - **Tester**: Verifies everything works
   - **Security Owner**: Checks for vulnerabilities

4. **You approve before changes are made** to your codebase.

**Common Use Cases:**

- **New Feature**: "Set agent to product manager. Create requirements for [feature name]"
- **Bug Fix**: "Set agent to forensic engineer. Investigate why [problem] happens"
- **Code Quality Check**: "Set agent to platform engineer. Scan codebase health"

**What You Get:**

- **13 specialized agents** covering the full SDLC (Product Manager, QA Lead, Architect, Developer, Tester, Security Owner, etc.)
- **Workflow orchestration** that tracks story state, dependencies, and handoffs
- **Quality enforcement** with 25+ built-in tools (compliance, security, code quality)
- **Codebase mapping** that captures team patterns and knowledge
- **Synchronous engineering** that collapses delivery lifecycle through parallel execution

**No Technical Knowledge Required:** Just describe what you need in plain English. The AI handles the rest.

**Key Differentiator:** SEF-Agents works WITH your AI assistant (Cursor, Claude Desktop) to add quality gates, workflow context, and pattern memory—making AI-assisted development enterprise-ready.

---

## How It Works

**Step 1: Activate SEF-Agents**
- **You type:** "activate sef"
- **AI shows:** List of 13 available agents
- **You select:** Agent number or name (e.g., "1" or "discovery")

**Step 2: Use Agents**
- **User types:** Natural language requests in your AI assistant (Cursor, Claude Desktop, etc.)
- **AI assistant:** Translates to MCP tool calls automatically

**Example:**
- **You type:** "activate sef" → Select agent → "Set agent to discovery and scan this codebase"
- **AI calls:** `set_active_agent(agent_name="discovery")` (MCP tool)
- **AI performs:** Scans codebase, generates CODE_MAP.md

**Task Context:**
- **Minimal:** "Set agent to [agent_name]" → AI activates agent, may ask for task details
- **Recommended:** "Set agent to [agent_name] and [task description]" → AI activates and starts work immediately
- **Example:** "Set agent to forensic engineer and investigate why login fails" → Better than just "Set agent to forensic engineer"

---

## Greenfield Projects

New projects without existing codebase.

### Scenario 1: Starting a New Feature

**Role:** `discovery` → `product_manager` → `architect` → `developer`

**Task:** Build a new feature from scratch.

**What to Do:**

1. **Discovery Agent**
   - **You type:** "Set agent to discovery and scan this codebase" or "Set agent to discovery. Generate codemap for this project"
   - **AI does:** Scans directory, generates codemap (if files exist)
   - **Output:** `codemap/CODE_MAP.md`, `FEATURES.md`, `AGENTS.md`
   - **Edge Case:** Empty directory → AI skips codemap, proceeds to requirements

2. **Product Manager Agent**
   - **You type:** "Set agent to product manager. Create requirements for [feature name]" or "Set agent to product manager. Write requirements with AC for user authentication"
   - **AI does:** Creates `docs/requirements/STORY-XXX.md` with testable AC
   - **Prerequisites:** CODE_MAP.md (if code exists)
   - **Output:** Requirements with testable AC (Gherkin format)
   - **Edge Case:** Missing CODE_MAP.md → AI auto-delegates to discovery

3. **QA Lead Agent**
   - **You type:** "Set agent to QA lead. Validate the requirements" or "Set agent to QA lead. Check AC testability"
   - **AI does:** Validates AC testability, checks for ambiguities
   - **Output:** AC validation report
   - **Edge Case:** Ambiguous AC → AI documents assumptions, proceeds

4. **Architect Agent**
   - **You type:** "Set agent to architect. Design system for [feature]" or "Set agent to architect. Design integration boundaries"
   - **AI does:** Designs system boundaries, updates CODE_MAP.md
   - **Output:** Design document, integration points
   - **Edge Case:** No dependencies → AI creates minimal design doc

5. **Developer Agent**
   - **You type:** "Set agent to developer. Implement [feature name]" or "Set agent to developer. Build the authentication feature"
   - **AI does:** Implements per Elite Quality Protocol
   - **Output:** Code + tests (85% coverage minimum)
   - **Edge Case:** Missing design → AI requests architect handoff

**Happy Path:**
```
You: "Set agent to discovery and scan this codebase"
AI: Scans codebase, generates docs

You: "Set agent to product manager. Create requirements for user authentication"
AI: Creates requirements with AC

You: "Set agent to QA lead. Validate the requirements"
AI: Validates AC

You: "Set agent to architect. Design system for authentication"
AI: Designs system

You: "Set agent to developer. Implement authentication feature"
AI: Implements feature
```

---

### Scenario 2: New Project Initialization

**Role:** `discovery`

**Task:** Initialize project structure and documentation.

**What to Do:**

1. **Discovery Agent**
   - **You type:** "Set agent to discovery and initialize this project" or "Set agent to discovery. Generate project documentation"
   - **AI does:**
     - Generates codemap (if files exist)
     - Infers features from codemap
     - Creates AGENTS.md
     - Scans health (if code exists)
   - **Output:** `codemap/`, `FEATURES.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`
   - **Edge Case:** Empty project → AI generates minimal structure only

**Happy Path:**
```
You: "Set agent to discovery and initialize this project"
AI: Generates all discovery artifacts → Ready for requirements
```

---

## Brownfield Projects

Existing projects with codebase.

### Scenario 1: Adding Feature to Existing Codebase

**Role:** `discovery` → `product_manager` → `architect` → `developer`

**Task:** Add feature to existing system.

**What to Do:**

1. **Discovery Agent**
   - **You type:** "Set agent to discovery and scan this codebase" or "Set agent to discovery. Generate codemap for existing project"
   - **AI does:**
     - Generates codemap (scans existing code)
     - Populates context graph (levels: L1,L2)
     - Scans health (baseline quality)
   - **Output:** `codemap/CODE_MAP.md`, `sef-reports/context_graph.json`
   - **Edge Case:** Large codebase → You can say "Use faster scan" (AI uses L1 only)

2. **Product Manager Agent**
   - **You type:** "Set agent to product manager. Create requirements for [feature name]" or "Set agent to product manager. Write requirements for payment integration feature"
   - **Prerequisites:** CODE_MAP.md must exist
   - **AI does:** Reads CODE_MAP.md, identifies integration points
   - **Output:** Requirements with dependency analysis
   - **Edge Case:** CODE_MAP.md missing → AI auto-delegates to discovery

3. **Architect Agent**
   - **You type:** "Set agent to architect. Design integration for [feature]" or "Set agent to architect. Design payment integration boundaries"
   - **AI does:** Analyzes existing patterns, designs integration
   - **Output:** Design doc with boundary analysis
   - **Edge Case:** Conflicting patterns → AI documents trade-offs

4. **Developer Agent**
   - **You type:** "Set agent to developer. Implement [feature name]" or "Set agent to developer. Build payment integration feature"
   - **AI does:** Implements following existing patterns
   - **Output:** Code matching codebase style
   - **Edge Case:** Pattern mismatch → AI requests architect review

**Happy Path:**
```
You: "Set agent to discovery and scan this codebase"
AI: Scans codebase, generates codemap

You: "Set agent to product manager. Create requirements for payment integration"
AI: Creates requirements with integration analysis

You: "Set agent to architect. Design integration for payment feature"
AI: Designs integration

You: "Set agent to developer. Implement payment integration"
AI: Implements following existing patterns
```

---

### Scenario 2: Fixing a Bug

**Role:** `forensic_engineer` → `strategist` → `developer`

**Task:** Fix defect in existing code.

**What to Do:**

1. **Forensic Engineer Agent**
   - **You type:** "Set agent to forensic engineer and investigate [bug description]" or "Investigate why [symptom] happens"
   - **Better:** Provide context upfront: "Set agent to forensic engineer. The login API returns 500 errors when username contains special characters."
   - **AI does:** Root cause analysis (5 Whys), generates RCA report
   - **Output:** `sef-reports/forensic_engineer/rca_*.md`
   - **Note:** If you only say "Set agent to forensic engineer", AI will ask what to investigate
   - **Edge Case:** No logs → AI analyzes code paths only

2. **Strategist Agent**
   - **You type:** "Set agent to strategist" (AI has RCA context from previous step)
   - **AI does:** Reviews RCA, recommends solution with trade-offs
   - **Output:** Solution recommendation
   - **Edge Case:** Trivial fix → AI asks for approval before skipping strategist

3. **Developer Agent**
   - **You type:** "Set agent to developer" (AI has solution context)
   - **AI does:** Implements approved fix + regression test
   - **Output:** Fix + test coverage
   - **Edge Case:** Fix requires design change → AI escalates to architect

**Happy Path:**
```
You: "Set agent to forensic engineer. The login API returns 500 errors when username contains special characters."
AI: Performs RCA, generates report

You: "Set agent to strategist"
AI: Reviews RCA, recommends solution

You: "Approve the solution"
AI: Waits for approval

You: "Set agent to developer"
AI: Implements fix + regression test
```

**Best Practice:** Provide task context when activating agent. If you only activate without context, AI will ask clarifying questions.

**Mandatory:** User approval required before implementation.

---

### Scenario 3: Codebase Health Scan

**Role:** `platform_engineer`

**Task:** Assess codebase quality and technical debt.

**What to Do:**

1. **Platform Engineer Agent**
   - **You type:** "Set agent to platform engineer. Scan codebase health" or "Set agent to platform engineer. Run comprehensive health scan"
   - **AI does:**
     - Comprehensive health scan
     - Technical debt detection
     - Code quality scan (Python-specific)
     - Dead code detection
     - AI anti-pattern detection
   - **Output:** `sef-reports/health_report.md`, `docs/TECH_DEBT.md`
   - **Edge Case:** Non-Python project → AI skips code_quality scan

**Happy Path:**
```
You: "Set agent to platform engineer. Scan codebase health"
AI: Runs all scans → Generates health report → Identifies action items
```

---

## Common Scenarios

### Scenario 1: Story Workflow Tracking

**Role:** `scrum_master`

**Task:** Track story through SDLC phases.

**What to Do:**

1. **Initialize Workflow**
   - **You type:** "Initialize workflow for STORY-001" or "Start tracking STORY-001"
   - **AI does:** Creates workflow state
   - **Output:** Workflow state created

2. **Check State**
   - **You type:** "What's the status of STORY-001?" or "Check workflow state"
   - **AI does:** Retrieves current phase, artifacts, blockers
   - **Output:** Current phase, artifacts, blockers

3. **Get Next Agent**
   - **You type:** "What agent should I use next?" or "Suggest next agent"
   - **AI does:** Recommends agent based on current phase
   - **Output:** Recommended agent

**Happy Path:**
```
You: "Initialize workflow for STORY-001"
AI: Workflow initialized

You: "What's the status?"
AI: Shows current phase, artifacts

You: "What agent should I use next?"
AI: Recommends next agent

You: Complete phase → Repeat
```

**Edge Case:** Missing artifacts → AI blocks transition, shows what's missing.

---

### Scenario 2: Parallel Validation (Phase 6)

**Role:** `tester` + `security_owner` (parallel)

**Task:** Parallel testing and security validation.

**What to Do:**

1. **Start Parallel Phase**
   - **You type:** "Start parallel validation for STORY-001"
   - **AI does:** Initializes parallel tasks
   - **Output:** Parallel tasks initialized

2. **Tester Agent**
   - **You type:** "Set agent to tester. Execute conceptual tests for STORY-001" or "Set agent to tester. Run E2E tests"
   - **AI does:** Executes conceptual tests
   - **Output:** Test execution report

3. **Security Owner Agent**
   - **You type:** "Set agent to security owner. Run security audit" or "Set agent to security owner. Audit code for vulnerabilities"
   - **AI does:** Runs security audit
   - **Output:** Security audit report

4. **Complete Tasks**
   - **You type:** "Tests passed" or "Security audit complete"
   - **AI does:** Marks tasks complete in workflow

**Happy Path:**
```
You: "Start parallel validation"
AI: Initializes parallel tasks

You: "Set agent to tester. Execute tests for STORY-001"
AI: Runs tests → Reports results

You: "Set agent to security owner. Run security audit"
AI: Runs audit → Reports results

You: "Both tasks complete"
AI: Workflow advances
```

**Edge Case:** One task fails → AI blocks workflow, shows what needs resolution.

---

### Scenario 3: Requirements Sequencing

**Role:** `product_manager`

**Task:** Determine story execution order.

**What to Do:**

1. **Generate Dependency Graph**
   - **You type:** "Show story dependencies" or "Generate dependency graph"
   - **AI does:** Analyzes requirements, generates graph
   - **Output:** Dependency graph visualization

2. **Get Ready Stories**
   - **You type:** "Which stories are ready?" or "Show ready stories"
   - **AI does:** Finds stories with all dependencies satisfied
   - **Output:** List of ready stories

3. **Get Critical Path**
   - **You type:** "What's the critical path?" or "Show critical path"
   - **AI does:** Identifies longest dependency chain
   - **Output:** Critical path visualization

**Happy Path:**
```
You: "Show story dependencies"
AI: Generates dependency graph

You: "Which stories are ready?"
AI: Lists ready stories

You: Execute ready stories first
```

**Edge Case:** Circular dependencies → AI reports error, requests manual resolution.

---

## Edge Cases

### Edge Case 1: Missing CODE_MAP.md

**Scenario:** Product Manager needs CODE_MAP.md but it's missing.

**What Happens:**
- **You type:** "Set agent to product manager. Create requirements for [feature]"
- **AI does:** Detects missing CODE_MAP.md, auto-delegates to Discovery
- **AI does:** Discovery generates CODE_MAP.md
- **AI does:** Product Manager resumes automatically

**User Experience:**
```
You: "Set agent to product manager. Create requirements for user auth"
AI: "CODE_MAP.md missing. Delegating to Discovery..."
AI: [Generates CODE_MAP.md]
AI: "Resuming as Product Manager..."
```

---

### Edge Case 2: Ambiguous Acceptance Criteria

**Scenario:** QA Lead finds AC untestable.

**What Happens:**
- **You type:** "Set agent to QA lead. Validate requirements" or "Set agent to QA lead. Check AC testability"
- **AI does:** Documents ambiguities, determines escalation level
- **Escalation levels:**
  - L1: AI documents assumptions, proceeds
  - L2: AI requests PM + QA session
  - L3: AI halts, requests user decision

**User Experience:**
```
You: "Set agent to QA lead. Validate requirements"
AI: "AC-3 is ambiguous. Documenting assumptions and proceeding." (L1)

OR

AI: "Multiple AC issues found. Requesting PM review." (L2)

OR

AI: "Cannot determine pass/fail criteria. User decision required." (L3)
```

---

### Edge Case 3: Fix Without Root Cause

**Scenario:** User requests fix but root cause unknown.

**What Happens:**
- **You type:** "Fix this bug: [description]" or "This is broken: [symptom]"
- **Better:** "Set agent to forensic engineer. Investigate why [symptom] happens."
- **AI does:** Mandatory Forensic Engineer RCA first
- **AI does:** Strategist recommends solution
- **AI does:** Requests user approval
- **AI does:** Developer implements after approval

**User Experience:**
```
You: "Set agent to forensic engineer. The login API returns 500 errors."
AI: "Investigating root cause..." [Forensic Engineer]
AI: "Root cause identified. Recommending solution..." [Strategist]
AI: "Proposed fix: [solution]. Approve?" [Waits]
You: "Yes, approve"
AI: "Implementing fix..." [Developer]
```

**Note:** Providing bug description upfront speeds up investigation.

---

### Edge Case 4: Parallel Task Failure

**Scenario:** One parallel task fails (tester or security_owner).

**What Happens:**
- **You type:** "Start parallel validation"
- **AI does:** Initializes parallel tasks
- **One task fails:**
  - **AI does:** Blocks workflow at Phase 6
  - **AI does:** Shows what failed and why
  - **You type:** "Fix the issue" or "Defer this test"
  - **AI does:** Either fixes and retries, or defers (logs tech debt)

**User Experience:**
```
You: "Start parallel validation"
AI: [Runs tests and security audit]
AI: "Tests passed. Security audit failed: [reason]"
AI: "Workflow blocked. Fix security issue or defer?"
You: "Fix it"
AI: [Fixes issue, retries]
```

---

### Edge Case 5: Missing Artifacts

**Scenario:** Workflow transition blocked by missing artifact.

**What Happens:**
- **You type:** "What's the status of STORY-001?"
- **AI does:** Shows missing artifacts
- **You type:** "Generate the missing design doc"
- **AI does:** Generates artifact, marks complete, unblocks workflow

**User Experience:**
```
You: "What's the status?"
AI: "Phase: Design. Missing artifact: design_doc"
You: "Generate the design doc"
AI: [Generates design] "Artifact complete. Workflow unblocked."
```

---

### Edge Case 6: Large Codebase Discovery

**Scenario:** Brownfield project with 1000+ files.

**What Happens:**
- **You type:** "Set agent to discovery and scan this large codebase" or "Set agent to discovery. Use fast scan for 1000+ files"
- **AI does:** Uses faster scan (L1 only), skips LLM synthesis
- **AI does:** Focuses on critical files

**User Experience:**
```
You: "Set agent to discovery and scan this large codebase"
AI: "Large codebase detected. Using fast scan (L1 only)..."
AI: [Scans critical files only]
AI: "Codemap generated. 1,234 files scanned."
```

---

### Edge Case 7: Non-Python Project

**Scenario:** Project uses JavaScript/TypeScript/Go.

**What Happens:**
- **You type:** "Set agent to platform engineer. Scan codebase health" or "Set agent to platform engineer. Run health scan for JavaScript project"
- **AI does:** Detects project type, skips Python-specific scans
- **AI does:** Runs universal health checks

**User Experience:**
```
You: "Set agent to platform engineer. Scan codebase health"
AI: "JavaScript project detected. Skipping Python-specific scans..."
AI: [Runs universal health checks]
AI: "Health report generated."
```

---

### Edge Case 8: E2E Testing Not Available

**Scenario:** Frontend story but Playwright MCP not configured.

**What Happens:**
- **You type:** "Set agent to tester. Run E2E tests" or "Set agent to tester. Execute frontend tests"
- **AI does:** Checks testing capabilities
- **AI does:** Offers options: defer, configure, or manual testing

**User Experience:**
```
You: "Set agent to tester. Run E2E tests"
AI: "Playwright MCP not available. Options:"
AI: "1. Defer E2E testing (log as tech debt)"
AI: "2. Configure Playwright MCP"
AI: "3. Manual testing"
You: "Defer it"
AI: [Defers, logs tech debt]
```

---

## Troubleshooting

### Issue: MCP Not Connecting

**Symptoms:** Tools not appearing in AI assistant.

**What to Do:**
1. Restart AI assistant after config change
2. Verify JSON syntax in MCP config
3. Check `uvx` installation: `curl -LsSf https://astral.sh/uv/install.sh | sh`
4. Verify MCP status in settings (green indicator)

**You type:** "What SEF agents are available?"
**Expected:** List of 13 agents
**If fails:** MCP not connected

---

### Issue: Agent Not Activating

**Symptoms:** Agent prompt not injected.

**What to Do:**
1. **First, activate SEF-Agents:** Type "activate sef" to initialize the system
2. Select an agent from the list (by number or name)
3. Use natural language: "Set agent to developer. Implement [task]" (not exact command)
4. Verify agent exists: "What agents are available?"
5. Check MCP connection status

**You type:** "activate sef" → Select agent → "Set agent to developer. Implement user login feature"
**Expected:** AI confirms agent activated, shows protocol, starts implementation
**If fails:** Check agent name spelling or try "activate sef" first

---

### Issue: Workflow Stuck

**Symptoms:** Phase transition blocked.

**What to Do:**
1. **You type:** "What's the status of STORY-001?"
2. **AI shows:** Missing artifacts or blockers
3. **You type:** "Generate the missing [artifact]"
4. **AI does:** Generates artifact, unblocks workflow

**You type:** "What's blocking STORY-001?"
**AI shows:** Missing artifacts or blockers
**You type:** "Generate the design doc"
**AI does:** Generates, unblocks

---

### Issue: Missing Artifacts

**Symptoms:** Discovery artifacts not generated.

**What to Do:**
1. **You type:** "Set agent to discovery. Generate all discovery artifacts"
2. **AI does:** Generates artifacts
3. **You type:** "Verify discovery artifacts"
4. **AI does:** Runs audit, shows what's missing

**You type:** "Set agent to discovery. Generate all discovery artifacts"
**AI does:** Generates all artifacts
**You type:** "Verify everything was created"
**AI does:** Audits, reports status

---

## Quick Reference

### What You Type (Natural Language)

| Scenario | Minimal (AI will ask for details) | Recommended (with context) |
|----------|-----------------------------------|----------------------------|
| New project | "Set agent to discovery" | "Set agent to discovery and scan this codebase" |
| New feature | "Set agent to product manager" | "Set agent to product manager. Create requirements for user authentication feature" |
| Bug fix | "Set agent to forensic engineer" | "Set agent to forensic engineer. Investigate why login API returns 500 errors" |
| Code review | "Set agent to PR reviewer" | "Set agent to PR reviewer. Review the changes in src/auth.py" |
| Health scan | "Set agent to platform engineer" | "Set agent to platform engineer. Scan codebase health" |
| Check status | "What's the status of STORY-001?" | (Context not needed) |
| Next agent | "What agent should I use next?" | (Context not needed) |

### Agent Sequence (Happy Paths)

| Task | What You Type (Sequence) |
|------|--------------------------|
| Fix | "activate sef" → Select agent → "Set agent to forensic engineer. Investigate [bug]" → "Set agent to strategist" → "Set agent to developer. Implement fix" |
| Feature | "activate sef" → Select agent → "Set agent to discovery. Scan codebase" → "Set agent to product manager. Create requirements for [feature]" → "Set agent to QA lead. Validate requirements" → "Set agent to architect. Design [feature]" → "Set agent to developer. Implement [feature]" |
| Review | "activate sef" → Select agent → "Set agent to PR reviewer. Review changes" → "Set agent to tester. Run tests" + "Set agent to security owner. Run audit" (parallel) |

### Common Requests

**Initial Activation:**
- "activate sef" (required first step - shows available agents)

**Agent Selection:**
- "Set agent to [agent_name]. [task description]" (recommended)
- "Set agent to [agent_name]" (minimal - AI will ask for details)
- "Switch to [agent_name]. [task]"
- "Use [agent_name] agent for [task]"

**Workflow:**
- "Initialize workflow for STORY-001"
- "What's the status?"
- "What agent should I use next?"

**Discovery:**
- "Scan this codebase"
- "Generate codemap"
- "Show project structure"

**Quality:**
- "Scan codebase health"
- "Check technical debt"
- "Run security audit"

**Sequencing:**
- "Show story dependencies"
- "Which stories are ready?"
- "What's the critical path?"

---

*Last updated: 2025-01-27*
