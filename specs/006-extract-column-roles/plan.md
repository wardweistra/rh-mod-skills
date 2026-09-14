# Implementation Plan: extract column roles

**Branch**: `006-extract-column-roles` | **Date**: 2026-09-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-extract-column-roles/spec.md`

## Summary

Extend `extract plan` so each projected sheet lists column **roles**. Header synonyms become a first-pass hint only. Re-running plan (without `--rehint`) rebuilds entities/elements from saved roles. Implement still copies the approved plan. Verify uses plan roles for coverage. No new command group.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: click, ruamel.yaml, pytest (unchanged)  
**Storage**: `process/plans/extract-plan.yaml` gains `sheets:`; inventory schema unchanged  
**Testing**: pytest + CliRunner; Dutch/English NKR, NBCA, unrecognized CSV remap  
**Target Platform**: POSIX CLI  
**Project Type**: CLI  
**Performance Goals**: extract plan on 153-row NKR <2s  
**Constraints**: CLI owns writes; no datatype guessing; injection boundary = copy cell strings; plan remains the only implement input  
**Scale/Scope**: P1 = plan `sheets` + NKR regression + remap CSV. P2 = preserve drops, duplicate-role fail, verify-from-roles

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | `extract plan` writes roles + elements; implement/verify unchanged owners; events unchanged |
| II. Plan → implement → verify | Pass | Role remap is an edit to the draft plan; implement still requires `approved` |
| III. Spec-linked validation | Pass | Tests for hint, remap, `--rehint`, drop preserve, duplicate-role, verify coverage |
| IV. Provenance | Pass | Provenance still names the columns used; conflicts for duplicate exclusive roles |
| V. Minimal surface | Pass | No `extract role` command; reviewer edits plan YAML (003 pattern) |

Post-design: same pass.

## Project Structure

```text
src/rh_mod_skills/commands/extract.py
skills/.curated/rh-mod-extract/SKILL.md
tests/unit/test_extract.py
specs/006-extract-column-roles/
example-project/models/<id>/process/plans/extract-plan.yaml
```

**Structure Decision**: Roles live on the existing extract plan. Hint matching stays a private helper; `propose_from_projections` takes optional saved sheets.

## Complexity Tracking

> No constitution violations.
