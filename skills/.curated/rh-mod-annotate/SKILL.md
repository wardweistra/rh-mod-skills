---
name: "rh-mod-annotate"
description: >
  Bind extracted inventory elements to terminology codes via ReasonHub MCP.
  CLI writes the plan, review HTML, picks import, and bindings; this skill
  runs MCP search and records hits with `rh-mod-skills annotate enrich`.
  Modes: plan · enrich · export · import · implement · verify.
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
    - "rh-mod-skills annotate export"
    - "rh-mod-skills annotate import"
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
      when: enrich — plan systems includes icd-10 or icd-10-cm
    - tool: reasonhub-search_rxnorm
      when: enrich — plan systems includes rxnorm
    - tool: reasonhub-search_ucum
      when: enrich — plan systems includes ucum
    - tool: reasonhub-search_all_codesystems
      when: enrich — plan systems includes all (cross-system; do not also fan out per named system)
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
4. For each planned element, MCP search with `top_k=5` (or the plan `query` if the reviewer edited it). If `systems` includes `all`, call `search_all_codesystems` once. Otherwise call the tool for each named system: `search_snomed`, `search_loinc`, `search_rxnorm`, `search_ucum`, `search_icd10` (`icd-10` and `icd-10-cm`). Default when `systems` is omitted/snomed-only: `search_snomed`.
5. Map MCP hits to FHIR system URIs. Copy `system`, `code`, and `display` exactly from the hit (especially for `all`). Do not transform `distance`. Aliases on `--candidate`: `snomed`, `loinc`, `icd-10`, `icd-10-cm` (`http://hl7.org/fhir/sid/icd-10-cm`), `rxnorm` (`http://www.nlm.nih.gov/research/umls/rxnorm`), `ucum` (`http://unitsofmeasure.org`). Never record `all` as a candidate system.
6. Record via CLI (at most five `--candidate` flags). Omit `--candidate` when MCP returned zero hits:

```bash
rh-mod-skills annotate enrich <model> --element <id-or-path> \
  --candidate 'http://snomed.info/sct|<code>|<display>|<distance>' \
  --lookup-query '<query used>'
```

7. Stop if any MCP call fails. Do not guess codes from `*dat` names or local value-domain lists.

## Review (export / import)

After enrich, generate the review page with the CLI. Do **not** write `annotate-review.html` or `annotate-picks.yaml` yourself.

```bash
rh-mod-skills annotate export <model>
```

Tell the reviewer to open `models/<model>/process/plans/annotate-review.html`, pick a candidate (or unbound / skip / replace), and download picks YAML. Then import:

```bash
rh-mod-skills annotate import <model> --from <picks.yaml>
```

Import updates the annotate plan only (`decision` / `chosen` / `reason`) and sets `status: draft`. It does not write `bindings.yaml`. If the plan was approved, import un-approves it.

## Implement

After import (or after the reviewer edited plan decisions), approve then implement:

```bash
rh-mod-skills annotate approve <model>
rh-mod-skills annotate implement <model>
rh-mod-skills annotate verify <model>
rh-mod-skills status <model>
```

`accept` with empty candidates fails. `replace` needs reviewer `chosen`. `unbound` needs `reason`. `reject`/`pending` skip the bindings row.

## Verify

`annotate verify` is read-only. Next stays `annotate` until every inventory path is bound or unbound.
