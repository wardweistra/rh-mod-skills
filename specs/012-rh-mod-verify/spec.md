# Feature Specification: rh-mod-verify

**Feature Branch**: `012-rh-mod-verify`  
**Created**: 2026-09-29  
**Status**: Draft  
**Depends On**: [001 — Framework](../001-rh-mod-framework/), [011 — formalize](../011-rh-mod-formalize/)  
**Input**: Read-only coordinator that runs the stage verifies already present (ingest, extract, annotate, specify, formalize), reports coverage and unbound leftovers, and treats a missing FHIR validator as advisory. Does not write tracking, plans, or artifacts. No mapping. Proving consumer: formalized ENCR.

## Clarifications

### Session 2026-09-29

- Q: Plan → approve → implement? → A: No. Coordinator is read-only like status (001 FR-013).
- Q: Append `validated`? → A: No. Verify must not advance lifecycle. Status next stays `verify` (re-runnable health check).
- Q: Unbound elements? → A: Advisory counts, always visible. Blocking only if a stage verify already blocks (e.g. unbound missing reason, checksum drift).
- Q: Validator binary? → A: Do not run one. Report `validator=not-run` as advisory.
- Q: Stages not yet reached? → A: Skip them. Do not fail a mid-lifecycle model for a missing logical model or StructureDefinition.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One-shot health check on a formalized model (Priority: P1)

An informaticist has formalized ENCR (`status` next is verify). They run the coordinator. It runs every applicable stage verify, prints coverage (inventory / bound / unbound / undecided), and passes if no stage is blocking. Unbound leftovers and validator-not-run are advisory. Tracking is unchanged.

**Why this priority**: This is the 001 cross-cutting verify promise after L3.

**Independent Test**: On a formalized mini model, `rh-mod-skills verify <model>` exits 0, names ingest through formalize as pass, shows unbound count, shows validator-not-run, and leaves tracking bytes identical. Run twice with the same report.

**Acceptance Scenarios**:

1. **Given** a formalized model, **When** verify runs twice, **Then** both pass, both show coverage and advisory unbound/validator-not-run, and tracking is unchanged.
2. **Given** a formalized model with unbound elements, **When** verify runs, **Then** those unbound counts are visible and do not fail the run by themselves.
3. **Given** a Snapshot checksum that no longer matches the file, **When** verify runs, **Then** it fails closed (formalize stage blocking).

---

### User Story 2 - Mid-lifecycle models skip later stages (Priority: P1)

A model that is only extracted should still get ingest + extract (+ annotate coverage if inventory exists) without failing because specify or formalize has not run.

**Why this priority**: Status next is verify only after formalize, but the coordinator is useful earlier (drift, coverage).

**Independent Test**: After extract implement (no specify), verify skips specify and formalize, does not mention a missing StructureDefinition as blocking, and does not write tracking.

**Acceptance Scenarios**:

1. **Given** an extracted model with no logical model, **When** verify runs, **Then** specify and formalize are skipped and the command can pass.
2. **Given** no models / no tracking, **When** verify runs, **Then** it reports the same empty-portfolio guidance as status and does not create files.

---

### User Story 3 - Portfolio verify (Priority: P2)

With no model argument, the coordinator reports every model in tracking (same shape as one-model, repeated). Any blocking model fails the overall run.

**Why this priority**: Matches status’s all-models entry.

**Independent Test**: Two models in one consumer; one healthy extracted, one with ingest checksum drift. Verify with no argument fails; the drifted model is named.

**Acceptance Scenarios**:

1. **Given** two models, **When** verify runs with no argument, **Then** each model is reported.
2. **Given** one of those models has blocking drift, **When** verify runs with no argument, **Then** the overall exit is failure.

---

### Edge Cases

- Initialized model with no sources: all stages skipped; not a blocking failure.
- Stage verify output is preserved (indented) under that stage’s pass/fail line.
- Mapping.xlsx / FML / StructureMap are not created.
- FSH is not generated.
- Re-running after a successful formalize does not change `status` next (still `verify`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Canonical command is `rh-mod-skills verify [model]`. Skills MUST NOT write files. MUST NOT append tracking events (including `validated`).
- **FR-002**: Optional model id. Missing id → every model in tracking (status-like). Unknown id → fail closed.
- **FR-003**: For each model, run existing stage verifies that apply: ingest if sources exist; extract if an extract plan exists; annotate if inventory exists; specify if `logical-model.yaml` exists; formalize if a computable snapshot or StructureDefinition exists. Skip the rest with an explicit skipped marker.
- **FR-004**: Overall failure if any applicable stage verify is blocking. Advisory: unbound count; `validator=not-run`. Unknown cardinality remains the stage’s advisory (specify/formalize), not a new coordinator block.
- **FR-005**: MUST print coverage when inventory exists: inventory path count, bound, unbound, undecided. Unbound MUST remain visible (001 SC-003).
- **FR-006**: MUST be idempotent and non-destructive (verify twice; tracking and artifacts unchanged).
- **FR-007**: MUST NOT run a FHIR validator binary and MUST NOT write mapping artifacts.
- **FR-008**: Curated skill `rh-mod-verify` MUST tell the agent to run the CLI and present the report. Status skill maps `Next: verify` to this skill.
- **FR-009**: After a passing coordinator run, `status` next remains `verify`.

### Key Entities

- **Coordinator report**: Per-model coverage plus per-stage pass / fail / skipped.
- **Stage verify**: Existing ingest/extract/annotate/specify/formalize verify (unchanged owners).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A formalized model with unbound leftovers produces a passing report that still lists those unbound counts in one command.
- **SC-002**: A checksum mismatch fails the coordinator in 100% of test runs without rewriting tracking.
- **SC-003**: An extracted-only model does not fail for a missing StructureDefinition in 100% of test runs.
- **SC-004**: Two consecutive coordinator runs on an unchanged model produce the same pass/fail outcome and leave tracking identical.

## Assumptions

- Formalized ENCR is the manual proving consumer. Unit tests reuse the specify/formalize mini pipeline.
- Unbound is never silently dropped; it is not a coordinator-level block.
- 001’s named event `validated` stays unused so verify cannot advance the lifecycle.
- `rh-map-skills` remains a separate product.

## Out of Scope

- FHIR Mapping Language, StructureMap, mapping.xlsx
- FSH generation
- Running a FHIR validator binary
- New plan/approve/implement gate
- Changing stage verify semantics except by invoking them
