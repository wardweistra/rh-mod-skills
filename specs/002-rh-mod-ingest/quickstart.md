# Quickstart: ingest proving corpus

Requires 001 `init` already run in `example-project/` (or run it first).

```bash
ROOT=/Users/ward/workspace/rh-mod-skills
cd "$ROOT/example-project"

uv run --project .. rh-mod-skills ingest plan nkr-breast \
  --source "$ROOT/tests/fixtures/l1/nkr-breast/IKNL_Data_dictionary.xlsx" \
  --origin-url "https://iknl.nl/nkr/cijfers-op-maat/over-datacatalogus"
uv run --project .. rh-mod-skills ingest approve nkr-breast
uv run --project .. rh-mod-skills ingest implement nkr-breast
uv run --project .. rh-mod-skills ingest verify nkr-breast
uv run --project .. rh-mod-skills status nkr-breast

uv run --project .. rh-mod-skills ingest plan encr-standard-dataset \
  --source "$ROOT/tests/fixtures/l1/encr-standard-dataset/ENCR-Recommendation-standard-dataset_Mar2023.pdf" \
  --origin-url "https://www.encr.eu/ENCR-Recommendations"
uv run --project .. rh-mod-skills ingest approve encr-standard-dataset
uv run --project .. rh-mod-skills ingest implement encr-standard-dataset
uv run --project .. rh-mod-skills ingest verify encr-standard-dataset
uv run --project .. rh-mod-skills status encr-standard-dataset
```

Expect: NKR next=extract, 153 projected rows; ENCR PDFs registered. Table projection of the 2023 standard dataset is [004](../004-rh-mod-ingest-pdf/).
