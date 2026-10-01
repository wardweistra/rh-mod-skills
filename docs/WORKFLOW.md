# RH Mod Skills — Workflow

## Lifecycle

```
L1 Ingest                    L2 Extract / Annotate / Specify         L3 Formalize
─────────                    ─────────────────────────────────       ────────────
Codebooks, dictionaries  →   Inventory + bindings 2.0 + LM YAML  →   N StructureDefinitions
(Excel/CSV/PDF tables)       (mappings / optional value_set;         (one per logical model)
                             multi-LM regroup on specify only)        + ValueSets when authored
```

```
models/<model-id>/sources/   models/<model-id>/structured/           models/<model-id>/computable/
```

**Map vs bind**: annotate `mappings[]` are concept mappings (formalize →
`ElementDefinition.mapping`). Authored `value_set` is the only path to a FHIR
ValueSet + binding. **rh-map-skills** (separate repo) starts after L3.

## Plan → Implement → Verify

Every lifecycle transition follows the same gate as rh-skills:

1. **Plan** — agent writes a durable review packet under `models/<model>/process/plans/`
2. **Human review** — approve / reject / needs-revision
3. **Implement** — CLI writes artifacts; fails if the plan is not approved
4. **Verify** — non-destructive; blocking errors vs warnings

## Skill stages

| Stage | Skill | Output | Pack |
|-------|-------|--------|------|
| Ingest | `rh-mod-ingest` | Structured L1 projection of the codebook | full |
| Extract | `rh-mod-extract` | `inventory.yaml`, `value-domains.yaml` | SKILL.md |
| Annotate | `rh-mod-annotate` | `bindings.yaml` | SKILL.md |
| Specify | `rh-mod-specify` | `logical-model.yaml` (`logical_models[]`) | full |
| Formalize | `rh-mod-formalize` | N logical `StructureDefinition`s + optional ValueSets + snapshot | full |
| IG | `rh-mod-ig` | One IG tree listing all SDs from snapshot | full |
| Verify | `rh-mod-verify` | Consolidated report | full |
| Status | `rh-mod-status` | Next step from tracking (read-only) | full |

## Guiding principle

> All deterministic work in `rh-mod-skills` CLI commands. All reasoning in SKILL.md.

The unit of work is a **model**, not a topic. Mapping workbooks are out of scope.
