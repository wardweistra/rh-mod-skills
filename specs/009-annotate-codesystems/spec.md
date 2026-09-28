# Feature Specification: annotate code systems

**Feature Branch**: `009-annotate-codesystems`  
**Created**: 2026-09-28  
**Status**: Implemented  
**Depends On**: [005 — rh-mod-annotate](../005-rh-mod-annotate/)  
**Input**: Wire the remaining ReasonHub-searchable code systems into annotate so a reviewer can ask for RxNorm, UCUM, ICD-10-CM, or a cross-system search the same way they already ask for SNOMED or LOINC. Default stays SNOMED. The CLI still does not search; it records system names on the plan and expands aliases when recording candidates.

## Clarifications

### Session 2026-09-28

- Q: Which systems to add? → A: The lookup service’s searchable set beyond SNOMED and LOINC: RxNorm, UCUM, ICD-10-CM, plus a cross-system search mode (`all`). Existing `icd-10` alias remains for plans that already use it.
- Q: Is `all` a code system? → A: No. It is a search-across-all hint on the plan. Recorded candidate rows still carry a concrete system URI from the hit (never a fake `all` URI).
- Q: Does default change? → A: No. Omitting `--system` still means SNOMED CT.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plan names the extra systems (Priority: P1)

An informaticist annotating a medication or unit field runs annotate plan with `--system rxnorm`, `--system ucum`, and/or `--system icd-10-cm` (repeatable, combinable with `snomed` / `loinc` / `icd-10`). The draft plan records those names. The skill later searches only the named systems. Bindings are not written.

**Why this priority**: Without first-class names, the agent has no contract to search RxNorm/UCUM/ICD-10-CM and reviewers cannot ask for them on the plan.

**Independent Test**: On an extracted `nkr-breast`, `annotate plan --element gesl --system rxnorm` writes `systems: [rxnorm]`. Same for `ucum` and `icd-10-cm`. Unknown `--system foo` fails and writes no plan.

**Acceptance Scenarios**:

1. **Given** an extracted model, **When** annotate plan runs with `--system rxnorm` (or `ucum`, or `icd-10-cm`), **Then** the plan `systems` list contains that name and status is draft.
2. **Given** `--system snomed --system rxnorm`, **When** plan runs, **Then** both names are recorded in order.
3. **Given** `--system not-a-system`, **When** plan runs, **Then** it fails closed and writes no plan.
4. **Given** no `--system`, **When** plan runs, **Then** `systems` is still `[snomed]`.

---

### User Story 2 - Enrich expands the new aliases (Priority: P1)

The skill recorded ReasonHub hits using short names (`rxnorm|…`, `ucum|…`, `icd-10-cm|…`). Enrich stores the canonical FHIR system URI, code, and display. Full `http…` URIs still work. The CLI does not call the lookup service.

**Why this priority**: Plan names are useless if enrich cannot record those systems as bindings-ready candidates.

**Independent Test**: Enrich `--candidate 'rxnorm|197361|Aspirin'` stores system `http://www.nlm.nih.gov/research/umls/rxnorm`. Same mapping for UCUM and ICD-10-CM. An `http://…` candidate is stored unchanged.

**Acceptance Scenarios**:

1. **Given** a draft plan element, **When** enrich records a `rxnorm|code|display` candidate, **Then** the plan candidate `system` is the RxNorm FHIR URI.
2. **Given** a `ucum|code|display` candidate, **When** enrich records it, **Then** `system` is the UCUM FHIR URI.
3. **Given** an `icd-10-cm|code|display` candidate, **When** enrich records it, **Then** `system` is the ICD-10-CM FHIR URI.
4. **Given** a candidate whose system already starts with `http`, **When** enrich records it, **Then** that URI is copied as-is.

---

### User Story 3 - Cross-system search mode (Priority: P2)

For a field whose system is unknown, the reviewer plans with `--system all`. The plan records `all`. The skill searches across the lookup service’s code systems and records each hit with that hit’s own system URI. Import/implement are unchanged.

