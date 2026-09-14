# Research: extract column roles

**Date**: 2026-09-14

## 1. Roles on the plan, not a growing synonym table

**Decision**: `extract-plan.yaml` includes `sheets[].columns[]` with `header`, `role`, and `origin` (`hint` | `reviewer`). Synonym tuples remain a hint used only when a sheet has no saved roles or when `extract plan --rehint` is passed.

**Rationale**: English NKR and NBCA already forced hint-list growth. The next registry should be a plan edit.

**Alternatives considered**: Keep extending `ID_HEADERS` (rejected — product encodes every codebook). Fuzzy/prefix matching (rejected — silent mis-assignment). New `extract role` CLI (rejected — principle V; 003 already edits plan YAML).

## 2. Re-run plan after remap; implement still copies the plan

**Decision**: After the reviewer changes roles, they run `extract plan` again. Implement does not re-scan projections with roles. That keeps 003’s “approved plan is the only inventory input”.

**Rationale**: Silent re-merge on implement would restore dropped rows unless we re-implement 003 merge logic twice.

**Alternatives considered**: Implement derives inventory from projections + roles (rejected — duplicates 003 and risks undoing drops).

## 3. Preserve decisions by provenance

**Decision**: On re-plan, copy element `decision`/`reason` by `(source, sheet, row)`. Copy entity `title`/`decision`/`merge_into`/`reason` when the derived entity id still exists.

**Rationale**: Role tweaks must not clear a privacy drop. Category remaps that change entity ids are an honest rebuild.

**Alternatives considered**: Never preserve (too destructive). Preserve renamed entity ids via a stable key (extra schema; not needed for P1).

## 4. Duplicate exclusive roles fail at implement

**Decision**: Draft plan records `conflicts` of type `duplicate-role`. Proposal uses first column per role so the reviewer can still see a draft. Implement fails until duplicates are cleared.

**Rationale**: Fail closed on ambiguity; still allow a readable draft.

**Alternatives considered**: Fail plan immediately (harder to show the problem). First-wins with no conflict (silent).
