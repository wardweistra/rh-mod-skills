# Quickstart: remap roles on an unrecognized sheet

From `example-project/`:

```bash
uv run --project .. rh-mod-skills extract plan nkr-breast
```

Confirm `process/plans/extract-plan.yaml` has `sheets[0].columns` with `variabele_name` → `id`, `variabele_categorie` → `category`, `variabele_label` → `label`.

To remap a sheet that hints poorly: edit those `role` values, then:

```bash
uv run --project .. rh-mod-skills extract plan nkr-breast
uv run --project .. rh-mod-skills extract approve nkr-breast
uv run --project .. rh-mod-skills extract implement nkr-breast --replace
uv run --project .. rh-mod-skills extract verify nkr-breast
```

To throw away saved roles and hint from headers again:

```bash
uv run --project .. rh-mod-skills extract plan nkr-breast --rehint
```
