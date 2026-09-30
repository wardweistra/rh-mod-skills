# reason-mod-skills Development Guidelines

Sibling of rh-skills. Last updated: 2026-09-29

## Active Technologies

- Python 3.13+ + click 8.0+, ruamel.yaml 0.18+, httpx, openpyxl, pdfplumber
- YAML on filesystem under `models/<model>/structured/`
- Consumer-root `tracking.yaml` with `models:` (not `topics:`)
- FHIR R4 JSON logical models under `models/<model>/computable/`
- Speckit (`.specify/`) for feature specs, plans, and tasks
- Optional: ReasonHub MCP for terminology search/lookup/expand; annotate CLI records MCP hits via `annotate enrich` (no HTTP search)

## Project Structure

```text
src/rh_mod_skills/
skills/.curated/
specs/
schemas/
tests/
tests/fixtures/l1/
example-project/
```

## Commands

```bash
uv sync
uv run rh-mod-skills --help
uv run pytest
```

## Code Style

Python 3.13, Click command groups, ruamel.yaml for round-trip YAML. Follow rh-skills conventions: CLI owns durable writes; SKILL.md owns reasoning.

## Out of scope

FHIR Mapping Language, StructureMap, and Excel mapping workbooks belong in rh-map-skills.

## Recent Changes

- 013-rh-mod-ig: `ig sync` stages a buildable stub (`definition.page` Home only, `input/includes/menu.xml`, create-if-missing `index.md`) plus snapshot JSON and pinned HL7 scripts; no Java / no publisher.jar; IG JSON rewritten each sync; skill owns publisher error triage
- 012-rh-mod-verify: `rh-mod-skills verify [model]` is a read-only coordinator over ingest/extract/annotate/specify/formalize verify; coverage + unbound + `validator=not-run`; no tracking writes; status next stays verify
- 011-rh-mod-formalize: `formalize plan|approve|implement|verify` writes FHIR R4 `StructureDefinition` (`kind=logical`), one ValueSet per bound element, and `computable/snapshot.yaml` (SHA-256); canonical last segment = model id; path name portions ≤ 64 (extract slugs); unknown cardinality → `0..1`; unknown datatype fails closed; no FHIR Python library or validator binary
- 010-rh-mod-specify: `specify plan|approve|implement|verify` writes `logical-model.yaml` from annotate-complete inventory+bindings; types stay unknown unless recognized FHIR or reviewer-filled; no FHIR JSON
- 009-annotate-codesystems: `annotate plan --system` accepts `icd-10-cm`, `rxnorm`, `ucum`, and `all` (cross-system search); default remains snomed; enrich expands those aliases to FHIR URIs
- 008-annotate-review: `annotate export` writes static HTML from the plan; `annotate import --from` applies picks YAML (accept by rank, unbound/skip/replace); import sets draft and does not write `bindings.yaml`
- 007-ingest-status-skills: curated `rh-mod-ingest` and `rh-mod-status` (SKILL.md + reference.md + examples); CLI unchanged
- Constitution 1.1.0: L1 tabular ingest is Excel, CSV, and PDF table projections (same YAML). Markdown-only L1 remains forbidden. OCR out of scope.
- 006-extract-column-roles: extract plan `sheets[].columns` roles; header synonyms are a hint; remap in the plan then re-run `extract plan`
- 005-rh-mod-annotate: `annotate plan|enrich|export|import|approve|implement|verify` writes `bindings.yaml` on implement; MCP lookup in `rh-mod-annotate` skill; CLI does not HTTP-search
- 004-rh-mod-ingest-pdf: `ingest` projects PDF tables (ENCR Table 1/2 proving); register-only when no tables
- L1 fixtures: `nkr-breast-en` (English NKR Excel) and `nbca` (NBCA 2026 PDF). Extract header synonyms include English `variable_*` and Dutch `variabele` / `dataset`.
- 003-rh-mod-extract: `extract plan|approve|implement|verify` — inventory from table projections
- 002-rh-mod-ingest: `ingest plan|approve|implement|verify` — Excel/CSV table projection; PDF tables added in 004
- 001-rh-mod-framework: `init`, `status`, consumer-root tracking, `models/<id>/` layout

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
