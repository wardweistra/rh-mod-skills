# Implementation Plan: rh-mod-formalize

**Branch**: `011-rh-mod-formalize` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

## Summary

Gated `formalize plan|approve|implement|verify`. Implement writes FHIR R4 `StructureDefinition` (`kind=logical`), per-bound-element ValueSets, and `computable/snapshot.yaml` with SHA-256 checksums. Unknown cardinality → `0..1`. Unknown datatype fails. Stdlib JSON; no FHIR library; no validator binary; no mapping files.

## Technical Context

**Language/Version**: Python 3.13+, Click, ruamel.yaml, stdlib json  
**Primary Dependencies**: specify logical-model loader; no fhir.resources  
**Storage**: `process/plans/formalize-plan.yaml`, `computable/*.json`, `computable/snapshot.yaml`  
**Testing**: pytest; mini specified model with types filled  
**Target Platform**: POSIX CLI  
**Project Type**: CLI + curated skill  
**Constraints**: CLI writes; fail unknown types; default card 0..1; no FML  
**Scale/Scope**: ENCR 124 elements; one SD + N ValueSets

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | formalize owns JSON + snapshot |
| II. Plan → implement → verify | Pass | approve + canonical/version gate |
| III. Spec-linked validation | Pass | unknown type fail; checksum verify |
| IV. Provenance | Pass | copy LM bindings only; no invented codes |
| V. Minimal surface | Pass | new `formalize` group is 001 L3 |

Post-design: same pass. No fhir.resources (unjustified).

## Project Structure

```text
src/rh_mod_skills/commands/formalize.py
src/rh_mod_skills/cli.py
skills/.curated/rh-mod-formalize/
tests/unit/test_formalize.py
```

**Structure Decision**: New Click group. JSON emitted as dicts.

## Complexity Tracking

> No constitution violations.
