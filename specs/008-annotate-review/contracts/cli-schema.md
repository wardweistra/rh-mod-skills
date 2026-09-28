# CLI: annotate export / import (008)

Extends [005 cli-schema](../005-rh-mod-annotate/contracts/cli-schema.md).

```
rh-mod-skills annotate export <model>
rh-mod-skills annotate import <model> --from FILE
```

Existing `plan | enrich | approve | implement | verify` unchanged.

### export

Reads `annotate-plan.yaml`. Writes `process/plans/annotate-review.html`.

Fails if plan missing. Does not require `approved`. Does not call ReasonHub. Does not write bindings. Does not append tracking events.

### import

`--from` required. Reads picks YAML. Updates matching plan elements by `path`. Sets plan `status: draft`.

Fails if: plan missing; picks `model` ≠ argument; unknown path; accept without valid pick rank; unbound without reason; replace without chosen system+code+display.

Does not write `bindings.yaml`. Does not append `element_bound`.

### HTML download

The generated page includes a control that downloads picks YAML (client-side). The CLI does not need a browser. Tests write a picks file directly to `import --from`.
