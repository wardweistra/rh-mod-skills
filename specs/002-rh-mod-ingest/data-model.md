# Data model: ingest (002)

## Ingest plan

**Path**: `models/<id>/process/plans/ingest-plan.yaml`

```yaml
model: nkr-breast
status: draft   # draft | approved | rejected
sources:
  - path: /abs/path/to/file.xlsx
    name: iknl-data-dictionary
    type: excel          # excel | csv | pdf | other
    projection: tables   # tables | skipped
    origin_url: https://...
```

## Source original

`models/<id>/sources/raw/<filename>` — unmodified bytes.

## Table projection

`models/<id>/sources/projections/<name>.yaml`

```yaml
source: IKNL_Data_dictionary.xlsx
type: excel
sheets:
  - name: Variabelen
    columns: [variabele_name, variabele_categorie, variabele_label]
    rows:
      - [gebdat, Patiëntgegevens, Geboortedatum]
```

## Tracking (`models[].sources[]`)

`name`, `file`, `type`, `checksum`, `ingested_at`, `origin_url`, `projection`, `projection_file` (optional)

Events: `source_added` (per-model and root).
