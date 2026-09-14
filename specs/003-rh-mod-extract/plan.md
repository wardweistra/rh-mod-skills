# Implementation Plan: rh-mod-extract

**Branch**: `003-rh-mod-extract` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-rh-mod-extract/spec.md`

## Summary

Add gated `rh-mod-skills extract` (`plan` → `approve` → `implement` → `verify`). Read ingested **table projections** only (not raw Excel, not PDF text). Default IKNL proposal: one entity per `variabele_categorie`, one element per row, datatype/cardinality `unknown`. Implement writes `structured/inventory.yaml` from the approved plan. PDF-only models fail plan. No bindings, no FHIR types, no curated skill yet.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: click, ruamel.yaml (no new packages)  
**Storage**: `process/plans/extract-plan.yaml`, `structured/inventory.yaml`, optional `structured/value-domains.yaml`, `tracking.yaml`  
**Testing**: pytest + CliRunner; IKNL fixture via ingest; ENCR PDF-only negative case  
**Target Platform**: POSIX CLI  
**Project Type**: CLI  
**Performance Goals**: 153-row IKNL extract plan <1s  
**Constraints**: No Markdown L1; no datatype guessing (`*dat` ≠ date); no PDF row invention; injection boundary = copy cell strings from projections  
**Scale/Scope**: Proving model `nkr-breast`; ENCR waits on 004 table projections

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | `extract plan/approve/implement/verify` own all writes; events `extract_planned`, `inventory_derived` |
| II. Plan → implement → verify | Pass | `approve` is the human gate; implement fails if plan missing or not `approved` |
| III. Spec-linked validation | Pass | Tests for 153/5 IKNL, unapproved implement, PDF-only fail, verify idempotence, drop/rename, `--replace` |
| IV. Provenance | Pass | Each element keeps source/sheet/row/columns; conflicts listed, not collapsed; untrusted cells copied only |
| V. Minimal surface | Pass | One new command group on existing CLI; no extra dependency; annotate remains 005+ |

Constitution 1.1.0: extract consumes table projections (Excel/CSV now; PDF tables after 004). Flattening to Markdown is still forbidden.

## Project Structure

```text
src/rh_mod_skills/commands/extract.py
src/rh_mod_skills/cli.py
schemas/inventory-schema.yaml
src/rh_mod_skills/schemas/inventory-schema.yaml
tests/unit/test_extract.py
models/<id>/process/plans/extract-plan.yaml
models/<id>/structured/inventory.yaml
```

**Structure Decision**: Single extract module on the existing Click group, matching ingest. No curated skill until CLI exists.

## Complexity Tracking

> No constitution violations.
