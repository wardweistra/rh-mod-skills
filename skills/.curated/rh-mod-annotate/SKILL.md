---
name: "rh-mod-annotate"
description: >
  Bind extracted inventory elements to terminology codes via ReasonHub MCP.
  CLI writes the plan and bindings; this skill runs MCP search and records
  hits with `rh-mod-skills annotate enrich`. Modes: plan · enrich · implement · verify.
compatibility: "rh-mod-skills >= 0.1.0"
metadata:
  author: "RH Mod Skills"
  version: "1.0.0"
  source: "skills/.curated/rh-mod-annotate/SKILL.md"
  lifecycle_stage: "l2-semi-structured"
  reads_from:
    - tracking.yaml
    - models/<model>/structured/inventory.yaml
    - models/<model>/process/plans/annotate-plan.yaml
  writes_via_cli:
    - "rh-mod-skills annotate plan"
    - "rh-mod-skills annotate enrich"
    - "rh-mod-skills annotate approve"
    - "rh-mod-skills annotate implement"
    - "rh-mod-skills annotate verify"
    - "rh-mod-skills status"
  uses_mcp:
    - tool: reasonhub-search_snomed
      when: enrich — default candidate system
    - tool: reasonhub-search_loinc
      when: enrich — plan systems includes loinc
    - tool: reasonhub-search_icd10
      when: enrich — plan systems includes icd-10
    - tool: reasonhub-codesystem_lookup
      when: enrich — confirm display / canonical system URI before recording
---

# rh-mod-annotate

Annotate is the L2 terminology-binding stage. Extract already owns inventory
shape. This skill proposes codes; specify later fills datatypes. Mapping (FML,
StructureMap, mapping.xlsx) is out of scope.

**MCP ownership**: this skill/agent performs ReasonHub searches. The CLI does
not look up codes. `annotate enrich` only records `--candidate` rows you already
collected. If MCP is unavailable, stop and tell the user — do not invent codes
and do not write `bindings.yaml` yourself.

**Never inspect `rh-mod-skills` source code.** Use this skill and the CLI help.

## User Input

```text
$ARGUMENTS
```

First word is the mode. Typical: `plan nkr-breast --element gesl`.

## Plan

1. Confirm extract is done (`inventory.yaml` present). If not, tell the user to run extract.
2. Run `rh-mod-skills annotate plan <model> --element …` (or `--all-undecided`).
3. Plan writes empty `candidates: []`. Query defaults to inventory display (Dutch for NKR). Do not translate the label as a substitute for binding.
4. For each planned element, MCP search with `top_k=5` (or the plan `query` if the reviewer edited it). Prefer `search_snomed` unless the plan `systems` list says otherwise.
5. Map MCP hits to FHIR system URIs (`http://snomed.info/sct`, `http://loinc.org`, `http://hl7.org/fhir/sid/icd-10`). Copy `code` and `display` exactly. Do not transform `distance`.
6. Record via CLI (at most five `--candidate` flags). Omit `--candidate` when MCP returned zero hits:

```bash
rh-mod-skills annotate enrich <model> --element <id-or-path> \
  --candidate 'http://snomed.info/sct|<code>|<display>|<distance>' \
  --lookup-query '<query used>'
```

7. Stop if any MCP call fails. Do not guess codes from `*dat` names or local value-domain lists.

## Implement

Reviewer sets `decision` (`accept` / `reject` / `replace` / `unbound`) on the plan. Then:

```bash
rh-mod-skills annotate approve <model>
rh-mod-skills annotate implement <model>
rh-mod-skills annotate verify <model>
rh-mod-skills status <model>
```

`accept` with empty candidates fails. `replace` needs reviewer `chosen`. `unbound` needs `reason`. `reject`/`pending` skip the bindings row.

## Verify

`annotate verify` is read-only. Next stays `annotate` until every inventory path is bound or unbound.
