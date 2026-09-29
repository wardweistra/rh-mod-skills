# Research: rh-mod-verify

**Date**: 2026-09-29

## 1. Command shape

**Decision**: Top-level `rh-mod-skills verify [model]`, same optional argument as `status`. Not `verify plan|approve|implement`.

**Rationale**: 001 FR-013 excepts read-only coordinators. Nested `ingest verify` stays the stage owner.

## 2. How to invoke stages

**Decision**: `click.testing.CliRunner().invoke(<group>, ["verify", model])` in-process so env (`RH_REPO_ROOT`, etc.) is shared.

**Rationale**: Avoids subprocess PATH issues; stage verify_cmd functions are not a stable import API (name clash).

## 3. Skip vs fail

**Decision**: Skip specify without `logical-model.yaml`; skip formalize without snapshot or StructureDefinition JSON; skip extract without extract plan; skip ingest without sources; skip annotate without inventory.

**Rationale**: Mid-lifecycle must not fail for later artifacts.

## 4. `validated` event

**Decision**: Do not append it.

**Rationale**: Verify must not advance lifecycle; status next remains `verify`.
