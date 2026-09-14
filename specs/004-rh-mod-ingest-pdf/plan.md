# Implementation Plan: rh-mod-ingest-pdf

**Branch**: `004-rh-mod-ingest-pdf` | **Date**: 2026-09-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-rh-mod-ingest-pdf/spec.md`

## Summary

Extend `rh-mod-skills ingest` so PDF data dictionaries can produce the same L1 table projection as Excel/CSV. Plan lists detected tables for review; implement writes only included tables. Proving file: ENCR 2023 standard dataset → Table 1 (Variable/Comment, 20 rows, pages 2–3) and Table 2 (cancer type / stage / remarks, 5 rows, page 4). `pdfplumber` is the justified extra dependency. OCR and Markdown-only L1 remain forbidden.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: click, ruamel.yaml, openpyxl, pdfplumber (PDF tables)  
**Storage**: `process/plans/ingest-plan.yaml` (PDF `tables[]`), `sources/raw/`, `sources/projections/<name>.yaml`  
**Testing**: pytest + CliRunner; ENCR proving PDF; generated empty/text-only PDFs  
**Target Platform**: POSIX CLI  
**Project Type**: CLI  
**Performance Goals**: 6-page ENCR PDF plan <3s  
**Constraints**: Same projection schema as Excel; no Markdown-only L1; no OCR; untrusted PDF text copied only; Excel/CSV behavior unchanged  
**Scale/Scope**: P1 = one proving PDF (two tables). P2 = companion PDFs may skip independently.

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | Extends existing `ingest plan/approve/implement/verify`; no new command group |
| II. Plan → implement → verify | Pass | PDF tables are previewed in the plan; implement honors include/exclude |
| III. Spec-linked validation | Pass | Tests for Table 1+2, exclude junk, skip reasons, mixed Excel+PDF, extract after projection |
| IV. Provenance | Pass | Original PDF + checksum; sheet name/page in projection; injection boundary = copy cells |
| V. Minimal surface | Pass | Extends ingest; `pdfplumber` justified (no stdlib PDF tables). Extract synonyms `variable`/`comment` only so Table 1 can extract |

## Project Structure

```text
src/rh_mod_skills/pdf_tables.py
src/rh_mod_skills/commands/ingest.py
tests/unit/test_ingest.py
tests/unit/test_ingest_pdf.py
pyproject.toml
```

**Structure Decision**: PDF detection lives in `pdf_tables.py`; ingest remains the write owner. No curated skill until this CLI path exists.

## Complexity Tracking

> No constitution violations. `pdfplumber` is an allowed extra dependency (stdlib cannot reconstruct PDF tables).
