# Research: annotate code systems

**Date**: 2026-09-28

## 1. ReasonHub searchable systems

**Decision**: First-class aliases match what ReasonHub actually indexes: SNOMED CT, LOINC, RxNorm, ICD-10-CM, UCUM. Cross-system search is plan alias `all`.

**Rationale**: `list_available_codesystem_versions` on ReasonHub returns those five URIs. `search_icd10` is ICD-10-CM (`http://hl7.org/fhir/sid/icd-10-cm`), not WHO ICD-10.

**Alternatives considered**: Drop `icd-10` (breaks 005 plans). Treat `all` as a fake URI (would poison bindings).

## 2. Keep `icd-10`

**Decision**: `icd-10` → `http://hl7.org/fhir/sid/icd-10` unchanged. New `icd-10-cm` → `http://hl7.org/fhir/sid/icd-10-cm`. Skill uses `search_icd10` for both `icd-10` and `icd-10-cm`; recorded candidate URI follows the alias used (or the MCP hit URI when `all`).

**Rationale**: 005 already shipped `icd-10`. ReasonHub does not index WHO ICD-10; reviewers who want CM must say `icd-10-cm`.

## 3. `all` is a search mode

**Decision**: Valid on `--system` only. `system_uri("all")` raises. Enrich `--candidate 'all|…'` fails.

**Rationale**: Candidates must be bindable FHIR Codings.

## 4. Canonical URIs

| Alias | URI |
|-------|-----|
| snomed | `http://snomed.info/sct` |
| loinc | `http://loinc.org` |
| icd-10 | `http://hl7.org/fhir/sid/icd-10` |
| icd-10-cm | `http://hl7.org/fhir/sid/icd-10-cm` |
| rxnorm | `http://www.nlm.nih.gov/research/umls/rxnorm` |
| ucum | `http://unitsofmeasure.org` |

## 5. Skill MCP map

| Plan `systems` | MCP tool |
|----------------|----------|
| snomed | `search_snomed` |
| loinc | `search_loinc` |
| icd-10, icd-10-cm | `search_icd10` |
| rxnorm | `search_rxnorm` |
| ucum | `search_ucum` |
| all (present) | `search_all_codesystems` (once; do not also fan out per named system) |

Copy MCP `system` URI from the hit when using `all`. Cap remains 5.
