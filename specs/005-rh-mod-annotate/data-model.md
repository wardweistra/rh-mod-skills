# Data model: annotate (005)

## Annotate plan

**Path**: `models/<id>/process/plans/annotate-plan.yaml`

```yaml
model: nkr-breast
status: draft    # draft | approved
systems: [snomed]
elements:
  - id: gesl
    path: patientgegevens.gesl
    display: Geslacht
    query: Geslacht
    decision: pending    # pending | accept | reject | replace | unbound
    strength: example    # example | preferred | extensible | required
    reason: ""
    chosen:              # required for replace; optional for accept
      system: null
      code: null
      display: null
    candidates:
      - system: http://snomed.info/sct
        code: "263495000"
        display: Gender
        rank: 1
```

## Bindings

**Path**: `models/<id>/structured/bindings.yaml`

Only accept/replace/unbound rows. Key = `path`.

```yaml
model: nkr-breast
bindings:
  - path: patientgegevens.gesl
    id: gesl
    display: Geslacht
    status: bound          # bound | unbound
    decision: accept       # accept | replace | unbound
    strength: example
    system: http://snomed.info/sct
    code: "263495000"
    display_term: Gender
    reason: ""
  - path: patientgegevens.gebdat
    id: gebdat
    display: Geboortedatum
    status: unbound
    decision: unbound
    strength: null
    system: null
    code: null
    display_term: null
    reason: identifier / no terminology needed
```

## Status derivation

Undecided = inventory element path with no bindings row.  
Next = `annotate` if any undecided; `specify` when every path has bound or unbound.

## Tracking

Events: `annotate_planned` (plan write); `element_bound` (batched implement: lists paths + decisions).  
`models[].structured` gains `bindings.yaml`.
