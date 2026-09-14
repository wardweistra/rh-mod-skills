# Research: rh-mod-ingest-pdf

**Date**: 2026-09-14

## 1. Table library

**Decision**: `pdfplumber` (`Page.extract_tables()`, `page.chars` for text-layer detection).

**Rationale**: Pure Python, no Ghostscript/Java. Constitution extra-dependency gate: stdlib and `pypdf` do not reconstruct table grids. Camelot needs Ghostscript; tabula needs Java.

**Alternatives considered**: Camelot, tabula-py, `pdftotext` (forbidden as the only L1 form).

## 2. Continued tables

**Decision**: Merge consecutive-page tables with the same column count. If the next page repeats the header, drop that header row. If it does not, append all rows and warn `continued-without-header`. Do not concatenate different column counts.

**Rationale**: ENCR Table 1 header is on page 2; page 3 continues with “Postal code…” (no repeated header). Silent header-as-data would poison extract.

**Alternatives considered**: One sheet per page (spec forbids silent split of a continued codebook table).

## 3. Naming

**Decision**: Prefer a standalone `Table N` line on the first page of a merged group. Else `page-{n}-table-{i}`. Duplicate titles append ` (p.{page})`.

**Rationale**: Spec allows sheet name to be the table title. ENCR page 2 has `Table 1`; page 4 has `Table 2`.

## 4. Default include/exclude

**Decision**: `include` when ≥2 columns and ≥2 data rows; otherwise `exclude` with reason `too-small`. Reviewer may flip decisions in the plan.

**Rationale**: Cover-page fragments should not default into the codebook. ENCR Table 1/2 both pass.

## 5. Re-project when checksum is unchanged

**Decision**: If the plan asks for `tables`, rewrite the projection even when the PDF checksum matches a prior `skipped` registration.

**Rationale**: example-project already registered the ENCR PDF as skipped. Skipping on checksum match would make 004 a no-op.

## 6. Extract synonyms

**Decision**: Add identifier synonym `variable` and label synonym `comment` in extract (003). No ENCR-specific extract parser.

**Rationale**: SC-005 requires extract to run on the projected tables. Constitution V: extend existing header detection.

## 7. Page text sidecar

**Decision**: Do not write page-text files in this feature.

**Rationale**: Spec FR-005 is MAY. Extra files would invite extract to read prose.
