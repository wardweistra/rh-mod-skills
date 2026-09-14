# Getting Started

This repo has a working workspace skeleton, L1 ingest (Excel/CSV/PDF tables), and L2 extract from table projections. Curated skills are not implemented yet.

## 1. Open the right workspace

Open `/Users/ward/workspace/rh-mod-skills` as its own Cursor window (sibling of `rh-skills`, not a subfolder of it). Speckit skills live under `.agents/skills/`.

## 2. Install the CLI

```bash
cd /Users/ward/workspace/rh-mod-skills
uv sync
uv run rh-mod-skills --help
uv run rh-mod-skills version
```

## 3. Try the proving models

```bash
cd example-project
uv run --project .. rh-mod-skills status
```

`nkr-breast` is extracted (IKNL, 153 elements, 5 entities, next=`annotate`). `encr-standard-dataset` is extracted from ENCR Table 1 (20 variables) + Table 2 (5 rows); companion PDFs remain skipped. Both next=`annotate`.

Re-run from scratch with [001 quickstart](../specs/001-rh-mod-framework/quickstart.md), [002 quickstart](../specs/002-rh-mod-ingest/quickstart.md), [003 extract](../specs/003-rh-mod-extract/quickstart.md), then [004 PDF tables](../specs/004-rh-mod-ingest-pdf/quickstart.md). Use `--project ..`, not `--directory ..`.

## 4. Next specification work

Implement annotate, specify, formalize. Do not author `skills/.curated/rh-mod-*` until the matching CLI commands exist.

## 5. What this product will not do

If you need mappings between two FHIR models, that is **rh-map-skills**. Do not add `mapping.xlsx` or FML here.

## Related docs

- [Constitution](../.specify/memory/constitution.md)
- [Framework spec](../specs/001-rh-mod-framework/spec.md)
- [Ingest spec](../specs/002-rh-mod-ingest/spec.md)
- [Extract spec](../specs/003-rh-mod-extract/spec.md)
- [PDF ingest spec](../specs/004-rh-mod-ingest-pdf/spec.md)
- [Workflow](WORKFLOW.md)
