# rh-mod-annotate reference

CLI owns durable writes. This skill owns ReasonHub MCP search + enrich recording.

## Map vs bind

| Concept | Where it lives | Formalize effect |
|---------|----------------|------------------|
| **Mapping** | `bindings[].mappings[]` (system/code/display/decision) | `StructureDefinition.mapping` + `ElementDefinition.mapping` |
| **ValueSet binding** | `bindings[].value_set` (`strength` + `concepts[]`) | ValueSet + `ElementDefinition.binding` only when authored |
| **Unbound** | `status: unbound` + `reason` | No mapping metadata, no VS |

Accepting a code is a **mapping**, not inventing a ValueSet. Multiple systems on
one path are normal (≤1 code per system URI). Strength lives **only** on
`value_set`, never on mapping rows.

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
    value_set:
      strength: preferred
      concepts:
        - system: http://loinc.org
          code: "LA15170-6"
          display: Male
        - system: http://loinc.org
          code: "LA15171-4"
          display: Female
    reason: ""
```

`value_set` may be `null` (mappings-only). Reviewers may author it on the annotate
plan YAML before implement. `status: mapped` when mappings and/or `value_set`
present; `unbound` requires empty mappings, `value_set: null`, and a reason.

schema_version ≠ 2.0 or root-level `system`/`code`/`strength` → fail closed; **re-annotate**.

## Annotate-complete

Every inventory path has `status: mapped` (≥1 mapping and/or authored `value_set`)
or `unbound` (non-empty reason, empty mappings, null `value_set`).
