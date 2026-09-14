# Tasks: rh-mod-extract

**Input**: `/specs/003-rh-mod-extract/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required (CLI contract, IKNL proving, PDF-only fail-closed, verify, replace gate).

Implemented 2026-09-13.

## Phase 1: Setup

- [x] T001 Add `schemas/inventory-schema.yaml` and bundle via `make sync-schemas`

## Phase 2: Foundational

- [x] T002 Implement `src/rh_mod_skills/commands/extract.py` (plan/approve/implement/verify, column detection, provenance, `--replace`)
- [x] T003 Register extract on `src/rh_mod_skills/cli.py`

## Phase 3: User Story 1 — IKNL inventory (P1)

- [x] T004 [US1] Tests in `tests/unit/test_extract.py`: plan 5 entities / 153 elements, unapproved implement writes nothing, approved implement writes inventory with `unknown` types, status next=`annotate`, `inventory_derived`

## Phase 4: User Story 2 — Reviewer edits (P1)

- [x] T005 [US2] Drop `gebdat` + rename entity; implement must not restore dropped rows; verify reports plan-excluded

## Phase 5: User Story 3 — PDF-only, verify, replace (P1)

- [x] T006 [US3] ENCR PDF-only extract plan fails with no plan file; verify twice adds zero events; `--replace` required to overwrite inventory; homonyms kept distinct

## Phase 6: User Story 4 — Value domains (P2)

- [x] T007 [US4] IKNL writes no `value-domains.yaml`; a two-sheet code-list fixture writes domains + element ref

## Phase 7: Polish

- [x] T008 Run extract on `example-project/nkr-breast`; confirm ENCR still fail-closed
- [x] T009 `uv run pytest` passes
