# Tasks: rh-mod-verify

**Input**: Design documents from `/specs/012-rh-mod-verify/`

## Phase 1: Foundational

- [x] T001 Implement `rh-mod-skills verify [model]` in `src/rh_mod_skills/commands/verify.py`; register on `cli.py`

## Phase 2: User Story 1 — Formalized health check (P1)

- [x] T002 [US1] Tests: formalized mini model → pass twice; tracking unchanged; coverage + unbound + validator-not-run
- [x] T003 [US1] Checksum tamper fails coordinator; no tracking write

## Phase 3: User Story 2 — Mid-lifecycle skip (P1)

- [x] T004 [US2] Tests: extracted-only skips specify/formalize and can pass; empty portfolio matches status guidance

## Phase 4: User Story 3 — Portfolio (P2)

- [x] T005 [US3] Tests: no-arg reports two models; one blocking model fails overall

## Phase 5: Polish

- [x] T006 Author `skills/.curated/rh-mod-verify/`; update status skill (`Next: verify`)
- [x] T007 [P] AGENTS.md, README, GETTING_STARTED, WORKFLOW; skills pack test
- [x] T008 `uv run pytest`
