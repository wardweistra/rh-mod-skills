# rh-mod-annotate reference

CLI owns durable writes. This skill owns ReasonHub MCP search + enrich recording.

## Map vs bind

| Concept | Where it lives | Formalize effect (US1) |
|---------|----------------|------------------------|
| **Mapping** | `bindings[].mappings[]` (system/code/display/decision) | `StructureDefinition.mapping` + `ElementDefinition.mapping` |
| **ValueSet binding** | `bindings[].value_set` (reserved; later) | ValueSet + `ElementDefinition.binding` only when authored |
| **Unbound** | `status: unbound` + `reason` | No mapping metadata, no VS |

Accepting a code is a **mapping**, not inventing a ValueSet. Multiple systems on
one path are normal (≤1 code per system URI). Strength does **not** live on
mapping rows.

## Commands

```
rh-mod-skills annotate plan <model> (--element ID_OR_PATH)... [--system SYS]...
rh-mod-skills annotate plan <model> --all-undecided [--system SYS]...
rh-mod-skills annotate enrich <model> --element ID_OR_PATH [--candidate SYS|CODE|DISPLAY]...
rh-mod-skills annotate export <model>
rh-mod-skills annotate import <model> --from picks.yaml
rh-mod-skills annotate approve <model>
rh-mod-skills annotate implement <model> [--replace]
rh-mod-skills annotate verify <model>
```

## Bindings 2.0 shape

```yaml
schema_version: "2.0"
bindings:
  - path: table-1.sex-at-birth
    status: mapped
    mappings:
      - system: http://loinc.org
        code: "76689-9"
        display: Sex assigned at birth
        decision: accept
    value_set: null
    reason: ""
```

schema_version ≠ 2.0 or root-level `system`/`code`/`strength` → fail closed; **re-annotate**.

## Annotate-complete

Every inventory path has `status: mapped` (≥1 mapping) or `unbound` (non-empty reason, empty mappings).
