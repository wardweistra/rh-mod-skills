# Research: entity graph + mapping/binding split

**Date**: 2026-09-30  
**Spec**: [spec.md](./spec.md)  
**Approach (non-normative)**: Project store `docs/pipeline-entity-and-binding-approach.md`

Locked Ward decisions are inputs, not reopened. This file records implementable design choices that the approach left to plan.

---

## 1. Delivery order

**Decision**: Ship **Epic A** (mappings vs ValueSet) before **Epic B** (multi-LM regroup + multi-SD + IG).

**Rationale**: Approach Phase 1–4; highest leverage is stopping singleton-VS-from-single-code. Epic B needs new LM shape; Epic A can keep today’s `entities[]` tree and only change binding snapshots.

**Alternatives considered**: Big-bang both epics (higher risk); Epic B first (leaves dishonest ValueSets longer).

---

## 2. Schema version / clean break

**Decision**: Bump `bindings-schema.yaml` and `logical-model-schema.yaml` to `schema_version: "2.0"`. No compat loader, migrate CLI, or `--compat` flag. Loaders that require 2.0 shapes fail closed on 1.0 singleton rows with a message to re-annotate / re-specify.

**Rationale**: Locked decision 4; preferences prefer clean breaks with no install base.

**Alternatives considered**: Dual-read 1.0→mappings (rejected — compat burden).

---

## 3. Bindings row shape (Epic A)

**Decision**:

```yaml
status: mapped | unbound          # phase 1
mappings:                         # 0..*; ≤1 code per system URI
  - system: http://loinc.org
    code: "76689-9"
    display: Sex assigned at birth
    decision: accept              # accept | replace
value_set: null                   # reserved; authored only in phase 2
reason: ""                        # required iff unbound
```

- Annotate-complete: every inventory path is `mapped` (≥1 mapping) or `unbound` (reason required).  
- Phase 2: `value_set: { strength, concepts[] }` may appear with or without mappings; status becomes `decided` when either mappings or value_set is present (see §4).  
- Strength lives **only** on `value_set`, never on mapping rows.  
- Duplicate system URI in `mappings[]` → implement / verify fail closed.

**Rationale**: Matches FR-A02–A05; keeps phase 1 CLI surface small.

**Alternatives considered**: Keep `status: bound` for mappings (confusing vs ValueSet binding); auto-promote mapping → example VS (rejected).

---

## 4. Phase 2 ValueSet status word

**Decision**: When Epic A phase 2 lands, rename/generalize durable status to `decided | unbound`, where `decided` means mappings and/or `value_set` present. Phase 1 MAY write `mapped` and treat it as the decided-with-mappings-only synonym; verify/status accept `mapped` as complete. Tasks may collapse to `decided` in one schema pass if cheaper.

**Rationale**: Avoids two breaking renames; phase 1 tests can key on `mapped`.

---

## 5. Annotate plan / multi-accept UX (Epic A)

**Decision**: Plan elements store `mappings: []` (durable picks) and optional pending `candidates[]` (unchanged enrich). Accept/replace appends or replaces the mapping for that candidate’s system (≤1 per system). `unbound` clears mappings and requires reason. Export/import HTML/picks evolve to accept-by-system (or multi-rank across systems); exact HTML fields are task-level but must not force single-coding.

**Rationale**: Multi-system search (009) already fills candidates; implement must persist more than one.

**Alternatives considered**: Separate plan per system (rejected — worse UX); only last accept wins across all systems (rejected — loses multi-map).

---

## 6. Formalize mapping emission (Epic A)

**Decision**: For each distinct `mappings[].system` on an LM element, ensure a `StructureDefinition.mapping` identity (id = stable slug from URI; `uri` = system). Emit `ElementDefinition.mapping[{identity, map}]` with `map` = code (identity carries system). No ConceptMap JSON. ValueSet + `ElementDefinition.binding` **only** if `value_set` present (phase 2); mappings-only → neither VS nor binding.

**Rationale**: Locked decision 3; FR-A07–A08.

**Alternatives considered**: `map` = `system|code` without identities (less browseable); ConceptMap per element (deferred).

---

