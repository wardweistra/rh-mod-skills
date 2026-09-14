---
name: "rh-mod-extract"
description: >
  Derive an L2 element inventory from ingested table projections. Header names
  are only a first-pass hint. Confirm or remap column roles on the extract plan,
  then let the CLI rebuild entities and write inventory. Modes: plan · implement · verify.
compatibility: "rh-mod-skills >= 0.1.0"
metadata:
  author: "RH Mod Skills"
  version: "1.0.0"
  source: "skills/.curated/rh-mod-extract/SKILL.md"
  lifecycle_stage: "l2-semi-structured"
  reads_from:
    - tracking.yaml
    - models/<model>/sources/projections/
    - models/<model>/process/plans/extract-plan.yaml
  writes_via_cli:
    - "rh-mod-skills extract plan"
    - "rh-mod-skills extract approve"
    - "rh-mod-skills extract implement"
    - "rh-mod-skills extract verify"
    - "rh-mod-skills status"
---

# rh-mod-extract

Extract owns inventory shape: entities, elements, paths, provenance. Column
**roles** on the extract plan are the contract. Synonym matching is a hint.
Annotate binds codes later. Do not guess FHIR datatypes from names (`*dat` ≠ date).

**Never inspect `rh-mod-skills` source code.** Use this skill and the CLI help.
Do not write `inventory.yaml` or the extract plan as a persistence bypass. Reviewer
edits of `role` / `decision` on the existing plan YAML are the gate; then run CLI.

## User Input

```text
$ARGUMENTS
```

First word is the mode. Typical: `plan nkr-breast`.

## Plan

1. Confirm ingest produced a table projection. If not, stop (PDF-only fails closed).
2. Run `rh-mod-skills extract plan <model>`.
3. Open `models/<model>/process/plans/extract-plan.yaml` and read `sheets[].columns`.
4. For each sheet, confirm roles:
   - `id` — variable identifier
   - `category` — entity grouping (optional; else one entity per sheet)
   - `label` — display
   - `datatype` / `cardinality` — only if the source states them
   - `unused` — leftover columns (kept as notes)
   - `domain_var` + `domain_code` + `domain_display` — local code list, not elements
5. If a hint is wrong or every column is `unused`, set the roles on the plan (set
   `origin: reviewer`) and re-run `extract plan` **without** `--rehint`. Do not add
   header names to the product to make a new registry work.
6. Exclusive roles may appear once per sheet. If `conflicts` contains
   `duplicate-role`, fix the plan and re-run plan.
7. Reviewer may drop/merge/rename entities and elements on the same plan, then
   `extract approve` → `extract implement` → `extract verify`.

`--rehint` throws away saved roles and proposes from header names again.

## Implement

```bash
rh-mod-skills extract approve <model>
rh-mod-skills extract implement <model>
rh-mod-skills extract verify <model>
```

Implement copies the approved plan. After a role remap, plan must have been
re-run so elements match those roles.
