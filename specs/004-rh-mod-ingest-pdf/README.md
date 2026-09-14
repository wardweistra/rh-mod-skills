# 004-rh-mod-ingest-pdf

PDF data dictionaries → same L1 table projection as Excel/CSV. Extends `ingest`, does not add extract-time PDF parsing.

| Artifact | Path |
|----------|------|
| Spec | [spec.md](spec.md) |
| Quality checklist | [checklists/requirements.md](checklists/requirements.md) |

**Proving file**: `ENCR-Recommendation-standard-dataset_Mar2023.pdf` → Table 1 + Table 2.

Next: `speckit-plan` / implement 004. Extract (003) can ship on Excel first; ENCR extract waits on this projection.
