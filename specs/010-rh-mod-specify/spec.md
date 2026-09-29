# Feature Specification: rh-mod-specify

**Feature Branch**: `010-rh-mod-specify`  
**Created**: 2026-09-29  
**Status**: Implemented  
**Depends On**: [001 — Framework](../001-rh-mod-framework/), [003 — extract](../003-rh-mod-extract/), [005 — annotate](../005-rh-mod-annotate/)  
**Input**: After every inventory path is bound or unbound, specify converges inventory + bindings into one human-editable logical model (`structured/logical-model.yaml`). Types and cardinality stay unknown unless the source already stated a real type or the reviewer fills them on the plan. CLI writes; skill reasons. Formalize (FHIR JSON) is out of this slice. Proving consumer: ENCR annotate-complete.

## Clarifications

### Session 2026-09-29

- Q: Slice or whole model? → A: Whole model. Specify plan fails unless every inventory path already has a bound or unbound row. Incomplete nkr-breast cannot specify yet; complete ENCR can.
- Q: Does the CLI invent FHIR types from labels? → A: No. Copy inventory datatype only when it is a recognized FHIR type. Codebook letters such as `F`/`A` and `unknown` stay `unknown` on the plan. Reviewer (or skill proposing into the plan YAML) fills types before approve.
- Q: One binding per element? → A: Yes. Copy the existing bindings row onto that element (bound snapshot or unbound+reason). Do not invent codes. Do not add a second system.
- Q: Formalize in this spec? → A: No. No `StructureDefinition`, ValueSet, or snapshot manifest.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Draft a specify plan from a complete annotation (Priority: P1)

An informaticist has finished annotating ENCR (`status` next is specify). They run specify plan. The CLI writes a draft plan with every inventory entity/element, provenance, and the matching binding snapshot. Types and cardinality that are not recognized FHIR values are `unknown`. No logical-model file yet. No ReasonHub call.

**Why this priority**: Without a durable plan, specify would skip the review gate.

**Independent Test**: On a consumer where every inventory path is bound or unbound, specify plan writes `process/plans/specify-plan.yaml` with the same paths as inventory, each carrying provenance and the bindings row for that path. `logical-model.yaml` is absent. Incomplete bindings → fail closed, no plan.

**Acceptance Scenarios**:

1. **Given** annotate-complete inventory+bindings, **When** specify plan runs, **Then** a draft plan lists every inventory path, grouped by entity, with provenance and binding snapshot.
2. **Given** any undecided inventory path, **When** specify plan runs, **Then** it fails closed and writes no plan.
3. **Given** inventory datatype `F`, `A`, or `unknown`, **When** specify plan runs, **Then** the plan element `datatype` is `unknown` (not `F`/`A`).
4. **Given** inventory datatype `date` (or another recognized FHIR type), **When** specify plan runs, **Then** that datatype is copied onto the plan.

---

### User Story 2 - Review types, then implement the logical model (Priority: P1)

The reviewer (or skill) sets datatypes and cardinality on the draft plan where they can be honest (e.g. birth date → `date`, sex → `code`). They approve. Implement writes `structured/logical-model.yaml` from that plan only: paths, types, cardinality, provenance, binding snapshots. Tracking records `model_specified`. Status next becomes formalize. Bindings and inventory are unchanged.

**Why this priority**: This is the L2 handoff artifact. Formalize must not re-read the codebook.

**Independent Test**: Edit one plan element to `datatype: date` and `cardinality: 0..1`, approve, implement. Logical model contains that type/card, every inventory path, and binding snapshots. Inventory/bindings bytes unchanged. Status next is formalize.

**Acceptance Scenarios**:

1. **Given** a draft specify plan, **When** implement runs without approve, **Then** it fails closed and writes no logical model and no `model_specified`.
2. **Given** an approved plan, **When** implement runs, **Then** `structured/logical-model.yaml` matches the plan elements (minus plan `status`) and tracking lists that file.
3. **Given** implement succeeded, **When** status runs, **Then** stage is specified and next is formalize.
4. **Given** implement succeeded, **When** inventory and bindings files are hashed, **Then** they are unchanged.

---

### User Story 3 - Verify without advancing formalize (Priority: P2)

Specify verify reports whether the logical model covers the inventory, carries provenance, and keeps bound/unbound integrity. Unknown type/cardinality are advisory. Verify does not write tracking events. Missing logical model or path mismatch is blocking.

**Why this priority**: Same verify contract as ingest/extract/annotate.

**Independent Test**: After a successful implement, verify twice with identical counts and unchanged tracking. A logical model missing a path fails. Unknown datatypes are reported as warnings, not a failed verify (unless other blocking issues).

