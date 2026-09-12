# CLI Contracts: RH Mod Skills Framework (implementation slice)

**Phase**: 1 — Design  
**Branch**: `001-rh-mod-framework`  
**Date**: 2026-09-11

**Entry point**: `rh-mod-skills` (`rh_mod_skills.cli:main`)

```
rh-mod-skills <command> [arguments] [flags]
```

Global: `--help` / `-h` on the group and every command. Existing `version` is unchanged.

This slice adds `init` and `status` only. No `ingest`, `extract`, `annotate`, `specify`, `formalize`, or mapping commands.

---

## `rh-mod-skills init`

Scaffold a model directory and register it in `tracking.yaml`.

```
rh-mod-skills init <model> [--title TEXT] [--description TEXT] [--author TEXT]
```

**Arguments**:
- `<model>` (required): kebab-case id (`^[a-z][a-z0-9-]*$`)

**Flags**:
- `--title`: display name (default: title-cased id)
- `--description`: short purpose (default: `"A source data model"`)
- `--author`: person or team (default: `git config user.name`, else `unknown`)

**Durable writes** (canonical owner of these paths):
- `<consumer-root>/tracking.yaml` — create skeleton if missing; append model entry; append `model_created`
- `models/<model>/` tree: `sources/`, `structured/`, `computable/`, `process/plans/`
- `models/<model>/MODEL.md`
- `models/<model>/process/notes.md`

**Stdout** (human):
```
✓ Initialized model: nkr-breast
  Location: .../models/nkr-breast
  Tracking: .../tracking.yaml
```

**Exit codes**:
- `0`: created
- `1`: model already registered, invalid name, or refused tool-repo cwd
- `2`: usage error

**Must not**:
- Copy L1 files into `sources/`
- Emit `source_added`
- Create `topics/`
- Follow plan → implement → verify (scaffolding; see research §4)

---

## `rh-mod-skills status`

Read-only report of model lifecycle from `tracking.yaml` and artifact presence.

```
rh-mod-skills status [<model>]
```

**Arguments**:
- `<model>` (optional): if omitted, list every model

**Durable writes**: none. MUST NOT append events.

**Stdout** (single model, after init, no sources):
```
Model: nkr-breast
Title: NKR breast cancer data dictionary
Stage: initialized
Sources: 0
Next: ingest
```

**Stdout** (all models): one row per model (`name`, `stage`, `next`).

**Stage derivation (001)**:
- `initialized` — `model_created` present, no `source_added`
- later stages are out of slice; if unknown future events appear, still do not suggest mapping

**Exit codes**:
- `0`: reported
- `1`: no `tracking.yaml`, or named model not found

---

## Out of contract (must not exist after this slice)

| Command | Owner |
|---------|--------|
| `ingest *` | 002 |
| `extract *`, `annotate *`, `specify *`, `formalize *` | later specs |
| `structuremap`, mapping workbook, FML | never (rh-map-skills) |
