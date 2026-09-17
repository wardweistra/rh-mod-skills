# Implementation Plan: ingest and status skills

**Branch**: `007-ingest-status-skills` | **Date**: 2026-09-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-ingest-status-skills/spec.md`

## Summary

Author `skills/.curated/rh-mod-ingest/` and `skills/.curated/rh-mod-status/` (full packs: SKILL.md, reference.md, examples). CLI unchanged. Ingest skill reasons then calls existing `ingest plan|approve|implement|verify`. Status skill is read-only and maps CLI `Next` to a skill name. Docs (README, Getting Started) catch up. Extract/annotate companion files stay out of this slice.

## Technical Context

**Language/Version**: Markdown skills (agent-facing); Python CLI unchanged (3.13+)  
**Primary Dependencies**: existing `rh-mod-skills ingest` / `status`; skill template under `skills/_template/`  
**Storage**: no new artifacts; skills describe `ingest-plan.yaml`, `sources/raw/`, `sources/projections/`, `tracking.yaml`  
**Testing**: pytest regression (no CLI change); assert required skill files exist; walkthrough against 002/004 proving fixtures  
**Target Platform**: Cursor agent + POSIX CLI  
**Project Type**: CLI + curated skills  
**Performance Goals**: n/a (docs)  
**Constraints**: CLI owns writes; no Markdown L1; no OCR; never inspect CLI source from the skill; constitution skill pack = SKILL.md + reference.md + examples  
**Scale/Scope**: two skills; proving models `nkr-breast` and `encr-standard-dataset`

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | Skills reason; ingest CLI still owns copies/projections/events; status writes nothing |
| II. Plan → implement → verify | Pass | Ingest skill uses existing gate. Status is read-only (justified; 001 status is not a gated stage) |
| III. Spec-linked validation | Pass | File-presence tests; ingest/status pytest still green; skill walkthroughs in quickstart |
| IV. Provenance | Pass | Skill requires origin URL when known; skip reasons explicit; no invented PDF rows |
| V. Minimal surface | Pass | No new command; two skill directories matching WORKFLOW.md names |

Post-design: same pass. Status has no plan artifact because the CLI is already read-only.

## Project Structure

```text
skills/.curated/rh-mod-ingest/
  SKILL.md
  reference.md
  examples/excel-plan.md
  examples/pdf-tables.md
skills/.curated/rh-mod-status/
  SKILL.md
  reference.md
  examples/output.md
docs/GETTING_STARTED.md
README.md
docs/WORKFLOW.md
tests/unit/test_skills_pack.py   # required files present
specs/007-ingest-status-skills/
```

**Structure Decision**: Curated skills live under `skills/.curated/<name>/` per constitution. Follow `rh-inf-ingest` / `rh-inf-status` shape, with opposite L1 rule (tables, not Markdown).

## Complexity Tracking

> No constitution violations. Status without plan→implement is the existing 001 command, not a new exception.
