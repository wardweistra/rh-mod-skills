# Data model: specify

## Specify plan

**Path**: `models/<id>/process/plans/specify-plan.yaml`

```yaml
model: encr
status: draft    # draft | approved
entities:
  - id: table-1
    title: Standard dataset
    elements:
      - id: sex-at-birth
        path: table-1.sex-at-birth
        display: Sex at birth
        datatype: code          # recognized FHIR type or unknown
        cardinality: unknown    # n..m / n..* or unknown
        issues:
          - unknown-cardinality
        binding:
          status: bound
          decision: accept
          strength: example
          system: http://loinc.org
          code: "76689-9"
          display: Sex assigned at birth
          reason: ""
        provenance:
          source: encr-recommendation-standard-dataset-mar2023
          sheet: Table 1
          row: 3
          columns:
            id: Variable
            category:
            label:
```

## Logical model

**Path**: `models/<id>/structured/logical-model.yaml`

Same `model` + `entities` tree as the approved plan (no `status` field).

## Binding snapshot

Copied from `bindings.yaml` at plan time. Bound: system/code/display/strength/decision. Unbound: reason; system/code/display/strength null. System URIs stripped of surrounding whitespace.
