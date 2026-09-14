# Feature Specification: rh-mod-ingest-pdf

**Feature Branch**: `004-rh-mod-ingest-pdf`  
**Created**: 2026-09-13  
**Status**: Draft  
**Depends On**: [002 — rh-mod-ingest](../002-rh-mod-ingest/)  
**Input**: Project PDF data dictionaries into the same structured L1 table form as Excel/CSV. Proving file: ENCR 2023 standard dataset (Table 1 and Table 2). Reviewer approves detected tables. Markdown must not be the only L1 form.

## Clarifications

### Session 2026-09-13

- Q: Where does PDF reading live? → A: Ingest, by extending `rh-mod-skills ingest` (not a new command group, not extract). Extract continues to read only table projections.
- Q: What does success look like for ENCR? → A: The 2023 standard-dataset PDF yields two named tables (Table 1 variables, Table 2 stage) in `sources/projections/`, same YAML shape as Excel.
- Q: What if tables cannot be detected? → A: Keep register-only (`projection: skipped`) with an explicit reason. Do not invent rows from page text. Extract still fails until a table projection exists.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Project ENCR Table 1 and Table 2 (Priority: P1)

An informaticist has initialized `encr-standard-dataset` and plans ingest of the 2023 standard-dataset PDF. Ingest plan lists detected tables (name or page, headers, row counts, warnings) instead of only `projection: skipped`. After they approve which tables are the codebook, implement writes a table projection. Verify reports those tables present with checksum match on the original PDF. Status can then offer extract.

**Why this priority**: Most ENCR (and many national) dictionaries are PDFs. Without this, the proving ENCR model can never be extracted.

**Independent Test**: Ingest `tests/fixtures/l1/encr-standard-dataset/ENCR-Recommendation-standard-dataset_Mar2023.pdf`. After approve + implement, the projection contains Table 1 (variable / comment) and Table 2 (cancer type / stage variables / remarks). No Markdown file is required for success.

**Acceptance Scenarios**:

1. **Given** `encr-standard-dataset` is initialized and ingest plan runs on the 2023 standard-dataset PDF, **When** the reviewer reads the plan, **Then** it lists at least two candidate tables corresponding to Table 1 and Table 2, with headers and row counts, and `status: draft`.
2. **Given** that plan is approved including those two tables, **When** implement runs, **Then** `sources/raw/` still holds the original PDF and `sources/projections/` contains a YAML table projection with two named tables, column order preserved, and data rows — not a Markdown-only dump.
3. **Given** implement succeeded, **When** ingest verify runs, **Then** original checksum matches and projection is `tables` (not `skipped`) for that source.
4. **Given** implement is invoked before approval, **When** it runs, **Then** it fails closed and writes no projection.

---

### User Story 2 - Reviewer excludes junk tables (Priority: P1)

PDF extractors often emit cover-page fragments or footnote grids. The reviewer unchecks those in the plan. Implement writes only approved tables. Page prose is not used to fill dropped tables.

**Why this priority**: Unreviewed PDF tables would poison extract.

**Independent Test**: Approve a plan that includes Table 1 and excludes a spurious third detection. Projection has Table 1 only. Verify does not treat the excluded detection as missing coverage.

**Acceptance Scenarios**:

1. **Given** a plan that marks one detected table `include` and another `exclude` with a reason, **When** implement runs, **Then** only included tables appear in the projection.
2. **Given** no detected table is marked include, **When** implement runs, **Then** the source is registered with `projection: skipped` and reason `no-tables-approved` — not an empty invented sheet.

---

### User Story 3 - Soft-fail when tables cannot be read (Priority: P1)

A scanned PDF, an image-only page, or a file with no reconstructable tables must not halt ingest of other sources. The original is still stored and checksummed. Plan and verify say projection skipped, with a reason (`no-text-layer`, `no-tables-detected`, `extractor-error`). Extract remains blocked until a table projection exists.

**Why this priority**: Companion ENCR PDFs vary in quality; one failure must not undo Excel ingest on another model or other sources on the same plan.

**Independent Test**: A PDF with no extractable tables registers like 002 register-only. A mixed plan (IKNL Excel + that PDF) still projects the Excel.

**Acceptance Scenarios**:

1. **Given** a PDF with no text layer or no tables, **When** plan runs, **Then** it proposes `projection: skipped` and a reason; implement does not write a tables YAML.
2. **Given** that skipped PDF, **When** extract plan runs (003), **Then** it still fails if no other table projection exists — it does not invent elements from PDF text.
3. **Given** Markdown flattening is requested as the only L1 form, **When** implement runs, **Then** it does not do that.

