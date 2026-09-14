# CLI: ingest (PDF tables)

Same commands as 002. PDF behavior changes as follows.

```
rh-mod-skills ingest plan <model> --source FILE [--source FILE ...] [--origin-url URL]
rh-mod-skills ingest approve <model>
rh-mod-skills ingest implement <model> [--acknowledge-drift]
rh-mod-skills ingest verify <model>
```

### plan

For `.pdf` sources, open the file and list detected tables (`id`, `name`, `pages`, `columns`, `row_count`, `warnings`, `decision`). Default `projection: tables` when at least one table is `include`; otherwise `skipped` with `skip_reason`. Does not copy files. Excel/CSV unchanged.

Exit 1 only for missing model / usage. Soft-fail PDF detection (`extractor-error`) still writes a draft plan.

### implement

Unapproved still fails closed. For included PDF tables, write `sources/projections/<name>.yaml` with `type: pdf` and one sheet per included table. Original PDF stays in `sources/raw/`. No Markdown L1 file.

If every detected table is `exclude`, register `projection: skipped` / `no-tables-approved`.

If checksum matches a prior skip but the plan now requests tables, rewrite the projection (do not no-op).

One source’s skip does not roll back another source on the same plan.

### verify

For PDF `tables`: original, checksum, projection present, sheet/column/row counts.  
For PDF `skipped`: original, checksum, reason (`no-text-layer` / `no-tables-detected` / `no-tables-approved` / `extractor-error`).
