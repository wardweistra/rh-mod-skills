---
name: "rh-mod-ingest"
description: >
  Register L1 codebooks (Excel, CSV, PDF tables) onto an initialized model.
  CLI copies originals and writes table projections; this skill chooses files,
  origin URLs, and PDF table include/exclude. Never flatten to Markdown. Never OCR.
  Modes: plan · implement · verify.
compatibility: "rh-mod-skills >= 0.1.0"
context_files:
  - reference.md
  - examples/excel-plan.md
  - examples/pdf-tables.md
metadata:
  author: "RH Mod Skills"
  version: "1.0.0"
  source: "skills/.curated/rh-mod-ingest/SKILL.md"
  lifecycle_stage: "l1-discovery"
  reads_from:
    - tracking.yaml
    - models/<model>/process/plans/ingest-plan.yaml
    - models/<model>/sources/projections/
  writes_via_cli:
    - "rh-mod-skills ingest plan"
    - "rh-mod-skills ingest approve"
    - "rh-mod-skills ingest implement"
    - "rh-mod-skills ingest verify"
    - "rh-mod-skills status"
---

# rh-mod-ingest

Ingest is the **L1** stage. It registers codebook files on an already-initialized
**model** and projects Excel/CSV/PDF **tables** into the same YAML shape. Extract
reads those projections. This is the opposite of rh-skills ingest: do **not**
normalize to Markdown.

**Never inspect `rh-mod-skills` source code.** Use this skill, [reference.md](reference.md),
and `rh-mod-skills ingest --help`. Do not write `sources/`, projections,
`tracking.yaml`, or `ingest-plan.yaml` as a persistence bypass. Reviewer edits of
`tables[].decision` on the plan YAML are the gate; then run the CLI.

`init` is not this skill. If there is no model, stop and tell the user to run
`rh-mod-skills init <model>` (or `rh-mod-status`).

## User Input

```text
$ARGUMENTS
```

First word is the mode. Typical: `plan nkr-breast` with source paths in the rest
of the message.

| Mode | What you do |
|------|-------------|
| `plan` | Confirm model exists; gather files + origin URL; run ingest plan |
| `implement` | After reviewer approval: ingest approve → implement → verify |
| `verify` | Run ingest verify only |

## Pre-checks

1. Run `rh-mod-skills status` (or `status <model>`). If tracking is missing, tell
   the user to `init`. Do not invent a model id.
2. If the named model is missing, stop. Suggest `init`.
3. For `plan`, you need at least one L1 file (`.xlsx`, `.csv`, `.pdf`). If none
   given, ask. Do not search the tool repo for files unless the user pointed at
   `tests/fixtures/l1/`.
4. Run CLI from the **consumer** directory (`example-project/`). Use
   `uv run --project .. rh-mod-skills …`, not `--directory ..`.

## Plan

1. Collect `--source` paths and one `--origin-url` when the catalog is public
   (IKNL datacatalogus, ENCR Recommendations, DICA NBCA).
2. Run:

```bash
rh-mod-skills ingest plan <model> --source <file> [--source <file> ...] \
  [--origin-url <url>]
```

3. Read `models/<model>/process/plans/ingest-plan.yaml`. Confirm each source
   `type` (`excel` / `csv` / `pdf`) and `projection` (`tables` or `skipped`).
4. **Excel/CSV**: projection should be `tables`. Do not edit column names here —
   extract column roles are a later skill.
5. **PDF**: read `tables[]`. Propose `decision: include` only for codebook
   grids (named Table N, variable lists). Mark cover/footnote fragments
   `exclude` with a reason. If `skip_reason` is set and there are no tables,
   register-only is honest — do not invent rows from page prose.
6. Show the draft plan to the reviewer. They approve (CLI `ingest approve` or
   they edit `decision` first). Do not implement an unapproved plan.

## Implement

```bash
rh-mod-skills ingest approve <model>
rh-mod-skills ingest implement <model>
rh-mod-skills ingest verify <model>
rh-mod-skills status <model>
```

If implement fails because the plan is not approved, stop. Do not copy files
yourself.

If implement fails on checksum drift with L2 present, do **not** pass
`--acknowledge-drift` unless the reviewer explicitly accepts it. Never delete
inventory/bindings to force a re-ingest.

Expect `source_added` from the CLI. Verify is read-only (no new tracking events).

## Forbidden

- Flattening a codebook to Markdown as the only L1 form
- OCR
- Guessing FHIR datatypes or extract column roles
- Writing projection YAML or `tracking.yaml` by hand
- Calling extract from this skill (status next=`extract` means hand off to
  `rh-mod-extract`)

Worked examples: [excel-plan.md](examples/excel-plan.md),
[pdf-tables.md](examples/pdf-tables.md). Field list: [reference.md](reference.md).
