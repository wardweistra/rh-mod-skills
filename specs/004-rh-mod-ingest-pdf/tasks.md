# Tasks: rh-mod-ingest-pdf

**Input**: `/specs/004-rh-mod-ingest-pdf/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

Implemented 2026-09-14.

## Phase 1: Setup

- [x] T001 Add `pdfplumber` in `pyproject.toml` (justified extra dependency)

## Phase 2: Foundational

- [x] T002 Implement `src/rh_mod_skills/pdf_tables.py` (text-layer check, extract, merge continued tables, captions, default include/exclude)
- [x] T003 Extend `src/rh_mod_skills/commands/ingest.py` plan/implement/verify for PDF `tables[]` and re-project when checksum matches a prior skip

## Phase 3: User Story 1 — ENCR Table 1 and Table 2 (P1)

- [x] T004 [US1] Tests in `tests/unit/test_ingest_pdf.py`: plan lists Table 1 + Table 2; implement writes two sheets; verify `projection: tables`; unapproved implement writes no projection; no Markdown

## Phase 4: User Story 2 — Exclude junk (P1)

- [x] T005 [US2] Exclude Table 2 in the plan → projection has Table 1 only; all-exclude → `skipped` / `no-tables-approved`

## Phase 5: User Story 3 — Soft-fail (P1)

- [x] T006 [US3] Empty PDF → `no-text-layer`; text-only PDF → `no-tables-detected`; mixed Excel + empty PDF still projects Excel; extract still fails on skip-only models

## Phase 6: User Story 4 — Independent sources (P2)

- [x] T007 [US4] Two PDFs on one plan: proving file projects, empty PDF skips, implement does not roll back the proving projection

## Phase 7: Polish

- [x] T008 Add extract header synonyms `variable` / `comment` in `src/rh_mod_skills/commands/extract.py`
- [x] T009 Re-ingest proving PDF in `example-project/` and extract; update AGENTS.md / README / 002 PDF-skip test
- [x] T010 `uv run pytest` passes
