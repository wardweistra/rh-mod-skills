# 002-rh-mod-ingest

Structured L1 ingest for Excel/CSV, plus PDF registration. Depends on 001 `init`.

| Artifact | Path |
|----------|------|
| Spec | [spec.md](spec.md) |
| Plan | [plan.md](plan.md) |
| Research | [research.md](research.md) |
| Data model | [data-model.md](data-model.md) |
| Quickstart | [quickstart.md](quickstart.md) |
| Quality checklist | [checklists/requirements.md](checklists/requirements.md) |
| Proving fixtures | [../../tests/fixtures/l1/README.md](../../tests/fixtures/l1/README.md) |

**P1 proving models** (ingested in `example-project/`)

- `nkr-breast` — IKNL Excel (153 variables) → table projection
- `encr-standard-dataset` — 22 ENCR English PDFs → register only

PDF table projection is specified separately as [004-rh-mod-ingest-pdf](../004-rh-mod-ingest-pdf/). Extract (003) reads table projections only.
