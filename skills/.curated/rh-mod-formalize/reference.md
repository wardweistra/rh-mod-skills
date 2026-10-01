# rh-mod-formalize reference

## Commands

```
rh-mod-skills formalize plan <model>
rh-mod-skills formalize approve <model>
rh-mod-skills formalize implement <model>
rh-mod-skills formalize verify <model>
```

Plan requires `structured/logical-model.yaml` with `logical_models[]`
(`schema_version: "2.0"`). Implement requires an approved plan with http(s)
`canonical_base` and a non-empty `version`. Verify does not write tracking.

## Files

| File | Who writes it |
|------|----------------|
| `process/plans/formalize-plan.yaml` | `formalize plan` / `approve` |
| `computable/StructureDefinition-<lm-id>.json` | one per `logical_models[]` entry |
| `computable/ValueSet-*.json` | only when LM element has authored `value_set` |
| `computable/snapshot.yaml` | `formalize implement` |

The CLI owns every durable write. Do not hand-author FHIR JSON. No ConceptMap.

## Plan fields

- `canonical_base` — http(s) base; implement derives
  `{canonical_base}/StructureDefinition/{lm-id}` per LM
- `canonical` — primary/root LM URL (for IG package guess)
- `logical_models[]` — `{id, canonical}` rows listed on the plan
- `version` — non-empty string
- `unknown_datatype` — paths; implement fails if non-empty
- `unknown_cardinality` — count defaulted to `0..1`
- `mapped` / `value_set_bound` / `unbound` — counts from LM elements

Proving example: `canonical_base: https://encr.eu/fhir/recommendations` →
`…/StructureDefinition/encr-patient` etc. Validation is http(s) + last segment
= lm-id, not ENCR-only hardcoding.

## StructureDefinition rules

- One SD per LM; `kind: logical`; root path = lm-id; URL last segment = lm-id
- Entities = `BackboneElement`; leaf types from LM
- `Reference` → `type[].targetProfile` = target LM canonical
- **Mappings**: `StructureDefinition.mapping` + `ElementDefinition.mapping`
- **ValueSet**: only when authored `value_set` (strength + concepts)
- Path name portions ≤ 64; unknown cardinality → `0..1`
- **No ConceptMap**

## Snapshot

Stores `canonical_base`, primary `canonical`, `version`, `logical_models[]`,
and `files[]` for every SD + ValueSet with SHA-256.

## Verify

Blocking: missing SD(s), `kind` ≠ `logical`, differential path mismatch,
mappings-only path with VS/binding, `value_set` path missing VS/binding,
Reference missing targetProfile, checksum mismatch, ConceptMap present.

Advisory: `cardinality-default-n=…`, `value_set_bound=…`, `logical_models=N`,
`validator=not-run`.
