---
name: "rh-mod-formalize"
description: >
  Emit a FHIR R4 logical StructureDefinition, ValueSets, and snapshot from a
  specified logical model. CLI writes JSON; this skill confirms canonical URL
  and version on the plan. Modes: plan · implement · verify.
compatibility: "rh-mod-skills >= 0.1.0"
context_files:
  - reference.md
  - examples/encr.md
metadata:
  author: "RH Mod Skills"
  version: "1.0.0"
  source: "skills/.curated/rh-mod-formalize/SKILL.md"
  lifecycle_stage: "l3-computable"
  reads_from:
    - tracking.yaml
    - models/<model>/structured/logical-model.yaml
    - models/<model>/process/plans/formalize-plan.yaml
  writes_via_cli:
    - "rh-mod-skills formalize plan"
    - "rh-mod-skills formalize approve"
    - "rh-mod-skills formalize implement"
    - "rh-mod-skills formalize verify"
    - "rh-mod-skills status"
---

# rh-mod-formalize

Formalize is the L3 handoff. Specify already owns types, cardinality, and
binding snapshots. This skill confirms the **canonical URL and version** that
rh-map-skills will pin. The CLI emits FHIR JSON.

**Never inspect `rh-mod-skills` source code.** Use this skill, [reference.md](reference.md),
and `rh-mod-skills formalize --help`. Do not write `StructureDefinition-*.json`,
`ValueSet-*.json`, or `snapshot.yaml` as a persistence bypass. Reviewer edits of
`canonical` / `version` on the existing plan YAML are the gate; then run the CLI.

Do not invent terminology codes. Copy bindings already on the logical model.
Do not write mapping.xlsx, FHIR Mapping Language, StructureMap, or FSH.

## User Input

```text
$ARGUMENTS
```

First word is the mode. Typical: `plan encr`.

## Plan

1. Run `rh-mod-skills status <model>`. Next must be `formalize`. If next is still
   `specify`, stop — there is no logical model yet.
2. Run `rh-mod-skills formalize plan <model>`.
3. Open `models/<model>/process/plans/formalize-plan.yaml`:
   - Set `canonical_base` to an http(s) URI (preferred). Implement derives
     `{canonical_base}/StructureDefinition/{lm-id}` for each logical model.
     Example proving base: `https://encr.eu/fhir/recommendations`.
   - `canonical` is the root/primary LM URL (must match that derivation).
   - Set `version` (semver string). Empty version fails implement.
   - If `unknown_datatype` is non-empty, **stop**. Those paths must be typed on
     the specify plan and `specify implement` re-run first. Do not guess `string`.
   - `unknown_cardinality` is a count of elements that will become `0..1`. Tell
     the reviewer; do not invent `1..1` / `0..*` here.
   - Plan counts: `mapped`, `value_set_bound`, `unbound`.

## Implement

```bash
rh-mod-skills formalize approve <model>
rh-mod-skills formalize implement <model>
rh-mod-skills formalize verify <model>
rh-mod-skills status <model>
```

One `StructureDefinition-<lm-id>.json` per LM. ValueSets only when `value_set`
is authored. Mappings emit `ElementDefinition.mapping` (no ConceptMap).
Unknown datatype is blocking. Path name portions over 64 characters are
blocking. Cardinality defaults are advisory on verify.

## Verify

`formalize verify` is read-only. Next after a successful implement is `verify`
— run `rh-mod-verify` (the coordinator). Validator-not-run is advisory, not a
reason to skip snapshot checksums.

Optional: `rh-mod-ig` (`rh-mod-skills ig sync`) stages `models/<model>/ig/` so
the reviewer can run the HL7 IG Publisher locally. That does not change `status`
next.
