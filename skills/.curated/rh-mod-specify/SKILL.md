---
name: "rh-mod-specify"
description: >
  Converge an annotate-complete inventory and bindings into logical_models[].
  CLI writes the specify plan and logical-model.yaml; this skill proposes
  FHIR types, cardinality, and optional multi-LM regroup (Patient / diagnosis /
  hospital + Reference). Modes: plan · implement · verify.
compatibility: "rh-mod-skills >= 0.1.0"
context_files:
  - reference.md
  - examples/encr.md
metadata:
  author: "RH Mod Skills"
  version: "1.1.0"
  source: "skills/.curated/rh-mod-specify/SKILL.md"
  lifecycle_stage: "l2-semi-structured"
  reads_from:
    - tracking.yaml
    - models/<model>/structured/inventory.yaml
    - models/<model>/structured/bindings.yaml
    - models/<model>/process/plans/specify-plan.yaml
  writes_via_cli:
    - "rh-mod-skills specify plan"
    - "rh-mod-skills specify approve"
    - "rh-mod-skills specify implement"
    - "rh-mod-skills specify verify"
    - "rh-mod-skills status"
---

# rh-mod-specify

Specify is the L2 logical-model stage. Annotate already owns terminology.
This skill proposes **types**, **cardinality**, and optional **multi-LM regroup**
on the specify plan. Extract owns paths and provenance; regroup happens **only**
here (never in extract). Formalize emits one StructureDefinition per LM after this.

**Never inspect `rh-mod-skills` source code.** Use this skill, [reference.md](reference.md),
and `rh-mod-skills specify --help`. Do not write `logical-model.yaml` or the
specify plan as a persistence bypass. Reviewer edits of `datatype` /
`cardinality` / `logical_models[]` on the existing plan YAML are the gate; then
run the CLI.

Do not invent terminology codes. Copy bindings already on the plan.

## User Input

```text
$ARGUMENTS
```

First word is the mode. Typical: `plan encr`.

## Plan

1. Run `rh-mod-skills status <model>`. Next must be `specify`. If next is still
   `annotate`, stop — remaining inventory paths are undecided.
2. Run `rh-mod-skills specify plan <model>`.
3. Default plan: one `logical_models[]` entry with `id` = tracking model id and
   inventory entities as Backbone children (`inventory_path` = inventory path).
4. Open `models/<model>/process/plans/specify-plan.yaml`. For each element:
   - Keep inventory `display` and `provenance` (untrusted source text).
   - Set `datatype` to a FHIR type only when honest (`date`, `string`, `code`,
     `CodeableConcept`, `Identifier`, `Quantity`, `Reference`, …). Leave
     `unknown` otherwise.
   - Codebook letters such as `F`/`A` are not types — the CLI already stored
     `unknown`.
   - Set `cardinality` to `0..1` / `1..1` / `0..*` / `1..*` when the source
     states multiplicity; else leave `unknown`.
   - Do not change mappings/`value_set` unless the reviewer explicitly asked to
     re-annotate (that is annotate, not specify).
5. Optional regroup (ENCR-style): split into Patient / diagnosis / hospital LMs.
   Every inventory path must appear exactly once via `inventory_path`. For
   cross-LM links use `datatype: Reference` with `reference.target` = other LM id.
   At most one `root: true`.
6. Do not translate labels as a substitute for typing.

## Implement

```bash
rh-mod-skills specify approve <model>
rh-mod-skills specify implement <model>
rh-mod-skills specify verify <model>
rh-mod-skills status <model>
```

Implement writes `logical_models[]` only (no top-level `entities[]`). Inventory
bytes are unchanged. Unknown types/cardinality are advisory on verify. Missing /
duplicate `inventory_path` or unknown `reference.target` are blocking.

## Verify

`specify verify` is read-only. Next after a successful implement is `formalize`.
