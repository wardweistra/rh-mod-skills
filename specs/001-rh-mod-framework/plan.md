# Implementation Plan: RH Mod Skills Framework (workspace skeleton)

**Branch**: `001-rh-mod-framework` | **Date**: 2026-09-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-rh-mod-framework/spec.md`

**Implementation slice**: `init`, `tracking.yaml`, `models/<id>/` layout, read-only `status`. Ingest of the IKNL Excel and ENCR PDF is **002**, not this plan.

## Summary

Stand up the consumer-project operating system for logical-model authoring: a kebab-case **model** workspace under `models/<id>/`, an append-only `tracking.yaml` at the consumer root, and a status command that names **ingest** as the next step. Duplicate rh-skills tracking helpers in `rh_mod_skills.common` (lock, atomic write, named events). Do not parse codebooks, do not author curated skills, and do not add mapping commands.

Proving models (fixtures already on disk, not ingested here): `nkr-breast` (IKNL Excel) and `encr-standard-dataset` (ENCR 2023 PDF).

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: click 8.0+, ruamel.yaml 0.18+ (httpx unused in this slice)  
**Storage**: Filesystem YAML (`tracking.yaml`) + directories under `models/`  
**Testing**: pytest (`tests/unit/`); CliRunner against tmp consumer roots  
**Target Platform**: POSIX (macOS 12+, Linux); same as rh-skills CLI users  
**Project Type**: CLI tool consumed from a separate project directory  
**Performance Goals**: `init` and `status` complete in <1s for tens of models  
**Constraints**: No `topics/`; no FML/StructureMap; no Markdown flattening; no durable writes outside named CLI commands; do not init inside the tool repo unless `example-project/` or `RH_REPO_ROOT`  
**Scale/Scope**: One consumer project, two proving models in this slice; ingest/extract/annotate/specify/formalize deferred

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Deterministic CLI Boundary | Pass | `init` owns directory + tracking writes. `status` writes nothing. Helpers in `common.py`; no skill writes. |
| II. Reviewable Lifecycle Artifacts | Pass (justified) | Init is scaffolding, not a stage transition — no plan file. Status is read-only. First gated stage is ingest (002). |
| III. Spec-Linked Validation | Pass | Unit tests for kebab-case, duplicate init, tracking events, status next-step, tool-repo refusal. |
| IV. Provenance and Binding Integrity | Pass (n/a this slice) | No source bytes parsed. Fixtures copied into `tests/fixtures/l1/` with origin URLs in README. |
| V. Minimal Surface Area | Pass | Only `init` and `status` added. Ingest not implemented here despite US1 scenario 2. No mapping commands. |

Post-design re-check: same. Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-rh-mod-framework/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli-schema.md
│   └── tracking-schema.md
└── tasks.md             # speckit-tasks (not this command)
```

### Source Code (repository root)

```text
src/rh_mod_skills/
├── cli.py                         # register init + status
├── common.py                      # consumer root, tracking lock/events
├── commands/
│   ├── init.py
│   └── status.py
└── schemas/                       # bundled copy via make sync-schemas

schemas/
└── tracking-schema.yaml

tests/
├── unit/
│   ├── test_cli.py
│   ├── test_init.py
│   └── test_status.py
└── fixtures/l1/
    ├── README.md
    ├── nkr-breast/IKNL_Data_dictionary.xlsx
    └── encr-standard-dataset/ENCR-Recommendation-standard-dataset_Mar2023.pdf

example-project/                   # allowed consumer cwd for manual init
```

**Structure Decision**: Single Python package CLI (already bootstrapped). Consumer layout is `models/` + `tracking.yaml`, tested against tmp paths. Curated skills stay empty.

## Complexity Tracking

> No constitution violations to justify.
