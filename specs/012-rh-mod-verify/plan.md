# Implementation Plan: rh-mod-verify

**Branch**: `012-rh-mod-verify` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

## Summary

Read-only `rh-mod-skills verify [model]` coordinator. Invokes existing stage `verify` subcommands when their artifacts exist, prints coverage + unbound, reports `validator=not-run`, never writes tracking. Status next stays `verify`.

## Technical Context

**Language/Version**: Python 3.13+, Click  
**Primary Dependencies**: existing ingest/extract/annotate/specify/formalize verify  
**Storage**: none (read-only)  
**Testing**: pytest; mini extracted vs formalized pipelines  
**Target Platform**: POSIX CLI  
**Project Type**: CLI + curated skill  
**Constraints**: no tracking writes; skip missing stages; no validator binary; no mapping  
**Scale/Scope**: ENCR already formalized; coordinator must finish in one command

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | coordinator reads only; skills do not write |
| II. Plan → implement → verify | Pass | justified exception: read-only coordinator (001 FR-013) |
| III. Spec-linked validation | Pass | idempotence + skip + checksum fail tests |
| IV. Provenance | Pass | unbound remains visible; blocking vs advisory |
| V. Minimal surface | Pass | one top-level `verify`; reuses stage verifies |

Post-design: same pass. Do not append `validated`.

## Project Structure

```text
src/rh_mod_skills/commands/verify.py
src/rh_mod_skills/cli.py
skills/.curated/rh-mod-verify/
tests/unit/test_verify.py
```

**Structure Decision**: Single Click command (like `status`), not a gated group.

## Complexity Tracking

> No constitution violations. Read-only exception is explicit in 001 FR-013.
