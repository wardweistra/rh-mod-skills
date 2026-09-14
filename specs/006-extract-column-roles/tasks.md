# Tasks: extract column roles

**Input**: Design documents from `/specs/006-extract-column-roles/`  
**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli-schema.md](./contracts/cli-schema.md)

## Phase 1: Foundational

- [x] T001 Write 006 spec, plan, research, data-model, CLI contract, quickstart
- [x] T002 Refactor `src/rh_mod_skills/commands/extract.py`: hint helper, `sheets` on plan, `propose_from_projections` uses saved roles, `--rehint`, preserve decisions, duplicate-role fail on implement, verify uses plan roles

## Phase 2: User Story 1 — Plan shows roles, NKR still extracts

- [x] T003 [US1] Assert IKNL extract plan writes `sheets` with id/category/label roles; 153/5 counts unchanged (`tests/unit/test_extract.py`)
- [x] T004 [US1] English NKR and NBCA still extract from hints

## Phase 3: User Story 2 — Remap unrecognized layout

- [x] T005 [US2] Unrecognized CSV: unused roles + row ids; after remap + re-plan, ids/labels follow roles; `--rehint` restores hints

## Phase 4: User Story 3 — Preserve drops, fail duplicates

- [x] T006 [US3] Re-plan keeps a dropped element by provenance
- [x] T007 [US3] Duplicate `id` role: implement fails, no inventory
- [x] T008 [US3] Verify after remap uses plan roles (`missing=0`)

## Phase 5: Polish

- [x] T009 [P] Author `skills/.curated/rh-mod-extract/SKILL.md` (reason about roles; CLI writes)
- [x] T010 Update `AGENTS.md` recent changes; 003 research points at 006 for the role contract
- [x] T011 `uv run pytest`

## Independent tests

- US1: IKNL plan has roles + 153 elements without reviewer edits
- US2: `foo`/`bar` CSV remaps without code changes
- US3: drop survives re-plan; two `id` columns block implement
