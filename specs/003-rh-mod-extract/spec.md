# Feature Specification: rh-mod-extract

**Feature Branch**: `003-rh-mod-extract`  
**Created**: 2026-09-13  
**Status**: Draft  
**Depends On**: [001 — Framework](../001-rh-mod-framework/), [002 — rh-mod-ingest](../002-rh-mod-ingest/)  
**Input**: Extract an L2 element inventory (and value domains when present) from ingested tabular L1 projections. Proving model: `nkr-breast` (IKNL). Extract is a separate gated stage from annotate.

## Clarifications

### Session 2026-09-13

- Q: What does extract own vs annotate? → A: Extract owns inventory shape: entities, elements, paths, provenance, datatype/cardinality if stated in the source otherwise `unknown`, and local value-domain refs. Terminology bindings are annotate (005+). PDF table ingest is 004.
- Q: How are entities formed from the IKNL dictionary? → A: Default proposal is one entity per distinct `variabele_categorie` and one element per data row. The reviewer may merge, split, rename, or drop in the plan before approval. Implement writes only what the approved plan contains.
- Q: What about ENCR PDFs? → A: Extract requires at least one table projection. A PDF-only model fails plan with guidance — it does not invent rows from PDF text.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract the NKR breast inventory (Priority: P1)

An informaticist has ingested the IKNL Excel into `nkr-breast`. They run extract plan. The plan proposes five entities from the category column (Patiëntgegevens, Tumorgegevens, Behandelgegevens, Procesgegevens, Risicofactoren) and 153 elements with source provenance (sheet, column, row). Datatype and cardinality are `unknown` because the dictionary does not state them. After approval, implement writes `structured/inventory.yaml`. Verify confirms every projected row is represented or explicitly dropped in the plan, and status says next is annotate.

**Why this priority**: Without a reviewable inventory, annotate and specify have nothing honest to bind or formalize.

**Independent Test**: On a consumer with `nkr-breast` ingested from `tests/fixtures/l1/nkr-breast/IKNL_Data_dictionary.xlsx`, extract plan → approve → implement produces inventory with 153 elements, five entities, provenance to sheet `Variabelen`, and no bindings file.

**Acceptance Scenarios**:

1. **Given** `nkr-breast` is ingested with the IKNL table projection, **When** extract plan runs, **Then** `models/nkr-breast/process/plans/extract-plan.yaml` lists five proposed entities matching the category counts (Behandelgegevens 60, Tumorgegevens 37, Procesgegevens 33, Patiëntgegevens 18, Risicofactoren 5) and 153 proposed elements, each with source sheet/column/row, and `structured/` is still empty of inventory.
2. **Given** that plan is not approved, **When** extract implement runs, **Then** it fails closed and writes no `structured/inventory.yaml` and no `inventory_derived` event.
3. **Given** an approved extract plan, **When** implement runs, **Then** `structured/inventory.yaml` contains those entities and elements, datatype and cardinality are `unknown` unless the plan recorded an explicit source-stated value, and tracking records `inventory_derived`.
4. **Given** implement succeeded, **When** status runs, **Then** the model stage is extracted and next is annotate — not mapping, not formalize.

---

### User Story 2 - Reviewer edits the plan before it becomes L2 (Priority: P1)

The default plan is a starting proposal, not truth. A reviewer drops a privacy-sensitive element, merges two categories, or renames an entity. Implement must follow the approved plan, not silently restore dropped rows from the projection.

**Why this priority**: Constitution requires a human gate. IKNL includes identifiable constructs (dates, hospitals); dropping or regrouping must be durable and reviewable.

**Independent Test**: Approve a plan that omits `gebdat` and renames `Patiëntgegevens` to `Patient`. Implement inventory has 152 elements, no `gebdat`, and the renamed entity. Verify reports `gebdat` as plan-excluded, not as a missing-row error.

**Acceptance Scenarios**:

