# Feature Specification: rh-mod-formalize

**Feature Branch**: `011-rh-mod-formalize`  
**Created**: 2026-09-29  
**Status**: Draft  
**Depends On**: [001 — Framework](../001-rh-mod-framework/), [010 — specify](../010-rh-mod-specify/)  
**Input**: Emit FHIR R4 `StructureDefinition` (`kind=logical`), ValueSets for bound elements, and a snapshot manifest from an approved specified logical model. Unknown cardinality defaults to `0..1`. Unknown datatype fails closed. No mapping artifacts. Proving consumer: specified ENCR.

## Clarifications

### Session 2026-09-29

- Q: Unknown cardinality? → A: Default `0..1` at formalize. Verify reports how many defaults were applied (advisory).
- Q: Unknown datatype? → A: Fail closed on implement. Do not emit `string` as a guess.
- Q: ValueSets? → A: One ValueSet per bound element (the single coding already on the logical model). Unbound elements get no binding. Strength is copied (`example` stays example).
- Q: FHIR validator? → A: Formalize writes JSON without requiring a validator. Verify reports validator-not-run as advisory.
- Q: Canonical URL / version? → A: Required on the formalize plan before implement. Plan may propose defaults; empty/non-http canonical fails.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Draft a formalize plan from a specified model (Priority: P1)

An informaticist has specified ENCR (`status` next is formalize). They run formalize plan. The CLI writes a draft plan with proposed canonical URL, version, and counts of elements that will default cardinality or that still have unknown datatype. No `computable/` files yet.

**Why this priority**: Canonical URL and version are the rh-map-skills pin; they must be reviewable.

**Independent Test**: On a specified mini model, formalize plan writes `process/plans/formalize-plan.yaml` with `status: draft`, a proposed `http…` canonical, and a version. `computable/` stays empty. Missing logical model → fail closed.

**Acceptance Scenarios**:

1. **Given** a specified logical model, **When** formalize plan runs, **Then** a draft plan records canonical, version, and element counts (including unknown-cardinality defaults).
2. **Given** no `logical-model.yaml`, **When** formalize plan runs, **Then** it fails closed and writes no plan.
3. **Given** elements with unknown datatype, **When** plan runs, **Then** the plan lists those paths (implement will still fail until they are typed in specify).

---

### User Story 2 - Implement StructureDefinition, ValueSets, and snapshot (Priority: P1)

The reviewer confirms canonical URL and version, approves, and implement writes FHIR JSON under `computable/` plus a snapshot manifest with file checksums. Tracking records `model_formalized`. Status next is verify. Logical model YAML is unchanged. No mapping files.

**Why this priority**: This is the L3 handoff.

**Independent Test**: Approve a plan with an http canonical and version. Implement writes one StructureDefinition with `kind: logical` whose differential paths cover the logical-model elements, a ValueSet for each bound element, and a manifest listing those files with checksums. Unbound elements have no ValueSet. Unknown-cardinality elements appear as min=0 max=1.

**Acceptance Scenarios**:

1. **Given** a draft formalize plan, **When** implement runs without approve, **Then** it fails and writes no `computable/` files and no `model_formalized`.
2. **Given** an approved plan with canonical + version, **When** implement runs, **Then** `computable/` contains a `StructureDefinition` (`kind: logical`) and ValueSets for bound elements only, plus a snapshot manifest with checksums.
3. **Given** an element with unknown datatype, **When** implement runs, **Then** it fails closed and writes no computable artifacts.
4. **Given** implement succeeded, **When** status runs, **Then** stage is formalized and next is verify.
5. **Given** implement succeeded, **When** mapping.xlsx / `.map` / StructureMap are sought, **Then** they do not exist.

---

### User Story 3 - Verify snapshot without a FHIR validator (Priority: P2)

Formalize verify checks that the StructureDefinition kind is logical, differential paths match the logical model, ValueSets match bound elements, and manifest checksums match files on disk. Missing validator is advisory, not blocking. Verify does not write tracking.

**Why this priority**: Same verify contract as other stages; 001 already allows validator-skipped.

