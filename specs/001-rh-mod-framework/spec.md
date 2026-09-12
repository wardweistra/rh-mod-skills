# Feature Specification: RH Mod Skills Framework

**Feature Branch**: `001-rh-mod-framework`  
**Created**: 2026-09-11  
**Status**: Draft  
**Input**: Bootstrap a sibling product to rh-skills that turns source data models and codebooks into fully specified FHIR logical models, leaving mappings to rh-map-skills.

## Clarifications

### Session 2026-09-11

- Q: What does 001 actually implement vs later specs? → A: Workspace skeleton only (`init`, consumer-root `tracking.yaml`, `models/<id>/` layout, read-only `status`). Structured ingest is 002.
- Q: Where do tracking and sources live? → A: One `tracking.yaml` at the consumer project root with a `models:` list. L1 files live under `models/<id>/sources/`, not a shared repo-root `sources/` and not `topics/`.
- Q: What are the first proving L1 inputs? → A: Two models: `nkr-breast` (IKNL Excel data dictionary, 153 variables) and `encr-standard-dataset` (ENCR 2023 standard-dataset PDF plus the other English recommendation PDFs from [ENCR Recommendations](https://www.encr.eu/ENCR-Recommendations)). Fixtures at `tests/fixtures/l1/`.
- Q: Does init require plan → implement → verify? → A: No. Init is scaffolding; ingest is the first gated stage.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Informaticist bootstraps a model workspace (Priority: P1)

A clinical informaticist has a vendor codebook or research data dictionary (Excel or CSV). They initialize a model in a consumer project, register the source file, and see it tracked with a checksum and original tabular structure available for extraction — not flattened to a Markdown dump.

**Why this priority**: Without a model-scoped workspace and structure-preserving ingest, no later stage has a stable place to write inventory, bindings, or a logical model.

**Independent Test**: `rh-mod-skills init <model>` creates `models/<model>/` plus `tracking.yaml`; ingest registers an `.xlsx` or `.csv` without requiring pandoc-to-Markdown as the only normalized form.

**Acceptance Scenarios**:

1. **Given** an empty consumer project, **When** the user runs `rh-mod-skills init tumor-registry --title "Tumor registry codebook"`, **Then** `models/tumor-registry/` exists with `sources/`, `structured/`, `computable/`, and `process/plans/`, and `tracking.yaml` records `model_created`.
2. **Given** a codebook `.xlsx` with two sheets, **When** ingest implement runs, **Then** the raw file is checksummed and a structured L1 representation preserves sheet names and columns.
3. **Given** ingest has run, **When** `rh-mod-skills status <model>` runs, **Then** it reports the model is ready for extract and not yet specified or formalized.

---

### User Story 2 - Extract and annotate an element inventory (Priority: P1)

From the ingested codebook, the agent proposes an L2 inventory of entities and elements (path, datatype, cardinality, local value domain, source provenance). A reviewer approves the plan. The agent then walks elements with the user and ReasonHub to bind terminology, recording reviewer decisions.

**Why this priority**: The inventory plus bindings are the only honest input to a fully specified logical model. Annotation is a separate review loop from inventory shape.

**Independent Test**: After an approved extract plan, derive writes `structured/inventory.yaml` (and value domains). After annotation review, `structured/bindings.yaml` contains system/code/display/strength per bound element and unbound elements remain explicit.

**Acceptance Scenarios**:

1. **Given** a normalized codebook, **When** extract plan runs, **Then** it proposes entities/elements with source sheet/column provenance and writes a durable plan under `models/<model>/process/plans/`.
2. **Given** the extract plan is not approved, **When** extract implement is invoked, **Then** it fails closed and writes nothing to `structured/`.
3. **Given** approved inventory elements, **When** annotate plan proposes codes via ReasonHub, **Then** the reviewer can accept, reject, or replace per element before any binding file is finalized.
4. **Given** an element with no acceptable code, **When** annotation is finalized, **Then** the element is recorded as `unbound` with a reason — it is not silently omitted.

---

### User Story 3 - Specify and formalize a FHIR logical model (Priority: P1)

The informaticist converges the inventory and bindings into a fully specified L2 logical model (paths, types, cardinality, bindings, relationships, open issues), then formalizes it to a FHIR R4 `StructureDefinition` with `kind=logical` plus `ValueSet` resources for bound domains. A FHIR validator accepts the StructureDefinition.

**Why this priority**: This is the product handoff. rh-map-skills must be able to pin a canonical URL and version and map from this snapshot without re-reading the codebook.

**Independent Test**: Formalize writes `computable/StructureDefinition-*.json` with `kind=logical` whose differential elements match the L2 specified model; `rh-mod-skills verify` reports unbound required elements as warnings or errors per policy.

**Acceptance Scenarios**:

1. **Given** inventory + bindings, **When** specify implement runs after plan approval, **Then** `structured/logical-model.yaml` is a complete element tree with provenance and binding references.
2. **Given** a specified logical model, **When** formalize implement runs, **Then** `computable/` contains a `StructureDefinition` with `kind: logical` and `ValueSet` resources for required bindings.
3. **Given** formalize has succeeded, **When** a snapshot manifest is read, **Then** it includes canonical URL, version, and file checksums suitable for rh-map-skills to pin.
4. **Given** mapping work is requested inside this CLI (`structuremap`, `.map`, mapping.xlsx), **When** the command is invoked, **Then** it does not exist — that work is out of scope.

---

### User Story 4 - Status and verify across the model lifecycle (Priority: P2)

The informaticist asks “where is this model?” and “what is still unbound?” without changing files. Verify is rerunnable and distinguishes blocking errors from warnings.

**Why this priority**: Cross-cutting status is how the agent chooses the next skill; it can ship after the P1 slice but should be specified now so tracking events are named consistently.

**Independent Test**: Status reads only `tracking.yaml` and artifact presence; verify does not write lifecycle events that advance the model.

**Acceptance Scenarios**:

1. **Given** a model mid-annotation, **When** status next-steps runs, **Then** it names annotate or specify as the next stage and does not suggest mapping.
2. **Given** a formalized model with unbound optional elements, **When** verify runs, **Then** it reports advisory warnings and a non-zero or zero exit according to documented policy (blocking vs warning).

---

## Edge Cases

- Excel workbooks with multiple sheets, merged headers, or code-list tabs separate from the data dictionary tab
- CSV-only dictionaries with no explicit cardinality (must be flagged, not invented)
- Homonyms: same column name, different meaning on different sheets
- Local codes that look like SNOMED/LOINC identifiers but are not
- Re-ingest of a changed codebook: checksum change must invalidate or require rematch of downstream L2/L3
- FHIR validator unavailable: formalize still writes JSON; verify reports validator-skipped as advisory
- Model ids must be kebab-case and unique within a consumer project

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST use `models/<model-id>/` as the unit of work. Commands MUST NOT use `topics/<topic>/`.
- **FR-002**: `rh-mod-skills init <model>` MUST create the model directory tree and append `model_created` to `tracking.yaml`.
- **FR-003**: Ingest MUST support `.xlsx` and `.csv` in v1, preserving sheet (or file) name, column headers, and row values in a structured L1 form. Markdown flattening MUST NOT be the only normalized representation.
- **FR-004**: Extract MUST produce `structured/inventory.yaml` describing entities, elements, datatypes, cardinality (or `unknown`), value-domain refs, and source provenance.
- **FR-005**: Extract and annotate MUST be separate stages with separate plan artifacts and approval gates.
- **FR-006**: Annotate MUST record, per element: candidate codes, reviewer decision, bound `system|code|display`, binding strength, or an explicit `unbound` reason.
- **FR-007**: Annotate MAY use ReasonHub MCP tools for search, lookup, subsumes, and expand. Absence of MCP MUST fail annotation of new bindings with a clear error, not invent codes.
- **FR-008**: Specify MUST write `structured/logical-model.yaml` that is sufficient to generate a FHIR logical model without returning to the codebook.
- **FR-009**: Formalize MUST write FHIR R4 `StructureDefinition` (`kind=logical`) and `ValueSet` JSON under `computable/`.
- **FR-010**: Formalize MUST write a snapshot manifest (canonical, version, file checksums) intended as the rh-map-skills input contract.
- **FR-011**: The product MUST NOT generate mapping.xlsx, FHIR Mapping Language, or `StructureMap` resources.
- **FR-012**: All durable writes MUST go through named CLI commands; skills MUST NOT write artifacts directly.
- **FR-013**: Stage transitions MUST follow plan → implement → verify except for read-only status/verify coordinators.
- **FR-014**: Tracking events MUST be append-only named events (`model_created`, `source_added`, `extract_planned`, `inventory_derived`, `annotate_planned`, `element_bound`, `model_specified`, `model_formalized`, `validated`).
- **FR-015**: Re-ingest that changes a source checksum MUST be visible in status and MUST NOT silently overwrite approved L2/L3 artifacts.

### Key Entities

- **Model**: Named workspace under `models/<id>/` representing one source data model evolving toward a FHIR logical model.
- **Source**: L1 codebook or dictionary file with checksum and structured L1 projection.
- **Inventory**: L2 catalog of entities and elements with provenance.
- **Value domain**: L2 local code list extracted from the source.
- **Binding**: Reviewed terminology annotation on an element.
- **Logical model (L2)**: Fully specified element tree ready for FHIR formalization.
- **Logical model (L3)**: FHIR `StructureDefinition` (`kind=logical`) plus ValueSets.
- **Snapshot**: Versioned handoff package for rh-map-skills.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A two-sheet Excel codebook can be ingested, extracted, annotated for at least 10 elements, specified, and formalized to a validator-accepted logical `StructureDefinition` without any mapping artifacts being produced.
- **SC-002**: Every L3 element path is traceable to an L2 inventory row and an L1 sheet/column (or an explicit `derived` flag).
- **SC-003**: Unbound elements remain visible in verify output; they are never dropped during formalize without a recorded reason.
- **SC-004**: A second consumer can copy `computable/` + snapshot manifest and resolve the logical model by canonical URL/version without the original codebook.
- **SC-005**: CLI-first and agent-native modes share the same commands; no skill writes files except by invoking the CLI.

## Assumptions

- v1 source formats are Excel and CSV codebooks only. FHIR StructureDefinition import, XSD, and OMOP DDL are later ingest plugins.
- Target FHIR version is R4.
- ReasonHub is the terminology service, matching rh-skills.
- rh-map-skills does not exist yet; the snapshot contract is defined here so that repo can depend on it later.
- Shared CLI framework with rh-skills may later move to `rh-skills-core`; v1 may duplicate patterns rather than import rh-skills as a dependency.

## Out of Scope

- Excel mapping workbooks and FHIR Mapping Language (rh-map-skills)
- Mapping a logical model onto US Core or base FHIR resources (rh-map-skills with an imported target SD)
- Clinical guideline extraction, CQL, PlanDefinition (rh-skills)
- Authoring FSH as source of truth
