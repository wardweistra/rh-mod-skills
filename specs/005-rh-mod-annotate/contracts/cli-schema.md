# CLI: annotate

```
rh-mod-skills annotate plan <model> (--element ID_OR_PATH)... [--system SYS]...
rh-mod-skills annotate plan <model> --all-undecided [--system SYS]...
rh-mod-skills annotate enrich <model> --element ID_OR_PATH [--candidate SYS|CODE|DISPLAY]...
rh-mod-skills annotate approve <model>
rh-mod-skills annotate implement <model> [--replace]
rh-mod-skills annotate verify <model>
```

`--system` values: `snomed` (default if omitted), `loinc`, `icd-10`. Repeatable. Recorded on the plan for the skill; plan does not search.

### plan

Reads `structured/inventory.yaml`. Writes `process/plans/annotate-plan.yaml` with `status: draft` and empty `candidates` per element. Search query defaults to inventory display. Does not call ReasonHub.

Fails if: no inventory; extract/ingest not clean; neither `--element` nor `--all-undecided`; both flags; unknown `--element`; duplicate id without path.

Appends `annotate_planned`. Does not write `bindings.yaml`.

### enrich

Records MCP hits already collected by the agent. `--candidate` format: `system|code|display[|distance[|confidence]]`. At most five kept (ReasonHub rank order as passed). No `--candidate` → `candidates: []` (zero hits). Fails if the plan is missing, approved, or the element is not in the plan. Copies strings only.

### approve

Sets `status: approved`. Fails if plan missing.

### implement

Fails if plan missing or not `approved`. Writes/merges `structured/bindings.yaml`:
- `accept` → bound (chosen or first candidate; empty candidates fail)
- `replace` → bound (`chosen` required)
- `unbound` → unbound (`reason` required)
- `pending` / `reject` → skip row

`--replace` rewrites the whole file from this plan’s durable decisions only.  
Appends one `element_bound`. No `logical-model.yaml`, no FHIR.

### verify

Read-only. Reports bound / unbound / undecided counts vs inventory. Blocking: bound path not in inventory, unbound missing reason. Must not mutate `tracking.yaml`.

### status (existing command)

Next is `annotate` while any inventory path is undecided; `specify` only when all are bound or unbound.
