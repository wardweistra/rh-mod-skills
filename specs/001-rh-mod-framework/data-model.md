# Data Model: RH Mod Skills Framework (implementation slice)

**Phase**: 1 — Design  
**Branch**: `001-rh-mod-framework`  
**Date**: 2026-09-11

The data model is filesystem-based. 001 creates the skeleton; 002 fills `sources/`.

---

## Directory layout (consumer project)

```text
<consumer-root>/
  tracking.yaml
  models/
    <model-id>/
      MODEL.md
      sources/              # L1 originals (empty until 002)
      structured/           # L2 YAML (empty until extract)
      computable/           # L3 FHIR JSON (empty until formalize)
      process/
        plans/
        notes.md
```

Proving consumer for tests: `example-project/` (or a pytest tmp directory). Fixture bytes live in the *tool* repo at `tests/fixtures/l1/`, not inside a model until ingest copies them.

---

## Entity: Model

The unit of work. One source data model on its way to one FHIR logical model.

**Identity**: kebab-case directory name; unique within the consumer project; pattern `^[a-z][a-z0-9-]*$`.

**Location**: `models/<model-id>/`

**Fields** (in `tracking.yaml` → `models[]`):

| Field | Required | Notes |
|-------|----------|--------|
| `name` | yes | Equals directory name |
| `title` | yes | Human-readable |
| `description` | yes | Short purpose |
| `author` | yes | Person or team |
| `created_at` | yes | UTC ISO-8601 |
| `sources` | yes | List; empty after init |
| `structured` | yes | List; empty after init |
| `computable` | yes | List; empty after init |
| `events` | yes | Per-model append-only log |

**Lifecycle (001 view)**: `initialized` when `model_created` exists and `sources` is empty. Later stages are derived from events, not a mutable `state` field.

---

## Entity: Tracking file

**Location**: `<consumer-root>/tracking.yaml`

**Identity**: one file per consumer project.

```yaml
schema_version: "1.0"
models: []
events: []
```

**Validation**:
- `schema_version` MUST be `"1.0"`
- `models[].name` unique
- events are append-only (CLI helpers only)
- no `topics:` key

**Root events (001 emits)**:

| Type | When |
|------|------|
| `model_created` | `init` succeeded |

**Per-model events (001 emits)**:

| Type | When |
|------|------|
| `created` | same as root `model_created`, on the model entry |

**Reserved types** (schema lists them; later specs emit them): `source_added`, `extract_planned`, `inventory_derived`, `annotate_planned`, `element_bound`, `model_specified`, `model_formalized`, `validated`.

Event object:

```yaml
timestamp: "2026-09-11T14:00:00Z"
type: model_created
description: "Model scaffolded with rh-mod-skills init"
```

---

## Entity: MODEL.md

Human-facing stub written by `init`. Not a lifecycle authority (`tracking.yaml` is).

Frontmatter: `name`, `description`, `author`, `created`.

---

## Entity: Source (stub in 001)

Present in the data model so tracking schema and directory exist. 001 MUST NOT copy or checksum files.

002 will add:

| Field | Notes |
|-------|--------|
| `name` | kebab-case |
| `file` | model-relative path under `sources/` |
| `type` | `excel` \| `csv` \| `pdf` \| … |
| `checksum` | SHA-256 of original bytes |
| `ingested_at` | ISO-8601 |
| `origin_url` | optional provenance |

---

## State transitions (001)

```text
(none) --init--> initialized
```

`status` maps `initialized` → next step `ingest`. It MUST NOT suggest mapping, FML, or StructureMap.

---

## Validation rules

- Re-init of an existing model name fails closed (no overwrite).
- Invalid model id (not kebab-case) fails closed.
- Init inside the tool repo (except `example-project/` or `RH_REPO_ROOT`) fails closed.
- Missing `tracking.yaml` on `status` is an error with guidance to run `init`.
