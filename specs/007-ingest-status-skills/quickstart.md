# Quickstart: ingest and status skills

From a consumer (`example-project/`):

```bash
uv run --project .. rh-mod-skills status
```

Expect CLI `Next` values. The status skill adds at most one sentence naming `rh-mod-ingest` / `rh-mod-extract` / `rh-mod-annotate`.

Ingest proving (agent follows `rh-mod-ingest`, does not write YAML by hand):

```bash
uv run --project .. rh-mod-skills ingest plan nkr-breast \
  --source ../tests/fixtures/l1/nkr-breast/IKNL_Data_dictionary.xlsx \
  --origin-url https://iknl.nl/nkr/cijfers-op-maat/over-datacatalogus
uv run --project .. rh-mod-skills ingest approve nkr-breast
uv run --project .. rh-mod-skills ingest implement nkr-breast
uv run --project .. rh-mod-skills ingest verify nkr-breast
uv run --project .. rh-mod-skills status nkr-breast
```

PDF: plan the ENCR 2023 standard-dataset PDF, keep Table 1 and Table 2 included, leave companions skipped when the plan says so. Never emit a Markdown codebook.

Skill files to author: `skills/.curated/rh-mod-ingest/` and `skills/.curated/rh-mod-status/` (SKILL.md, reference.md, examples).
