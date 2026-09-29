# CLI: verify (012)

```
rh-mod-skills verify
rh-mod-skills verify <model>
```

### Behavior

Read-only. Optional model id. No model → every tracking model. Unknown model → fail closed.

Per model: coverage line (if inventory present); then ingest/extract/annotate/specify/formalize as `pass` / `fail` / `skipped`. Advisory line includes `unbound=N` when coverage exists and always `validator=not-run`.

Exit non-zero if any applicable stage fails, or if any model in a portfolio run fails.

Does not write tracking, plans, JSON, or mapping files.
