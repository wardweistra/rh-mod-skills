# rh-mod-specify reference

## Commands

```
rh-mod-skills specify plan <model>
rh-mod-skills specify approve <model>
rh-mod-skills specify implement <model>
rh-mod-skills specify verify <model>
```

Plan requires every inventory path mapped or unbound (bindings 2.0). Implement
requires an approved specify plan. Verify does not write tracking.

## Files

| File | Who writes it |
|------|----------------|
| `process/plans/specify-plan.yaml` | `specify plan` / `approve` |
| `structured/logical-model.yaml` | `specify implement` |

## logical_models[]

```yaml
schema_version: "2.0"
model: recommendations          # tracking id
logical_models:
  - id: encr-patient            # default: tracking model id when unregrouped
    title: Patient
    root: true                  # optional; at most one
    entities:                   # Backbone groups under this LM
      - id: demographics
        elements:
          - id: birth-date
            path: birth-date
            inventory_path: table-1.date-of-birth
            datatype: date
            cardinality: 0..1
            status: unbound
            mappings: []
            value_set: null
            reason: "…"
            provenance: {…}
          - id: managing-hospital
            path: managing-hospital
            inventory_path: table-1.managing-hospital
            datatype: Reference
            reference:
              target: encr-hospital
            …
  - id: encr-hospital
    title: Hospital
    entities: […]
```

Default when the reviewer does nothing: one LM (`id` = tracking model id) with
inventory entities as Backbone children.

## Datatype rules

Copied from inventory only when it is a recognized FHIR type. Otherwise
`unknown`. Reviewer may set:

- primitives: `boolean`, `integer`, `decimal`, `string`, `date`, `dateTime`, `code`, …
- complex: `CodeableConcept`, `Coding`, `Identifier`, `Quantity`, `Period`, `Reference`, …

`Reference` requires `reference.target` equal to another `logical_models[].id`.

Not types: `F`, `A`, `unknown`, free-text codebook codes.

Cardinality: `n..m` or `n..*` or `unknown`.

## Binding / mapping snapshot

Each element carries annotate 2.0 fields on the element itself (not a nested
singleton `binding`):

- `status`: `mapped` | `unbound`
- `mappings[]`: system/code/display/decision (may be empty when unbound or value_set-only)
- `value_set`: null or `{strength, concepts[]}`
- `reason`: required when unbound
- `inventory_path`: required; every inventory path claimed exactly once

Specify copies snapshots; it does not invent codes or ValueSets. Regroup only on
the specify plan — never in extract.
