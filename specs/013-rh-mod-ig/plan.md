# Implementation Plan: rh-mod-ig

**Branch**: `013-rh-mod-ig` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

## Summary

Ungated `rh-mod-skills ig sync <model>` stages `models/<id>/ig/` from `computable/snapshot.yaml`. Copies pinned [ig-publisher-scripts](https://github.com/HL7/ig-publisher-scripts) launchers via httpx; mirrors JSON into `input/models` and `input/vocabulary`; regenerates ImplementationGuide. Does not run Java.

## Technical Context

**Language/Version**: Python 3.13+, Click, httpx, ruamel.yaml  
**Primary Dependencies**: formalize snapshot + JSON; HL7 scripts at pin `9e6c7de21624e99dfd6739657a7895dfbe7d1357`  
**Storage**: `models/<id>/ig/`  
**Testing**: pytest; stub httpx; reuse formalize mini pipeline  
**Target Platform**: POSIX CLI (also copies `.bat`)  
**Project Type**: CLI + curated skill  
**Constraints**: no Java; no publisher.jar; no ig.ini clobber; managed-file delete only  
**Scale/Scope**: ENCR ~120 JSON files copied

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | `ig sync` owns all IG writes |
| II. Plan → implement → verify | Pass | justified: generated view, not a stage (001 FSH clause / FR-013 analog) |
| III. Spec-linked validation | Pass | scaffold, idempotent delete, no jar tests |
| IV. Provenance | Pass | copy snapshot JSON only; no invented codes |
| V. Minimal surface | Pass | new `ig` group; does not overload formalize |

Post-design: same pass. httpx already in the stack.

## Project Structure

```text
src/rh_mod_skills/commands/ig.py
src/rh_mod_skills/cli.py
skills/.curated/rh-mod-ig/
tests/unit/test_ig.py
```

**Structure Decision**: Click group `ig` with `sync` (room for a later `build` that still must not land in this slice).

## Complexity Tracking

> No constitution violations. Ungated generated view is explicit in the spec.
