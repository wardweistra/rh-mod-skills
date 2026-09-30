# Tasks: entity graph + mapping/binding split

**Input**: Design documents from `/specs/014-entity-and-binding/`  
**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli-schema.md](./contracts/cli-schema.md), [quickstart.md](./quickstart.md)

**Tests**: Include pytest + CliRunner coverage for every CLI/schema behavior change (constitution III; repo tasks convention).

**Organization**: Epic **A** (US1 → US2) before Epic **B** (US3 → US4). Plan phases A1–A3 map to US1/US2; B1–B3 map to US3/US4.

**Format**: `- [ ] [ID] [P?] [Story?] Description with file path`

---

## Phase 1: Setup

**Purpose**: Confirm design anchors and test layout before schema/CLI edits

- [x] T001 Confirm touch set from [plan.md](./plan.md) and create `tests/fixtures/bindings-2/` directory for synthetic mini consumers (mapped-only + later multi-LM)
- [x] T002 [P] Update `specs/014-entity-and-binding/README.md` status to note tasks ready / implementation not started

---

## Phase 2: Foundational (blocking)

**Purpose**: Schema 2.0 + shared fail-closed loaders. **No user story until this completes.**

- [x] T003 Bump `schemas/bindings-schema.yaml` to `schema_version: "2.0"` with `status` (`mapped`|`unbound`), `mappings[]` (system/code/display/decision), optional `value_set` null/object, `reason`; forbid root-level singleton `system`/`code`/`strength`
- [x] T004 [P] Bump `schemas/logical-model-schema.yaml` to `schema_version: "2.0"` element snapshot fields `mappings` / `value_set` / `reason` (keep `entities[]` for Epic A; reserve/document `logical_models[]` for Epic B without requiring it yet)
- [x] T005 Add shared bindings 2.0 load/validate helpers (fail closed on 1.0 singleton rows with re-annotate message; duplicate system URI fails) used by annotate/specify/formalize — place next to existing loaders in `src/rh_mod_skills/` (e.g. extend `commands/annotate.py` helpers or a small shared module already used by stages)
- [x] T006 Run schema sync if the repo uses it (`make sync-schemas` or documented equivalent); ensure example-project / fixtures are not silently auto-migrated

**Checkpoint**: Schemas and fail-closed 1.0 detection exist; user stories can start

---

## Phase 3: User Story 1 — Multi-system mappings without inventing a ValueSet (Epic A / P1) 🎯 MVP

**Goal**: Annotate persists `mappings[]`; specify copies snapshots; formalize emits `ElementDefinition.mapping` only; no singleton ValueSet; clean break on legacy bindings.

**Independent Test**: Mini consumer — two mappings on one path, no `value_set` → formalize SD has mapping metadata and **zero** ValueSet for that path; 1.0 bindings file fails closed.

### Tests for User Story 1

- [x] T007 [P] [US1] Tests in `tests/unit/test_annotate.py` (or new `tests/unit/test_annotate_mappings.py`): implement writes `schema_version: "2.0"` with two systems in `mappings[]`; no `value_set` from mappings; duplicate system fails; unbound clears mappings + requires reason; 1.0 singleton row rejected on verify/implement
- [x] T008 [P] [US1] Tests in `tests/unit/test_specify.py`: annotate-complete 2.0 → plan/LM element snapshots carry `mappings[]` (not root system/code/strength); incomplete/undecided still fails
- [x] T009 [P] [US1] Tests in `tests/unit/test_formalize.py`: mappings-only element → SD has `StructureDefinition.mapping` + `ElementDefinition.mapping`; no ValueSet/binding for that path; no ConceptMap; 1.0 LM/bindings fail closed

### Implementation for User Story 1

- [x] T010 [US1] Update annotate plan/enrich/approve/implement/verify in `src/rh_mod_skills/commands/annotate.py` for `mappings[]` upsert-by-system; remove strength-on-coding; write bindings 2.0; status complete = every path `mapped`|`unbound`
- [x] T011 [US1] Update `src/rh_mod_skills/annotate_review.py` export/import so picks can accept multiple systems without coercing to one coding
- [x] T012 [US1] Update specify plan/implement/verify in `src/rh_mod_skills/commands/specify.py` to copy mapping/unbound snapshots into LM `entities[]` elements (`schema_version: "2.0"`)
- [x] T013 [US1] Update formalize in `src/rh_mod_skills/commands/formalize.py`: emit mapping identities + `ElementDefinition.mapping`; **stop** singleton-VS-from-mapping; introduce `canonical_base` on formalize plan (derive single SD URL `{canonical_base}/StructureDefinition/{model}` for Epic A one-SD path); drop sole “last segment == tracking id” check in favor of derived URL rules from research §8
- [x] T014 [US1] Update curated skill `skills/.curated/rh-mod-annotate/` (and specify/formalize skill notes as needed) for map-vs-bind; CLI still owns writes
- [x] T015 [US1] Add/adjust mini fixture under `tests/fixtures/bindings-2/` for mapped-only path used by US1 tests

