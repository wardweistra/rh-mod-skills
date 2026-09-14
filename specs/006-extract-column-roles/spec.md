# Feature Specification: extract column roles

**Feature Branch**: `006-extract-column-roles`  
**Created**: 2026-09-14  
**Status**: Draft  
**Depends On**: [003 — rh-mod-extract](../003-rh-mod-extract/), [002 — rh-mod-ingest](../002-rh-mod-ingest/), [004 — PDF tables](../004-rh-mod-ingest-pdf/)  
**Input**: Stop encoding each registry’s column names into extract. The extract plan lists every projected column and a proposed role. Header-name hints are a first pass only. The reviewer remaps roles in the plan. Re-running extract plan rebuilds entities and elements from those roles. Implement still writes inventory only from the approved plan.

## Clarifications

### Session 2026-09-14

- Q: Are header synonyms the extract contract? → A: No. They are a first-pass hint when a sheet has no saved roles. The durable contract is per-column roles on the extract plan.
- Q: Does implement re-read the codebook using roles? → A: No. Implement still copies include-only rows from the approved plan (003). After a role remap, extract plan must be run again so entities/elements match the new roles, then approve.
- Q: Which roles exist? → A: `id`, `category`, `label`, `datatype`, `cardinality`, `unused`, and for local code lists `domain_var`, `domain_code`, `domain_display`. Exclusive roles may be assigned at most once per sheet.
- Q: What if headers are unrecognized? → A: Every column is listed as `unused`. Extract still proposes one entity per sheet and one element per row (row identifiers). The reviewer maps roles; they do not wait for a product patch.
- Q: Are drop/rename/merge decisions lost when plan is re-run after a role edit? → A: Element include/drop and reason are kept for the same source sheet+row. Entity title/decision/merge are kept when the derived entity id is unchanged. A category remap that changes entity ids is expected to produce new entity ids.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plan shows column roles and still extracts NKR (Priority: P1)

An informaticist runs extract plan on ingested `nkr-breast`. The plan lists the three IKNL columns with proposed roles identifier / category / label (from header hints). Entities and elements are the same 5 × 153 proposal as today. They approve without touching roles. Implement writes the same inventory.

**Why this priority**: Existing proving models must not regress. Roles are additive to the plan, not a new stage.

**Independent Test**: Ingest the Dutch IKNL Excel, run extract plan, confirm the plan’s column roles and 153 elements, approve, implement. Inventory counts unchanged. English NKR and NBCA still extract via hints.

**Acceptance Scenarios**:

1. **Given** `nkr-breast` is ingested, **When** extract plan runs, **Then** the plan lists each projected column with a role, identifier/category/label are proposed for the IKNL headers, and 153 elements / five entities are proposed as in 003.
2. **Given** that plan is not approved, **When** implement runs, **Then** it fails closed (unchanged).
3. **Given** the reviewer does not change roles, **When** they approve and implement, **Then** inventory matches the 003 proving counts and provenance still names the columns used.

---

### User Story 2 - Reviewer remaps roles on an unrecognized layout (Priority: P1)

A CSV uses headers `foo` and `bar`. Extract plan lists both as unused and proposes row-based elements. The reviewer sets `foo` to identifier and `bar` to label, then re-runs extract plan. The new proposal uses those cells as id and display. They approve and implement. No product synonym change was required.

**Why this priority**: This is the reason for the feature. A fourth registry must not require a Python header list edit.

**Independent Test**: Ingest a two-column CSV with non-synonym headers. First plan: unused roles, row identifiers. After remapping roles and re-running plan: element ids and displays come from those columns. Implement follows the rebuilt plan.

**Acceptance Scenarios**:

1. **Given** a projected sheet whose headers are not in the hint list, **When** extract plan runs, **Then** every column appears with role unused and elements are still proposed (one per row).
2. **Given** the reviewer assigned identifier and label on that plan, **When** extract plan runs again, **Then** entities/elements are rebuilt from those roles, not from the original unused guess, and the saved roles are not overwritten by hints.
3. **Given** that rebuilt plan is approved, **When** implement runs, **Then** inventory uses the remapped identifiers and labels.
4. **Given** the reviewer asks to ignore saved roles and hint again, **When** extract plan runs in that mode, **Then** roles are proposed from header hints as on a first plan.

---

### User Story 3 - Re-plan keeps drops; duplicate roles fail closed (Priority: P2)

