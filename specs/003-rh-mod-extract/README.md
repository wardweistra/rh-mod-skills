# 003-rh-mod-extract

L2 inventory from ingested table projections. Depends on 001 `init` and 002 `ingest`. PDF tables are **004**. Annotate is **005+**.

| Artifact | Path |
|----------|------|
| Spec | [spec.md](spec.md) |
| Plan | [plan.md](plan.md) |
| Research | [research.md](research.md) |
| Data model | [data-model.md](data-model.md) |
| Quickstart | [quickstart.md](quickstart.md) |
| Tasks | [tasks.md](tasks.md) |
| Quality checklist | [checklists/requirements.md](checklists/requirements.md) |

**Proving model**: `nkr-breast` (IKNL, 153 rows → 5 entities).  
**Negative case**: `encr-standard-dataset` (PDF-only) must not invent rows.

Implemented: `rh-mod-skills extract plan|approve|implement|verify`. Next to implement: [004 PDF tables](../004-rh-mod-ingest-pdf/).
