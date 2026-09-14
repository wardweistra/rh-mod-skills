# 004-rh-mod-ingest-pdf

PDF data dictionaries → same L1 table projection as Excel/CSV. Extends `ingest`.

| Artifact | Path |
|----------|------|
| Spec | [spec.md](spec.md) |
| Plan | [plan.md](plan.md) |
| Research | [research.md](research.md) |
| Data model | [data-model.md](data-model.md) |
| Quickstart | [quickstart.md](quickstart.md) |
| Tasks | [tasks.md](tasks.md) |
| Quality checklist | [checklists/requirements.md](checklists/requirements.md) |

**Proving file**: `ENCR-Recommendation-standard-dataset_Mar2023.pdf` → Table 1 (20 rows) + Table 2 (5 rows).

Implemented: ingest plan lists detected tables; implement writes included sheets. Extract on ENCR now succeeds.
