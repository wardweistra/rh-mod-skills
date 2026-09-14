# Quickstart: extract nkr-breast

Requires 002 ingest already run in `example-project/` (IKNL table projection present).

```bash
ROOT=/Users/ward/workspace/rh-mod-skills
cd "$ROOT/example-project"

uv run --project .. rh-mod-skills extract plan nkr-breast
uv run --project .. rh-mod-skills extract approve nkr-breast
uv run --project .. rh-mod-skills extract implement nkr-breast
uv run --project .. rh-mod-skills extract verify nkr-breast
uv run --project .. rh-mod-skills status nkr-breast

# PDF-only must fail until 004 projects tables
uv run --project .. rh-mod-skills extract plan encr-standard-dataset
```

Expect: NKR 5 entities, 153 elements, datatype/cardinality `unknown`, next=`annotate`. ENCR plan exits non-zero (no table projection).
