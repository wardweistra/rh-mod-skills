# Quickstart: ingest ENCR PDF tables

Requires `encr-standard-dataset` initialized (001) and previously PDF-registered (002) or a fresh consumer.

```bash
ROOT=/Users/ward/workspace/rh-mod-skills
cd "$ROOT/example-project"

uv run --project .. rh-mod-skills ingest plan encr-standard-dataset \
  --source "$ROOT/tests/fixtures/l1/encr-standard-dataset/ENCR-Recommendation-standard-dataset_Mar2023.pdf" \
  --origin-url "https://www.encr.eu/ENCR-Recommendations"
uv run --project .. rh-mod-skills ingest approve encr-standard-dataset
uv run --project .. rh-mod-skills ingest implement encr-standard-dataset
uv run --project .. rh-mod-skills ingest verify encr-standard-dataset
uv run --project .. rh-mod-skills status encr-standard-dataset

uv run --project .. rh-mod-skills extract plan encr-standard-dataset
uv run --project .. rh-mod-skills extract approve encr-standard-dataset
uv run --project .. rh-mod-skills extract implement encr-standard-dataset
uv run --project .. rh-mod-skills extract verify encr-standard-dataset
```

Expect: projection with **Table 1** (Variable/Comment, 20 rows) and **Table 2** (3 columns, 5 rows); no Markdown L1; extract succeeds (does not invent PDF prose).
