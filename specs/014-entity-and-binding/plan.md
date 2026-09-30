# Implementation Plan: entity graph + mapping/binding split

**Branch**: `014-entity-and-binding` (work branch `cursor/entity-mapping-specs-bdd1`) | **Date**: 2026-09-30 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/014-entity-and-binding/spec.md`  
**Approach (non-normative)**: Project store `docs/pipeline-entity-and-binding-approach.md`

## Summary

Evolve annotate → specify → formalize → `ig sync` so that (Epic A) concept mappings are first-class multi-system metadata emitted as `ElementDefinition.mapping` without auto-ValueSets, and (Epic B) specify can regroup inventory paths into multiple logical models with `Reference` links, each formalized to its own StructureDefinition under a configurable `{canonical_base}/StructureDefinition/{lm-id}`, packaged in one IG per tracking model. Clean break from schema 1.0 singleton bindings — no compat loaders. **Implement Epic A before Epic B.** Product CLI changes are out of this plan pass; they follow `/speckit.tasks`.

## Technical Context

**Language/Version**: Python 3.13+, Click 8+, ruamel.yaml 0.18+, stdlib json  
**Primary Dependencies**: existing annotate/specify/formalize/ig command modules; no fhir.resources; no ConceptMap  
**Storage**: `structured/bindings.yaml` (2.0), `structured/logical-model.yaml` (2.0), stage plans under `process/plans/`, `computable/*.json` + `snapshot.yaml`, `models/<id>/ig/`  
**Testing**: pytest + CliRunner; synthetic mini consumers (not live ENCR)  
**Target Platform**: POSIX CLI  
**Project Type**: CLI + curated skills  
**Performance Goals**: ENCR-scale (~124 elements) plan/implement unchanged order of magnitude (<2s plan)  
**Constraints**: CLI owns durable writes; skills own regroup / map-vs-bind reasoning; fail closed on unknown datatype; no FML/StructureMap; no legacy compat; no hardcoded ENCR-only canonical validation  
**Scale/Scope**: schema bumps + annotate/specify/formalize/ig + skills + tests; two epics sequenced A→B

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. CLI boundary | Pass | annotate/specify/formalize/ig remain sole writers; skills edit plan YAML only |
| II. Plan → implement → verify | Pass | Existing gated stages; no new ungated write path (ig sync stays ungated as today) |
| III. Spec-linked validation | Pass | Spec stories + this plan; tasks (follow-up) must cover schema/CLI/verify contracts |
| IV. Provenance / binding integrity | Pass* | `inventory_path` + provenance retained; mappings record system/code/display/decision; **strength applies to ValueSet bindings only** (research §11) — mapped vs VS-bound vs unbound reported separately |
| V. Minimal surface | Pass | Extend existing command groups/schemas; no parallel annotate2; no migrate CLI |

Post-design: same pass. No fhir.resources. No ConceptMap in v1.

## Project Structure

### Documentation (this feature)

```text
specs/014-entity-and-binding/
├── plan.md                 # This file
├── research.md             # Phase 0
├── data-model.md           # Phase 1
├── quickstart.md           # Phase 1
├── contracts/cli-schema.md # Phase 1
├── spec.md
├── README.md
├── checklists/requirements.md
└── tasks.md                # Created by /speckit.tasks — Epic A then B
```

### Source Code (repository root) — intended touch set

```text
schemas/bindings-schema.yaml
schemas/logical-model-schema.yaml
src/rh_mod_skills/commands/annotate.py
src/rh_mod_skills/commands/specify.py
src/rh_mod_skills/commands/formalize.py
src/rh_mod_skills/commands/ig.py          # Epic B: multi-SD resource list
src/rh_mod_skills/annotate_review.py      # Epic A: export/import multi-map
src/rh_mod_skills/commands/verify.py      # counts: mapped / VS-bound / unbound
skills/.curated/rh-mod-annotate/
skills/.curated/rh-mod-specify/
skills/.curated/rh-mod-formalize/
skills/.curated/rh-mod-ig/
tests/unit/test_annotate*.py
tests/unit/test_specify*.py
tests/unit/test_formalize*.py
tests/unit/test_ig*.py
tests/fixtures/…                          # mini mapped + multi-LM fixtures
```

**Structure Decision**: Extend existing Click groups and schemas in place (constitution V). Epic A changes bindings + formalize mapping emission while keeping single-SD `entities[]`. Epic B introduces `logical_models[]`, `canonical_base`, multi-SD snapshot, IG listing.

## Epic split (implementation sequencing)

| Phase | Epic | Deliverable |
|-------|------|-------------|
| A1 | A | `bindings` 2.0 + annotate plan/implement/verify for `mappings[]`; fail closed on 1.0 rows; skill map-vs-bind |
| A2 | A | specify copies mapping snapshots; formalize emits `ElementDefinition.mapping`; **stop** singleton VS from mappings |
| A3 | A | Optional `value_set` authoring + formalize VS/binding only when present; verify distinguishes mapped vs VS-bound |
| B1 | B | specify plan regroup → `logical_models[]` + `inventory_path` + `Reference`/`reference.target` |
| B2 | B | formalize N SDs from `canonical_base`; snapshot lists all; Reference targetProfile/canonicals |
| B3 | B | `ig sync` one IG listing all logical SDs; status/verify coverage across multi-LM |

## Complexity Tracking

> No constitution violations requiring justification. Strength-on-ValueSet-only is an interpretation of IV documented in research §11, not a principle waiver.
