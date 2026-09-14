# Data model: extract (003)

## Extract plan

**Path**: `models/<id>/process/plans/extract-plan.yaml`

```yaml
model: nkr-breast
status: draft   # draft | approved
allow_empty: false
entities:
  - id: patientgegevens
    title: Patiëntgegevens
    decision: include   # include | drop | merge-into
    merge_into: null
    reason: ""
elements:
  - id: gebdat
    display: Geboortedatum
    entity: patientgegevens
    path: patientgegevens.gebdat
    datatype: unknown
    cardinality: unknown
    value_domain: null
    decision: include   # include | drop
    reason: ""
    notes: {}
    provenance:
      source: iknl-data-dictionary
      sheet: Variabelen
      row: 1            # 1-based index into projection sheet.rows
      columns:
        id: variabele_name
        category: variabele_categorie
        label: variabele_label
conflicts: []
```

## Inventory

**Path**: `models/<id>/structured/inventory.yaml`

Written only from an approved plan. Nested entities; dropped rows omitted (they remain in the plan).

```yaml
model: nkr-breast
entities:
  - id: patientgegevens
    title: Patiëntgegevens
    elements:
      - id: gebdat
        display: Geboortedatum
        path: patientgegevens.gebdat
        datatype: unknown
        cardinality: unknown
        provenance:
          source: iknl-data-dictionary
          sheet: Variabelen
          row: 1
          columns:
            id: variabele_name
            category: variabele_categorie
            label: variabele_label
```

## Value domains (optional)

**Path**: `models/<id>/structured/value-domains.yaml`

Omitted when the source has no code-list sheet (IKNL).

## Tracking

Events: `extract_planned` (plan write), `inventory_derived` (successful implement). Root + per-model.

`models[].structured` lists written L2 filenames (`inventory.yaml`, optionally `value-domains.yaml`).
