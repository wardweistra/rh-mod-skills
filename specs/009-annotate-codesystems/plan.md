# Implementation Plan: annotate code systems

**Branch**: `009-annotate-codesystems` | **Date**: 2026-09-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-annotate-codesystems/spec.md`

## Summary

Extend annotate `--system` and `--candidate` aliases to ReasonHub’s remaining searchable systems (RxNorm, UCUM, ICD-10-CM) plus a plan-only `all` search mode. Default `--system` is `all`. Keep `icd-10`. CLI still does not search; skill maps plan names to MCP tools. No new commands.

## Technical Context

**Language/Version**: Python 3.13+, Click, ruamel.yaml  
**Primary Dependencies**: existing `rh_mod_skills.terminology` alias table; ReasonHub MCP (skill-side)  
**Storage**: `annotate-plan.yaml` `systems:` list; candidate `system` URIs  
**Testing**: pytest + CliRunner; unit tests for aliases without network  
**Target Platform**: POSIX CLI  
**Project Type**: CLI  
**Performance Goals**: unchanged  
**Constraints**: CLI owns writes; no HTTP search; cap 5 candidates; `all` is not a URI  
**Scale/Scope**: alias table + skill MCP mapping + tests; HTML/import unchanged

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | Plan/enrich still CLI; skill still MCP |
| II. Plan → implement → verify | Pass | No new gated stage |
| III. Spec-linked validation | Pass | Tests for new aliases, unknown fail-closed, `all` not a candidate URI |
| IV. Provenance | Pass | Canonical FHIR URIs on candidates |
| V. Minimal surface | Pass | Extend `--system`; no new command |

Post-design: same pass.

## Project Structure

```text
src/rh_mod_skills/terminology.py
src/rh_mod_skills/commands/annotate.py
skills/.curated/rh-mod-annotate/SKILL.md
tests/unit/test_terminology.py
tests/unit/test_annotate.py
```

**Structure Decision**: Expand the existing alias map. Do not add a new CLI group.

## Complexity Tracking

> No constitution violations.
