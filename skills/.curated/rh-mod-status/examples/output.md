# Example: status on example-project

```bash
cd example-project
uv run --project .. rh-mod-skills status
```

```
Models: 2

nkr-breast	annotating	next:annotate
encr-standard-dataset	extracted	next:annotate
```

One extra sentence: next is annotate — use `rh-mod-annotate` (do not start specify).

Single model:

```bash
uv run --project .. rh-mod-skills status nkr-breast
```

```
Model: nkr-breast
Title: NKR breast cancer data dictionary
Stage: annotating
Sources: 1
Next: annotate
```

One extra sentence: `gesl` may already be bound; remaining inventory paths stay
undecided until annotate walks them. Still `rh-mod-annotate`, not specify.

Empty consumer (no tracking): CLI tells you to `init`. Do not invent a model.

User asks “did the Excel change?”: run `rh-mod-skills ingest verify nkr-breast`,
not a status subcommand.
