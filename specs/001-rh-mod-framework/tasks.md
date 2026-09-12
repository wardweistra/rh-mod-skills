# Tasks: RH Mod Skills Framework (workspace skeleton)

**Input**: Design documents from `/specs/001-rh-mod-framework/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/  
**Slice**: `init`, `tracking.yaml`, `models/<id>/`, read-only `status`. Ingest (US1 scenario 2) and US2/US3 are **002+**.

**Tests**: Required — CLI contracts, tracking events, and safety (tool-repo refusal).

**Organization**: Tasks grouped by the 001 slice of US1 (bootstrap) and US4 (status).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 = init workspace, US4 = status

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Test consumer fixture and schema sync already expected by the Makefile.

- [x] T001 Add `tests/conftest.py` with `tmp_consumer` (`RH_REPO_ROOT` → tmp dir, no pre-existing `tracking.yaml`)
- [x] T002 [P] Confirm `schemas/` and `src/rh_mod_skills/schemas/` exist so `make sync-schemas` has a target

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared path/tracking helpers every command uses. Blocks US1 and US4.

- [x] T003 Create `schemas/tracking-schema.yaml` from `specs/001-rh-mod-framework/contracts/tracking-schema.md` (`models:` not `topics:`)
- [x] T004 Copy schema into `src/rh_mod_skills/schemas/tracking-schema.yaml` (`make sync-schemas`)
- [x] T005 Implement `src/rh_mod_skills/common.py`: consumer root (`RH_REPO_ROOT` / `tracking.yaml` walk / cwd), tool-repo refusal helper, kebab-case check, SHA-256, ISO timestamps, ruamel lock + atomic write, `append_root_event` / `append_model_event`, `ensure_tracking`, `require_model`
- [x] T006 Add unit tests for consumer-root and kebab-case helpers in `tests/unit/test_common.py`

**Checkpoint**: Helpers exist; no CLI commands yet besides `version`

---

## Phase 3: User Story 1 - Bootstrap a model workspace (Priority: P1) 🎯 MVP

**Goal**: `rh-mod-skills init <model>` creates `models/<id>/` and appends `model_created`.

**Independent Test**: `init nkr-breast` in a tmp consumer creates dirs + `tracking.yaml` with `model_created`; duplicate init fails; tool-repo cwd refuses.

### Tests for User Story 1

- [x] T007 [P] [US1] Add `tests/unit/test_init.py`: kebab-case, duplicate, flags, directory tree (`sources/`, `structured/`, `computable/`, `process/plans/`), `MODEL.md`, events, tool-repo refusal, example-project allowed

### Implementation for User Story 1

- [x] T008 [US1] Implement `src/rh_mod_skills/commands/init.py` per `contracts/cli-schema.md`
- [x] T009 [US1] Register `init` on the Click group in `src/rh_mod_skills/cli.py`

**Checkpoint**: `uv run rh-mod-skills init nkr-breast` works from `example-project/` or `RH_REPO_ROOT`

---

## Phase 4: User Story 4 - Status across the model lifecycle (Priority: P2)

**Goal**: Read-only `status` reports `initialized` and next step `ingest`; never mapping.

**Independent Test**: After init, `status` and `status nkr-breast` print stage initialized and next ingest; missing tracking errors; no events appended.

### Tests for User Story 4

- [x] T010 [P] [US4] Add `tests/unit/test_status.py`: missing tracking, unknown model, list vs single, next=ingest, does not write tracking, does not mention mapping/FML/StructureMap

### Implementation for User Story 4

- [x] T011 [US4] Implement `src/rh_mod_skills/commands/status.py` per `contracts/cli-schema.md`
- [x] T012 [US4] Register `status` on the Click group in `src/rh_mod_skills/cli.py`

**Checkpoint**: `status` after init names ingest as next

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T013 [P] Run `uv run pytest` and fix failures
- [x] T014 [P] Validate `specs/001-rh-mod-framework/quickstart.md` against `example-project/`
- [x] T015 Update `specs/001-rh-mod-framework/README.md` to point at `tasks.md`

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 (blocks stories) → Phase 3 (US1 MVP) → Phase 4 (US4) → Phase 5
- US2 (extract/annotate) and US3 (specify/formalize) are **not** in this file
- US1 ingest scenarios belong to **002**

### Parallel opportunities

- T002 with T001
- T007 with T008 (TDD: write tests first, then init)
- T010 with T011 after init exists
- T013/T014 after commands land

### MVP

Phases 1–3 (`init` only). Status can follow immediately (same helpers).

## Notes

- Do not import `rh-skills`
- Do not create `topics/`
- Do not parse Excel/PDF in this feature
- Do not author `skills/.curated/*`
