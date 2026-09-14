# Quickstart: annotate gesl on nkr-breast

Requires 003 extract already run in `example-project/` (`structured/inventory.yaml` present). ReasonHub MCP must be connected in the agent. The CLI does not call ReasonHub.

```bash
ROOT=/Users/ward/workspace/rh-mod-skills
cd "$ROOT/example-project"

uv run --project .. rh-mod-skills annotate plan nkr-breast --element gesl
# Agent: MCP search (query from plan, default Geslacht — reviewer may change to sex/gender)
# Agent records hits (example):
uv run --project .. rh-mod-skills annotate enrich nkr-breast --element gesl \
  --candidate 'http://snomed.info/sct|263495000|Gender'
# Review process/plans/annotate-plan.yaml: set decision=accept (or replace/unbound)
uv run --project .. rh-mod-skills annotate approve nkr-breast
uv run --project .. rh-mod-skills annotate implement nkr-breast
uv run --project .. rh-mod-skills annotate verify nkr-breast
uv run --project .. rh-mod-skills status nkr-breast
```

Expect: bindings contain `patientgegevens.gesl` as bound; 152 elements still undecided; Next: `annotate`. No logical-model file.

`accept` with empty candidates (no enrich) fails closed — no invented codes.
