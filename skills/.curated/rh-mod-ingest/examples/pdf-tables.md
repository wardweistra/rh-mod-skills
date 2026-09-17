# Example: ingest ENCR PDFs (`encr-standard-dataset`)

Consumer: `example-project/`. Origin:
https://www.encr.eu/ENCR-Recommendations

Plan the 2023 standard-dataset PDF first (Table 1 + Table 2 are the codebook).
Companion English PDFs from the same page may be passed as extra `--source`
files; many will skip (no reconstructable tables).

```bash
cd example-project
uv run --project .. rh-mod-skills ingest plan encr-standard-dataset \
  --source ../tests/fixtures/l1/encr-standard-dataset/ENCR-Recommendation-standard-dataset_Mar2023.pdf \
  --origin-url https://www.encr.eu/ENCR-Recommendations
```

Read the draft plan. For the standard-dataset PDF, keep:

- Table 1 — Variable / Comment, ~20 rows, pages 2–3 (`continued-without-header` is OK)
- Table 2 — cancer type / stage variables / remarks, ~5 rows, page 4

Set any junk detection to `decision: exclude` with a reason on the plan YAML
(reviewer gate). Then:

```bash
uv run --project .. rh-mod-skills ingest approve encr-standard-dataset
uv run --project .. rh-mod-skills ingest implement encr-standard-dataset
uv run --project .. rh-mod-skills ingest verify encr-standard-dataset
```

Expect `projection: tables` for the standard-dataset file. Companions with
`skip_reason: no-tables-detected` (or `no-text-layer`) stay register-only —
that is success, not a prompt to OCR or dump Markdown.

NBCA proving PDF: `tests/fixtures/l1/nbca/IKNL-NBCA-2026-Variabelen-datadictionary-1-0-3-Raster.pdf`
on model `nbca` (continued table, include the merged grid).

If the user asks to OCR or “just make Markdown”, refuse. Extract is a later
skill; it needs a table projection, not page prose.
