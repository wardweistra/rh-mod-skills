# rh-mod-status reference

## Commands

```
rh-mod-skills status
rh-mod-skills status <model>
```

Writes: none. Does not append tracking events.

There is no `status check-changes`. Drift is `rh-mod-skills ingest verify <model>`.

## Stage → Next → skill

| CLI `Stage` | CLI `Next` | Name this skill |
|-------------|----------------|-----------------|
| initialized | ingest | `rh-mod-ingest` |
| ingested | extract | `rh-mod-extract` |
| extracted | annotate | `rh-mod-annotate` |
| annotating | annotate | `rh-mod-annotate` |
| extracted / annotating (every inventory path bound or unbound) | specify | not built yet |
| specified | formalize | not built yet |
| formalized | verify | `rh-mod-verify` not built yet |
| (no tracking / no models) | init | `rh-mod-skills init` |

`Next` is computed by the CLI (inventory vs bindings for annotate vs specify).
Do not recompute it from files and disagree with the CLI.

## Output shapes

Portfolio:

```
Models: 2

nkr-breast	annotating	next:annotate
encr-standard-dataset	extracted	next:annotate
```

One model:

```
Model: nkr-breast
Title: …
Stage: annotating
Sources: 1
Next: annotate
```

Add at most one sentence after this block. Do not add A/B/C choices.