**Why this priority**: ReasonHub can search all systems at once; the plan needs a name for that mode so the skill does not invent a default mix.

**Independent Test**: Plan `--system all` records `systems: [all]`. Enrich of mixed URI candidates still stores each URI. `all` is not a valid system on a `--candidate` row (must be a real system or `http` URI).

**Acceptance Scenarios**:

1. **Given** an extracted model, **When** annotate plan runs with `--system all`, **Then** the plan `systems` list is `[all]`.
2. **Given** `all` on the plan, **When** enrich records candidates with concrete `http` URIs from mixed systems, **Then** those URIs are stored (cap 5 unchanged).
3. **Given** `--candidate 'all|x|y'`, **When** enrich runs, **Then** it fails closed (`all` is not a code system URI).

---

### Edge Cases

- Existing `icd-10` alias remains valid and still maps to `http://hl7.org/fhir/sid/icd-10` (WHO ICD-10). New work that wants US ICD-10-CM uses `icd-10-cm`.
- Repeatable `--system` may mix `all` with named systems; `all` means cross-system search (skill uses that path; named systems are still recorded).
- Unknown alias fails; HTTP URI on `--system` remains allowed (same as 005).
- HTML review and import do not need new controls; they already show whatever `system` string is on the candidate.
- Mapping workbooks stay out of scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `annotate plan --system` MUST accept `snomed`, `loinc`, `icd-10`, `icd-10-cm`, `rxnorm`, `ucum`, and `all` (repeatable). Default when omitted remains `snomed`.
- **FR-002**: Unknown `--system` names MUST fail closed and MUST NOT write a plan.
- **FR-003**: `annotate enrich --candidate` MUST expand aliases `snomed`, `loinc`, `icd-10`, `icd-10-cm`, `rxnorm`, `ucum` to their canonical FHIR URIs. `http…` systems MUST be stored as given.
- **FR-004**: Alias `all` MUST NOT expand to a candidate system URI. A candidate whose system is `all` MUST fail.
- **FR-005**: Canonical URIs MUST be: SNOMED CT `http://snomed.info/sct`; LOINC `http://loinc.org`; ICD-10 `http://hl7.org/fhir/sid/icd-10`; ICD-10-CM `http://hl7.org/fhir/sid/icd-10-cm`; RxNorm `http://www.nlm.nih.gov/research/umls/rxnorm`; UCUM `http://unitsofmeasure.org`.
- **FR-006**: The annotate skill MUST search RxNorm, UCUM, and ICD-10-CM when those names are on the plan, and MUST use cross-system search when `all` is on the plan. The CLI MUST still not look up codes.
- **FR-007**: Existing annotate commands (export, import, approve, implement, verify) MUST keep working without new flags. Candidate cap remains 5.
- **FR-008**: No new tracking event. Plan still appends `annotate_planned` only.

### Key Entities

- **Plan `systems` list**: Aliases (and optional `all`) telling the skill which lookup to run.
- **Candidate `system`**: Always a FHIR URI after enrich; never `all`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can request RxNorm, UCUM, or ICD-10-CM on a plan in one command and see that name persisted before any lookup.
- **SC-002**: 100% of enrich rows that used a supported short name store the matching canonical URI (no leftover alias on `system`).
- **SC-003**: Unknown system names fail in 100% of test runs and leave no plan file.
- **SC-004**: A plan with `all` can record mixed-system candidates; none of those rows have `system: all`.

## Assumptions

- 005 annotate CLI and skill already exist. This slice only expands the system vocabulary.
- ReasonHub remains the lookup service; searchable systems today are SNOMED CT, LOINC, RxNorm, ICD-10-CM, and UCUM.
- Default binding strength stays `example`. Query still defaults to inventory display.
- Specify/formalize and Excel review are out of scope.

## Out of Scope

- Changing the SNOMED default
- CLI HTTP search
- New HTML review controls
- Specify / formalize
- Mapping workbooks, FML, StructureMap
