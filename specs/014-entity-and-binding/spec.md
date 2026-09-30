# Feature Specification: entity graph + mapping/binding split

**Feature Branch**: `014-entity-and-binding` (work branch `cursor/entity-mapping-specs-bdd1`)  
**Created**: 2026-09-30  
**Status**: Implemented  
**Depends On**: [005 — annotate](../005-rh-mod-annotate/), [009 — annotate codesystems](../009-annotate-codesystems/), [010 — specify](../010-rh-mod-specify/), [011 — formalize](../011-rh-mod-formalize/), [013 — ig](../013-rh-mod-ig/)  
**Input**: Split concept mappings from ValueSet bindings, and allow one tracking model to own multiple logical StructureDefinitions linked by references. Approach narrative (non-normative): Project store `docs/pipeline-entity-and-binding-approach.md`. Proving example: ENCR recommendations (`encr-patient` / `encr-diagnosis` / `encr-hospital`).

This feature has **two epics**. Implementers may ship Epic A before Epic B (see sequencing in the approach doc). Both are required for the full outcome.

## Clarifications

### Session 2026-09-30

Locked by Ward Weistra (encoded from approach decisions; not re-asked):

- Q: Separate StructureDefinitions per logical entity? → A: Yes — option A (multi-LM inside one tracking model). Reject single-SD Backbone-only interim and split-tracking-models.
- Q: Canonical URL pattern? → A: `{org-base}/fhir/{project-or-model}/StructureDefinition/{logical-model-id}`. Configurable consumer/model canonical base (not hardcoded ENCR). Proving: `https://encr.eu/fhir/recommendations/StructureDefinition/encr-patient` (and diagnosis/hospital).
- Q: Concept-mapping FHIR form for v1? → A: `ElementDefinition.mapping` only (with StructureDefinition.mapping identities). No ConceptMap resources in this feature’s v1 scope.
- Q: Legacy singleton bound rows / old ValueSets? → A: Clean break. Ignore legacy; no compat loaders, schema bridges, migrate CLI, or auto-synthesize singleton ValueSets from old bound rows.
- Q: ValueSet authoring UX timing? → A: Mappings-first (Epic A phase 1); ValueSet authoring is phase 2 within Epic A.
- Q: Reference YAML shape? → A: `datatype: Reference` + `reference.target` (target = other logical model id).
- Q: IG packaging? → A: One IG per tracking model listing all logical SDs.
- Q: When does clinical regroup happen? → A: Only on specify plan — not extract clinical entities early.

## Epics

| Epic | Name | Primary stages | Outcome |
|---|---|---|---|
| **A** | Mapping vs ValueSet binding split | annotate → specify (snapshot copy) → formalize | Multi-system concept mappings as FHIR element mapping metadata; ValueSets only when explicitly authored (phase 2) |
| **B** | Multi-entity logical models + references | specify → formalize → ig sync | N logical StructureDefinitions per tracking model; Reference edges; one IG lists all SDs |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record multi-system concept mappings without inventing a ValueSet (Epic A, Priority: P1)

An informaticist annotating ENCR sex-at-birth accepts a LOINC code and a SNOMED code for the same inventory path. Annotate implement writes `mappings[]` (≤1 code per system). No ValueSet is implied. Formalize later emits `ElementDefinition.mapping` entries for those systems and does **not** emit a ValueSet for that path unless a `value_set` block exists.

**Why this priority**: Today’s singleton ValueSet conflates meaning with allowed values; this is the highest-leverage honesty fix.

**Independent Test**: On a mini annotate-complete model, implement two mappings on one path and none for `value_set`. Formalize writes mapping metadata on the SD and zero ValueSet files for that path. Old-style single `system`/`code`/`strength` rows are not silently upgraded — missing new-shape bindings fails closed or requires re-annotate (no compat loader).

**Acceptance Scenarios**:

