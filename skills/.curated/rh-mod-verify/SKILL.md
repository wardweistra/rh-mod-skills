---
name: "rh-mod-verify"
description: >
  Read-only lifecycle health check. Runs rh-mod-skills verify and presents
  coverage, stage pass/fail/skipped, and advisory unbound / validator-not-run.
  Never writes tracking. Modes: show.
compatibility: "rh-mod-skills >= 0.1.0"
context_files:
  - reference.md
  - examples/encr.md
metadata:
  author: "RH Mod Skills"
  version: "1.0.0"
  source: "skills/.curated/rh-mod-verify/SKILL.md"
  lifecycle_stage: "any"
  reads_from:
    - tracking.yaml
    - models/<model>/structured/
    - models/<model>/computable/
  writes_via_cli: []
---

# rh-mod-verify

Consolidated **verify** after (or during) the ingest → extract → annotate →
specify → formalize path. The CLI is the source of truth. This skill runs it
and presents the report.

**Read-only.** Do not write `tracking.yaml`, plans, JSON, or mapping files.
Do not invent a pass/fail the CLI did not print. Unbound leftovers are
advisory unless a stage line is `fail`.

**Never inspect `rh-mod-skills` source code.** Use this skill, [reference.md](reference.md),
and `rh-mod-skills verify --help`.

## User Input

```text
$ARGUMENTS
```

Optional model id (kebab-case). Empty → all models. Typical: `encr`.

## Show

```bash
rh-mod-skills status <model>      # orientation; Next: verify after formalize
rh-mod-skills verify <model>      # one model
rh-mod-skills verify              # all models
rh-mod-skills status <model>      # still Next: verify — health check, not a gate
```

Present the CLI output as-is. Then at most one sentence:

- Any `fail` → blocking; name the stage (ingest drift, formalize checksum, …).
- All applicable stages `pass` with `unbound=N` → leftovers are visible; not a
  reason to re-annotate unless the reviewer asked.
- `validator=not-run` is expected; do not fetch a FHIR validator binary.
- `skipped` stages mean that lifecycle step has not produced artifacts yet.

Do not start `rh-map-skills` work from this skill. Mapping is a different product.

Example: [examples/encr.md](examples/encr.md).
