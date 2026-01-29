# SEF Platform Metrics & Artifacts

This document defines the core metrics and artifact outputs verified for the SEF Platform as of December 2025.

## 1. Functional Roles (13)
The following agents are registered as active functional roles:
1.  **Product Manager**: Requirements & AC definition.
2.  **QA Lead**: AC validation & integrity scoring.
3.  **Architect**: System design & ADR generation.
4.  **Developer**: Implementation & code quality.
5.  **Tester**: E2E verification & visual proof.
6.  **Security Owner**: Threat modeling & security audits.
7.  **Scrum Master**: Flow optimization & handoff logging.
8.  **PR Reviewer**: Release integrity & risk assessment.
9.  **Discovery**: Codebase archaeology & mapping.
10. **Test Designer**: Conceptual test case generation.
11. **Forensic Engineer**: Incident investigation.
12. **Platform Engineer**: DevEx orchestration & health scans.
13. **Strategist**: Divergent solution brainstorming.

## 2. Tools (50+)
The platform provides over 50 specialized MCP tools across the following domains:
- **Workflow Management**: task tracking, handoffs, and phase gating.
- **Codebase Analysis**: codemapping, flow mapping, and dependency graphing.
- **Enterprise Scanning**: complexity, dead code, quality, documentation, and AI pattern detection.
- **Security Audit**: network, URL, secret, dependency, and file operation auditing.
- **Verification**: browser-based UI testing and conceptual task execution.

## 3. Artifacts (50+)
Verified unique artifact types produced during a **single story lifecycle**:

| Lifecycle Phase | Artifacts Produced | Count |
| :--- | :--- | :---: |
| **Discovery** | `CODE_MAP.md`, `ARCHITECTURE.md`, `EXTERNAL_DEPS.md`, `TECH_DEBT.md` | 4 |
| **Requirements** | `requirements/[ID].md`, `ac_validated` (state), AC Integrity Report | 3 |
| **Design** | `[ID]_design.md`, `FLOW_DIAGRAM.md`, `DEPENDENCY_GRAPH.md`, `design_approved` | 4 |
| **Implementation** | `implementation_done` (state), Linter Output Logs | 2 |
| **Code Review** | `review_passed` (state), PR Review Risk Matrix | 2 |
| **Health Scan** | `health_report.md/.json`, Quality, Dead Code, Docs, AI, Complexity (MD+JSON) | 12 |
| **Security Audit** | `security_audit.md`, Network, URL, Secret, Dep, File Scans (JSON) | 6 |
| **Verification** | `tests_passed`, `test_execution.jsonl`, `conceptual_tests.json`, `ui_report.md` | 4 |
| **Test Evidence** | Step Screenshots (x3), Final Pass Screenshot | 4 |
| **Lifecycle Mgmt** | `handoff_log.jsonl`, `executive-summary.json`, `project_status.md` | 3 |
| **On-Demand** | ADRs, Strategy Analysis, Post-Mortems | 6 |
| **TOTAL** | **Unique Artifact Types per Story Lifecycle** | **50+** |

---
*Definition: An Artifact is a persistent output used for reporting, audit trails, or as machine-verifiable input for subsequent agents.*
