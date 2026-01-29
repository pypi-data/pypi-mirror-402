# Mermaid Templates (Pre-Validated)

## Rule: Use ONLY These Templates

Do NOT freestyle Mermaid. Fill placeholders in these pre-validated templates only.

---

## Template 1: System Context

Use for high-level system overview showing external actors and boundaries.

```mermaid
flowchart TB
    subgraph External
        USER[User]
        EXT1[ExternalService1]
    end
    subgraph System[SystemName]
        API[APIGateway]
        SVC[CoreService]
        DB[(Database)]
    end
    USER --> API
    API --> SVC
    SVC --> DB
    SVC --> EXT1
```

**Placeholders to replace:**
- `SystemName` → Your system name (alphanumeric only)
- `ExternalService1` → External service name
- `APIGateway`, `CoreService`, `Database` → Your component names

---

## Template 2: Module Dependencies

Use for showing internal module relationships.

```mermaid
flowchart LR
    API[api] --> SVC[services]
    API --> AUTH[auth]
    SVC --> MODELS[models]
    SVC --> DB[database]
    AUTH --> MODELS
```



---

## Template 3: Request Flow (Sequence)

Use for showing request/response lifecycle.

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant S as Service
    participant D as Database
    C->>A: HTTPRequest
    A->>S: ProcessRequest
    S->>D: Query
    D-->>S: ResultSet
    S-->>A: ProcessedData
    A-->>C: HTTPResponse
```



---

## Template 4: Component Diagram (Classes)

Use for showing class/component relationships.

```mermaid
classDiagram
    class ServiceName {
        +publicMethod()
        -privateMethod()
        +attribute: Type
    }
    class RepositoryName {
        +find()
        +save()
    }
    ServiceName --> RepositoryName
```



---

## Template 5: Data Flow (Simple)

Use for ETL or data pipeline visualization.

```mermaid
flowchart LR
    SOURCE[(Source)] --> TRANSFORM[Transform]
    TRANSFORM --> VALIDATE{Validate}
    VALIDATE -->|Valid| LOAD[(Target)]
    VALIDATE -->|Invalid| ERROR[ErrorQueue]
```



---

## Template 6: External Integrations

Use for showing third-party API boundaries.

```mermaid
flowchart TB
    subgraph Internal
        SVC[Service]
        CACHE[(Cache)]
    end
    subgraph External
        API1[PaymentAPI]
        API2[EmailAPI]
        API3[StorageAPI]
    end
    SVC --> CACHE
    SVC --> API1
    SVC --> API2
    SVC --> API3
```

---

## Syntax Rules (MANDATORY)

### Node IDs
✅ Alphanumeric only: `UserSvc`, `DB1`, `API`
❌ No hyphens: `user-svc`
❌ No underscores: `user_svc`
❌ No spaces: `user svc`

### Labels with Special Characters
✅ Use quotes: `A["Label (with parens)"]`
✅ Use quotes: `B["Items: 5"]`
❌ No quotes: `A[Label (breaks)]`

### Arrows
| Diagram | Solid | Dashed | With Label |
|---------|-------|--------|------------|
| Flowchart | `-->` | `-.->` | `-->\|label\|` |
| Sequence | `->>` | `-->>` | `->>` with `: label` |
| Class | `-->` | `..>` | N/A |

### Size Limits
- Max 10 nodes per diagram
- Max 15 edges per diagram
- Split larger diagrams into multiple

---

## Fallback: Use Tables

When diagram is complex or uncertain, use tables instead:

```markdown
## Module Dependencies

| Module | Depends On | Relationship |
|--------|------------|--------------|
| `api.routes` | `services.core` | Import |
| `services.core` | `models.user` | Import |
| `services.core` | `clients.db` | Composition |
```

Tables have zero syntax risk and render everywhere.

---

## Validation Checklist

Before including ANY Mermaid diagram:

- [ ] Template matches one of the 6 above
- [ ] Node IDs: alphanumeric only
- [ ] Labels with special chars: quoted `["..."]`
- [ ] Arrow syntax: matches table above
- [ ] Node count: ≤ 10
- [ ] Edge count: ≤ 15

If ANY check fails → use TABLE format instead.
