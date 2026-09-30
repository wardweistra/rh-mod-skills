# rh-mod-verify reference

## Commands

```
rh-mod-skills verify
rh-mod-skills verify <model>
```

Writes: none. Does not append tracking events (including `validated`).

Stage verifies remain the owners:

```
rh-mod-skills ingest verify <model>
rh-mod-skills extract verify <model>
rh-mod-skills annotate verify <model>
rh-mod-skills specify verify <model>
rh-mod-skills formalize verify <model>
```

The coordinator runs those that apply and skips the rest.

## When a stage runs

| Stage | Runs when |
|-------|-----------|
| ingest | sources exist |
| extract | extract plan exists |
| annotate | inventory exists |
| specify | `logical-model.yaml` exists |
| formalize | snapshot or StructureDefinition JSON exists |

## Report

- `coverage: inventory=N bound=B unbound=U undecided=D` (if inventory exists)
- `ingest: pass` / `fail` / `skipped` (same for other stages)
- `advisory: unbound=U validator=not-run`

Blocking: any applicable stage `fail` (checksum drift, path mismatch, missing
required artifact for that stage).

Advisory: unbound counts; validator-not-run; unknown cardinality from specify
or formalize (those stages already treat them as advisory).

## Status

`Next: verify` does not change after a passing run. Re-run anytime.
