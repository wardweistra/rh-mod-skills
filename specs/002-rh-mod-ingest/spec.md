# Feature Specification: rh-mod-ingest

**Feature Branch**: `002-rh-mod-ingest`  
**Created**: 2026-09-11  
**Status**: Draft  
**Depends On**: [001 — RH Mod Skills Framework](../001-rh-mod-framework/)  
**Input**: Ingest L1 source dictionaries into a model workspace with structure-preserving Excel/CSV projection. First proving corpus: IKNL NKR breast cancer Excel data dictionary and ENCR 2023 standard dataset PDF.

## Clarifications

### Session 2026-09-11

- Q: What is in the first proving corpus? → A: `nkr-breast` uses the IKNL Excel export (1 sheet `Variabelen`, 153 variables, columns `variabele_name` / `variabele_categorie` / `variabele_label`) from the [NKR-datacatalogus](https://iknl.nl/nkr/cijfers-op-maat/over-datacatalogus). `encr-standard-dataset` uses the ENCR 2023 [standard dataset PDF](https://www.encr.eu/ENCR-Recommendations) (Table 1 + Table 2) plus the other English recommendation PDFs from that page (cited companions and the rest of the English list). All are registered as L1; only Excel/CSV get a table projection.
- Q: How is PDF handled in v1? → A: Register original bytes, checksum, and optional origin URL. Do not flatten to Markdown as the only form. Extracting PDF tables into rows is a later ingest plugin, not this feature.
- Q: Is ingest gated? → A: Yes. `plan → human approval → implement → verify`. Implement fails closed without an approved plan.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingest the IKNL breast cancer dictionary (Priority: P1)

An informaticist has initialized `nkr-breast` and has the IKNL Excel data dictionary. They run ingest plan, approve it, then implement. The original workbook is stored under the model’s sources, checksummed, and a structured projection lists the sheet name, the three column headers in order, and all 153 variable rows. Status then says the model is ready for extract.

**Why this priority**: This is the first file that can be tried end-to-end as structured L1. Without it, extract has nothing honest to read.

**Independent Test**: From a consumer directory with `nkr-breast` already initialized, ingest the fixture `tests/fixtures/l1/nkr-breast/IKNL_Data_dictionary.xlsx`. After implement, the original file is present, a structured table projection contains 153 data rows, and `source_added` is in tracking. No Markdown file is required for success.

**Acceptance Scenarios**:

1. **Given** `nkr-breast` is initialized and an approved ingest plan names the IKNL workbook, **When** ingest implement runs, **Then** the original `.xlsx` is copied into `models/nkr-breast/sources/`, a SHA-256 checksum is recorded, and a structured projection preserves sheet `Variabelen` and columns `variabele_name`, `variabele_categorie`, `variabele_label` with 153 data rows.
2. **Given** that ingest has completed, **When** a reviewer opens the projection, **Then** row values match the workbook (e.g. `gebdat` / `Patiëntgegevens` / `Geboortedatum`) and category counts are intact (Behandelgegevens 60, Tumorgegevens 37, Procesgegevens 33, Patiëntgegevens 18, Risicofactoren 5).
3. **Given** ingest implement is invoked with no approved plan, **When** the command runs, **Then** it fails closed and writes no source files and no `source_added` event.

---

### User Story 2 - Register the ENCR standard dataset PDF (Priority: P1)

The same informaticist initializes `encr-standard-dataset` and registers the ENCR 2023 standard-dataset PDF as an L1 source, including the public origin URL. The PDF is stored and checksummed. Ingest does not pretend the PDF has been turned into rows. Status reports the source as registered and that structured projection was skipped because the type is PDF.

**Why this priority**: The ENCR document is a real first L1 input and the European counterpart to NKR. Registering it now preserves provenance; inventing a Markdown dump would violate the constitution.

**Independent Test**: Ingest the fixture `tests/fixtures/l1/encr-standard-dataset/ENCR-Recommendation-standard-dataset_Mar2023.pdf` with origin URL `https://www.encr.eu/ENCR-Recommendations`. Original bytes and checksum are stored; no Markdown-only normalized form is produced; verify reports projection skipped for PDF.

**Acceptance Scenarios**:

1. **Given** `encr-standard-dataset` is initialized and an approved plan names the ENCR PDF, **When** ingest implement runs, **Then** the original PDF is stored under `models/encr-standard-dataset/sources/`, checksummed, and tracking records `source_added` with type `pdf` and the origin URL.
2. **Given** that PDF ingest completed, **When** ingest verify runs, **Then** it reports original present, checksum match, and structured projection `skipped` (not failed) for PDF.
3. **Given** a user asks ingest to flatten the PDF to Markdown as the only normalized form, **When** implement runs, **Then** it does not do that — Markdown is not an acceptable sole L1 projection.

---

### User Story 3 - Plan, verify, and re-ingest safely (Priority: P1)

Before writing, ingest plan lists each source, its type, and whether a structured projection will run. After implement, verify is rerunnable and writes nothing. If the IKNL file is replaced with different bytes, verify flags checksum drift and implement MUST NOT silently overwrite approved L2/L3 artifacts.

**Why this priority**: Provenance and the constitution’s re-ingest rule are the safety net for trying real dictionaries more than once.

**Independent Test**: Run plan (no writes of sources), implement, verify (no tracking events). Change the Excel bytes, run verify — drift is reported. With L2 present, implement without an explicit rematch/force path leaves L2 untouched.

**Acceptance Scenarios**:

1. **Given** initialized `nkr-breast` and the IKNL path, **When** ingest plan runs, **Then** a durable plan under `models/nkr-breast/process/plans/` lists the file, type `excel`, and `projection: tables`, and no source files are copied yet.
2. **Given** ingest has completed, **When** ingest verify runs twice, **Then** both runs report original present, checksum match, projection row/column counts, and neither run appends tracking events.
3. **Given** the stored Excel checksum no longer matches the file on disk, **When** verify runs, **Then** it reports the source as changed (blocking for that source) and does not rewrite L2.
4. **Given** `structured/` already contains reviewer-approved artifacts and the codebook checksum changed, **When** implement runs without an explicit rematch acknowledgement, **Then** it fails closed and does not overwrite those artifacts.

---

### User Story 4 - Ingest a CSV dictionary (Priority: P2)

A registry exports a codebook as CSV instead of Excel. Ingest treats the file as a single sheet named after the file stem, preserves header row and data rows, and records type `csv`.

**Why this priority**: Constitution v1 formats are Excel and CSV. CSV can ship after the IKNL Excel path works.

**Independent Test**: Convert or author a three-column CSV with the same headers as IKNL (subset of rows). Ingest produces a structured projection with one sheet and those columns.

**Acceptance Scenarios**:

1. **Given** an approved plan for a `.csv` codebook, **When** implement runs, **Then** the original CSV is stored and the projection has one sheet, ordered headers, and all data rows.

---

### Edge Cases

- Workbook with multiple sheets: each sheet is a named table in the projection; sheets are not silently merged
- Empty sheet or header-only sheet: projection records zero data rows; verify warns, does not invent cardinality
- Duplicate column headers on one sheet: preserved as-is and flagged as a warning
- Homonyms across sheets: allowed; provenance is sheet + column
- Merged Excel header cells: treat as untrusted layout; fail or warn per sheet rather than guess a flattened header
- File type not xlsx/csv/pdf: plan may list it; implement registers original + checksum and skips structured projection with an explicit reason
- Source content may contain adversarial text (injection): analysis/commands MUST declare an injection boundary before reading cell values for anything other than copy/checksum/tabular projection
- Two models in one consumer project: ingest on `nkr-breast` MUST NOT write under `encr-standard-dataset/`
- Missing model / not initialized: fail with guidance to run `init`
- Idempotent re-run with unchanged checksum: skip copy; keep existing projection; do not duplicate `source_added`

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Canonical write owner is `rh-mod-skills ingest` (`plan`, `implement`, `verify`). Skills MUST NOT write source files or tracking events directly.
- **FR-002**: `ingest plan <model>` MUST write a durable plan under `models/<model>/process/plans/` listing each source path, detected type, origin URL (if given), and whether structured table projection will run. Plan MUST NOT copy sources.
- **FR-003**: `ingest implement <model>` MUST fail closed if that plan is missing or not approved.
- **FR-004**: Implement MUST copy original bytes into `models/<model>/sources/`, record SHA-256, type, and optional origin URL, and append `source_added` (append-only named event helpers from 001).
- **FR-005**: For `.xlsx` and `.csv`, implement MUST write a structured table projection that preserves sheet (or file-stem) name, column header order, and row values. Markdown flattening MUST NOT be the only normalized form and MUST NOT be required for success.
- **FR-006**: For `.pdf`, implement MUST store original + checksum and MUST skip structured table projection with an explicit skipped reason. It MUST NOT emit a Markdown-only L1 form.
- **FR-007**: The IKNL proving file MUST project sheet `Variabelen` with headers `variabele_name`, `variabele_categorie`, `variabele_label` and 153 data rows.
- **FR-008**: `ingest verify <model>` MUST be non-destructive (no lifecycle events). It MUST report per source: original present, checksum match or drift, projection present/skipped, and for tabular sources a row/column count.
- **FR-009**: Checksum drift MUST be visible in verify and MUST NOT silently overwrite approved L2/L3 artifacts on implement.
- **FR-010**: Source dictionary content is untrusted. Copy, checksum, and tabular projection are in-bounds; any later linguistic analysis MUST occur only after an explicit injection-boundary declaration in the skill (when that skill exists).
- **FR-011**: Ingest MUST NOT create mapping workbooks, FHIR Mapping Language, or `StructureMap` resources.
- **FR-012**: Tabular projection MUST NOT invent cardinality, datatypes, or terminology bindings — those belong to extract/annotate.
- **FR-013**: A source registered on one model MUST NOT appear as a file under a different model’s `sources/`.
- **FR-014**: `status` (from 001) after successful tabular ingest MUST report the model ready for extract, not for mapping.

### Key Entities

- **Ingest plan**: Reviewable file listing sources to register, types, projection intent, and approval state.
- **Source original**: Unmodified L1 file bytes under the model’s `sources/` tree, with checksum and optional origin URL.
- **Table projection**: Machine-readable L1 form of sheets/columns/rows derived from Excel or CSV. Not an inventory and not a logical model.
- **Skipped projection**: Record that a registered source (e.g. PDF) has no table projection yet, with a reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can ingest the IKNL Excel fixture into `nkr-breast` and independently confirm 153 projected rows and the five category counts without opening Excel, in a single implement after plan approval.
- **SC-002**: A reviewer can ingest the ENCR PDF fixtures into `encr-standard-dataset` and independently confirm each original file hash matches the fixture; no Markdown dump is required or produced as the sole L1 form.
- **SC-003**: Verify on an unchanged ingest reports the same pass result on two consecutive runs and adds zero tracking events.
- **SC-004**: After a checksum change, verify flags the source before any L2 file is modified.
- **SC-005**: 100% of durable source writes in this feature go through `rh-mod-skills ingest`; agents do not create source files by hand.

## Assumptions

- 001 `init` / `tracking.yaml` / `models/<id>/` exist (or land immediately before this implementation).
- v1 structured projection formats are Excel (`.xlsx`) and CSV only. `.xls` and ODS are out of scope.
- PDF table extraction (ENCR Table 1 / Table 2 → rows) is a later ingest plugin. Companion ENCR PDFs in `tests/fixtures/l1/encr-standard-dataset/` are registered the same way as the index PDF.
- The two proving sources are two models, not one model with two files. Mapping NKR → ENCR is rh-map-skills.
- Projection stores literals from the sheet; it does not translate Dutch labels or bind SNOMED/ICD-O.
- `openpyxl` (or equivalent) is an allowed dependency expansion justified in the 002 plan, not this spec.
- Curated skill `rh-mod-ingest` is authored only after these CLI commands exist.

## Out of Scope

- PDF/OCR table extraction (ENCR PDFs are registered as originals only in this feature)
- Translations of ENCR recommendations (ES/FR/RO/DE) and the Toronto Childhood Cancer Stage Guidelines (endorsement page only, no ENCR-hosted PDF)
- Element inventory, value domains, terminology bindings
- FHIR `StructureDefinition` / ValueSet generation
- Mapping workbooks, FML, StructureMap
- Import of OMOP DDL, XSD, or existing FHIR StructureDefinitions
