# RH Mod Skills — Workflow

## Lifecycle

```
L1 Ingest                    L2 Extract / Annotate / Specify         L3 Formalize
─────────                    ─────────────────────────────────       ────────────
Codebooks, dictionaries  →   Inventory + bindings + LM YAML     →    StructureDefinition
(Excel/CSV structure kept)   (human-editable, reviewer-gated)         kind=logical + ValueSets
```

```
models/<model-id>/sources/   models/<model-id>/structured/           models/<model-id>/computable/
```

**rh-map-skills** (separate repo) starts after L3: two snapshots in, mapping workbook then FHIR Mapping Language out.

## Plan → Implement → Verify

Every lifecycle transition follows the same gate as rh-skills:

1. **Plan** — agent writes a durable review packet under `models/<model>/process/plans/`
2. **Human review** — approve / reject / needs-revision
3. **Implement** — CLI writes artifacts; fails if the plan is not approved
4. **Verify** — non-destructive; blocking errors vs warnings

## Planned skill stages

| Stage | Skill | Output |
|-------|-------|--------|
| Ingest | `rh-mod-ingest` | Structured L1 projection of the codebook |
| Extract | `rh-mod-extract` | `inventory.yaml`, `value-domains.yaml` |
| Annotate | `rh-mod-annotate` | `bindings.yaml` |
| Specify | `rh-mod-specify` | `logical-model.yaml` |
| Formalize | `rh-mod-formalize` | FHIR logical `StructureDefinition` + ValueSets + snapshot manifest |
| Verify | `rh-mod-verify` | Consolidated report |
| Status | `rh-mod-status` | Next step from tracking |

## Guiding principle

> All deterministic work in `rh-mod-skills` CLI commands. All reasoning in SKILL.md.

The unit of work is a **model**, not a topic. Mapping workbooks are out of scope.
