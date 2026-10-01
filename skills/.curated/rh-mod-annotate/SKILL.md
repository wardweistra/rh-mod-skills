---
name: "rh-mod-annotate"
description: >
  Map extracted inventory elements to terminology codes via ReasonHub MCP.
  CLI writes the plan, review HTML, picks import, and bindings 2.0 (mappings[]);
  this skill runs MCP search and records hits with `annotate enrich`.
  Modes: plan · enrich · export · import · implement · verify.
compatibility: "rh-mod-skills >= 0.1.0"
metadata:
  author: "RH Mod Skills"
  version: "2.0.0"
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
      when: enrich — plan systems includes snomed
    - tool: reasonhub-search_loinc
      when: enrich — plan systems includes loinc
    - tool: reasonhub-search_icd10
      when: enrich — plan systems includes icd-10 or icd-10-cm
    - tool: reasonhub-search_rxnorm
      when: enrich — plan systems includes rxnorm
    - tool: reasonhub-search_ucum
      when: enrich — plan systems includes ucum
    - tool: reasonhub-search_all_codesystems
      when: enrich — default / plan systems includes all (cross-system; do not also fan out per named system)
    - tool: reasonhub-codesystem_lookup
      when: enrich — confirm display / canonical system URI before recording
---

# rh-mod-annotate

Annotate is the L2 **concept-mapping** stage. Extract already owns inventory
shape. This skill proposes codes; specify later fills datatypes.

**Map vs bind**: Accepting LOINC and/or SNOMED on a path writes `mappings[]`.
That is **not** a FHIR ValueSet. Optional ValueSet authoring is a separate plan
field: `value_set: { strength, concepts[] }` (strength only there). Formalize
emits `ElementDefinition.mapping` for mappings-only paths, and ValueSet +
`ElementDefinition.binding` only when `value_set` is authored.

FML / StructureMap / mapping.xlsx remain out of scope (rh-map-skills).

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
3. Plan writes empty `candidates: []` and `mappings: []`. Query defaults to inventory display. Do not translate the label as a substitute for a mapping.
4. For each planned element, MCP search with `top_k=5` (or the plan `query` if the reviewer edited it). If `systems` includes `all` (plan default when `--system` is omitted), call `search_all_codesystems` once. Otherwise call the tool for each named system.
5. Map MCP hits to FHIR system URIs. Copy `system`, `code`, and `display` exactly. Aliases on `--candidate`: `snomed`, `loinc`, `icd-10`, `icd-10-cm`, `rxnorm`, `ucum`. Never record `all` as a candidate system.
6. Record via CLI (at most five `--candidate` flags):

```bash
rh-mod-skills annotate enrich <model> --element <id-or-path> \
  --candidate 'http://snomed.info/sct|<code>|<display>|<distance>' \
  --lookup-query '<query used>'
```

7. Stop if any MCP call fails. Do not invent codes.

## Review (export / import)

```bash
rh-mod-skills annotate export <model>
rh-mod-skills annotate import <model> --from <picks.yaml>
```

Import upserts into plan `mappings[]` by system URI (≤1 per system). Unbound clears
mappings and requires `reason`. Import does not write `bindings.yaml`.

## Implement

```bash
rh-mod-skills annotate approve <model>
rh-mod-skills annotate implement <model>
rh-mod-skills annotate verify <model>
rh-mod-skills status <model>
```

Implement writes `schema_version: "2.0"` with `status: mapped|unbound` and
`mappings[]`. No root-level `system`/`code`/`strength`. Authored `value_set` on
the plan (strength + concepts) is persisted when present; mappings alone leave
`value_set: null`. Duplicate system URIs fail closed. Legacy 1.0 bindings fail
closed — message says **re-annotate**.

## Verify

`annotate verify` reports `mapped` / `vs_bound` / `unbound` / `undecided`.
Annotate-complete when every inventory path is `mapped` (≥1 mapping and/or
authored `value_set`) or `unbound` (reason; empty mappings; `value_set` null).
