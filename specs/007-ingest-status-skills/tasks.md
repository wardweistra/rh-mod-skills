# Tasks: ingest and status skills

**Input**: Design documents from `/specs/007-ingest-status-skills/`  
**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli-schema.md](./contracts/cli-schema.md)

**Tests**: File-presence tests for skill packs (plan); no CLI contract change.

## Phase 1: Setup

- [x] T001 Create `skills/.curated/rh-mod-ingest/examples/` and `skills/.curated/rh-mod-status/examples/` directories

## Phase 2: Foundational

- [x] T002 Add `tests/unit/test_skills_pack.py` asserting constitution packs exist (`SKILL.md`, `reference.md`, examples) for `rh-mod-ingest` and `rh-mod-status`, and that extract/annotate remain SKILL.md-only

## Phase 3: User Story 1 — IKNL Excel ingest skill (P1) 🎯 MVP

**Independent Test**: Agent following only `rh-mod-ingest` can plan/implement IKNL Excel via CLI; skill forbids hand-written projections and Markdown L1.

- [x] T003 [US1] Author `skills/.curated/rh-mod-ingest/SKILL.md` (plan → approve → implement → verify; CLI writes; no init; no Markdown/OCR; no source inspection)
- [x] T004 [P] [US1] Author `skills/.curated/rh-mod-ingest/reference.md` (plan fields, projection shape, events, origin URL)
- [x] T005 [P] [US1] Author `skills/.curated/rh-mod-ingest/examples/excel-plan.md` (IKNL `nkr-breast` walkthrough)

## Phase 4: User Story 2 — ENCR PDF table review (P1)

**Independent Test**: Skill reviews table include/exclude; register-only skip reasons; refuses OCR/Markdown.

- [x] T006 [US2] Extend `skills/.curated/rh-mod-ingest/SKILL.md` PDF table review and skip-reason path
- [x] T007 [US2] Extend `skills/.curated/rh-mod-ingest/reference.md` with skip reasons and `tables[].decision`
- [x] T008 [US2] Author `skills/.curated/rh-mod-ingest/examples/pdf-tables.md` (ENCR Table 1/2 include; companion skipped)

## Phase 5: User Story 3 — Status skill (P1)

**Independent Test**: `rh-mod-status` runs CLI status, one-sentence skill mapping, no second menu, drift → ingest verify.

- [x] T009 [US3] Author `skills/.curated/rh-mod-status/SKILL.md`
- [x] T010 [P] [US3] Author `skills/.curated/rh-mod-status/reference.md` (stage/next → skill table)
- [x] T011 [P] [US3] Author `skills/.curated/rh-mod-status/examples/output.md`

## Phase 6: Polish

- [x] T012 [P] Update `README.md` and `docs/GETTING_STARTED.md` and `docs/WORKFLOW.md` and `AGENTS.md` for ingest/status skills
- [x] T013 `uv run pytest`

## Dependencies

T001 → T002 (tests fail until packs exist; write tests then skills, or skills then tests). US1 SKILL.md before US2 extensions. US3 independent of US1/US2 after T001.

## MVP

T001–T005 (Excel ingest skill pack + file-presence test).
