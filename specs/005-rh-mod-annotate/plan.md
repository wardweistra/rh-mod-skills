# Implementation Plan: rh-mod-annotate

**Branch**: `005-rh-mod-annotate` | **Date**: 2026-09-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-rh-mod-annotate/spec.md`

## Summary

Add gated `rh-mod-skills annotate` (`plan` → `enrich` → `approve` → `implement` → `verify`). Plan writes a skeleton. The skill runs ReasonHub MCP and records hits with `enrich`. Implement writes `structured/bindings.yaml` from accept/replace/unbound only. Reject/pending skip the round. Status next stays `annotate` until every inventory path is bound or unbound. No FHIR types, no StructureDefinition.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: click, ruamel.yaml, httpx (unchanged stack; annotate does not HTTP-search)  
**Storage**: `process/plans/annotate-plan.yaml`, `structured/bindings.yaml`, `tracking.yaml`  
**Testing**: pytest + CliRunner; `annotate enrich --candidate` (no live ReasonHub in unit tests); extracted `nkr-breast` via existing ingest/extract helpers  
**Target Platform**: POSIX CLI  
**Project Type**: CLI  
**Performance Goals**: `--element gesl` plan <3s with live ReasonHub; fake client tests <1s; `--all-undecided` on 153 elements is allowed (advisory warn if >25)  
**Constraints**: CLI owns writes; MCP lookup is the skill; no invented codes; injection boundary = copy display strings and `--candidate` fields only; no datatype guessing  
**Scale/Scope**: P1 = `gesl` on `nkr-breast`. P2 = one ENCR Table 1 element

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | `annotate plan/enrich/approve/implement/verify` own all writes; MCP is skill-side; events `annotate_planned`, `element_bound` |
| II. Plan → implement → verify | Pass | `approve` is the human gate; implement fails if plan missing or not `approved` |
| III. Spec-linked validation | Pass | Tests for subset flags, fake vs missing ReasonHub, reject/unbound/replace, merge-by-path, `--replace`, verify counts, status next |
| IV. Provenance | Pass | Bindings keyed by inventory `path`; system/code/display/strength/decision recorded; untrusted labels copied only |
| V. Minimal surface | Pass | One command group; no extra package; no HTTP search client |

Post-design: same pass. Fake terminology client in tests is not a parallel write path.

## Project Structure

```text
src/rh_mod_skills/commands/annotate.py
src/rh_mod_skills/terminology.py          # candidate parse + system URIs; no HTTP
src/rh_mod_skills/commands/status.py
src/rh_mod_skills/cli.py
skills/.curated/rh-mod-annotate/SKILL.md
schemas/bindings-schema.yaml
src/rh_mod_skills/schemas/bindings-schema.yaml
tests/unit/test_annotate.py
tests/unit/test_status.py
models/<id>/process/plans/annotate-plan.yaml
models/<id>/structured/bindings.yaml
```

**Structure Decision**: Annotate command module matching extract/ingest. MCP lookup lives in `skills/.curated/rh-mod-annotate`. CLI `enrich` records `--candidate` strings only.

## Complexity Tracking

> No constitution violations.
