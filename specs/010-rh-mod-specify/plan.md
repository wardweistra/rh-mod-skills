# Implementation Plan: rh-mod-specify

**Branch**: `010-rh-mod-specify` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-rh-mod-specify/spec.md`

## Summary

Add gated `specify plan|approve|implement|verify`. Plan requires annotate-complete. Implement writes `structured/logical-model.yaml` from the approved plan (paths, types, cardinality, provenance, binding snapshots). CLI does not invent types or codes. Formalize is out of scope. Skill `rh-mod-specify` proposes types onto the plan YAML, then runs CLI.

## Technical Context

**Language/Version**: Python 3.13+, Click, ruamel.yaml  
**Primary Dependencies**: existing annotate inventory/bindings loaders; no ReasonHub  
**Storage**: `process/plans/specify-plan.yaml`, `structured/logical-model.yaml`  
**Testing**: pytest + CliRunner; tiny CSV consumer (not live ENCR tree)  
**Target Platform**: POSIX CLI  
**Project Type**: CLI + curated skill  
**Performance Goals**: 124-element ENCR plan <2s  
**Constraints**: CLI writes; unknown for F/A; strip system URI whitespace; no FHIR JSON  
**Scale/Scope**: one command group + skill pack + schema + tests

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | specify commands own plan + LM |
| II. Plan → implement → verify | Pass | approve gate |
| III. Spec-linked validation | Pass | incomplete annotate fail-closed; verify advisory vs blocking |
| IV. Provenance | Pass | copy inventory provenance; binding snapshot; no invented codes |
| V. Minimal surface | Pass | new `specify` group is the 001-named stage |

Post-design: same pass.

## Project Structure

```text
src/rh_mod_skills/commands/specify.py
src/rh_mod_skills/cli.py
schemas/logical-model-schema.yaml
skills/.curated/rh-mod-specify/
tests/unit/test_specify.py
```

**Structure Decision**: New Click group `specify`, same shape as extract/annotate.

## Complexity Tracking

> No constitution violations.
