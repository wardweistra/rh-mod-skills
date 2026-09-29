# Tasks: rh-mod-ig

**Input**: Design documents from `/specs/013-rh-mod-ig/`

## Phase 1: Foundational

- [x] T001 Implement `ig sync` in `src/rh_mod_skills/commands/ig.py`; register on `cli.py`

## Phase 2: User Story 1 — Scaffold (P1)

- [x] T002 [US1] Tests: snapshot → ig.ini, stubbed scripts, SD in models/, VS in vocabulary/, ImplementationGuide; no snapshot fails; no publisher.jar
- [x] T003 [US1] `status` next remains verify; `ig_synced` appended

## Phase 3: User Story 2 — Idempotent sync (P1)

- [x] T004 [US2] Tests: customized ig.ini preserved; stale managed ValueSet deleted; unmanaged file kept; scripts not re-fetched at same pin

## Phase 4: User Story 3 — Skill (P2)

- [x] T005 Author `skills/.curated/rh-mod-ig/`; mention from formalize skill

## Phase 5: Polish

- [x] T006 [P] AGENTS.md, README, GETTING_STARTED, WORKFLOW; skills pack test
- [x] T007 `uv run pytest`