**Acceptance Scenarios**:

1. **Given** a specified model whose paths match inventory, **When** verify runs twice, **Then** both pass and tracking is unchanged.
2. **Given** a logical-model path not in inventory (or an inventory path missing from the LM), **When** verify runs, **Then** it fails closed.
3. **Given** bound elements without system/code or unbound without reason, **When** verify runs, **Then** those are blocking.
4. **Given** elements with `datatype: unknown`, **When** verify otherwise passes, **Then** it still passes and reports an advisory unknown-type count.

---

### Edge Cases

- No inventory / no bindings file: fail with extract/annotate guidance.
- Re-plan after implement: new draft plan; implement again overwrites `logical-model.yaml` and appends another `model_specified`.
- Binding path not in inventory: specify plan fails (annotate verify should have caught this).
- Leading/trailing whitespace on copied system URIs is stripped.
- Relationships beyond entity grouping are out of scope (no extra graph).
- Mapping workbooks / FHIR JSON stay out of scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Canonical write owner is `rh-mod-skills specify` (`plan`, `approve`, `implement`, `verify`). Skills MUST NOT write the specify plan or `logical-model.yaml`.
- **FR-002**: `specify plan <model>` MUST fail if inventory is missing or any inventory path is not bound or unbound in `bindings.yaml`. MUST NOT call ReasonHub. MUST NOT write `logical-model.yaml`.
- **FR-003**: The specify plan MUST include every inventory entity and element (path, id, display), provenance copied from inventory, and a binding snapshot copied from that path’s bindings row (bound: system, code, display, strength, decision; unbound: reason, no code).
- **FR-004**: Plan `datatype` MUST be a recognized FHIR type copied from inventory, or `unknown`. Codebook letters (`F`, `A`, and other non-types) MUST become `unknown`. Plan `cardinality` MUST be a `n..m` / `n..*` form copied from inventory, or `unknown`.
- **FR-005**: `specify approve` MUST set plan `status: approved`. `specify implement` MUST fail if the plan is missing or not approved.
- **FR-006**: Implement MUST write `structured/logical-model.yaml` from the approved plan (complete element tree). MUST append `model_specified`. MUST NOT write FHIR resources or change inventory/bindings.
- **FR-007**: `specify verify` MUST be non-destructive. Blocking: missing LM, path set ≠ inventory, missing provenance, bound missing system/code, unbound missing reason. Advisory: unknown datatype or cardinality counts. MUST NOT append tracking events.
- **FR-008**: After successful implement, `status` MUST report stage `specified` and next `formalize`.
- **FR-009**: The curated skill `rh-mod-specify` MUST tell the agent to run specify plan, propose types/cardinality onto the existing plan YAML (reviewer edits), then approve → implement → verify. The skill MUST NOT persist the logical model itself.
- **FR-010**: No mapping.xlsx, FML, StructureMap, or `computable/` writes in this feature.

### Key Entities

- **Specify plan**: Review packet under `process/plans/specify-plan.yaml` (draft | approved).
- **Logical model (L2)**: `structured/logical-model.yaml` — entity/element tree sufficient to formalize later without the codebook.
- **Binding snapshot**: Copy of the annotate decision on that element (not a live join at read time).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On an annotate-complete model, a reviewer can produce a logical model covering 100% of inventory paths in one approve+implement.
- **SC-002**: Unapproved implement leaves `logical-model.yaml` absent in 100% of test runs.
- **SC-003**: Specify never creates or updates `bindings.yaml` or `inventory.yaml`.
- **SC-004**: After implement, status next is formalize (not annotate, not mapping).
- **SC-005**: Codebook datatype letters never appear as logical-model datatypes.

## Assumptions

- Annotate-complete ENCR (`~/fhir-specs/r4/ENCR`, model `encr`) is the manual proving consumer. Unit tests use a small synthetic codebook, not that tree.
- Default binding strength on snapshots stays whatever annotate stored.
- Recognized FHIR types are R4 primitives plus common complex types used on logical models (`CodeableConcept`, `Coding`, `Identifier`, `Quantity`, `Period`, `Reference`, `HumanName`, `Address`). Reviewer may set those on the plan.
- Specify does not translate Dutch/English labels.
- Status skill currently says specify is “not built yet”; this feature updates that sentence.

## Out of Scope

- Formalize (`StructureDefinition`, ValueSets, snapshot manifest)
- Inferring types from display names or `*dat` suffixes
- Multiple bindings per element
- HTML review UI for types
- Mapping workbooks, FML, StructureMap
- OCR
