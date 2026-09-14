# Tasks: rh-mod-annotate

**Input**: Design documents from `/specs/005-rh-mod-annotate/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-schema.md, quickstart.md

**Tests**: Required (CLI contract, fake ReasonHub, fail-closed missing URL, reject/unbound/replace, merge/`--replace`, verify, status next, ENCR one-element).

Implemented 2026-09-14.

**Organization**: User stories from spec.md. Do not author `skills/.curated/rh-mod-annotate` until this CLI exists.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 from spec.md
- Include exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Schema on the bundle path extract/ingest already use

- [x] T001 Copy `schemas/bindings-schema.yaml` to `src/rh_mod_skills/schemas/bindings-schema.yaml` via `make sync-schemas` (keep `schemas/README.md` in sync)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Terminology client, command group, status next-step. No user story work until this is done.

**⚠️ CRITICAL**: Blocks all user stories

- [x] T002 Implement `TerminologyClient` protocol and `HttpxTerminologyClient` in `src/rh_mod_skills/terminology.py` (`RH_REASONHUB_URL` required, optional `RH_REASONHUB_TOKEN`; `--system` map `snomed`/`loinc`/`icd-10`; `top_k=5`; raise on missing URL or HTTP error; do not invent codes)
- [x] T003 [P] Add injectable fake client returning ≤5 ranked SNOMED hits for `"Geslacht"` (and empty list when asked) in `tests/unit/annotate_fakes.py`
- [x] T004 Scaffold `annotate` Click group (`plan` / `approve` / `implement` / `verify`) in `src/rh_mod_skills/commands/annotate.py` and register it on `src/rh_mod_skills/cli.py` so `--help` lists `annotate`
- [x] T005 Change `next_step` in `src/rh_mod_skills/commands/status.py` so next is `annotate` while any inventory path is undecided and `specify` only when every path is bound or unbound; keep stage `annotating` after `annotate_planned` / `element_bound`; extend `tests/unit/test_status.py`

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 — Bind a first slice of NKR breast (Priority: P1) 🎯 MVP

**Goal**: `--element gesl` → plan (≤5 candidates) → approve → implement writes one bound row; 152 others stay undecided; status next stays `annotate`; no logical-model / FHIR.

**Independent Test**: Extracted `nkr-breast` in `tmp_consumer`, fake ReasonHub: plan `gesl`, accept, implement → `structured/bindings.yaml` has `patientgegevens.gesl` only.

### Tests for User Story 1

- [x] T006 [P] [US1] Failing tests in `tests/unit/test_annotate.py`: neither `--element` nor `--all-undecided` fails; both together fail; `--element gesl` writes `process/plans/annotate-plan.yaml` (`status: draft`, query `Geslacht`, ≤5 candidates, path `patientgegevens.gesl`); inventory unchanged; unapproved implement writes no bindings and no `element_bound`; accept + implement binds only `gesl` with strength `example`; no `logical-model.yaml`; events `annotate_planned` then batched `element_bound`; status next=`annotate`

### Implementation for User Story 1

- [x] T007 [US1] Resolve `--element` (unique `id` or exact `path`; duplicate id without path fails closed) in `src/rh_mod_skills/commands/annotate.py`
- [x] T008 [US1] `annotate plan` reads `structured/inventory.yaml`, calls `TerminologyClient.search`, writes draft `annotate-plan.yaml`, appends `annotate_planned`; fail if no inventory or extract/ingest not clean
- [x] T009 [US1] `annotate approve` sets plan `status: approved`
- [x] T010 [US1] `annotate implement` on `decision: accept` writes `structured/bindings.yaml` (chosen or `candidates[0]`), lists the file on `models[].structured`, appends one batched `element_bound`; fail if plan missing or not approved; do not write FHIR

**Checkpoint**: US1 independently testable (`uv run pytest tests/unit/test_annotate.py`)

---

## Phase 4: User Story 2 — Reviewer rejects, replaces, or leaves unbound (Priority: P1)

**Goal**: Implement follows plan decisions only. Unbound+reason is durable. Reject/pending skip the row. Replace uses reviewer `chosen`.

**Independent Test**: Approved plan unbinds `gebdat` with reason and replaces `gesl`; bindings show those two rows; verify does not treat unbound-with-reason as missing.

### Tests for User Story 2

- [x] T011 [P] [US2] Tests in `tests/unit/test_annotate.py`: `unbound` + reason → unbound row; `replace` + `chosen` → replacement not candidate; `reject` and `pending` → no row, element stays undecided; implement does not auto-pick SNOMED for pending elements

### Implementation for User Story 2

- [x] T012 [US2] Decision branches in `src/rh_mod_skills/commands/annotate.py` implement: accept / replace (`chosen` required) / unbound (`reason` required) / skip pending+reject; accept with empty candidates fails

**Checkpoint**: US1 and US2 both pass

---

## Phase 5: User Story 3 — Plan, verify, refuse invented codes (Priority: P1)

**Goal**: No invented codes. Verify is read-only. Merge by path; `--replace` wipes. `--all-undecided` and `--system` work.

**Independent Test**: Plan without `RH_REASONHUB_URL` fails and writes no candidates. Verify twice adds zero tracking events. Merge keeps other rows; `--replace` does not.

### Tests for User Story 3

- [x] T013 [P] [US3] Tests in `tests/unit/test_annotate.py`: missing URL → plan fails, no `*dat` invention; fake zero hits → plan writes `candidates: []`; verify twice same bound/unbound/undecided counts and zero new events; re-implement one path merges; `--replace` rewrites whole file; pending/reject must not delete an existing row; no inventory → fail with extract guidance; `--all-undecided` covers remaining paths (warn if >25); `--system loinc` recorded on the plan; unknown `--element` fails; homonym id without path fails

### Implementation for User Story 3

- [x] T014 [US3] `annotate verify` in `src/rh_mod_skills/commands/annotate.py` reports bound / unbound / undecided vs inventory; blocking: bound path not in inventory, unbound missing reason; must not mutate `tracking.yaml`
- [x] T015 [US3] Merge-by-path, `--replace`, `--all-undecided`, repeatable `--system`, extract-drift fail-closed in `src/rh_mod_skills/commands/annotate.py`

**Checkpoint**: Fail-closed terminology and verify are done

---

## Phase 6: User Story 4 — ENCR Table 1 English labels (Priority: P2)

**Goal**: Same gated flow on `encr-standard-dataset`. English labels still go through ReasonHub; not auto-bound.

**Independent Test**: After ENCR extract, annotate one Table 1 element through plan → approve → implement; other ENCR elements remain undecided.

### Tests for User Story 4

- [x] T016 [P] [US4] Test in `tests/unit/test_annotate.py` (reuse ENCR ingest/extract helpers from `tests/unit/test_extract.py`): one Table 1 `--element` (path or unique id) with fake client → one bindings row; inventory unchanged; remaining ENCR elements undecided

### Implementation for User Story 4

- [x] T017 [US4] Remove any `nkr-breast`-only assumptions in `src/rh_mod_skills/commands/annotate.py` so ENCR works without extra flags

**Checkpoint**: Annotate is model-agnostic

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Proving consumer + green suite. Still no curated skill.

- [x] T018 [P] If `RH_REASONHUB_URL` is set, run `specs/005-rh-mod-annotate/quickstart.md` against `example-project/` `nkr-breast --element gesl`; if unset, skip live lookup (do not invent codes)
- [x] T019 Update `specs/005-rh-mod-annotate/README.md` and `AGENTS.md` Recent Changes once CLI exists (annotate implemented; skill still not authored)
- [x] T020 `uv run pytest` passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Start immediately
- **Foundational (Phase 2)**: Depends on T001 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP
- **US2 (Phase 4)**: Depends on US1 implement path (same `annotate.py`)
- **US3 (Phase 5)**: Depends on US1 plan/implement; verify can start after T010
- **US4 (Phase 6)**: Depends on US1; should already pass if T017 is a no-op
- **Polish (Phase 7)**: After desired stories (MVP can stop after US1 + T020)

### User Story Dependencies

- **US1 (P1)**: After Phase 2 — no other stories
- **US2 (P1)**: After US1 (extends implement decisions)
- **US3 (P1)**: After US1 (verify/merge/fail-closed); overlaps US2 unbound counts
- **US4 (P2)**: After US1 — same commands, different model

### Parallel Opportunities

- T003 with T002 after T001
- T006 / T011 / T013 / T016 test files can be written in parallel (same `tests/unit/test_annotate.py` — avoid colliding hunks if one person)
- Live quickstart T018 is independent of unit tests once T010 exists

---

## Parallel Example: User Story 1

```bash
# Tests first (must fail against missing behavior):
Task: "Failing gesl plan/approve/implement/status tests in tests/unit/test_annotate.py"

# Then implement in order (same file):
Task: "Resolve --element in src/rh_mod_skills/commands/annotate.py"
Task: "annotate plan + TerminologyClient in src/rh_mod_skills/commands/annotate.py"
Task: "annotate approve + implement accept in src/rh_mod_skills/commands/annotate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1–2 (schema, terminology, command group, status next)
2. Phase 3 US1 (`gesl` slice)
3. **STOP and VALIDATE**: `uv run pytest tests/unit/test_annotate.py tests/unit/test_status.py`
4. Demo: one bound NKR element, next still `annotate`

### Incremental Delivery

1. Setup + Foundational
2. US1 → MVP
3. US2 → reject / replace / unbound
4. US3 → verify, merge, fail-closed, `--all-undecided`
5. US4 → ENCR proving
6. Polish → example-project + AGENTS.md

### Notes

- Inject `TerminologyClient` in tests; never hit the network in unit tests
- Default binding strength `example`
- Key bindings by inventory `path`
- Events: one `annotate_planned` per plan; one batched `element_bound` per implement
- `httpx` is already a dependency — no new package
