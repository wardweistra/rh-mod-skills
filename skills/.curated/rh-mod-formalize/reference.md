# rh-mod-formalize reference

## Commands

```
rh-mod-skills formalize plan <model>
rh-mod-skills formalize approve <model>
rh-mod-skills formalize implement <model>
rh-mod-skills formalize verify <model>
```

Plan requires `structured/logical-model.yaml` (`schema_version: "2.0"`). Implement
requires an approved plan with http(s) `canonical_base` (preferred) or `canonical`,
and a non-empty `version`. Verify does not write tracking.

## Files

| File | Who writes it |
|------|----------------|
| `process/plans/formalize-plan.yaml` | `formalize plan` / `approve` |
| `computable/StructureDefinition-<model>.json` | `formalize implement` |
| `computable/ValueSet-*.json` | only when LM element has authored `value_set` (not from mappings) |
| `computable/snapshot.yaml` | `formalize implement` |

The CLI owns every durable write. Do not hand-author FHIR JSON.

## Plan fields

- `canonical_base` — http(s) base; implement derives
  `{canonical_base}/StructureDefinition/{model}` for Epic A single-SD
- `canonical` — derived SD URL (must match base + model id)
- `version` — non-empty string
- `unknown_datatype` — paths; implement fails if non-empty
- `unknown_cardinality` — count defaulted to `0..1`
- `mapped` / `unbound` — counts from LM element status/mappings

## StructureDefinition rules

- `kind: logical`, `baseDefinition` Base, `type` = canonical URL
- Root path = model id; last URL segment = model id
- Each dotted path name portion ≤ 64 characters
- Entities = `BackboneElement`; leaf types from LM
- Unknown cardinality → min 0, max 1
- **Mappings**: emit `StructureDefinition.mapping` identities + `ElementDefinition.mapping`
  (`map` = code). Do **not** emit ValueSet or `ElementDefinition.binding` from mappings alone
- **No ConceptMap** resources
- Unbound elements: no mapping entries, no VS

## Snapshot

`snapshot.yaml` lists relative JSON paths and SHA-256 plus `canonical_base`,
canonical, and version. Mapping workbooks are out of scope.

## Verify

Blocking: missing SD, `kind` ≠ `logical`, differential path mismatch, mappings-only
path with a ValueSet/binding, checksum mismatch, canonical last segment ≠ model id,
path name portion > 64, ConceptMap present.

Advisory: `cardinality-default-n=…`, `validator=not-run`.
