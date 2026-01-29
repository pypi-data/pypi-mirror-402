# External APIs Registry

> **Purpose:** Track external dependencies detected in codebase.
> Auto-compared against `external_detector.py` scan by `cross_repo_linker.py`.

**Last Updated:** YYYY-MM-DD

---

## Registered Dependencies

### Environment Variables

| Env Var | Purpose | Contract/Docs | Notes |
|---------|---------|---------------|-------|
| `STRIPE_API_KEY` | Payment processing | [Stripe API Docs](https://stripe.com/docs) | Production key in vault |
| `DATABASE_URL` | Primary database | - | Managed by infra |

### API Clients (Libraries)

| Library | Purpose | Version | Contract/Docs |
|---------|---------|---------|---------------|
| `stripe` | Payment API | `>=5.0.0` | [Stripe Python](https://github.com/stripe/stripe-python) |
| `boto3` | AWS services | `>=1.26.0` | [Boto3 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) |

### External URLs

| Domain | Purpose | Contract/Docs | Notes |
|--------|---------|---------------|-------|
| `api.partner.com` | Partner integration | `docs/contracts/partner-api.yaml` | Rate limited |

---

## Schema Reference

### Adding a Dependency

When `external_detector.py` finds an unregistered dependency:

1. **Determine if it's intentional** (not test data or dead code)
2. **Add to appropriate section above**
3. **Document purpose** (what it's used for)
4. **Link contract/docs** if available (optional)

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| Name (Env Var/Library/Domain) | ✅ | Identifier matching detected value |
| Purpose | ✅ | What this dependency is used for |
| Contract/Docs | ❌ | Link to API docs or contract file |
| Version | ❌ | Required version (for libraries) |
| Notes | ❌ | Additional context |

### Matching Rules

The `cross_repo_linker.py` matches by:
- **Env vars:** Exact match on variable name
- **Libraries:** Exact match on import name
- **URLs:** Domain match (ignores path/query)

### Gap Types

| Gap | Meaning | Action |
|-----|---------|--------|
| `unregistered` | Detected in code but not in registry | Review and add if intentional |
| `stale` | In registry but not detected in code | Remove or verify still needed |
| `version_mismatch` | Detected version differs from registry | Update registry or pin version |
