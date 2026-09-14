# Research: RH Mod Skills Framework (implementation slice)

**Phase**: 0 — Pre-Design Research  
**Branch**: `001-rh-mod-framework`  
**Date**: 2026-09-11

This slice implements the workspace skeleton only (`init`, `tracking.yaml`, directory layout, read-only `status`). Structured L1 ingest is specified in 002.

---

## 1. Unit of work: model, not topic

**Decision**: Consumer projects use `models/<model-id>/`. The CLI MUST NOT create or read `topics/`.

**Rationale**: rh-skills organizes work as clinical topics that consume shared guideline sources. This product organizes work as a source data model evolving toward one FHIR logical model. Mixing `topics/` would collide with rh-skills and contradict the constitution.

**Alternatives considered**: Reuse `topics/` with a `kind: model` flag (rejected — same path, different semantics). Put each model in its own git repo (rejected — a consumer may hold ENCR and NKR side by side).

---

## 2. `tracking.yaml` lives at the consumer root

**Decision**: One `tracking.yaml` at the consumer project root (the directory from which the informaticist runs the CLI). It contains a `models:` list. Named events are append-only via shared helpers; raw string writes are forbidden.

**Rationale**: Matches the rh-skills operational pattern (one tracking file, many units of work) so status can list every model. Per-model tracking files would make `status` with no argument scan the tree and invite drift.

**Alternatives considered**: `models/<id>/tracking.yaml` only (rejected — no project-level index). Dual files (rejected — two write paths).

---

## 3. Sources are owned by the model

**Decision**: Raw L1 files live at `models/<id>/sources/`, not a repo-root `sources/` shared across models.

**Rationale**: A codebook belongs to one model. Sharing ENCR across models is a later copy-or-pin concern, not a v1 requirement. rh-skills shares `sources/` because one guideline PDF feeds many topics; that does not apply here.

**Alternatives considered**: Root `sources/` plus per-model references (deferred until a source is proven to feed two models).

---

## 4. Init is scaffolding, not a gated stage

**Decision**: `rh-mod-skills init` writes directories and a `model_created` event without `plan → implement → verify`. `status` is read-only and writes nothing.

**Rationale**: Constitution II requires the gated flow for features that *advance lifecycle state*. Init creates the workspace; ingest is the first gated stage (002). This matches rh-skills `init`.

**Alternatives considered**: Force a plan file before mkdir (rejected — nothing to review).

---

## 5. Consumer root vs tool repo

**Decision**: Resolve the consumer root by walking up from cwd for `tracking.yaml`. If none exists, `init` uses cwd. If cwd (or the resolved root) is this tool repository (`pyproject.toml` name `rh-mod-skills`) and is not `example-project/`, `init` MUST refuse unless `RH_REPO_ROOT` is set.

**Rationale**: rh-skills `repo_root()` also treats `pyproject.toml` as a root marker, which makes it easy to scaffold inside the tool repo. This product’s unit of work is a *consumer* project.

**Alternatives considered**: Always require `--root` (worse UX). Silently init inside the tool repo (rejected).

---

## 6. Proving corpus (L1 inputs on disk)

**Decision**: Copy the user-provided sources into `tests/fixtures/l1/` now. Do not ingest them in 001.

| Model id | Fixture | Shape |
|----------|---------|--------|
| `nkr-breast` | `IKNL_Data_dictionary.xlsx` | 1 sheet `Variabelen`; columns `variabele_name`, `variabele_categorie`, `variabele_label`; 153 variables in 5 categories (Patiëntgegevens, Tumorgegevens, Behandelgegevens, Procesgegevens, Risicofactoren). From the [NKR-datacatalogus](https://iknl.nl/nkr/cijfers-op-maat/over-datacatalogus). |
| `encr-standard-dataset` | `encr-standard-dataset/*.pdf` (22 English files) | ENCR 2023 standard dataset (Table 1 + Table 2) plus cited companions (incidence date, basis of diagnosis, treatment, recurrence, multiple primaries, CNS, haematological, condensed TNM) and the other English PDFs on [ENCR Recommendations](https://www.encr.eu/ENCR-Recommendations). |

**Rationale**: Two models, not one. ENCR is a European minimum dataset; NKR breast is a national tumour-specific dictionary. Mapping between them is rh-map-skills.

**Alternatives considered**: One model with both files as sources (rejected — different identities and versions). Flatten the PDF to Markdown in 001 (forbidden by constitution).

---

## 7. Excel/CSV now, PDF structured extract later

**Decision**: 001 does not parse source bytes. 002 structured projection is `.xlsx` / `.csv` only. PDF is registered as original bytes + checksum; extracting Table 1 / Table 2 into rows is [004-rh-mod-ingest-pdf](../004-rh-mod-ingest-pdf/).

**Rationale**: Constitution delivery constraint and 001 assumptions. The IKNL workbook is the first file that can round-trip sheet/column/row. The ENCR PDF is still a first-class L1 source for provenance.

**Alternatives considered**: Pandoc-to-Markdown as the only L1 form (forbidden). Shipping a PDF table parser in 001 (out of slice).

---

## 8. Duplicate rh-skills CLI helpers, do not import rh-skills

**Decision**: Copy the tracking lock / append-event / SHA-256 patterns into `rh_mod_skills.common`. Do not depend on the `rh-skills` package.

**Rationale**: 001 assumptions allow duplication until `rh-skills-core` exists. Importing rh-skills would pull clinical L2 types this product must not own.

**Alternatives considered**: Extract `rh-skills-core` now (too much scope). Vendor the rh-skills repo (rejected).

---

## 9. Event names reserved in schema, emitted later

**Decision**: The tracking schema enumerates the FR-014 event types now. 001 only *emits* `model_created` (root and per-model).

**Rationale**: Status next-steps in 001 can already name “ingest” as the next stage when `source_added` is absent, without ingest existing yet.

**Alternatives considered**: Invent a parallel event vocabulary (rejected — FR-014 is the contract).
