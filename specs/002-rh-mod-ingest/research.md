# Research: rh-mod-ingest

**Date**: 2026-09-12

## 1. Excel library

**Decision**: `openpyxl` (read-only, `data_only=True`).  
**Rationale**: stdlib cannot parse xlsx; constitution allows a justified extra dependency.  
**Alternatives**: pandas (heavier), xlrd (xls only).

## 2. Projection format

**Decision**: YAML under `sources/projections/<source-name>.yaml` with `sheets[].name`, `columns`, `rows`.  
**Rationale**: Machine-readable, round-trippable with ruamel, not Markdown.  
**Alternatives**: JSON (fine, but YAML matches the rest of the product), per-sheet CSV (splits provenance).

## 3. Originals location

**Decision**: `sources/raw/<original-filename>` keep the source filename.  
**Rationale**: Checksum of original bytes; reviewers can open the same file they supplied.

## 4. Approval command

**Decision**: `ingest approve <model>` sets `status: approved` on the plan.  
**Rationale**: Durable write must go through CLI, not a skill editing YAML.

## 5. PDF

**Decision**: Register only. `projection: skipped`, reason `pdf`.  
**Rationale**: Spec + constitution 1.0 delivery constraint. ENCR Table 1/2 extraction is [004-rh-mod-ingest-pdf](../004-rh-mod-ingest-pdf/) (constitution 1.1.0 now allows PDF table projections).
