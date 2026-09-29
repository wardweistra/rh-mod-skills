# rh-mod-specify reference

## Commands

```
rh-mod-skills specify plan <model>
rh-mod-skills specify approve <model>
rh-mod-skills specify implement <model>
rh-mod-skills specify verify <model>
```

Plan requires every inventory path bound or unbound. Implement requires an
approved specify plan. Verify does not write tracking.

## Files

| File | Who writes it |
|------|----------------|
| `process/plans/specify-plan.yaml` | `specify plan` / `approve` |
| `structured/logical-model.yaml` | `specify implement` |

## Datatype rules

Copied from inventory only when it is a recognized FHIR type. Otherwise
`unknown`. Reviewer may set:

- primitives: `boolean`, `integer`, `decimal`, `string`, `date`, `dateTime`, `code`, …
- complex: `CodeableConcept`, `Coding`, `Identifier`, `Quantity`, `Period`, `Reference`, …

Not types: `F`, `A`, `unknown`, free-text codebook codes.

Cardinality: `n..m` or `n..*` or `unknown`.

## Binding snapshot

Each element carries the annotate row (one coding or unbound+reason). Specify
does not add a second code system.
