# CLI: ingest

```
rh-mod-skills ingest plan <model> --source FILE [--source FILE ...] [--origin-url URL]
rh-mod-skills ingest approve <model>
rh-mod-skills ingest implement <model> [--acknowledge-drift]
rh-mod-skills ingest verify <model>
```

### plan

Writes `process/plans/ingest-plan.yaml` with `status: draft`. Detects type from suffix. Does not copy sources.

Exit 0 on write; 1 if model missing; 2 usage.

### approve

Sets `status: approved`. Fails if plan missing.

### implement

Fails if plan missing or not approved. Copies each source to `sources/raw/`, checksums, writes table projection for excel/csv, skips PDF (no Markdown). Appends `source_added`. Idempotent on unchanged checksum (no duplicate event). If `structured/` has artifacts and a source checksum changed, fail unless `--acknowledge-drift` (still does not delete L2).

### verify

Read-only. Per source: original present, checksum match/drift, projection present or skipped + reason. For tables: sheet/column/row counts. Exit 1 if any blocking (missing file, drift).