1. **Given** an approved plan that excludes one projected row, **When** implement runs, **Then** that element is absent from inventory and listed in the plan as dropped with a reason.
2. **Given** an approved plan that merges two categories into one entity, **When** implement runs, **Then** inventory has that single entity and the original two category names appear only in provenance, not as separate entities.
3. **Given** implement is asked to “refresh from the codebook” ignoring the plan, **When** it runs, **Then** it does not — the approved plan is the only input to inventory writes.

---

### User Story 3 - Plan, verify, and refuse PDF-only extract (Priority: P1)

Extract plan is a durable review packet. Verify is rerunnable and writes nothing. A model with only registered PDFs (no table projection) cannot be extracted. Homonyms (same variable name on different sheets) keep distinct paths. Conflicts in names or types are surfaced, not collapsed.

**Why this priority**: Provenance and fail-closed behavior are how extract stays honest on mixed ENCR+NKR workspaces.

**Independent Test**: Extract plan on `encr-standard-dataset` (22 PDFs, no projections) exits non-zero with a message to add a table projection. On `nkr-breast`, verify twice after implement adds zero tracking events.

**Acceptance Scenarios**:

1. **Given** `encr-standard-dataset` has PDF sources only, **When** extract plan runs, **Then** it writes no extract plan (or writes none that can be approved) and reports that structured table projection is required.
2. **Given** a completed extract, **When** verify runs twice, **Then** both runs report the same coverage (projected rows vs inventory vs plan-excluded) and neither appends tracking events.
3. **Given** two sheets share an element name with different labels, **When** plan runs, **Then** both appear as separate elements with sheet provenance; they are not merged by name.
4. **Given** `structured/` already has an approved inventory and extract implement is re-run without an explicit replace acknowledgement, **Then** it fails closed and does not overwrite.

---

### User Story 4 - Record local value domains when the source has them (Priority: P2)

Some dictionaries include code-list sheets or value columns. Extract records those as `structured/value-domains.yaml` and points elements at them. The IKNL proving export has no value lists — then the file is omitted or empty, and elements have no domain ref. Extract must not invent codes or bind SNOMED/LOINC.

**Why this priority**: Needed for later annotate, but the first proving file has no domains.

**Independent Test**: A two-sheet fixture (dictionary + code list for one variable) yields a value domain and an element `value_domain` ref. The IKNL fixture yields no invented domain.

**Acceptance Scenarios**:

1. **Given** only the IKNL three-column dictionary, **When** implement runs, **Then** no value domain is invented; elements have no fabricated code lists.
2. **Given** a projection with an explicit local code list for an element, **When** implement runs after approval, **Then** `value-domains.yaml` contains that list and the element references it.

---

### Edge Cases

