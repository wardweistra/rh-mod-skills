# rh-mod-skills

rh-mod-skills turns **source data models and codebooks** into **fully specified FHIR logical models**.

It is a sibling of [rh-skills](https://github.com/reason-healthcare/rh-skills). That repo encodes clinical knowledge (guidelines → FHIR + CQL). This one encodes **data models** (codebooks / dictionaries → annotated logical models → FHIR `StructureDefinition` with `kind=logical`).

Mappings between two logical models (or a logical model and FHIR resources) belong in a third sibling, **rh-map-skills**. This repo publishes a versioned model snapshot; it does not emit FHIR Mapping Language or `StructureMap`.

---

## Lifecycle

```
L1 Ingest                         L2 Specify                         L3 Formalize
─────────────────────             ──────────                         ────────────
Codebooks, dictionaries,    ──→   Inventory, bindings,         ──→   FHIR StructureDefinition
Excel/CSV/PDF tables              fully specified LM YAML            (kind=logical) + ValueSets
(structure kept; not MD-only)
```

Planned skills (CLI for init/status/ingest exists; curated SKILL.md files do not):

| Skill | Stage | Job |
|-------|-------|-----|
| `rh-mod-ingest` | L1 | Register source dictionaries; preserve tabular structure |
| `rh-mod-extract` | L2 | Element inventory + value domains |
| `rh-mod-annotate` | L2 | Per-element terminology binding with the user + ReasonHub |
| `rh-mod-specify` | L2 | Fully specified logical model (human-editable YAML) |
| `rh-mod-formalize` | L3 | FHIR logical-model `StructureDefinition` (+ ValueSets) |
| `rh-mod-verify` | cross-cutting | Coverage, unbound elements, validator checks |
| `rh-mod-status` | cross-cutting | Next step from `tracking.yaml` |

## Operating principles (same as rh-skills)

- **CLI writes, skills reason.** Durable artifacts go through `rh-mod-skills` commands.
- **Plan → human review → implement → verify** at every stage.
- **YAML is canonical.** Excel, CSV, and PDF table projections are L1 sources, not L2 truth. Mapping workbooks live in rh-map-skills.

## Consumer project layout

```text
models/<model-id>/
  sources/                         # L1 codebooks: Excel, CSV, PDF (tables projected, not MD-only)
  structured/
    inventory.yaml                 # tables/classes, elements, types, cardinality
    value-domains.yaml             # local code lists
    bindings.yaml                  # terminology annotations
    logical-model.yaml             # fully specified LM
  computable/
    StructureDefinition-*.json     # FHIR logical model
    ValueSet-*.json
  process/plans/ ...
tracking.yaml
```

`rh-map-skills` will consume the `computable/` snapshot (and pin canonical URL + version). It will not re-parse the original codebook.

## Status

`init`, `status`, `ingest` (Excel/CSV/PDF table projections), and `extract` work. Curated skills and annotate/specify/formalize are not built yet.

Try the proving consumer:

```bash
cd example-project
uv run --project .. rh-mod-skills status
```

1. Read [`.specify/memory/constitution.md`](.specify/memory/constitution.md)
2. Read [`specs/001-rh-mod-framework/spec.md`](specs/001-rh-mod-framework/spec.md)
3. Next product spec: annotate (`rh-mod-annotate`)

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- ReasonHub MCP for terminology annotation (same setup as rh-skills)

```bash
uv sync
uv run rh-mod-skills --help
```

## Sibling products

| Repo | Owns |
|------|------|
| **rh-skills** | Clinical evidence → L2 artifacts → FHIR + CQL |
| **rh-mod-skills** (this repo) | Source models → annotated LM → FHIR logical `StructureDefinition` |
| **rh-map-skills** (planned) | Two FHIR models → L2 mapping workbook → FHIR Mapping Language |