The reviewer dropped `gebdat` for privacy, then remapped an unused column and re-ran plan. The drop remains on that source row. Two columns marked as identifier is a conflict: the draft plan records it; implement does not write inventory until the reviewer leaves a single identifier column.

**Why this priority**: Role remap must not undo the human gate. Ambiguous roles must not silently pick a column.

**Independent Test**: Drop one IKNL row, re-run plan without `--rehint`, confirm the drop remains. Assign `id` twice, approve, implement fails and writes no inventory.

**Acceptance Scenarios**:

1. **Given** a draft plan with an element dropped by source row, **When** extract plan is re-run using saved roles, **Then** that row stays dropped with its reason.
2. **Given** two columns on one sheet share an exclusive role, **When** implement runs, **Then** it fails closed and does not write inventory.
3. **Given** verify after a successful role-remap extract, **When** it runs, **Then** coverage uses the plan’s roles (not a fresh synonym pass) and writes no tracking events.

---

### Edge Cases

- Empty identifier cells are skipped only when an identifier role is assigned (legend rows).
- A sheet with domain_var + domain_code + domain_display roles is a local code list, not an element sheet.
- Missing role entries for a column default to unused when plan is re-run against a projection that gained a column.
- Approved plan re-run becomes draft again (same as 003 overwrite).
- Entity id rename in the plan is kept only if extract plan is not re-run; re-plan derives entity ids from the category role (or sheet name).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `rh-mod-skills extract plan` MUST write, for each projected sheet, every column header with a role (`id`, `category`, `label`, `datatype`, `cardinality`, `unused`, `domain_var`, `domain_code`, `domain_display`) and whether that role came from a hint or was already on the plan.
- **FR-002**: When a sheet has no saved roles, plan MUST propose roles from a small header-hint list (Dutch/English IKNL, NBCA, generic name/id/label). Hints MUST NOT be required for extract to succeed.
- **FR-003**: When a draft plan already lists roles for a sheet, a subsequent `extract plan` MUST use those roles to rebuild entities and elements, unless the caller asked to hint again.
- **FR-004**: Exclusive roles (`id`, `category`, `label`, `datatype`, `cardinality`, `domain_var`, `domain_code`, `domain_display`) MUST be unique per sheet. Duplicates are plan conflicts; implement MUST fail until they are resolved.
- **FR-005**: Implement MUST continue to write `structured/inventory.yaml` only from an approved plan’s include-only entities/elements (003). It MUST NOT re-interpret raw projections via the hint list.
- **FR-006**: Re-running plan MUST preserve element `decision` and `reason` keyed by source + sheet + row, and entity `title` / `decision` / `merge_into` / `reason` when the derived entity id still exists.
- **FR-007**: Verify MUST measure coverage from the plan’s roles (or the same proposal the plan used), not from a synonym-only rebuild that would disagree after a remap.
- **FR-008**: Canonical writes remain `extract plan|approve|implement`; events remain `extract_planned` and `inventory_derived`. No new command group. The extract skill MAY reason about roles; it MUST NOT write inventory or the plan as a bypass of the CLI (reviewer edits of the plan YAML remain the 003 gate).

### Key Entities

- **Column role**: One projected column on one sheet, with a role and origin (hint vs already on the plan).
- **Extract plan sheet**: Projection identity (source name, sheet name), column roles, and whether the sheet is elements vs local value domain.
- **Element / entity**: Unchanged from 003; derived from the sheet’s roles instead of a global header table.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can extract a codebook whose headers are not in the hint list by editing roles on the plan and re-running extract plan, without a product code change, in one review cycle.
- **SC-002**: Dutch NKR (153 / 5), English NKR (153 / 5), and NBCA (120 / 3) still extract from hints with zero role edits.
- **SC-003**: After a role remap, verify reports `missing=0` for included rows; a second verify adds zero tracking events.
- **SC-004**: 100% of inventory writes still go through `rh-mod-skills extract implement` from an approved plan.

## Assumptions

- 003 extract CLI already exists; this feature extends the plan artifact.
- L1 remains Excel/CSV/PDF table projections (002/004). Extract still fails closed without a table projection.
- Header hints stay as a convenience for known proving files; new registries are expected to use role remap rather than expanding the hint list as the primary fix.
- Annotate, specify, and mapping are out of scope.
- Datatype and cardinality stay `unknown` unless a column has that role and the cell is non-empty.

## Out of Scope

- Inferring FHIR types from names (`*dat` ≠ date)
- Automatic language translation of headers
- A separate `extract role` CLI (reviewer edits plan YAML; re-run `extract plan`)
- Changing ingest projection shape
