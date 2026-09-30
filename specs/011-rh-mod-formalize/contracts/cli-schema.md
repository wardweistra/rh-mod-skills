# CLI: formalize (011)

```
rh-mod-skills formalize plan <model>
rh-mod-skills formalize approve <model>
rh-mod-skills formalize implement <model>
rh-mod-skills formalize verify <model>
```

### plan

Requires `structured/logical-model.yaml`. Writes `formalize-plan.yaml`. Proposes `canonical` `http://example.org/fhir/StructureDefinition/<model>` and `version: 0.1.0`. No `computable/` writes. No tracking event.

### approve

Sets `status: approved`.

### implement

Fails if not approved; canonical missing, not http(s), or last path segment ≠ model id; version empty; any unknown datatype; any FHIR path name portion > 64. Writes SD + ValueSets + snapshot. Appends `model_formalized`. Lists files on `models[].computable`. Does not mutate logical-model.yaml.

### verify

Read-only. Blocking: missing SD, kind ≠ logical, path mismatch, missing VS for bound, checksum mismatch. Advisory: cardinality-default-n; validator-not-run. No tracking writes.
