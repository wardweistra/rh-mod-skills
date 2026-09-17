# Example: ingest IKNL Excel (`nkr-breast`)

Consumer: `example-project/`. Model already initialized.

```bash
cd example-project
uv run --project .. rh-mod-skills status nkr-breast
# Stage: initialized  Next: ingest  → this skill
```

Plan (CLI writes the plan; do not create the YAML yourself):

```bash
uv run --project .. rh-mod-skills ingest plan nkr-breast \
  --source ../tests/fixtures/l1/nkr-breast/IKNL_Data_dictionary.xlsx \
  --origin-url https://iknl.nl/nkr/cijfers-op-maat/over-datacatalogus
```

Expect draft plan: `type: excel`, `projection: tables`, sheet `Variabelen`,
153 data rows after implement.

Reviewer approves, then:

```bash
uv run --project .. rh-mod-skills ingest approve nkr-breast
uv run --project .. rh-mod-skills ingest implement nkr-breast
uv run --project .. rh-mod-skills ingest verify nkr-breast
uv run --project .. rh-mod-skills status nkr-breast
# Next: extract → hand off to rh-mod-extract
```

English labels: same flow with
`tests/fixtures/l1/nkr-breast-en/IKNL_Data_dictionary_en.xlsx` on model
`nkr-breast-en`.

Do not write `sources/projections/iknl-data-dictionary.yaml` yourself.
Do not convert the workbook to Markdown.
