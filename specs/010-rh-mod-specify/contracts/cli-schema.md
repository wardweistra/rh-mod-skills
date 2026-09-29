# CLI: specify (010)

```
rh-mod-skills specify plan <model>
rh-mod-skills specify approve <model>
rh-mod-skills specify implement <model>
rh-mod-skills specify verify <model>
```

### plan

Requires inventory + annotate-complete bindings. Writes `specify-plan.yaml` (`status: draft`). Does not write `logical-model.yaml`. Does not call ReasonHub. No tracking event.

Fails if: no inventory; bindings missing; any inventory path undecided; binding path not in inventory.

### approve

Sets `status: approved`. Fails if plan missing.

### implement

Fails if plan missing or not approved. Writes `structured/logical-model.yaml`. Appends `model_specified`. Lists `logical-model.yaml` on `models[].structured`. Does not mutate inventory or bindings.

### verify

Read-only. Reports element count, unknown-datatype/cardinality counts. Blocking: missing LM, path mismatch, missing provenance, bound without system/code, unbound without reason. Must not mutate `tracking.yaml`.

### status (existing)

After `model_specified`: stage `specified`, next `formalize`.
