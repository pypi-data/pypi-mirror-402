# Code Map Standard (Curator)

## 1. Root Map (Primary: `CODE_MAP.md`, Secondary: `docs/CODE_MAP.md`)
**Detection Priority**:
1. Root `CODE_MAP.md`
2. `docs/CODE_MAP.md` (secondary endpoint)

**Focus**: Architecture, Modules.
**Schema**:
- **High-Level Architecture**: Diagram/Text.
- **Key Workflows**: List top 3.
- **Module Registry**: Table(`Directory`, `Purpose`, `Owner`, `Status`).

## 2. Child Map (`project/subdir/CODE_MAP.md`)
**Focus**: Implementation.
**Schema**:
- **Purpose**: 1-line description.
- **Public API**: Exported classes/functions.
- **File Index**: Table(`File`, `Classes`, `Functions`, `Dependencies`).

## 3. Tables (REQUIRED)
- **Directory Structure**: (`Directory`, `Purpose`, `Key Files`, `Dependencies`).
- **API Endpoints**: (`Endpoint`, `Method`, `Handler`, `Req/Res Models`).
- **Key Classes**: (`Class`, `File`, `Methods`, `Dependencies`).
- **Tools**: (`Tool`, `Input`, `Output`, `Purpose`).
- **Ext. Deps**: (`Dep`, `Version`, `Purpose`).

## 4. Security
- ❌ NO Secrets/PII.
- ✅ Use `<ENV_VAR>` placeholders.

## 5. Maintenance
- Update when: Adding API/Class/Tool or changing Architecture.