1. **Given** an annotate plan with two accepted candidates on different systems for one path, **When** annotate implement runs, **Then** `bindings.yaml` stores both under `mappings[]` and does not create `value_set` solely from those mappings.
2. **Given** a path with mappings and no `value_set`, **When** formalize implement runs, **Then** the StructureDefinition carries `ElementDefinition.mapping` for those systems and no ValueSet resource is written for that path.
3. **Given** a legacy pre-split `bindings.yaml` (single bound coding row), **When** annotate/specify/formalize run without a re-plan into the new shape, **Then** the CLI does not auto-synthesize a singleton ValueSet or silently rewrite the file via a compat bridge.

---

### User Story 2 - Optional ValueSet binding with strength (Epic A phase 2, Priority: P2)

For a coded element that needs an allowed value domain, the reviewer authors a `value_set` (strength + concepts) independently of mappings. Formalize emits a multi-concept ValueSet and `ElementDefinition.binding`. Unbound still means no mappings and no value_set, with a reason.

**Why this priority**: Needed for real bindings, but mappings-first ships value sooner.

**Independent Test**: Author `value_set.strength: preferred` with two concepts on one path; formalize emits one ValueSet and a binding. A path with only mappings still has no ValueSet.

**Acceptance Scenarios**:

1. **Given** a path with an authored `value_set`, **When** formalize implement runs, **Then** a ValueSet and ElementDefinition.binding with that strength exist.
2. **Given** a path with neither mappings nor value_set, **When** annotate implement marks unbound, **Then** a reason is required and formalize emits neither mapping nor binding for that path.
3. **Given** verify after formalize, **When** counts are reported, **Then** mapped-only paths are distinguishable from ValueSet-bound paths.

---

### User Story 3 - Regroup inventory into multiple logical models with references (Epic B, Priority: P1)

At specify plan time, the reviewer (or skill proposing into the plan) regroups inventory paths into logical models (e.g. Patient, Diagnosis, Hospital), marks separate LMs, and types a hospital link as `Reference` with `reference.target: encr-hospital`. Extract source categories are unchanged. Implement writes `logical-model.yaml` with `logical_models[]` and `inventory_path` provenance on every element.

**Why this priority**: Without specify-owned regrouping, formalize cannot emit reusable entity boundaries.

**Independent Test**: Specify plan starts from annotate-complete inventory; reviewer splits into three LMs and one Reference edge; implement covers 100% of inventory paths via `inventory_path`; extract inventory bytes unchanged.

**Acceptance Scenarios**:

1. **Given** annotate-complete inventory, **When** specify plan runs, **Then** the draft plan can express multiple logical models and Reference targets (skill may propose; CLI persists).
2. **Given** every inventory path is assigned to exactly one LM element via `inventory_path`, **When** specify implement runs, **Then** `logical-model.yaml` contains those `logical_models[]` and inventory/bindings are unchanged.
3. **Given** a Reference element with `reference.target` pointing at another LM id in the same tracking model, **When** specify verify runs, **Then** coverage passes if all inventory paths are claimed and the target LM id exists.
4. **Given** extract inventory entities, **When** clinical regroup is desired, **Then** it is done only on specify plan — extract `merge_into` is not required to express clinical entities.

---

### User Story 4 - Formalize N StructureDefinitions and sync one IG (Epic B, Priority: P1)

Formalize emits one `StructureDefinition` (`kind=logical`) per logical model id. Canonical URLs use the configured base: `{canonical_base}/StructureDefinition/{logical-model-id}`. Snapshot lists all SDs (and any ValueSets). `ig sync` stages **one** IG for the tracking model with every logical SD under `input/models/`.

**Why this priority**: This is the L3/IG handoff rh-map-skills and publishers consume.

**Independent Test**: With three LMs and ENCR-style `canonical_base` `https://encr.eu/fhir/recommendations`, formalize writes three SD URLs ending in `encr-patient`, `encr-diagnosis`, `encr-hospital`. `ig sync` lists all three in the IG definition. No ConceptMap files.

**Acceptance Scenarios**:

