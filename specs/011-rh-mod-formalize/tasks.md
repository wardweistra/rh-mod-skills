# Tasks: rh-mod-formalize

**Input**: Design documents from `/specs/011-rh-mod-formalize/`

## Phase 1: Foundational

- [x] T001 Implement `formalize plan|approve|implement|verify` in `src/rh_mod_skills/commands/formalize.py`; register on `cli.py`

## Phase 2: User Story 1 — Plan (P1)

- [x] T002 [US1] Tests: specified LM → draft plan with canonical/version; missing LM fails
- [x] T003 [US1] Plan lists unknown-datatype paths and unknown-cardinality count

## Phase 3: User Story 2 — Implement (P1)

- [x] T004 [US2] Tests: unapproved implement fails; unknown datatype fails; approved implement writes SD kind=logical, VS for bound only, snapshot checksums; status formalized
- [x] T005 [US2] Implement applies 0..1 default; no mapping files; LM unchanged

## Phase 4: User Story 3 — Verify (P2)

- [x] T006 [US3] Tests: verify twice idempotent; checksum tamper fails; kind check
- [x] T007 [US3] Verify does not mutate tracking

## Phase 5: Polish

- [x] T008 Author `skills/.curated/rh-mod-formalize/`; update status skill
- [x] T009 [P] AGENTS.md, README, GETTING_STARTED, WORKFLOW; skills pack test
- [x] T010 `uv run pytest`
