# Implementation Plan: annotate review

**Branch**: `008-annotate-review` | **Date**: 2026-09-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-annotate-review/spec.md`

## Summary

Add `annotate export` (static HTML from the plan) and `annotate import --from` (picks YAML → plan `decision`/`chosen`/`reason`). Import never writes bindings; approved plans become draft. HTML-first; no server; no Excel. Update `rh-mod-annotate` skill: export after enrich, reviewer picks, import, then existing approve/implement.

## Technical Context

**Language/Version**: Python 3.13+, Click, ruamel.yaml  
**Primary Dependencies**: stdlib HTML generation (no new web framework); existing annotate module  
**Storage**: `process/plans/annotate-review.html`, downloaded `annotate-picks.yaml`; plan remains `annotate-plan.yaml`  
**Testing**: pytest + CliRunner; fixture plan with three `gesl` candidates; no browser automation required for P1 (assert HTML contains path/codes; import from a written picks file)  
**Target Platform**: POSIX CLI; reviewer opens HTML in any browser  
**Project Type**: CLI  
**Performance Goals**: export of 153-element plan <2s  
**Constraints**: CLI owns HTML/picks writes; copy cell strings only; no ReasonHub; no mapping.xlsx; injection boundary = plan fields into HTML text (escape)  
**Scale/Scope**: P1 = `gesl` export + accept pick 1 import. P2 = unbound/skip/replace + import resets approved

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | `annotate export` / `import` own files; skill does not write HTML |
| II. Plan → implement → verify | Pass | Import updates draft plan; implement still requires approve |
| III. Spec-linked validation | Pass | Tests for export HTML contents, import mapping, fail-closed paths, no bindings write |
| IV. Provenance | Pass | Pick by rank against plan candidates; replace is explicit chosen; HTML escaped |
| V. Minimal surface | Pass | Subcommands on existing `annotate` group; not a new command or Excel format |

Post-design: same pass. No new tracking event (import is not `element_bound`).

## Project Structure

```text
src/rh_mod_skills/commands/annotate.py
src/rh_mod_skills/annotate_review.py   # HTML + picks load/dump helpers
skills/.curated/rh-mod-annotate/SKILL.md
tests/unit/test_annotate_review.py
models/<id>/process/plans/annotate-review.html
```

**Structure Decision**: Helpers beside annotate (same as `pdf_tables.py` for ingest). Keep implement/bindings logic untouched.

## Complexity Tracking

> No constitution violations.