1. **Given** a multi-LM logical model and configured canonical base, **When** formalize implement runs, **Then** one StructureDefinition JSON per LM id exists with canonical `{base}/StructureDefinition/{lm-id}`.
2. **Given** Reference elements, **When** formalize implement runs, **Then** those elements type as Reference targeting the corresponding logical model canonical URLs.
3. **Given** a successful multi-SD formalize, **When** `ig sync` runs, **Then** one IG tree for the tracking model includes all logical SDs (and ValueSets if any).
4. **Given** formalize output, **When** ConceptMap resources are sought, **Then** none exist in this feature’s v1 scope.

---

### Edge Cases

- Reviewer does nothing on a **new** specify plan: single logical model with Backbone-style grouping remains allowed (fresh default, not a legacy compat loader for old LM files).
- Duplicate mapping systems on one path (two SNOMED codes): fail closed (deterministic; no last-wins).
- `reference.target` names a missing LM id: specify verify / formalize implement fail closed.
- Canonical base missing or not http(s): formalize implement fails closed.
- Path name portions still ≤ 64 characters (existing formalize rule).
- FML / StructureMap / mapping.xlsx remain out of scope (rh-map-skills).
- No Java IG Publisher or validator binary in this CLI.

## Requirements *(mandatory)*

### Functional Requirements — Epic A (mappings vs bindings)

- **FR-A01**: Canonical write owner for bindings remains `rh-mod-skills annotate` (`plan` / `enrich` / `export` / `import` / `approve` / `implement` / `verify`). Skills MUST NOT write `bindings.yaml`.
- **FR-A02**: Annotate MUST allow up to one accepted coding **per code system** per inventory path under `mappings[]`. Searching multiple systems remains candidate discovery only.
- **FR-A03**: Annotate MUST NOT treat a mapping coding as a ValueSet. MUST NOT auto-create `value_set` from mappings alone.
- **FR-A04**: Binding strength, when present, MUST live only on an authored `value_set` (phase 2), not on each mapping row.
- **FR-A05**: Unbound MUST mean no mappings and no `value_set`, with a required reason.
- **FR-A06**: Specify MUST copy mapping and optional value_set snapshots onto logical-model elements; MUST NOT invent codes; MUST drop the prior “exactly one binding coding per element” rule.
- **FR-A07**: Formalize MUST emit `StructureDefinition.mapping` identities and `ElementDefinition.mapping` for each mapping; MUST NOT emit ConceptMap resources in v1.
- **FR-A08**: Formalize MUST emit a ValueSet and ElementDefinition.binding **only** when `value_set` is present; MUST NOT emit singleton ValueSets from mappings-only paths.
- **FR-A09**: The CLI MUST NOT provide legacy compat loaders, schema bridges, migrate commands, or flags that rewrite old bound rows into singleton ValueSets. Clean break is required.
- **FR-A10**: Curated `rh-mod-annotate` (and related) skill guidance MUST teach map-vs-bind; CLI still owns durable writes.

### Functional Requirements — Epic B (entity graph)

- **FR-B01**: Canonical write owner for regrouping remains `rh-mod-skills specify` (`plan` / `approve` / `implement` / `verify`). Skills propose regroupings onto the plan YAML only.
- **FR-B02**: Specify plan MUST be the **only** stage that owns clinical/logical regrouping of inventory paths into `logical_models[]`. Extract MUST NOT be required to express clinical entities early.
- **FR-B03**: Every inventory path MUST appear on exactly one logical-model element via `inventory_path` after specify implement; verify MUST fail closed on gaps or duplicates.
- **FR-B04**: Logical references MUST use `datatype: Reference` and `reference.target` equal to another `logical_models[].id` in the same tracking model.
- **FR-B05**: Formalize MUST emit one FHIR R4 `StructureDefinition` (`kind=logical`) per `logical_models[]` entry.
- **FR-B06**: Each StructureDefinition canonical MUST be `{canonical_base}/StructureDefinition/{logical-model-id}` where `canonical_base` is configurable consumer/model config (pattern `{org-base}/fhir/{project-or-model}`). The CLI MUST NOT hardcode only ENCR URLs; ENCR recommendations is the proving example.
- **FR-B07**: Tracking model id MAY differ from logical-model / SD ids. Snapshot MUST list all SDs (and ValueSets if any).
- **FR-B08**: `ig sync` MUST stage **one IG per tracking model** that lists all logical StructureDefinitions from the snapshot.
- **FR-B09**: Curated `rh-mod-specify` / `rh-mod-formalize` / `rh-mod-ig` skills MUST describe multi-LM regroup, canonical base, and IG listing; CLI owns writes.