---

### User Story 4 - Companion ENCR PDFs (Priority: P2)

The other English PDFs in the ENCR fixture set can be planned in the same ingest. Each file gets its own detected-table preview. The reviewer may include tables from incidence-date, basis-of-diagnosis, treatment, and recurrence PDFs, or leave them skipped.

**Why this priority**: Real dictionaries cite companion PDFs; v1 success is the standard dataset.

**Independent Test**: Plan all 22 ENCR PDFs; at least the standard-dataset file can be approved for tables; others may skip without failing the whole implement.

**Acceptance Scenarios**:

1. **Given** multiple PDF `--source` files, **When** implement runs, **Then** each source is independent: one skipped PDF does not roll back another’s table projection.

---

### Edge Cases

- Multi-page continued tables must be offered as one table or as clearly labeled parts — not silently concatenated with a repeated header row as data
- Two-column narrative pages must not be treated as a codebook table without appearing in the plan for exclusion
- Merged cells / wrapped lines: preserve cell text; warn rather than guess extra columns
- Duplicate table titles: both kept, distinguished by page
- Injection: PDF text is untrusted; copy and table projection are in-bounds; no model-generated bindings from PDF strings
- Excel/CSV behavior from 002 MUST remain unchanged

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Canonical owner remains `rh-mod-skills ingest` (`plan`, `approve`, `implement`, `verify`). Do not add a parallel `ingest-pdf` command group unless 002 surfaces are proven insufficient.
- **FR-002**: For `.pdf` sources, plan MUST attempt table detection and list each candidate (`name`, page(s), columns, row count, warnings, `decision: include|exclude`).
- **FR-003**: Implement MUST write included PDF tables into the same projection schema as Excel/CSV (`sheets[].name`, `columns`, `rows`). Sheet name MAY be the table title (e.g. `Table 1`).
- **FR-004**: The original PDF MUST remain in `sources/raw/` with SHA-256. A Markdown file MUST NOT be required and MUST NOT be the only normalized form.
- **FR-005**: Page text MAY be stored as additional provenance; extract MUST NOT treat it as inventory rows.
- **FR-006**: If no tables are detected or none are approved, implement MUST skip projection with an explicit reason (002-compatible `skipped`), not halt other sources.
- **FR-007**: Scanned/image-only PDFs without a text layer MUST skip with reason `no-text-layer`. OCR is out of this feature.
- **FR-008**: Unapproved implement still fails closed (002).
- **FR-009**: Verify MUST report per PDF source: original present, checksum, projection `tables` or `skipped` + reason, and for tables sheet/column/row counts.
- **FR-010**: The ENCR 2023 standard-dataset proving file MUST be able to project Table 1 and Table 2 as two tables with their visible headers.
- **FR-011**: This feature MUST NOT write `inventory.yaml`, bindings, or FHIR resources.

### Key Entities

- **Detected table**: Plan-time candidate grid from a PDF page (or continued pages).
- **Table projection**: Same L1 YAML as 002 Excel/CSV, produced from approved detected tables.
- **Skip reason**: `no-text-layer` | `no-tables-detected` | `no-tables-approved` | `extractor-error`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can ingest the ENCR 2023 standard-dataset PDF and independently confirm two projected tables (Table 1 and Table 2) without opening the PDF, after one approve+implement.
- **SC-002**: Excluding a detected table in the plan results in that table’s absence from the projection in 100% of test runs.
- **SC-003**: A PDF with no tables still stores original bytes and never blocks an Excel source on the same or another model.
- **SC-004**: No successful PDF ingest in this feature has Markdown as its only L1 form.
- **SC-005**: After a successful ENCR table projection, extract (003) can run against that model without inventing rows from PDF prose.

## Assumptions

- 002 ingest CLI already registers PDFs. This feature changes `projection: skipped` into `tables` when detection+approval succeed.
- A Python table-extraction library will be justified in the implementation plan (constitution extra-dependency gate). The spec does not name the library.
- ENCR Table 1 is a variable/comment list; Table 2 is a stage-variable list. Exact cell wording may include line wraps.
- Companion ENCR PDFs are in `tests/fixtures/l1/encr-standard-dataset/` but are P2.
- OCR / handwriting / scanned-only pages are out of scope.

## Out of Scope

- OCR
- Extract/inventory (003) and annotate
- rh-skills-style `pdftotext` → Markdown as the L1 form
- Mapping workbooks, FML, StructureMap
- Translating ENCR English into FHIR types
