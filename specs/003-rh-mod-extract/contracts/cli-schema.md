# CLI: extract

```
rh-mod-skills extract plan <model>
rh-mod-skills extract approve <model>
rh-mod-skills extract implement <model> [--replace]
rh-mod-skills extract verify <model>
```

### plan

Reads ingested table projections. Writes `process/plans/extract-plan.yaml` with `status: draft`. Appends `extract_planned`. Does not write `structured/`.

Exit 0 on write. Exit 1 if model missing, not ingested, L1 checksum drift, or no table projection (PDF-only). Must not write a plan in the fail-closed cases.

### approve

Sets `status: approved`. Fails if plan missing.

### implement

Fails if plan missing or not `approved`. Writes `structured/inventory.yaml` from include-only plan rows (merges/drops/renames honored). Writes `value-domains.yaml` only when the plan/projection has local code lists. Appends `inventory_derived`. Does not write `bindings.yaml` or FHIR resources.

If `structured/inventory.yaml` already exists, fail unless `--replace`.

### verify

Read-only. Reports: plan approved, inventory present, entity/element counts, projected rows covered vs plan-excluded vs missing, conflicts, unknown datatype/cardinality counts (advisory). Exit 1 on blocking issues (missing inventory, missing projected row not excluded). Must not mutate `tracking.yaml`.
