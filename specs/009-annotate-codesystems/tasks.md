# Tasks: annotate code systems

**Input**: Design documents from `/specs/009-annotate-codesystems/`  
**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli-schema.md](./contracts/cli-schema.md)

## Phase 1: Foundational

- [x] T001 Expand alias table in `src/rh_mod_skills/terminology.py` (`icd-10-cm`, `rxnorm`, `ucum`; `all` is plan-only and not a URI)
- [x] T002 Accept new `--system` values in `src/rh_mod_skills/commands/annotate.py`; default `all`; unknown still fails

## Phase 2: User Story 1 — Plan names (P1)

- [x] T003 [US1] Tests: `--system rxnorm|ucum|icd-10-cm` recorded; combinable; unknown fails; default all
- [x] T004 [US1] Help text lists the new aliases

## Phase 3: User Story 2 — Enrich aliases (P1)

- [x] T005 [US2] Tests: enrich `rxnorm|…`, `ucum|…`, `icd-10-cm|…` store canonical URIs; `http…` pass-through
- [x] T006 [US2] `parse_candidate_flag` expands those aliases

## Phase 4: User Story 3 — `all` (P2)

- [x] T007 [US3] Tests: plan `--system all`; enrich mixed `http` URIs; `--candidate all|…` fails
- [x] T008 [US3] Plan accepts `all`; enrich rejects `all` as a candidate system

## Phase 5: Polish

- [x] T009 Update `skills/.curated/rh-mod-annotate/SKILL.md` MCP map (rxnorm, ucum, icd-10-cm, all)
- [x] T010 [P] Update `AGENTS.md` recent changes
- [x] T011 `uv run pytest`
