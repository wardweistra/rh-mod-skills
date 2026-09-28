# Quickstart: review gesl in HTML

From `example-project/` after enrich of `gesl`:

```bash
uv run --project .. rh-mod-skills annotate export nkr-breast
```

Open `models/nkr-breast/process/plans/annotate-review.html`. Select a candidate. Download picks YAML.

```bash
uv run --project .. rh-mod-skills annotate import nkr-breast --from /path/to/annotate-picks.yaml
uv run --project .. rh-mod-skills annotate approve nkr-breast
uv run --project .. rh-mod-skills annotate implement nkr-breast
uv run --project .. rh-mod-skills annotate verify nkr-breast
```

Expect `bindings.yaml` to contain the picked code only after implement, not after import.
