# Quickstart: plan RxNorm / all

From `example-project/` after extract:

```bash
uv run --project .. rh-mod-skills annotate plan nkr-breast --element gesl --system rxnorm
uv run --project .. rh-mod-skills annotate plan nkr-breast --element gesl --system all
```

Expect `systems: [rxnorm]` or `[all]`. Then the skill MCP-searches and records with `annotate enrich --candidate 'rxnorm|…|…'` (or an `http://…` URI from cross-system hits).