**Checkpoint**: MVP — multi-system meaning without fake ValueSets; legacy 1.0 fails closed

---

## Phase 4: User Story 2 — Optional ValueSet binding with strength (Epic A phase 2 / P2)

**Goal**: Author `value_set` independently; formalize emits VS + binding only when present; verify distinguishes mapped vs VS-bound vs unbound.

**Independent Test**: Path with `value_set.strength: preferred` + two concepts → one ValueSet + binding; mappings-only path still has no VS.

### Tests for User Story 2

- [ ] T016 [P] [US2] Tests in `tests/unit/test_annotate.py` / mappings test module: implement persists authored `value_set`; unbound still forbids mappings+value_set; strength only on `value_set`
- [ ] T017 [P] [US2] Tests in `tests/unit/test_formalize.py`: `value_set` present → ValueSet + ElementDefinition.binding; mappings-only still no VS; verify counts mapped vs value_set-bound vs unbound
- [ ] T018 [P] [US2] Tests in `tests/unit/test_verify.py` (coordinator) if counts surface there — mapped / VS-bound / unbound advisory or reported fields

### Implementation for User Story 2

- [ ] T019 [US2] Extend annotate plan/implement/verify (+ export/import if needed) in `src/rh_mod_skills/commands/annotate.py` and `annotate_review.py` for optional `value_set` authoring; annotate-complete allows decided = mappings and/or value_set (research §4 — collapse `mapped`→`decided` if doing in one pass)
- [ ] T020 [US2] Specify copies `value_set` snapshots in `src/rh_mod_skills/commands/specify.py`
- [ ] T021 [US2] Formalize builds multi-concept ValueSet + binding only when `value_set` present in `src/rh_mod_skills/commands/formalize.py`; plan counts include value_set-bound
- [ ] T022 [US2] Update `src/rh_mod_skills/commands/verify.py` and skills (`rh-mod-annotate`, `rh-mod-formalize`) so mapped vs VS-bound vs unbound are distinct

**Checkpoint**: Epic A complete (mappings-first + optional VS)

---

## Phase 5: User Story 3 — Regroup into multiple logical models with references (Epic B / P1)

**Goal**: Specify-owned `logical_models[]` + `inventory_path` + `Reference`/`reference.target`; extract unchanged; default single LM when reviewer does nothing.

**Independent Test**: Split into ≥2 LMs + one Reference; 100% inventory coverage via `inventory_path`; inventory bytes unchanged.

### Tests for User Story 3

- [ ] T023 [P] [US3] Tests in `tests/unit/test_specify.py`: plan/implement write `logical_models[]`; default one LM id = tracking model id; Reference requires `reference.target`; verify fails on missing/duplicate `inventory_path` or unknown target; extract inventory file hash unchanged
- [ ] T024 [P] [US3] Mini multi-LM fixture under `tests/fixtures/bindings-2/` (Patient + Hospital + Reference) for specify tests

### Implementation for User Story 3

- [ ] T025 [US3] Finalize `schemas/logical-model-schema.yaml` for required `logical_models[]`, `inventory_path`, `reference.target`, optional `root`
- [ ] T026 [US3] Implement specify plan regroup surface + implement/verify in `src/rh_mod_skills/commands/specify.py` (CLI persists; no extract clinical regroup)
- [ ] T027 [US3] Update `skills/.curated/rh-mod-specify/` to propose Patient/diagnosis/hospital-style splits and Reference edges onto the plan YAML only

**Checkpoint**: L2 multi-entity graph ready; formalize still may be single-SD until US4

---

## Phase 6: User Story 4 — N StructureDefinitions + one IG (Epic B / P1)

**Goal**: One SD per LM under `{canonical_base}/StructureDefinition/{lm-id}`; References target LM canonicals; snapshot lists all; `ig sync` one IG lists all SDs; no ConceptMap.

**Independent Test**: Three LMs + `canonical_base: https://encr.eu/fhir/recommendations` → three SD URLs (`encr-patient`, `encr-diagnosis`, `encr-hospital`); `ig sync` lists all three; no ConceptMap files.

### Tests for User Story 4

- [ ] T028 [P] [US4] Tests in `tests/unit/test_formalize.py`: N SD files; canonical last segment = lm-id; Reference targetProfile/canonical; snapshot has `canonical_base` + all files; mappings still emit; ConceptMap absent
- [ ] T029 [P] [US4] Tests in `tests/unit/test_ig.py`: `ig sync` copies all SDs into `input/models/` and IG `definition.resource` lists them; still one IG tree under tracking model