**Independent Test**: After implement, verify twice with identical reports and unchanged tracking. Tampering with a checksum fails. Unknown-datatype is not applicable post-implement (already failed). Cardinality defaults are advisory counts.

**Acceptance Scenarios**:

1. **Given** a successful implement, **When** verify runs twice, **Then** both pass and tracking is unchanged.
2. **Given** a manifest checksum that does not match the file, **When** verify runs, **Then** it fails closed.
3. **Given** StructureDefinition `kind` is not `logical`, **When** verify runs, **Then** it fails closed.

---

### Edge Cases

- Empty canonical or non-http canonical → implement fails.
- Re-implement overwrites `computable/` from the current approved plan.
- Hyphens in element ids are allowed on logical-model paths.
- FSH is not written (constitution: generated view, not this slice).
- Mapping workbooks remain forbidden.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Canonical write owner is `rh-mod-skills formalize` (`plan`, `approve`, `implement`, `verify`). Skills MUST NOT write FHIR JSON or the snapshot manifest.
- **FR-002**: `formalize plan <model>` MUST require `structured/logical-model.yaml`. MUST write `process/plans/formalize-plan.yaml` (`status: draft`) with proposed canonical URL, version, and counts. MUST NOT write `computable/`.
- **FR-003**: `formalize approve` MUST set plan `status: approved`. Implement MUST fail if the plan is missing, not approved, canonical is missing/not an http(s) URI, or version is empty.
- **FR-004**: Implement MUST fail closed if any logical-model element has `datatype: unknown`. MUST NOT invent types.
- **FR-005**: Implement MUST treat `cardinality: unknown` as `0..1` (min 0, max 1).
- **FR-006**: Implement MUST write FHIR R4 JSON: one `StructureDefinition` with `kind: logical` whose differential includes the model root, each entity as a backbone, and each element with type and cardinality; one `ValueSet` per bound element copying that element’s system/code/display; no ValueSet for unbound.
- **FR-007**: Implement MUST write a snapshot manifest (canonical, version, relative file paths, SHA-256 checksums) under the model (process or computable — one documented path). MUST append `model_formalized`. MUST list computable files on tracking. MUST NOT write mapping.xlsx, FML, or StructureMap. MUST NOT mutate the logical model YAML.
- **FR-008**: `formalize verify` MUST be non-destructive. Blocking: missing SD, kind ≠ logical, path coverage mismatch vs logical model, missing ValueSet for a bound element, checksum mismatch. Advisory: cardinality-default count; validator-not-run. MUST NOT append tracking events.
- **FR-009**: After successful implement, `status` MUST report stage `formalized` and next `verify`.
- **FR-010**: Curated skill `rh-mod-formalize` MUST tell the agent to plan, confirm canonical/version on the plan YAML, then approve → implement → verify. The skill MUST NOT write JSON itself.

### Key Entities

- **Formalize plan**: Canonical URL, version, review status.
- **Logical StructureDefinition**: FHIR R4 `kind=logical` JSON.
- **ValueSet**: One per bound logical-model element.
- **Snapshot manifest**: Pin contract for rh-map-skills (canonical, version, checksums).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A specified model with no unknown datatypes produces a `kind=logical` StructureDefinition covering 100% of logical-model elements in one approve+implement.
- **SC-002**: Unapproved implement leaves `computable/` empty in 100% of test runs.
- **SC-003**: Unknown datatype blocks implement in 100% of test runs (no guessed `string`).
- **SC-004**: After implement, status next is verify (not annotate, not mapping).
- **SC-005**: 0 mapping workbooks, `.map` files, or StructureMap resources are written.

## Assumptions

- Specified ENCR is the manual proving consumer. Unit tests use the small specify-demo pipeline with types filled.
- Binding strength `example` is copied onto ElementDefinition.binding.
- No Java FHIR validator is required in this slice.
- Root of the StructureDefinition path is the model id.

## Out of Scope

- FHIR Mapping Language, StructureMap, mapping.xlsx
- FSH generation
- Running a FHIR validator binary
- Changing specify type inference
- `rh-mod-verify` consolidated coordinator (status next names it; that skill stays later)
