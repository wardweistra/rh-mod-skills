# Implementation Plan: rh-mod-ingest

**Branch**: `002-rh-mod-ingest` | **Date**: 2026-09-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-rh-mod-ingest/spec.md`

## Summary

Add gated `rh-mod-skills ingest` (`plan` → `approve` → `implement` → `verify`). Excel/CSV get a YAML table projection (sheet/column/row). PDF is copied and checksummed with projection skipped. `openpyxl` is the justified extra dependency. First proving files: IKNL Excel (`nkr-breast`) and ENCR PDFs (`encr-standard-dataset`).

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: click, ruamel.yaml, openpyxl (Excel); stdlib csv for CSV  
**Storage**: `models/<id>/sources/raw/`, `sources/projections/`, `process/plans/ingest-plan.yaml`, `tracking.yaml`  
**Testing**: pytest + CliRunner; fixtures in `tests/fixtures/l1/`  
**Target Platform**: POSIX CLI  
**Project Type**: CLI  
**Performance Goals**: IKNL 153-row workbook ingest <2s  
**Constraints**: No Markdown-only L1; no FML; untrusted source bytes; no silent L2 overwrite on checksum change  
**Scale/Scope**: Two proving models; tens of PDF companions registered, not table-extracted

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | `ingest plan/approve/implement/verify` own all writes |
| II. Plan → implement → verify | Pass | `approve` is the human gate; implement fails if plan missing or not `approved` |
| III. Spec-linked validation | Pass | Tests for IKNL 153 rows, PDF skip, drift, unapproved implement |
| IV. Provenance | Pass | Checksum + origin URL; injection boundary: copy/project only |
| V. Minimal surface | Pass | One command group; `openpyxl` justified (stdlib cannot read xlsx) |

## Project Structure

```text
src/rh_mod_skills/commands/ingest.py
tests/unit/test_ingest.py
tests/fixtures/l1/...
models/<id>/sources/raw/
models/<id>/sources/projections/
models/<id>/process/plans/ingest-plan.yaml
```

**Structure Decision**: Single ingest module on the existing Click group. No curated skill until CLI exists.

## Complexity Tracking

> No constitution violations.
