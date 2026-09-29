# rh-mod-formalize reference

## Commands

```
rh-mod-skills formalize plan <model>
rh-mod-skills formalize approve <model>
rh-mod-skills formalize implement <model>
rh-mod-skills formalize verify <model>
```

Plan requires `structured/logical-model.yaml`. Implement requires an approved
plan with an http(s) `canonical` and a non-empty `version`. Verify does not
write tracking.

## Files

| File | Who writes it |
|------|----------------|
| `process/plans/formalize-plan.yaml` | `formalize plan` / `approve` |
| `computable/StructureDefinition-<model>.json` | `formalize implement` |
| `computable/ValueSet-<model>-<path-slug>.json` | `formalize implement` (bound only) |
| `computable/snapshot.yaml` | `formalize implement` |

The CLI owns every durable write. Do not hand-author FHIR JSON.

## Plan fields

- `canonical` — http(s) StructureDefinition URL (rh-map-skills pin)
- `version` — non-empty string
- `unknown_datatype` — paths; implement fails if this list is non-empty
- `unknown_cardinality` — count defaulted to `0..1`
- `bound` / `unbound` — counts copied from the logical model

## StructureDefinition rules

- `kind: logical`, `baseDefinition` Base, `type` = canonical URL
- Root path = model id
- Entities = `BackboneElement`
- Leaf types = logical-model `datatype` (no guessing)
- Unknown cardinality → min 0, max 1
- One ValueSet per **bound** element (system/code/display already on the LM)
- Unbound elements: no ValueSet, no ElementDefinition.binding
- Binding strength copied (`example` stays example)

## Snapshot

`snapshot.yaml` lists relative JSON paths and SHA-256 checksums plus canonical
and version. That is the rh-map-skills pin. Mapping workbooks are out of scope.

## Verify

Blocking: missing SD, `kind` ≠ `logical`, differential path mismatch, missing
ValueSet for a bound element, checksum mismatch.

Advisory: `cardinality-default-n=…`, `validator=not-run`.
