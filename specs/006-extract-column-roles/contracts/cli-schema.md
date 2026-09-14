# CLI: extract (006 column roles)

Same four subcommands as 003. `plan` gains `--rehint`.

```
rh-mod-skills extract plan <model> [--rehint]
rh-mod-skills extract approve <model>
rh-mod-skills extract implement <model> [--replace]
rh-mod-skills extract verify <model>
```

### plan

Writes `sheets` (column roles) plus entities/elements derived from those roles.

- No saved `sheets` (or `--rehint`): propose roles from header hints, then derive rows.
- Saved `sheets` without `--rehint`: keep roles (match by source + sheet name + header); new columns default to `unused`; rebuild entities/elements.
- Preserve element `decision`/`reason` by provenance; preserve entity title/decision/merge when entity id still exists.
- `status: draft`. Event `extract_planned`.
- Duplicate exclusive roles → `conflicts` entry `duplicate-role`; draft still written.

### approve

Unchanged. Does not validate roles.

### implement

Unchanged copy-from-plan, plus: fail if any `duplicate-role` conflict remains. Does not consult the hint list.

### verify

Coverage proposal uses the plan’s `sheets` roles (same as a non-`--rehint` rebuild), not a fresh synonym-only pass.
