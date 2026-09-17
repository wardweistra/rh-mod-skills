# Research: ingest and status skills

**Date**: 2026-09-17

## 1. Skills only; CLI already exists

**Decision**: 007 authors curated skills. Do not add ingest/status subcommands.

**Rationale**: 002/004/001 already own the write and read contracts. Principle V.

**Alternatives considered**: Status `check-changes` like rh-skills (rejected — ingest verify already reports drift).

## 2. Opposite of rh-inf-ingest

**Decision**: `rh-mod-ingest` never normalizes to Markdown, never infers a topic, never classifies evidence. It registers files onto an already-initialized **model** and reviews PDF table include/exclude.

**Rationale**: Constitution forbids Markdown-only L1. Unit of work is a model, not a topic.

**Alternatives considered**: Port rh-inf-ingest steps 1–5 (rejected — wrong product).

## 3. Status maps Next to a skill name

**Decision**: Present `rh-mod-skills status` output as-is. At most one sentence: `ingest` → `rh-mod-ingest`, `extract` → `rh-mod-extract`, `annotate` → `rh-mod-annotate`, `specify`/`formalize` → not built yet, `init` → `rh-mod-skills init`.

**Rationale**: Same contract as `rh-inf-status` (no second menu). CLI remains source of truth for next.

**Alternatives considered**: Skill recomputes stage from files (rejected — would diverge from `status.py`).

## 4. Full skill packs for these two only

**Decision**: Each new skill gets `SKILL.md`, `reference.md`, and `examples/`. Do not backfill extract/annotate in this spec.

**Rationale**: Constitution delivery constraint. User scoped backfill out.

**Alternatives considered**: SKILL.md-only to match extract/annotate (rejected — would deepen the gap).

## 5. Init stays outside ingest

**Decision**: Missing tracking or missing model → status (or a one-line ingest pre-check) tells the user to `init`. Ingest skill does not call `init` to invent a model id.

**Rationale**: Init is scaffolding (001), not a gated ingest write.
