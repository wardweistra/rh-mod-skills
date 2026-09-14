# Research: rh-mod-extract

**Date**: 2026-09-13

## 1. Read projections, not workbooks

**Decision**: Extract plan reads `sources/projections/*.yaml` recorded in tracking with `projection: tables`. It does not open raw `.xlsx` as the only form.

**Rationale**: L1 truth is the approved ingest projection. Re-parsing Excel would bypass checksum/provenance.

**Alternatives considered**: Re-read openpyxl on implement (rejected — duplicates 002 and skips reviewer-facing L1).

## 2. Default entities from category column

**Decision**: Prefer identifier/category/label headers in this order: IKNL names (`variabele_name`, `variabele_categorie`, `variabele_label`), then synonyms (`name`/`id`/`code`, `category`/`group`/`entity`, `label`/`description`/`title`). No category column → one entity per sheet. Unrecognized layout → one entity per sheet, one element per row, leftover columns in `notes`.

**Rationale**: Spec assumptions. Fail-open on layout so a CSV with different headers still extracts.

**Alternatives considered**: Require exact IKNL headers (too brittle). Infer FHIR types from `*dat` (forbidden).

## 3. Plan is the only implement input

**Decision**: Implement copies include-only entities/elements from `extract-plan.yaml`. Drops, merges (`decision: merge-into` + `merge_into`), and renames in the plan are authoritative. Projection is not re-merged on implement.

**Rationale**: Constitution II human gate. Silent restore of `gebdat` would violate US2.

**Alternatives considered**: Implement always refreshes from projection then applies a diff (more code, easier to undo reviewer drops).

## 4. PDF-only fail closed

**Decision**: If the model has no table projection, plan exits non-zero and writes no `extract-plan.yaml`. Message points at ingest tables and 004 for PDFs.

**Rationale**: Spec US3 / FR-010. Inventing rows from PDF text is forbidden.

**Alternatives considered**: Write an empty draft plan (too easy to approve by mistake).

## 5. Value domains

**Decision**: A projection sheet is a local code list only if it has columns matching variable + code + display (synonyms: `variable`/`variabele`/`element`, `code`/`waarde`, `display`/`omschrijving`). IKNL’s three-column dictionary does not match — omit `value-domains.yaml`. Do not bind SNOMED/LOINC.

**Rationale**: US4 P2. Inventing codes from labels is annotate’s job, not extract’s.

**Alternatives considered**: Treat every unique label as a code (rejected).
