# reason-mod-skills Development Guidelines

Sibling of rh-skills. Last updated: 2026-09-11

## Active Technologies

- Python 3.13+ + click 8.0+, ruamel.yaml 0.18+, httpx
- YAML on filesystem under `models/<model>/structured/`
- Consumer-root `tracking.yaml` with `models:` (not `topics:`)
- FHIR R4 JSON logical models under `models/<model>/computable/`
- Speckit (`.specify/`) for feature specs, plans, and tasks
- Optional: ReasonHub MCP for terminology search/lookup/expand

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

- 002-rh-mod-ingest: `ingest plan|approve|implement|verify` — Excel/CSV table projection, PDF register-only
- 001-rh-mod-framework: `init`, `status`, consumer-root tracking, `models/<id>/` layout

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
