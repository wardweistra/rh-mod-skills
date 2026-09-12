# Quickstart: Framework skeleton (001)

This slice only creates a model workspace. It does not ingest the IKNL or ENCR files.

## Setup

```bash
cd /Users/ward/workspace/rh-mod-skills
uv sync
uv run pytest
```

## Init two proving models (consumer cwd)

Use `example-project/` so init does not refuse the tool repo:

```bash
cd example-project
uv run --project .. rh-mod-skills init nkr-breast \
  --title "NKR breast cancer data dictionary" \
  --description "IKNL NKR variables for breast cancer"
uv run --project .. rh-mod-skills init encr-standard-dataset \
  --title "ENCR standard dataset" \
  --description "European Network of Cancer Registries minimum dataset (2023)"
uv run --project .. rh-mod-skills status
```

Use `--project` (not `--directory`) so the consumer cwd stays `example-project/`. `--directory` would switch into the tool repo and `init` would refuse.

Expect `models/nkr-breast/` and `models/encr-standard-dataset/` with empty `sources/`, plus `tracking.yaml` with two `model_created` events. `status` next-step is `ingest`.

L1 bytes for 002 live in the tool repo:

- `tests/fixtures/l1/nkr-breast/IKNL_Data_dictionary.xlsx`
- `tests/fixtures/l1/encr-standard-dataset/ENCR-Recommendation-standard-dataset_Mar2023.pdf`

## Verify locally

```bash
uv run pytest tests/unit/
```

After 002, ingest the fixtures into these models; 001 tests MUST still pass.