## 7. Epic A keeps single-SD LM tree

**Decision**: During Epic A, `logical-model.yaml` retains `entities[]` + element paths. Binding snapshot on each element becomes `mappings` / optional `value_set` / unbound reason (no single system/code/strength). Formalize still emits **one** StructureDefinition from `entities[]` → BackboneElement until Epic B.

**Rationale**: Smallest vertical slice for gap 2; avoids blocking mappings on regroup redesign.

---

## 8. `canonical_base` storage (Epic B)

**Decision**: Reviewable field on `formalize-plan.yaml`: `canonical_base` (http(s) URI, no trailing slash required; normalize by strip). Implement derives each SD URL as `{canonical_base}/StructureDefinition/{logical-model-id}`. Snapshot stores `canonical_base` plus per-file URLs. Default proposal for proving: `https://encr.eu/fhir/recommendations` when model id suggests ENCR recommendations; otherwise `https://example.org/fhir/{model}`. Do **not** hardcode ENCR-only validation — only the pattern and http(s) check. Drop “canonical last segment == tracking model id” for multi-LM; each SD’s last segment MUST equal its `logical-model-id`.

**Rationale**: Spec FR-B06; formalize plan already owns canonical review today.

**Alternatives considered**: tracking.yaml-only config (less visible at approve gate); per-LM full URL editing (verbose; still allow override later if needed).

---

## 9. Logical model graph (Epic B)

**Decision**:

```yaml
model: recommendations          # tracking id
logical_models:
  - id: encr-patient
    title: Patient
    root: true                  # optional; at most one
    elements:
      - id: managing-hospital
        path: managing-hospital
        inventory_path: table-1.managing-hospital
        datatype: Reference
        cardinality: 0..1
        reference:
          target: encr-hospital
        mappings: [...]
        value_set: null
        reason: ""
        provenance: {...}
```

- Specify plan is the only regroup surface; skill proposes, CLI writes.  
- Default new plan with no reviewer regroup: one `logical_models[]` entry (`id` = tracking model id) wrapping today’s inventory entities as Backbone children **or** flat elements under that single LM — choose one in tasks; prefer **one LM id = tracking id, entities become Backbone under that SD** to preserve ENCR-ish navigation until reviewer splits.  
- `inventory_path` required; specify verify: every inventory path claimed exactly once; `reference.target` must resolve to an LM id in the same file.

**Rationale**: Locked decisions 1, 6, 8; FR-B01–B04.

**Alternatives considered**: Split tracking models (rejected); extract clinical `merge_into` (rejected).

---

## 10. Multi-SD formalize + IG (Epic B)

**Decision**: One `StructureDefinition-{lm-id}.json` per LM; root path / `id` / URL last segment = `lm-id`. Reference types use `type: [{code: Reference, targetProfile: [<canonical of target LM>]}]` (or documented logical equivalent if targetProfile is awkward for kind=logical — prefer targetProfile to the other LM canonical). Snapshot `files[]` lists all SDs + ValueSets. `ig sync` already mirrors snapshot files — extend IG `definition.resource` listing for N SDs; still **one** IG tree under `models/<tracking-id>/ig/`. No ConceptMap folder.

**Rationale**: Locked decisions 1, 7; FR-B05–B08; minimize ig command surface (V).

---

## 11. Constitution IV (strength on mappings)

**Decision**: Interpret “terminology bindings MUST record … binding strength” as applying to **ValueSet bindings** (`value_set.strength`). Concept mappings record system/code/display/decision without strength. Unbound still requires reason. Report mapped vs VS-bound vs unbound distinctly in verify.

**Rationale**: Avoids fake strengths on meaning-only mappings; aligns with locked split.

**Alternatives considered**: Keep dummy `example` on every mapping (rejected — recreates the conflation).

---

## 12. In-repo fixtures / proving

**Decision**: Unit tests use tiny synthetic consumers under `tests/` (CliRunner), not live ENCR tree. Epic B adds a mini multi-LM fixture (Patient + Hospital + one Reference). ENCR recommendations remains the external proving consumer for canonical URLs.

**Rationale**: Same pattern as 010/011; no network.
