# CODE_MAP.md for `sef-agents`

## Purpose
[Describe the purpose of this directory]

## Directory Structure
| Item | Type | Purpose | Dependencies |
|------|------|---------|--------------|
| [`tests/`](tests/CODE_MAP.md) | Dir | [Desc] | - |
| [`docs/`](docs/CODE_MAP.md) | Dir | [Desc] | - |
| [`pitch-deck/`](pitch-deck/CODE_MAP.md) | Dir | [Desc] | - |
| [`sef-reports/`](sef-reports/CODE_MAP.md) | Dir | [Desc] | - |
| [`src/`](src/CODE_MAP.md) | Dir | [Desc] | - |
| `AGENT.md` | File | [Desc] | - |
| `handoff_log.jsonl` | File | [Desc] | - |
| `uv.lock` | File | [Desc] | - |
| `bandit-report.json` | File | [Desc] | - |
| `Dockerfile` | File | [Desc] | - |
| `Makefile` | File | [Desc] | - |
| `pyproject.toml` | File | [Desc] | - |
| `demo_security_scan.sh` | File | [Desc] | - |
| `README.md` | File | [Desc] | - |

## Key Classes / Functions
| Name | File | Purpose | Dependencies |
|------|------|---------|--------------|
| ...  | ...  | ...     | ...          |

## External Dependencies
*Auto-detected by external_detector.py*

### Environment Variables (External Endpoints)

| Variable | File | Line | Notes |
|----------|------|------|-------|
| `STRIPE_API_KEY` | `test_cross_repo_linker.py` | 68 | Environment variable for external endpoint |
| `UNKNOWN_SERVICE_URL` | `test_cross_repo_linker.py` | 95 | Environment variable for external endpoint |
| `DATABASE_URL` | `test_cross_repo_linker.py` | 69 | Environment variable for external endpoint |
| `PAYMENT_API_URL` | `test_external_detector.py` | 28 | Environment variable for external endpoint |
| `STRIPE_API_ENDPOINT` | `test_external_detector.py` | 40 | Environment variable for external endpoint |
| `AUTH_SERVICE_HOST` | `test_external_detector.py` | 50 | Environment variable for external endpoint |

### Hardcoded External URLs

| Domain | File | Line | Notes |
|--------|------|------|-------|
| `api.partner.com` | `test_cross_repo_linker.py` | 76 | ⚠️ Consider env var |
| `api.unknown.com` | `test_cross_repo_linker.py` | 102 | ⚠️ Consider env var |
| `malicious-site.xyz` | `test_security_scan.py` | 76 | ⚠️ Consider env var |
| `api.example.com` | `test_external_detector.py` | 123 | ⚠️ Consider env var |
| `api.stripe.com` | `test_external_detector.py` | 148 | ⚠️ Consider env var |
| `payments.example.com` | `test_external_detector.py` | 168 | ⚠️ Consider env var |


## Integration Boundaries
*Where this module connects to external systems*

| Boundary Type | Local Code | External System | Data Flow | Risk Level |
|---------------|------------|-----------------|-----------|------------|
| API Call      | [file.py]  | [External API]  | Outbound  | Medium     |
| Event Consumer| [file.py]  | [Message Queue] | Inbound   | Low        |

## Technical Debt
*Link to TECH_DEBT.md items in this directory*

| Debt ID | Location | Type | Severity | Status |
|---------|----------|------|----------|--------|
| See [TECH_DEBT.md](../../docs/templates/TECH_DEBT.md) for full registry |
