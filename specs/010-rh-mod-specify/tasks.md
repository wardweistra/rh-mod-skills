# Tasks: rh-mod-specify

**Input**: Design documents from `/specs/010-rh-mod-specify/`  
**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli-schema.md](./contracts/cli-schema.md)

## Phase 1: Foundational

- [x] T001 Add `schemas/logical-model-schema.yaml` and `make sync-schemas`
- [x] T002 Implement `specify plan|approve|implement|verify` in `src/rh_mod_skills/commands/specify.py`; register on `cli.py`

## Phase 2: User Story 1 — Plan (P1)

- [x] T003 [US1] Tests: annotate-complete → plan with all paths, provenance, binding snapshot; F/A → unknown; recognized type copied; incomplete annotate fails
- [x] T004 [US1] Plan fail-closed when undecided paths remain

## Phase 3: User Story 2 — Implement (P1)

- [x] T005 [US2] Tests: implement without approve fails; approved implement writes LM; inventory/bindings unchanged; status next formalize
- [x] T006 [US2] Implement copies approved plan; appends `model_specified`

## Phase 4: User Story 3 — Verify (P2)

- [x] T007 [US3] Tests: verify twice idempotent; path mismatch blocking; unknown types advisory
- [x] T008 [US3] Verify does not mutate tracking

## Phase 5: Polish

- [x] T009 Author `skills/.curated/rh-mod-specify/` (SKILL.md + reference.md + examples); update status skill “specify” mapping
- [x] T010 [P] AGENTS.md, README, GETTING_STARTED, WORKFLOW; `test_skills_pack.py` full pack
- [x] T011 `uv run pytest`