### Implementation for User Story 4

- [ ] T030 [US4] Multi-SD emit + snapshot in `src/rh_mod_skills/commands/formalize.py` from `logical_models[]` + `canonical_base`; path segments ≤ 64 still enforced
- [ ] T031 [US4] Update `src/rh_mod_skills/commands/ig.py` for multi-SD resource listing (one IG per tracking model)
- [ ] T032 [US4] Update verify coordinator / formalize verify coverage across multi-LM in `src/rh_mod_skills/commands/verify.py` and `formalize.py`
- [ ] T033 [US4] Update skills `skills/.curated/rh-mod-formalize/` and `skills/.curated/rh-mod-ig/` for multi-SD + canonical_base (ENCR recommendations as proving example, not hardcoded-only validation)

**Checkpoint**: Full Epic A+B outcome deliverable

---

## Phase 7: Polish & cross-cutting

- [ ] T034 [P] Update `AGENTS.md` Recent Changes to reflect implemented behavior (replace “CLI not implemented yet”)
- [ ] T035 [P] Update `docs/WORKFLOW.md` / `docs/GETTING_STARTED.md` only where bindings/LM/formalize/IG docs would mislead (map vs bind; multi-LM)
- [ ] T036 [P] Refresh in-repo example-project bindings/LM only if tests require — prefer re-annotate/re-specify in fixtures over compat loaders
- [ ] T037 Confirm no migrate CLI / `--compat` / ConceptMap writers were added
- [ ] T038 Run `uv run pytest` green; spot-check [quickstart.md](./quickstart.md) command sequence against CliRunner fixtures
- [ ] T039 Mark `specs/014-entity-and-binding/spec.md` / README status Implemented when all US checkpoints pass

---

## Dependencies & execution order

### Phase dependencies

- **Setup (1)** → **Foundational (2)** → **US1 (3)** → **US2 (4)** → **US3 (5)** → **US4 (6)** → **Polish (7)**
- Foundational **blocks** all user stories
- **US2 depends on US1** (needs mappings-first formalize behavior)
- **US3 depends on US1** (annotate-complete 2.0); preferably after US2 so snapshots include `value_set`, but US3 can start after US1 if `value_set` remains null
- **US4 depends on US3** (needs `logical_models[]`) and on US1 mapping emission

### User story mapping to plan phases

| Story | Plan phase | Epic |
|-------|------------|------|
| US1 | A1 + A2 | A |
| US2 | A3 | A |
| US3 | B1 | B |
| US4 | B2 + B3 | B |

### Parallel opportunities

- T003/T004 schemas in parallel after T001
- US1 tests T007/T008/T009 in parallel before/with implementation
- US2 tests T016–T018 in parallel
- US3 tests T023/T024 in parallel
- US4 tests T028/T029 in parallel
- Polish T034–T036 in parallel
- **Do not** parallelize Epic B before Epic A MVP (US1) is green

### Parallel example: User Story 1 tests

```bash
# After foundational (T003–T006):
Task: "US1 annotate mappings tests in tests/unit/test_annotate*.py"
Task: "US1 specify snapshot tests in tests/unit/test_specify.py"
Task: "US1 formalize mapping-only tests in tests/unit/test_formalize.py"
```

---

## Implementation strategy

### MVP first (US1 only)

1. Phase 1 Setup + Phase 2 Foundational  
2. Phase 3 US1 (annotate mappings → specify snapshot → formalize ElementDefinition.mapping, no VS)  
3. **STOP and VALIDATE** independent test for US1  
4. Demo: multi-system meaning without fake ValueSets  

### Incremental delivery

1. US1 MVP →  
2. US2 optional ValueSets → Epic A done →  
3. US3 specify multi-LM →  
4. US4 multi-SD + IG →  
5. Polish  

### Suggested first implementable slice

**T003–T015 (Foundational + US1)** — schema 2.0, annotate `mappings[]`, specify snapshot copy, formalize mapping metadata, fail closed on 1.0, skill map-vs-bind. No `value_set` UX, no multi-LM yet.

---

## Notes

- No product code in the Speckit tasks *generation* turn; this file is the queue for `/speckit.implement`
- No migrate CLI, `--compat`, ConceptMap, or extract clinical regroup tasks on purpose
- ENCR recommendations URLs are proving examples; validation is pattern/`canonical_base` http(s), not ENCR-only hardcoding
- Speckit `check-prerequisites.sh` may fail on work branch `cursor/entity-mapping-specs-bdd1`; feature dir remains `specs/014-entity-and-binding/`
