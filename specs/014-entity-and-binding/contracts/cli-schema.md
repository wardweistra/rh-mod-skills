# CLI contracts: 014 entity-and-binding

Command shapes stay the existing groups. Behavior deltas below. No new top-level command group. No migrate / `--compat` flags.

---

## Epic A — annotate

```
rh-mod-skills annotate plan <model> (--element ID_OR_PATH)... [--system SYS]...
rh-mod-skills annotate plan <model> --all-undecided [--system SYS]...
rh-mod-skills annotate enrich <model> --element ID_OR_PATH [--candidate SYS|CODE|DISPLAY]...
rh-mod-skills annotate export|import …          # multi-map aware (delta)
rh-mod-skills annotate approve <model>
rh-mod-skills annotate implement <model> [--replace]
rh-mod-skills annotate verify <model>
```

### Behavior deltas

| Command | Change |
|---------|--------|
| plan | Element records support multi-system candidates as today; durable slot is `mappings[]` (not single coding + strength). |
| enrich | Unchanged candidate recording; multiple systems may coexist on one element. |
| implement | Writes bindings `schema_version: "2.0"` with `mappings[]`. Accept/replace upserts by system URI (≤1 per system). Does **not** write `value_set` from mappings. Unbound requires reason; clears mappings. Fail closed if approved plan would emit duplicate systems. |
| verify | Reports mapped / unbound / undecided. Blocking: duplicate systems; mapped without code; unbound without reason; inventory path missing. **Rejects** 1.0 singleton rows (root `system`/`code`/`strength`) — message: re-annotate. |
| export/import | Picks may accept multiple systems; must not coerce to one coding. |
| status | Annotate-complete when every inventory path is `mapped` or `unbound` (phase 1). |

### Phase 2 annotate (same commands)

Implement/verify gain optional `value_set` authoring path (plan fields + skill guidance). Strength only on `value_set`. Complete = every path `unbound` or decided (mappings and/or value_set).

---

## Epic A — specify

```
rh-mod-skills specify plan|approve|implement|verify <model>
```

| Command | Change |
|---------|--------|
| plan | Requires annotate-complete under 2.0 rules. Copies `mappings` / `value_set` / unbound reason onto each element snapshot (no single system/code/strength). Still `entities[]` until Epic B. |
| implement | Writes LM `schema_version: "2.0"` with mapping snapshots. |
| verify | Blocking: mapped snapshot missing system/code; unbound missing reason; path ≠ inventory. Does not require ValueSet fields. |

---

## Epic A — formalize

```
rh-mod-skills formalize plan|approve|implement|verify <model>
```

| Command | Change |
|---------|--------|
| plan | Counts mapped vs value_set-bound vs unbound (instead of bound/unbound only). Epic A may still propose single `canonical` **or** `canonical_base` + one derived SD URL for the tracking-id LM — pick one in tasks; prefer introducing `canonical_base` early if cheap. |
| implement | Emits `StructureDefinition.mapping` identities + `ElementDefinition.mapping` for each mapping. **Does not** emit ValueSet/binding for mappings-only elements. Emits ValueSet+binding only when `value_set` present (phase 2). Still one SD from `entities[]` in Epic A. No ConceptMap. |
| verify | Blocking if a mappings-only path has a ValueSet; blocking if a `value_set` path lacks VS/binding; mapping identities/entries consistent with LM mappings. |

---

## Epic B — specify

| Command | Change |
|---------|--------|
| plan | Builds/allows `logical_models[]` with `inventory_path`, optional regroup from inventory entities. Skill proposes splits; CLI persists. Supports `datatype: Reference` + `reference.target`. Default: one LM id = tracking model id if reviewer does nothing. |
| implement | Writes `logical_models[]` LM (no parallel `entities[]` required once B ships — tasks choose migration of in-repo fixtures by re-specify). |
| verify | Every inventory path claimed exactly once via `inventory_path`; `reference.target` resolves; at most one `root: true`. |

---

## Epic B — formalize

| Command | Change |
|---------|--------|
| plan | Requires `canonical_base` (http(s)). Lists derived per-LM canonicals `{canonical_base}/StructureDefinition/{lm-id}`. Drops “last segment == tracking model id” as the sole check; each LM id must match its SD URL last segment. |
| implement | One `StructureDefinition-{lm-id}.json` per LM; Reference types target other LM canonicals; snapshot lists all files + `canonical_base`. |
| verify | Multi-SD path coverage vs `logical_models[]`; checksums; kind=logical; no ConceptMap files required/allowed in v1. |

---

## Epic B — ig

```
rh-mod-skills ig sync <model>
```

| Command | Change |
|---------|--------|
| sync | Still one IG under `models/<tracking-id>/ig/`. Copies **all** snapshot StructureDefinitions into `input/models/` and lists them in ImplementationGuide `definition.resource`. ValueSets unchanged folder. No ConceptMap directory. |

---

## Explicitly absent

- `rh-mod-skills migrate …`
- `--compat` / schema bridge flags
- Auto-synthesis of singleton ValueSets from mappings or from 1.0 bound rows
- ConceptMap writers
