---
name: "rh-mod-status"
description: >
  Read-only lifecycle orientation. Runs rh-mod-skills status and maps CLI Next
  to the next curated skill. Never writes tracking. Modes: show.
compatibility: "rh-mod-skills >= 0.1.0"
context_files:
  - reference.md
  - examples/output.md
metadata:
  author: "RH Mod Skills"
  version: "1.0.0"
  source: "skills/.curated/rh-mod-status/SKILL.md"
  lifecycle_stage: "any"
  reads_from:
    - tracking.yaml
  writes_via_cli: []
---

# rh-mod-status

Shows where each **model** is in the ingest → extract → annotate → specify →
formalize path. The CLI is the source of truth for `Stage` and `Next`. This
skill presents that output and may add **one sentence** naming the next skill.

**Read-only.** Do not write `tracking.yaml`, plans, or artifacts. Do not invent
a Next the CLI did not print. Do not append a lettered menu of alternatives.

**Never inspect `rh-mod-skills` source code.** Use this skill and
`rh-mod-skills status --help`.

## User Input

```text
$ARGUMENTS
```

Optional model id (kebab-case). Empty → all models. Typical: `nkr-breast`.

## Pre-checks

1. Run from the consumer directory (`example-project/`).
2. If `rh-mod-skills status` says there is no tracking file, tell the user to
   `rh-mod-skills init <model>`. Do not create the model yourself.
3. If a model id was given and the CLI errors, report that error. Do not `init`
   a missing id unless the user asked to initialize.

## Show

```bash
rh-mod-skills status              # all models
rh-mod-skills status <model>      # one model
```

Present the CLI output as-is. Then at most one sentence, using
[reference.md](reference.md):

- `Next: ingest` → run `rh-mod-ingest`
- `Next: extract` → run `rh-mod-extract`
- `Next: annotate` → run `rh-mod-annotate`
- `Next: specify` or `formalize` → those skills are not built yet
- `Next: init` → `rh-mod-skills init <model>`

If the user asks about source drift or checksums, point them to
`rh-mod-skills ingest verify <model>` (and `rh-mod-ingest` verify mode). Status
has no check-changes command.

Example transcript: [examples/output.md](examples/output.md).
