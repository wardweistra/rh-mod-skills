# Tasks: annotate review

**Input**: Design documents from `/specs/008-annotate-review/`  
**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli-schema.md](./contracts/cli-schema.md)

## Phase 1: Foundational

- [x] T001 Add `src/rh_mod_skills/annotate_review.py` (escape HTML, render page, load picks, apply picks by path)
- [x] T002 Wire `annotate export` and `annotate import --from` in `src/rh_mod_skills/commands/annotate.py` (no tracking events, no bindings write)

## Phase 2: User Story 1 — Export HTML (P1)

- [x] T003 [US1] Tests in `tests/unit/test_annotate_review.py`: export writes HTML with path/candidates; fails without plan; empty candidates still list unbound/skip
- [x] T004 [US1] Export command writes `process/plans/annotate-review.html`

## Phase 3: User Story 2 — Import accept by rank (P1)

- [x] T005 [US2] Tests: accept pick 1/2; unknown path fails; implement without approve fails; bindings unchanged
- [x] T006 [US2] Import copies ranked candidate into `chosen`, sets `decision: accept`, `status: draft`

## Phase 4: User Story 3 — Unbound / skip / replace / un-approve (P2)

- [x] T007 [US3] Tests: unbound+reason; reject; replace chosen; approved→draft; unbound without reason fails; model mismatch fails
- [x] T008 [US3] Apply those decisions in `annotate_review.py`

## Phase 5: Polish

- [x] T009 Update `skills/.curated/rh-mod-annotate/SKILL.md` (export after enrich; import; do not write HTML)
- [x] T010 [P] Update `AGENTS.md` recent changes; help lists export/import
- [x] T011 `uv run pytest`
