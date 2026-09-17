# Data model: ingest and status skills (007)

No new YAML schemas. Skills document existing 001/002/004 artifacts.

## Ingest plan (skill must describe)

Path: `models/<id>/process/plans/ingest-plan.yaml` — owned by ingest CLI.

Fields the ingest skill reasons about (see [002](../002-rh-mod-ingest/data-model.md) and [004](../004-rh-mod-ingest-pdf/data-model.md)):

| Field | Skill action |
|-------|----------------|
| `sources[].path` / `type` / `name` | Choose files; type from suffix via CLI |
| `origin_url` | Supply public catalog URL when known |
| `projection` | `tables` or `skipped` — never Markdown |
| `skip_reason` | Accept register-only: `no-text-layer`, `no-tables-detected`, `no-tables-approved`, `extractor-error` |
| `tables[].decision` | Reviewer include/exclude; skill proposes, does not silently include junk |

Implement still copies originals to `sources/raw/` and projections to `sources/projections/`. Event: `source_added`.

## Status vocabulary (skill must map)

| CLI `Stage` | CLI `Next` | Skill to name |
|-------------|----------------|---------------|
| initialized | ingest | `rh-mod-ingest` |
| ingested | extract | `rh-mod-extract` |
| extracted / annotating | annotate | `rh-mod-annotate` |
| extracted / annotating (all bound or unbound) | specify | not built yet |
| specified | formalize | not built yet |
| formalized | verify | `rh-mod-verify` not built yet |
| (no tracking) | init | `rh-mod-skills init` |

Status skill writes nothing. Drift → `ingest verify`, not a status mode.
