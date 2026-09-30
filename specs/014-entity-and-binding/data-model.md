# Data model: entity graph + mapping/binding split (014)

Schema target: `schema_version: "2.0"` for bindings and logical-model. No 1.0 dual-read.

---

## Epic A — bindings

**Path**: `models/<id>/structured/bindings.yaml`

```yaml
schema_version: "2.0"
model: recommendations
bindings:
  - path: table-1.sex-at-birth
    id: sex-at-birth
    display: Sex at birth
    status: mapped                 # mapped | unbound  (phase 1)
    mappings:
      - system: http://loinc.org
        code: "76689-9"
        display: Sex assigned at birth
        decision: accept           # accept | replace
      - system: http://snomed.info/sct
        code: "184100006"
        display: Patient sex
        decision: accept
    value_set: null                # phase 2 object or null
    reason: ""
  - path: table-1.date-of-birth
    id: date-of-birth
    display: Date of birth
    status: unbound
    mappings: []
    value_set: null
    reason: identifier / no terminology needed
```

### Phase 2 `value_set` (same file)

```yaml
    value_set:
      strength: preferred          # example | preferred | extensible | required
      concepts:
        - system: http://loinc.org
          code: "LA15170-6"
          display: Male
        - system: http://loinc.org
          code: "LA15171-4"
          display: Female
```

### Validation rules

| Rule | Blocking |
|------|----------|
| `path` unique; must exist in inventory when verify/specify | yes |
| `status: unbound` ⇒ non-empty `reason`; empty `mappings`; no `value_set` | yes |
| `status: mapped` ⇒ ≥1 mapping; each mapping has system+code; ≤1 row per system URI | yes |
| Duplicate system in `mappings[]` | yes |
| Mapping row MUST NOT carry `strength` | yes (schema) |
| `value_set` present ⇒ non-empty `strength` + ≥1 concept with system+code | yes (phase 2) |
| schema_version ≠ 2.0 or 1.0 singleton fields (`system`/`code`/`strength` at row root) | fail closed — re-annotate |

### Annotate plan (delta)

**Path**: `process/plans/annotate-plan.yaml`

Elements gain durable `mappings: []` (and phase 2 draft `value_set`). Candidates remain enrich input. Accept/replace upserts by system URI into `mappings`. Strength removed from element root in phase 1 (moves to `value_set` in phase 2).

### Annotate-complete / status

Every inventory path has a bindings row with `mapped` or `unbound` (phase 1). Phase 2: `decided` (mappings and/or value_set) or `unbound` — see research §4.

---

## Epic A — logical-model snapshot (still `entities[]`)

**Path**: `models/<id>/structured/logical-model.yaml` (post-specify)

Element `binding` object replaced by snapshot fields aligned with bindings 2.0:

```yaml
schema_version: "2.0"
model: recommendations
entities:
  - id: table-1
    title: Standard dataset
    elements:
      - id: sex-at-birth
        path: table-1.sex-at-birth
        display: Sex at birth
        datatype: code
        cardinality: 0..1
        mappings: [ ... ]          # copy from bindings
        value_set: null
        reason: ""
        provenance: { ... }
```

Formalize (Epic A): one SD; `StructureDefinition.mapping` + `ElementDefinition.mapping` from `mappings`; ValueSet only if `value_set` non-null.

---

## Epic B — logical models graph

**Path**: `models/<id>/structured/logical-model.yaml`

```yaml
schema_version: "2.0"
model: recommendations
logical_models:
  - id: encr-patient
    title: Patient
    root: true
    elements:
      - id: birth-date
        path: birth-date
        inventory_path: table-1.date-of-birth
        display: Date of birth
        datatype: date
        cardinality: 0..1
        mappings: []
        value_set: null
        reason: identifier / no terminology needed
        provenance: { ... }
      - id: managing-hospital
        path: managing-hospital
        inventory_path: table-1.managing-hospital
        display: Managing hospital
        datatype: Reference
        cardinality: 0..1
        reference:
          target: encr-hospital
        mappings: []
        value_set: null
        reason: ""
        provenance: { ... }
  - id: encr-hospital
    title: Hospital
    elements:
      - id: name
        path: name
        inventory_path: table-1.hospital-name
        datatype: string
        cardinality: 0..1
        mappings: []
        value_set: null
        reason: ""
        provenance: { ... }
```

### Validation rules (Epic B)

| Rule | Blocking |
|------|----------|
| Every inventory path appears on exactly one element via `inventory_path` | yes |
| `logical_models[].id` unique; path segments ≤ 64 chars | yes |
| `reference.target` MUST equal another LM id in the same file | yes |
| `datatype: Reference` without `reference.target` | yes |
| At most one `root: true` | yes (advisory if zero) |

Specify plan mirrors this tree under `status: draft|approved` (plus plan-only helper fields as needed).

Default unregrouped plan: single LM with `id` = tracking model id (research §9).

---

## Epic B — formalize plan / snapshot

**Path**: `process/plans/formalize-plan.yaml`

```yaml
model: recommendations
status: draft
canonical_base: https://encr.eu/fhir/recommendations
version: "0.1.0"
logical_models:
  - id: encr-patient
    canonical: https://encr.eu/fhir/recommendations/StructureDefinition/encr-patient
  - id: encr-diagnosis
    canonical: https://encr.eu/fhir/recommendations/StructureDefinition/encr-diagnosis
  - id: encr-hospital
    canonical: https://encr.eu/fhir/recommendations/StructureDefinition/encr-hospital
unknown_datatype: []
# counts: mapped / value_set_bound / unbound / unknown_cardinality
```

**Snapshot** `computable/snapshot.yaml`: stores `canonical_base`, `version`, and `files[]` for every SD + ValueSet with SHA-256. No ConceptMap entries.

**Computable files**:

- `StructureDefinition-<lm-id>.json` (one per LM)
- `ValueSet-<…>.json` only for elements with `value_set`
- `snapshot.yaml`

---

## Tracking / events

No new event types required for Epic A/B beyond existing `element_bound`, `model_specified`, `model_formalized`, `ig_synced`. Status next-stage names unchanged in spirit (annotate → specify → formalize → verify). Verify coordinator counts should report mapped / VS-bound / unbound when those fields exist.