- Dictionary with no category column: default one entity per sheet
- Empty projection or header-only sheet: plan warns; implement of an empty approved plan is allowed only if the reviewer recorded that intent
- Duplicate `variabele_name` in one sheet: both rows kept; flagged as a name conflict
- Source content is untrusted: injection boundary before any linguistic interpretation; copy/project/inventory-from-plan are in-bounds
- Checksum drift on the L1 projection vs ingest record: extract plan/implement fail closed until ingest verify is clean
- PDF + Excel on the same model: extract uses only table projections; PDFs stay provenance for annotate/specify, not inventory rows
- Model not ingested: fail with guidance to run ingest
- Skills MUST NOT write `inventory.yaml` directly

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Canonical write owner is `rh-mod-skills extract` (`plan`, `approve`, `implement`, `verify`). Skills MUST NOT write inventory or value-domain files directly.
- **FR-002**: `extract plan <model>` MUST read ingested table projections (not raw Excel as the only form, not Markdown) and write `models/<model>/process/plans/extract-plan.yaml` with `status: draft`, proposed entities, proposed elements, provenance, and drop/merge notes. It MUST append `extract_planned`.
- **FR-003**: Default proposal MUST be: one entity per distinct category value when a category column is present (IKNL: `variabele_categorie`); otherwise one entity per sheet. One element per data row. Element id is the source variable name (`variabele_name` / header named as the identifier column). Display is the source label (`variabele_label` or the identifier if no label column).
- **FR-004**: Each proposed element MUST include: id, display, entity ref, path, datatype (`unknown` unless source-stated), cardinality (`unknown` unless source-stated), optional value-domain ref, and provenance (source name, sheet, column headers used, row index).
- **FR-005**: Plan MUST NOT invent FHIR types, UCUM units, SNOMED/LOINC codes, or cardinality. Absence in the source is `unknown`, not a guessed `0..1`.
- **FR-006**: `extract approve <model>` MUST set plan `status: approved` via the CLI.
- **FR-007**: `extract implement <model>` MUST fail closed if the plan is missing or not approved, and MUST write `structured/inventory.yaml` exactly from the approved plan (including reviewer merges/drops/renames).
- **FR-008**: Successful implement MUST append `inventory_derived` and MUST NOT write `bindings.yaml` or `logical-model.yaml`.
- **FR-009**: `extract verify <model>` MUST be non-destructive. It MUST report: plan approved, inventory present, count of entities/elements, projected rows covered or explicitly excluded, conflicts, and unknown datatype/cardinality counts (advisory).
- **FR-010**: Extract MUST fail plan when the model has no table projection (PDF-only ENCR case), with a message that ingest projection `tables` is required.
- **FR-011**: Homonyms MUST remain distinct elements keyed by provenance, not collapsed by id alone.
- **FR-012**: Re-implement MUST NOT overwrite an existing inventory unless the caller passes an explicit replace acknowledgement analogous to ingest `--acknowledge-drift`.
- **FR-013**: Source dictionary content is untrusted. Implement MUST declare an injection boundary in the skill (when authored) before any free-text interpretation of labels.
- **FR-014**: Extract MUST NOT create mapping workbooks, FML, StructureMap, or FHIR StructureDefinitions.
- **FR-015**: After successful extract, `status` MUST report next step `annotate`.

### Key Entities

- **Extract plan**: Reviewable proposal of entities and elements with provenance, reviewer edits, and approval state.
- **Entity**: L2 grouping (IKNL category or sheet) with id, title, element list.
- **Element**: L2 field with id, display, path, datatype, cardinality, optional value-domain ref, provenance.
- **Value domain**: Local code list extracted from the source, not a terminology binding.
- **Inventory**: Durable `structured/inventory.yaml` ready for annotate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can extract `nkr-breast` and independently count 153 inventory elements and five entities matching the IKNL category totals, without opening Excel.
- **SC-002**: Unapproved implement leaves `structured/` without inventory in 100% of test runs.
- **SC-003**: Verify on unchanged extract reports the same coverage twice and adds zero tracking events.
- **SC-004**: Extract plan on a PDF-only model never produces an inventory of invented rows.
- **SC-005**: 100% of inventory writes go through `rh-mod-skills extract`; dropped elements remain listed in the plan with a reason.

## Assumptions

- 001 `init`/`status` and 002 `ingest` exist.
- The IKNL proving projection has columns `variabele_name`, `variabele_categorie`, `variabele_label` on sheet `Variabelen`.
- Identifier / category / label columns are detected by those names first, then by a small header synonym list (`name`/`id`/`code`, `category`/`group`/`entity`, `label`/`description`/`title`). Unrecognized layouts stay in the plan as one entity per sheet, one element per row, all columns retained as notes — they are not discarded.
- Annotate (ReasonHub bindings) is a later spec.
- Curated skill `rh-mod-extract` is authored only after these CLI commands exist.
- Dutch labels are stored as display text; extract does not translate them.

## Out of Scope

- Terminology binding, ReasonHub lookup, `bindings.yaml`
- `logical-model.yaml` and FHIR `StructureDefinition`
- PDF table extraction ([004-rh-mod-ingest-pdf](../004-rh-mod-ingest-pdf/)); this feature reads table projections only
- Mapping workbooks, FML, StructureMap
- Guessing FHIR datatypes from Dutch labels (e.g. treating `*dat` as `date`)
