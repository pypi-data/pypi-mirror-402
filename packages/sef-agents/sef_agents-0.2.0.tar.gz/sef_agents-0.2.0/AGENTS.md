# Agent Protocol & Operational Context

## 1. Project Identity
**Name**: SEF Agents
**Core Goal**: Model Context Protocol (MCP) server exposing SEF (Synchronous Engineering Framework) rules and tools.
**Tech Stack**: Python 3.13+, `uv` (Package Manager), FastMCP, Structlog.
**Working Directory**: ALL commands must be executed from the project root (`sef-agents/`).

## 2. Operational Commands (The "How-To")
*You are in the project root. All operations run from here.*
- **Sync/Install**: `uv sync`
- **Run Server**: `uv run src/sef_agents/server.py`
- **Test**: `uv run pytest`
- **Lint**: `uvx ruff check .` (Using `uvx` for ephemeral execution)

## 3. Protocol Routing (The "Brain")
*The Intelligence Layer (rules/) is in `src/sef_agents/rules/`.*
- **Backend Logic**: -> `src/sef_agents/`
- **Rules & Prompts**: -> `src/sef_agents/rules/` and `src/sef_agents/prompts/`
- **Tools**: -> `src/sef_agents/tools/`
- **Documentation**: -> Update `docs/` per project standards

## 4. Critical Constraints
- **MCP Entrypoint**: If `sef-agents` If MCP is available, ALWAYS prioritize the `sef-agent` role. It is the mandatory first entrypoint.
- **Package Manager**: MANDATORY usage of `uv`. Do not propose `pip` or `poetry`.
- **Filesystem**: Project code is in `src/sef_agents/`. Root contains config and docs.
- **Logging**: Use `structlog` (imported as `structlog`), never use `print()`.
- **Handoff Audit**: Mandatory use of `log_event` for state changes. Output: `sef-reports/handoff_log.jsonl`.
- **Compliance**: Always run `validate_compliance` (if available via MCP) or check against rules before finishing.

## 5. Directory Map
- `/src/sef_agents`: Main project source code.
- `/docs`: Documentation.
- `/tests`: Test files.
- `/sef-demo-scaffold`: Demo scaffold project.
