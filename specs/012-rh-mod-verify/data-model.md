# Data model: verify coordinator

No durable files. Report is stdout only.

## Per-model report

```text
Model: encr
coverage: inventory=124 bound=119 unbound=5 undecided=0
ingest: pass
extract: pass
annotate: pass
specify: pass
formalize: pass
advisory: unbound=5 validator=not-run
```

Skipped stages print `specify: skipped` (etc.). Failed stages print `formalize: fail` plus the stage’s blocking lines.

## Coverage

When `inventory.yaml` exists: count inventory paths; bound / unbound / undecided from bindings (same rules as annotate verify). Missing bindings → bound=0 unbound=0 undecided=inventory.

## Tracking

Unchanged. No `validated` event. No plan YAML.
