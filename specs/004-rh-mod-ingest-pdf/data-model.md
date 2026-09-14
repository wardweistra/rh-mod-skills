# Data model: ingest-pdf (004)

Extends the 002 ingest plan and projection. Excel/CSV fields unchanged.

## Ingest plan (PDF source)

```yaml
model: encr-standard-dataset
status: draft
sources:
  - path: /abs/path/to/ENCR-Recommendation-standard-dataset_Mar2023.pdf
    name: encr-recommendation-standard-dataset-mar2023
    type: pdf
    projection: tables          # tables | skipped
    skip_reason: null           # no-text-layer | no-tables-detected | no-tables-approved | extractor-error
    origin_url: https://www.encr.eu/ENCR-Recommendations
    tables:
      - id: t1
        name: Table 1
        pages: [2, 3]
        columns: [Variable, Comment]
        row_count: 20
        warnings: [continued-without-header]
        decision: include       # include | exclude
        reason: ""
      - id: t2
        name: Table 2
        pages: [4]
        columns: [Type of cancer, Recommended stage variables, Remarks]
        row_count: 5
        warnings: []
        decision: include
        reason: ""
```

## Table projection

Same schema as 002. `type: pdf`. Sheet `name` is the table title.

```yaml
source: ENCR-Recommendation-standard-dataset_Mar2023.pdf
type: pdf
sheets:
  - name: Table 1
    columns: [Variable, Comment]
    rows:
      - [Personal identification, Preferably a unique ID number, otherwise full name]
  - name: Table 2
    columns: [Type of cancer, Recommended stage variables, Remarks]
    rows:
      - [Solid cancers in adults, TNM classification of malignant tumours (UICC), ...]
```

## Tracking

`projection: tables` + `projection_file` when any table is included.  
`projection: skipped` + `skip_reason` otherwise. Event remains `source_added`.
