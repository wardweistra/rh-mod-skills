# Getting Started

This repo has a working workspace skeleton and L1 ingest. Curated skills are not implemented yet.

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

`nkr-breast` has the IKNL Excel table projection (153 rows). `encr-standard-dataset` has the ENCR PDFs registered (projection skipped). Next stage is extract.

Re-run from scratch with [001 quickstart](../specs/001-rh-mod-framework/quickstart.md) then [002 quickstart](../specs/002-rh-mod-ingest/quickstart.md). Use `--project ..`, not `--directory ..`.

## 4. Next specification work

Extract, annotate, specify, formalize — one spec each. Do not author `skills/.curated/rh-mod-*` until the matching CLI commands exist.

## 5. What this product will not do

If you need mappings between two FHIR models, that is **rh-map-skills**. Do not add `mapping.xlsx` or FML here.

## Related docs

- [Constitution](../.specify/memory/constitution.md)
- [Framework spec](../specs/001-rh-mod-framework/spec.md)
- [Ingest spec](../specs/002-rh-mod-ingest/spec.md)
- [Workflow](WORKFLOW.md)