### Cross-cutting

- **FR-X01**: Unit of work remains one consumer `models/<tracking-id>/` (constitution). Do not require splitting into multiple tracking models for v1.
- **FR-X02**: No FML, StructureMap, or mapping.xlsx writes. No FHIR Python library or validator binary requirement.
- **FR-X03**: Speckit governance artifacts (`spec.md` / `plan.md` / `tasks.md`) remain authoritative for acceptance; implementation follows tasks in dependency order (Epic A US1 before later stories).

### Key Entities

- **Concept mapping**: One coding per code system on an inventory/LM path (`mappings[]`).
- **ValueSet binding**: Optional authored value domain + strength (`value_set`).
- **Logical model (LM)**: Named entity inside a tracking model (`logical_models[].id`) that formalizes to one StructureDefinition.
- **Logical reference**: Element with `datatype: Reference` and `reference.target` → other LM id.
- **Canonical base**: Configurable `{org-base}/fhir/{project-or-model}` prefix for SD (and related) URLs.
- **Tracking model**: Consumer `models/<id>/` unit of work and IG package root.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can attach ≥2 code-system mappings to one path in a single annotate implement without producing a ValueSet for that path.
- **SC-002**: Formalize of a mappings-only path yields ElementDefinition.mapping metadata and 0 ValueSet files for that path in 100% of test runs.
- **SC-003**: Formalize never emits ConceptMap resources in this feature’s v1 acceptance suite.
- **SC-004**: A specify implement can place 100% of inventory paths into N≥2 logical models with at least one valid Reference edge, without changing extract inventory bytes.
- **SC-005**: Formalize + `ig sync` for the ENCR proving shape publish three logical SD canonicals under `https://encr.eu/fhir/recommendations/StructureDefinition/` (`encr-patient`, `encr-diagnosis`, `encr-hospital`) inside one IG for the tracking model.
- **SC-006**: Running the updated CLI against untouched legacy singleton-bound fixtures does not silently invent singleton ValueSets via a compat path (fail closed or require explicit re-annotate — never quiet rewrite).

## Assumptions

- Approach narrative in the Project store is authoritative for intent; this spec is authoritative for acceptance once planned/implemented.
- ENCR recommendations is the external proving consumer; in-repo fixtures may use a smaller multi-LM demo.
- Single-LM “reviewer does nothing” remains a valid **new-plan** default, not a loader for pre-feature `logical-model.yaml` shapes.
- `canonical_base` is a reviewable field on `process/plans/formalize-plan.yaml` (http(s)); implement derives `{canonical_base}/StructureDefinition/{logical-model-id}` (Epic A: lm-id = tracking model id).
- Bindings status enum: US1 uses `mapped` | `unbound`. US2 keeps `mapped` for mappings-only rows and treats a path with `value_set` (with or without mappings) as annotate-complete decided work without requiring a rename to `decided` unless a later task collapses the synonym.
- Duplicate same-system mappings fail closed.
- Schema version bumps to breaking `"2.0"` without a compat loader.
- Product CLI for US1+ is in scope for implementation tasks (historical Speckit-only constraint retired).

## Out of Scope

- FHIR Mapping Language, StructureMap, mapping.xlsx (rh-map-skills)
- ConceptMap resources (post-v1 optional polish)
- Running IG Publisher / Java / validator binary from this CLI
- Multiple tracking models as the primary multi-entity design
- Extract-stage clinical entity regrouping
- Legacy compatibility shims / migrate CLI / `--compat` flags
- Auto-inferring clinical entities or FHIR types from labels
- ConceptMap resources and ValueSet authoring UX beyond what tasks schedule (US2+)
